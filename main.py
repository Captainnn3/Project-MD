# main.py
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, tool
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain.memory import ConversationBufferMemory
import re   # import ครั้งเดียวพอ
from dotenv import load_dotenv

load_dotenv()
# ---- DATA ------------------------------------------------------------------
loader = CSVLoader(file_path="products-100.csv", encoding="utf-8")
docs = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50) \
       .split_documents(loader.load())

retriever = FAISS.from_documents(
    docs, OpenAIEmbeddings()
).as_retriever()

# ---- TOOLS -----------------------------------------------------------------
@tool
def price_products(question: str) -> str:
    """ตอบราคาสินค้าที่ถาม"""
    m = re.search(r"([\w\s]+)\s*(?:มีราคา|ราคาเท่าไหร่|ราคา|คืออะไร)", question)
    keyword = (m.group(1) if m else question).strip()

    hits, out = retriever.invoke(question), []
    for d in hits:
        if keyword.lower() in d.page_content.lower():
            price = re.search(r"Price:\s*(\d+)", d.page_content)
            curr  = re.search(r"Currency:\s*(\w+)", d.page_content)
            name  = re.search(r"Name:\s*([^,\n]+)", d.page_content)
            out.append(f"{name.group(1)} มีราคา {price.group(1)} {curr.group(1)}")
    return "\n".join(out) if out else "ไม่พบข้อมูลที่เกี่ยวข้อง"

@tool
def list_products(question: str) -> str:
    """ค้นหาสินค้าทั้งหมดที่มี keyword ตามคำถาม เช่น 'Wireless มีอะไรบ้าง'"""
    import re
    m = re.search(r"(?:สินค้า)?\s*([\w\s]+)\s*มีอะไรบ้าง|([\w\s]+)\s*อะไรบ้าง", question)
    if m and (m.group(1) or m.group(2)):
        keyword = (m.group(1) or m.group(2)).strip()
    else:
        keyword = question.strip()
    docs = retriever.invoke(question)
    results = []
    for doc in docs:
        if keyword.lower() in doc.page_content.lower():
            m_name = re.search(r"Name: ([^,\n]+)", doc.page_content)
            name = m_name.group(1) if m_name else keyword
            results.append(name)
    if results:
        return "พบสินค้า: " + ", ".join(results)
    return "ไม่พบข้อมูลที่เกี่ยวข้อง"

@tool
def other_csv(question: str) -> str:
    """ตอบคำถามทั่วไป"""
    return llm.invoke(question).content

tools = [price_products, list_products, other_csv]

# ---- AGENT -----------------------------------------------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(
    tools, llm, agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True, memory=memory
)

# ---- API -------------------------------------------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # เปิดหมด
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # รวมประวัติกับคำถามล่าสุด โดยระบุว่าใครพูด
    full_conversation = ""
    for msg in req.history:
        if msg["sender"] == "user":
            full_conversation += f"User: {msg['text']}\n"
        else:
            full_conversation += f"AI: {msg['text']}\n"
    
    # เพิ่มคำถามล่าสุด
    full_conversation += f"User: {req.question}\n"
    
    # ส่งไปให้ agent เลือกใช้ tools เอง
    response = agent.invoke({"input": full_conversation})
    return {"response": response["output"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
