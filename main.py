# ...existing code...
import os, asyncio, uuid, re
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pymongo import MongoClient

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.agents import initialize_agent, AgentType, tool
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.schema import Document, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory

# -------------------- Load ENV --------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MINDDOJO_INDEX = "minddojo_courses.index"

# -------------------- Connect MongoDB --------------------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["minddojo"]
courses_collection = db["courses"]
chat_collection = db["chat_sessions"]

# -------------------- Build / Load Retriever --------------------

EMB = OpenAIEmbeddings()

if os.path.exists(MINDDOJO_INDEX):
    retriever_minddojo = FAISS.load_local(
        MINDDOJO_INDEX, EMB, allow_dangerous_deserialization=True
    ).as_retriever()
else:
    courses = list(courses_collection.find({}))
    documents = []

    # รวมข้อมูลคอร์ส + วิทยากร
    for course in courses:
        fac_names = course.get("facilitators", [])
        fac_display = ", ".join(fac_names) if fac_names else "None"
        text = (
            f"[COURSE DATA]\n"
            f"Course Title (EN): {course.get('title','')}\n"
            f"Description (TH): {course.get('description','')}\n"
            f"Objectives (TH): {'; '.join(course.get('objectives', []))}\n"
            f"Duration: {course.get('duration','')}\n"
            f"Price: {course.get('price','')}\n"
            f"Facilitators: {', '.join(fac_names)}\n"
        )
        documents.append(Document(page_content=text, metadata={"type": "course", "id": str(course["_id"])}))

    # สร้าง FAISS
    faiss_store = FAISS.from_documents(documents, EMB)
    faiss_store.save_local(MINDDOJO_INDEX)
    retriever_minddojo = faiss_store.as_retriever(search_type="similarity", search_kwargs={"k":4})

@tool
def recommend_courses(q: str) -> str:
    """แนะนำหลักสูตรตามสถานการณ์ เช่น ปัญหาในองค์กร"""
    if re.search(r"(ทะเลาะ|ขัดแย้ง|ทำงานไม่เป็นทีม|บรรยากาศไม่ดี|ปัญหาในองค์กร)", q):
        return (
            "จากประสบการณ์ของ MindDoJo แนะนำหลักสูตร:\n"
            "- **Psychological Safety in Action** → เพื่อสร้างบรรยากาศทีมที่ปลอดภัยในการแสดงความคิดเห็น ลดความขัดแย้งภายในองค์กร\n"
            "- **Effective Communication** → เพื่อพัฒนาทักษะการฟังและสื่อสารเชิงบวก สร้างความเข้าใจและความร่วมมือในทีม"
        )
    
    elif re.search(r"(ผู้นำ|ภาวะผู้นำ)", q):
        return (
            "จากประสบการณ์ของ MindDoJo แนะนำหลักสูตร:\n"
            "- **Leadership Mindset** → เพื่อเสริมภาวะผู้นำและการบริหารทีมอย่างมีประสิทธิภาพ\n"
            "- **Psychological Safety in Action** → เพื่อสร้างความไว้วางใจและบรรยากาศที่เอื้อต่อการนำทีม"
        )
    
    elif re.search(r"(นวัตกรรม|ไอเดีย)", q):
        return ( "หลักสูตร **Design Thinking**\n"
        "- คำอธิบาย: หลักสูตรนี้เน้นการพัฒนาทักษะการคิดเชิงออกแบบ (Design Thinking)"
        "ซึ่งเป็นกระบวนการที่ช่วยให้ผู้เรียนสามารถแก้ไขปัญหาอย่างสร้างสรรค์และมีประสิทธิภาพ\n"
        "- วัตถุประสงค์: เข้าใจกระบวนการ Design Thinking, สร้างต้นแบบ, ทำงานร่วมกันเชิงสร้างสรรค์\n"
        "- ระยะเวลา: 1 day\n"
        "- ราคา: ฝ่ายขาย\n"
        "- วิทยากร: Songpathara Snidvongs (อ.จี้), นายจีรวัฒน์ เยาวนิช (อ.ต้น), นางสาวนฤมล ล้อมคง (อ.เฟิร์น)"
        )
    return None

tools = [recommend_courses]

# -------------------- Memory+Agent Setup --------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, streaming=True)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, memory=memory, verbose=False)

# -------------------- LLM Context --------------------
def build_context(question: str, k: int = 4) -> str:
    docs = retriever_minddojo.invoke(question)
    ctx = []

    for d in docs:
        if d.metadata.get("type") == "course":
            ctx.append(f"[COURSE DATA]\n{d.page_content}")

    return "\n\n".join(ctx[:k])

SYSTEM_INSTRUCT = """คุณคือ AI ผู้ช่วยฝ่ายขายของบริษัท MindDoJo คุณต้องให้คำตอบกับฝ่ายขายเพื่อตอบสนองความต้องการของลูกค้าเกี่ยวกับคอร์สฝึกอบรมต่าง ๆ ของบริษัท โดยใช้ข้อมูลจากฐานข้อมูลที่มีอยู่เท่านั้น เพื่อให้ฝ่ายขายไปเสนอขายลูกค้าต่อ 

### กฎสำคัญ: 
# 1. คุณต้องใช้ข้อมูลจากฐานข้อมูล MindDoJo ที่ให้มาเท่านั้น - ฐานข้อมูลมี [COURSE DATA] - ห้ามใช้ความรู้ภายนอกหรือเดาข้อมูลเอง 
# 2. หากข้อมูลที่ลูกค้าต้องการ **ไม่มีในฐานข้อมูล** ให้ตอบว่า: "ไม่พบข้อมูล กรุณาติดต่อฝ่ายพัฒนาเพิ่มเติม" 
# 3. **ห้ามสร้างชื่อคอร์สใหม่** โดยอิงจาก description/objectives - ต้องใช้ "Course Title (EN)" ตรงจากฐานข้อมูลเท่านั้น 
# 4. **ห้ามรวมคอร์สเข้าด้วยกัน** เช่น การสร้างคอร์สใหม่จากหลายคอร์ส 
# 5. **ห้ามเพิ่มรายชื่อ Facilitator อื่นที่ไม่ได้อยู่ในคอร์สนั้น** 
# 6. **ห้ามแปลชื่อคอร์ส (Course Title)** หรือ **ชื่อวิทยากร (Name, Nickname)** เป็นภาษาอื่น - ต้องใช้ตรงตามที่อยู่ในฐานข้อมูล 
# 7. ถ้าเจอ document หลายอันที่คล้ายกัน ให้เลือกอันที่ตรงกับคำถามที่สุด 
# 8. ส่วนข้อมูลอื่น เช่น **Description, Objectives, Expertise** สามารถอธิบายเป็นภาษาไทยได้ และสามารถอธิบายเพิ่มเติมได้ตามความเหมาะสม --- 
# 9. ในส่วนของ Description และ Objectives ให้สรุปมาตอบ
### วิธีการตอบ: 
# 1. **ถามถึงคอร์ส (Course)** 
    - แสดงข้อมูลดังนี้: 
    - Course Title (EN): 
    - Description (TH): 
    - Objectives (TH): 
    - Duration: 
    - Price: 
    - รายชื่อ Facilitators (ใช้ Name/Nickname ตรงจากฐานข้อมูล) 

# 2. **ถามถึงปัญหา (Problem Scenario)** 
    - วิเคราะห์ปัญหาจากคำถามของลูกค้า 
    - อ่าน description และ objectives ของทุกคอร์สในฐานข้อมูล 
    - เลือกคอร์สที่มีความเกี่ยวข้องกับปัญหาของคำถามมากที่สุด (สูงสุด 2 คอร์ส) 
    - แสดงผลดังนี้: 
    - Course Title (EN) 
    - เหตุผลสั้น ๆ (TH) ว่าทำไมคอร์สนี้แก้ปัญหาที่เล่าได้ 

--- 

### ตัวอย่างการตอบ: 
**Q:** "หลักสูตร Design Thinking มีอะไรบ้าง?" 
**A:** หลักสูตร **Design Thinking** 
    - คำอธิบาย: อ่านจาก Description ในฐานข้อมูล และอธิบายเพิ่มเติมตามความเหมาะสม 
    - วัตถุประสงค์: เข้าใจกระบวนการ Design Thinking, สามารถสร้างต้นแบบ, ทำงานร่วมกันเชิงสร้างสรรค์ 
    - ระยะเวลา: 1 day 
    - ราคา: ติดต่อฝ่ายขาย 
    - วิทยากร: ดร. สมชาย ใจดี, ชื่อเล่น
***ถ้าหากมีวิทยากรมากกว่า1คนให้แสดงทั้งหมด*** 

--- 

**Q:** "คนในองค์กรมีความขัดแย้งกันบ่อย ควรทำอย่างไร?" 
**A:** จากปัญหาที่เล่า แนะนำคอร์ส: 
    - **Psychological Safety in Action** → เน้นสร้างบรรยากาศทีมที่ปลอดภัยในการแสดงความคิดเห็น ลดการทะเลาะและความขัดแย้ง 
    - **Effective Communication** → ช่วยพัฒนาทักษะการฟังและการสื่อสาร ลดความเข้าใจผิดภายในทีม 

"""

# -------------------- FastAPI --------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str | None = None
    question: str

@app.post("/chat-stream")
async def chat_stream(req: ChatRequest):
    if not req.session_id:
        req.session_id = str(uuid.uuid4())

    past_chat = chat_collection.find_one({"session_id": req.session_id})
    history_msgs = past_chat.get("messages", []) if past_chat else []

    async def gen():
        q = req.question.strip()
        # ---TOOLS---
        tool_answer = recommend_courses(q)
        if tool_answer:
            for ch in tool_answer:
                yield ch
                await asyncio.sleep(0.01)
            _save_chat(req.session_id, q, tool_answer)
            return
        
        # --- RAG context ---
        ctx = build_context(q)
        history_text = "\n".join(
            f"ผู้ใช้: {m['text']}" if m['sender'] == "user" else f"AI: {m['text']}"
            for m in history_msgs
        )

        prompt = [
            SystemMessage(content=SYSTEM_INSTRUCT),
            HumanMessage(
                content=(
                    f"ประวัติการสนทนา:\n{history_text}\n\n"
                    f"ข้อมูลจากฐานข้อมูล:\n{ctx}\n\n"
                    f"คำถาม:\n{q}\n\nคำตอบ:"
                )
            ),
        ]

        handler = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, streaming=True)
        task = asyncio.create_task(llm.ainvoke(prompt, config={"callbacks": [handler]}))

        final_answer = ""
        async for token in handler.aiter():
            final_answer += token
            yield token
            await asyncio.sleep(0.01)
        await task

        _save_chat(req.session_id, q, final_answer)

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")

# -------------------- ฟังก์ชันช่วยเก็บประวัติ --------------------
def _save_chat(session_id: str, user_text: str, ai_text: str):
    """เก็บประวัติการสนทนาใน MongoDB"""
    chat_collection.update_one(
        {"session_id": session_id},
        {"$push": 
            {"messages": 
                {"$each":[
                    {"sender": "user", "text": user_text, "timestamp": datetime.utcnow()},

                    {"sender": "ai", "text": ai_text, "timestamp": datetime.utcnow()},
                    ]
                }
            }
        },
        upsert=True,
    )
    
# -------------------- Endpoint ดึงประวัติ --------------------
@app.get("/history/{session_id}")
def get_history(session_id: str):
    doc = chat_collection.find_one({"session_id": session_id})
    return doc or {"session_id": session_id, "messages": []}

# -------------------- Run --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# ...existing code...