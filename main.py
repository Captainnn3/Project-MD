# main.py — FastAPI + LangChain (MindDoJo AI Agent สำหรับฝ่ายขาย)
import os, asyncio, uuid
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pymongo import MongoClient

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.schema import Document, HumanMessage, SystemMessage

# -------------------- Load ENV --------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MINDDOJO_INDEX = "minddojo_courses.index"

# -------------------- Connect MongoDB --------------------
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["minddojo"]
courses_collection = db["courses"]
facilitators_collection = db["facilitators"]
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
        facilitator_ids = course.get("facilitators_ids", [])
        facs = list(facilitators_collection.find({"_id": {"$in": facilitator_ids}}))

        fac_data = [f"{f.get('_id','')}-{f.get('name','')} {f.get('nickname','')} {f.get('expertise',[])} {f.get('training_style',[])}" for f in facs]

        text = (
            f"[COURSE DATA]\n"
            f"Course Title (EN): {course.get('title','')}\n"
            f"Description (TH): {course.get('description','')}\n"
            f"Objectives (TH): {'; '.join(course.get('objectives', []))}\n"
            f"Duration: {course.get('duration','')}\n"
            f"Price: {course.get('price','')}\n"
            f"Facilitators: {', '.join(fac_data)}\n"
        )
        documents.append(Document(page_content=text, metadata={"facilitators_ids": facilitator_ids}))

    # สร้าง FAISS
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    faiss_store = FAISS.from_documents(docs, EMB)
    faiss_store.save_local(MINDDOJO_INDEX)
    retriever_minddojo = faiss_store.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": 4}
    )

# -------------------- LLM Context --------------------
def build_context(question: str, k: int = 4) -> str:
    docs = retriever_minddojo.invoke(question)
    ctx=[]
    for d in docs :
        if d.metadata.get("type") == "course":
            ctx.append(f"[COURSE DATA]\n{d.page_content}")
        elif d.metadata.get("type") == "facilitator": 
            ctx.append(f"[FACILITATOR DATA]\n{d.page_content}")
    return "\n\n".join(ctx[:k])

SYSTEM_INSTRUCT = """คุณคือ AI ผู้ช่วยฝ่ายขายของบริษัท MindDoJo  

### กฎสำคัญ:
1. คุณต้องใช้ข้อมูลจากฐานข้อมูล MindDoJo ที่ให้มาเท่านั้น  
   - ฐานข้อมูลมี 2 ส่วน: [COURSE DATA], [FACILITATOR DATA]  
   - ห้ามใช้ความรู้ภายนอกหรือเดาข้อมูลเอง  
2. หากข้อมูลที่ลูกค้าต้องการ **ไม่มีในฐานข้อมูล** ให้ตอบว่า:  
   "กรุณาติดต่อฝ่ายขายเพิ่มเติม"  
3. **ห้ามสร้างชื่อคอร์สใหม่** โดยอิงจาก description/objectives  
   - ต้องใช้ "Course Title (EN)" ตรงจากฐานข้อมูลเท่านั้น  
4. **ห้ามรวมคอร์สเข้าด้วยกัน** เช่น การสร้างคอร์สใหม่จากหลายคอร์ส 
5. **ห้ามเพิ่มรายชื่อ Facilitator อื่นที่ไม่ได้อยู่ในคอร์สนั้น**
6. **ห้ามแปลชื่อคอร์ส (Course Title)** หรือ **ชื่อวิทยากร (Name, Nickname)** เป็นภาษาอื่น  
   - ต้องใช้ตรงตามที่อยู่ในฐานข้อมูล
7. ถ้าเจอ document หลายอันที่คล้ายกัน ให้เลือกอันที่ตรงกับคำถามที่สุด
8. ส่วนข้อมูลอื่น เช่น **Description, Objectives, Expertise** สามารถอธิบายเป็นภาษาไทยได้ และสามารถอธิบายเพิ่มเติมได้ตามความเหมาะสม

---

### วิธีการตอบ:
1. **ถามถึงคอร์ส (Course)**  
   - แสดงข้อมูลดังนี้:  
     - Course Title (EN)  
     - Description (TH)  
     - Objectives (TH)  
     - Duration  
     - Price  
     - รายชื่อ Facilitators (ใช้ Name/Nickname ตรงจากฐานข้อมูล)  
   - ถ้าไม่มี Facilitators ให้ระบุว่า "กรุณาติดต่อฝ่ายขายเพิ่มเติม"  

2. **ถามถึงวิทยากร (Facilitator)**  
   - แสดงข้อมูลดังนี้:  
     - Name/Nickname  
     - Expertise (TH)  
     - Training Style (TH/EN ตามฐานข้อมูล)  
     - รายชื่อ Course Title (EN) ที่วิทยากรสอน  

3. **ถามถึงปัญหา (Problem Scenario)**  
   - วิเคราะห์ปัญหาจากคำถามของลูกค้า  
   - อ่าน description และ objectives ของทุกคอร์สในฐานข้อมูล  
   - เลือกคอร์สที่มีความเกี่ยวข้องกับปัญหาของคำถามมากที่สุด (สูงสุด 2 คอร์ส)  
   - แสดงผลดังนี้:  
     - Course Title (EN)  
     - เหตุผลสั้น ๆ (TH) ว่าทำไมคอร์สนี้แก้ปัญหาที่เล่าได้  

---

### ตัวอย่างการตอบ:

**Q:** "หลักสูตร Design Thinking มีอะไรบ้าง?"  
**A:**  
หลักสูตร **Design Thinking**  
- คำอธิบาย: อ่านจาก Description ในฐานข้อมูล และอธิบายเพิ่มเติมตามความเหมาะสม
- วัตถุประสงค์: เข้าใจกระบวนการ Design Thinking, สามารถสร้างต้นแบบ, ทำงานร่วมกันเชิงสร้างสรรค์  
- Duration: 1 day  
- Price: ติดต่อฝ่ายขาย  
- วิทยากร: ดร. สมชาย ใจดี, ชื่อเล่น (Expertise: Innovation, Training Style: Interactive) ***ถ้าหากมีวิทยากรมากกว่า1คนให้แสดงทั้งหมด*** 

---

**Q:** "วิทยากร สมชาย สอนคอร์สอะไรบ้าง?"  
**A:**  
วิทยากร: ดร. สมชาย ใจดี (สมชาย)  
- Expertise: Innovation, Leadership  
- Training Style: Friendly, Interactive  
- Courses: Design Thinking, Innovation Design Sprint  

---

**Q:** "คนในองค์กรมีความขัดแย้งกันบ่อย ควรทำอย่างไร?"  
**A:**  
จากปัญหาที่เล่า แนะนำคอร์ส:  
- **Psychological Safety in Action** → เน้นสร้างบรรยากาศทีมที่ปลอดภัยในการแสดงความคิดเห็น ลดการทะเลาะและความขัดแย้ง  
- **Effective Communication** → ช่วยพัฒนาทักษะการฟังและการสื่อสาร ลดความเข้าใจผิดภายในทีม  

"""


# -------------------- FastAPI --------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
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

        # --- ใช้ LLM + RAG ---
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
            )
        ]
        handler = AsyncIteratorCallbackHandler()
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, streaming=True)
        task = asyncio.create_task(llm.ainvoke(prompt, config={"callbacks": [handler]}))

        final_answer = ""
        async for token in handler.aiter():
            final_answer += token
            yield token
        await task

        # --- เก็บ history ลง MongoDB ---
        chat_collection.update_one(
            {"session_id": req.session_id},
            {"$push": {"messages": {"sender": "user", "text": q}}},
            upsert=True
        )
        chat_collection.update_one(
            {"session_id": req.session_id},
            {"$push": {"messages": {"sender": "ai", "text": final_answer}}},
            upsert=True
        )

    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8")

# -------------------- Endpoint ดึงประวัติ --------------------
@app.get("/history/{session_id}")
def get_history(session_id: str):
    doc = chat_collection.find_one({"session_id": session_id})
    return doc or {"session_id": session_id, "messages": []}

# -------------------- Run --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
