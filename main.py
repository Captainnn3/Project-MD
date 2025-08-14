# main.py  — FastAPI + LangChain (stream จริง + เร็วขึ้น)
import os, re, asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler

load_dotenv()

# -------------------- Load data ONE-TIME --------------------
INDEX_DIR = "products.index"
EMB = OpenAIEmbeddings()

if os.path.exists(INDEX_DIR):
    retriever = FAISS.load_local(
        INDEX_DIR, EMB, allow_dangerous_deserialization=True
    ).as_retriever()
else:
    loader = CSVLoader(file_path="products-100.csv", encoding="utf-8")
    docs = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50) \
           .split_documents(loader.load())
    faiss_store = FAISS.from_documents(docs, EMB)
    faiss_store.save_local(INDEX_DIR)
    retriever = faiss_store.as_retriever()

# -------------------- Fast tools (no LLM, ตอบไว) --------------------
# คอมไพล์ regex ล่วงหน้าให้เร็วขึ้น
PRICE_PAT = re.compile(r"([\w\s]+?)\s*(?:มีราคา|ราคาเท่าไหร่|ราคา|คืออะไร)")
LIST_PAT  = re.compile(r"(?:สินค้า)?\s*([\w\s]+?)\s*มีอะไรบ้าง|([\w\s]+?)\s*อะไรบ้าง")

def price_products_fast(q: str) -> str | None:
    m = PRICE_PAT.search(q)
    keyword = (m.group(1) if m else "").strip()
    if not keyword:  # ไม่ใช่โจทย์ถามราคา → ไม่จับทางลัดนี้
        return None
    hits = retriever.invoke(q)
    out = []
    for d in hits:
        if keyword.lower() in d.page_content.lower():
            price = re.search(r"Price:\s*(\d+)", d.page_content)
            curr  = re.search(r"Currency:\s*(\w+)", d.page_content)
            name  = re.search(r"Name:\s*([^,\n]+)", d.page_content)
            if price and curr and name:
                out.append(f"{name.group(1)} มีราคา {price.group(1)} {curr.group(1)}")
    return "\n".join(out) if out else "ไม่พบข้อมูลที่เกี่ยวข้อง"

def list_products_fast(q: str) -> str | None:
    m = LIST_PAT.search(q)
    if not m:
        return None
    keyword = (m.group(1) or m.group(2) or "").strip()
    if not keyword:
        return None
    docs = retriever.invoke(q)
    results = []
    for doc in docs:
        if keyword.lower() in doc.page_content.lower():
            m_name = re.search(r"Name:\s*([^,\n]+)", doc.page_content)
            if m_name:
                results.append(m_name.group(1))
    return ("พบสินค้า: " + ", ".join(dict.fromkeys(results))) if results else "ไม่พบข้อมูลที่เกี่ยวข้อง"

# -------------------- LLM (stream ตรง) --------------------
def build_context(question: str, k: int = 4) -> str:
    docs = retriever.invoke(question)
    return "\n\n".join(d.page_content for d in docs[:k])

SYSTEM_INSTRUCT = (
    "คุณเป็นผู้ช่วยตอบคำถามสินค้า ให้ตอบเป็นภาษาไทย กระชับ ชัดเจน "
    "ถ้าข้อมูลในบริบทไม่เพียงพอ ให้บอกว่าไม่พบข้อมูลที่เกี่ยวข้อง"
)

# -------------------- API --------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []  # [{sender: "user"|"bot", text: "..."}]

@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    """
    ลำดับทำงาน:
    1) ทางลัดไม่ใช้ LLM → ตอบทันที (ไหลทีละตัวอักษรเพื่อ UX)
    2) ถ้าจำเป็นต้องใช้ LLM → stream โทเคนตรงจาก OpenAI
    """
    async def gen():
        q = req.question.strip()

        # 1) ลองตอบทางลัดก่อนเพื่อลด latency
        for fast_fn in (price_products_fast, list_products_fast):
            fast_ans = fast_fn(q)
            if fast_ans:  # พบคำตอบแล้ว → สตรีมทีละตัวอักษรทันที
                for ch in fast_ans:
                    yield ch
                    await asyncio.sleep(0)  # ปล่อย event loop
                return

        # 2) ใช้ LLM + RAG แบบ stream จริง
        ctx = build_context(q)
        prompt = (
            f"{SYSTEM_INSTRUCT}\n\n"
            f"ประวัติบทสนทนา (ถ้ามี):\n" +
            "\n".join(f"{'ผู้ใช้' if m.get('sender')=='user' else 'บอท'}: {m.get('text','')}"
                      for m in req.history) +
            f"\n\nบริบทที่ค้นเจอ:\n{ctx}\n\nคำถาม:\n{q}\n\nคำตอบ:"
        )

        # handler ใหม่ต่อคำขอ (ห้ามใช้ตัวเดียวทั้งแอป)
        handler = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, streaming=True)

        # สั่งให้ LLM เริ่มตอบใน background แล้วเรารอรับโทเคนจาก handler
        task = asyncio.create_task(llm.ainvoke(prompt, config={"callbacks": [handler]}))

        async for token in handler.aiter():
            # token เป็นสตริงทีละชิ้น (ไม่บัฟเฟอร์ก้อนใหญ่)
            yield token

        await task  # รอให้เรียบร้อยก่อนจบสตรีม

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")

# (Optional) endpoint sync เดิม เผื่ออยากเก็บไว้
class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
def chat_sync(req: ChatRequest):
    ans = price_products_fast(req.question) or list_products_fast(req.question)
    if not ans:
        ctx = build_context(req.question)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        prompt = f"{SYSTEM_INSTRUCT}\n\nบริบท:\n{ctx}\n\nคำถาม:\n{req.question}\n\nคำตอบ:"
        ans = llm.invoke(prompt).content
    return {"response": ans}

if __name__ == "__main__":
    import uvicorn
    # tip: workers=1 สำหรับ dev streaming จะง่ายที่สุด
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
