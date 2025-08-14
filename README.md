# Chat-AI (React + FastAPI)

แชทถาม-ตอบ

---

## คุณสมบัติ
- ถาม-ตอบข้อมูลสินค้าจากไฟล์ `products-100.csv`
- ถามทั่วไปได้ด้วย OpenAI (fallback)
- จดจำประวัติแชท สนทนาแบบมีบริบท
- UI ทันสมัยด้วย React (Vite)

---

## สิ่งที่ต้องมี
- Python 3.11 ขึ้นไป
- Node.js 18 ขึ้นไป
- OpenAI API Key

---

## โครงสร้างโปรเจค
```
main.py             # FastAPI backend
products-100.csv    # ข้อมูลสินค้า (CSV)
requirements.txt    # Python dependencies
src/                # React frontend
.env                # ใส่ OpenAI API key
```

---

## การใช้บนเครื่องด้วย Docker

1. **ติดตั้ง Docker Desktop**
   - ดาวน์โหลด: https://www.docker.com/products/docker-desktop/

2. **สร้างไฟล์ `.env`** (ใส่ OpenAI API Key)
   - ตัวอย่างเนื้อหา:
     ```
     OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
     ```

3. **ดึง image จาก Docker Hub**
   ```sh
   docker pull sarawutdev/chat-ai:latest
   ```

4. **รัน container พร้อมเชื่อม .env**
   ```sh
   docker run -d -p 8000:8000 -p 5173:5173 --env-file .env sarawutdev/chat-ai:latest
   ```
   - ถ้า .env ไม่อยู่ใน working directory ให้ระบุ path เต็ม เช่น
     `--env-file C:/Users/ADMIN/Desktop/Chat-AI/.env`

5. **เปิดใช้งาน**
   - Frontend: http://localhost:5173
   - Backend (API): http://localhost:8000

---

## Flow การทำงานของระบบ

1. **Frontend (React)**
   - ผู้ใช้พิมพ์คำถามในเว็บ (http://localhost:5173)
   - ระบบส่งคำถามและประวัติแชทไปยัง backend (API)

2. **Backend (FastAPI + LangChain)**
   - รับ request ที่ `/chat`
   - รวมประวัติแชทกับคำถามล่าสุด
   - สร้าง agent ที่มี tools (เช่น price_products, list_products, general_question)
   - agent วิเคราะห์คำถาม เลือก tool ที่เหมาะสม
   - ถามข้อมูลจาก CSV/FAISS หรือ fallback ไป LLM (OpenAI)
   - ส่งคำตอบกลับ frontend

3. **Frontend**
   - แสดงคำตอบบอทในหน้าต่างแชท
   - ผู้ใช้สามารถถามต่อได้ (history จะถูกส่งไป backend ทุกครั้ง)

---

## การใช้งาน API
- `POST /chat` ส่ง JSON `{question, history}` เพื่อถามแชทบอท

ตัวอย่าง:
```json
{
  "question": "สินค้า Wireless มีอะไรบ้าง",
  "history": [
    {"sender": "user", "text": "สวัสดี"},
    {"sender": "bot", "text": "สวัสดีค่ะ! มีอะไรให้ช่วยถามเกี่ยวกับสินค้าไหมคะ?"}
  ]
}
```

---

## หมายเหตุ
- ถามเกี่ยวกับสินค้า: ระบบจะตอบจาก CSV ก่อน ถ้าไม่พบจะใช้ AI ช่วยตอบ
- ประวัติแชทช่วยให้สนทนาต่อเนื่อง
- สามารถปรับแต่งข้อมูลใน CSV หรือ logic backend ได้ตามต้องการ

---
