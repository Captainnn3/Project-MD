# seed.py — Many-to-Many Courses ↔ Facilitators
from bson import ObjectId
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["minddojo"]

courses_collection = db["courses"]
facilitators_collection = db["facilitators"]

courses_collection.delete_many({})
facilitators_collection.delete_many({})

# ====== Courses ======
courses = [
    {
          "_id": "c1",
          "title": "Design Thinking", 
          "family": "Innovation & Design Thinking", 
          "description": "หลักสูตร Experience Design Thinking มุ่งเน้นให้ผู้เข้าร่วมเรียนรู้กระบวนการ Design Thinking แบบครบวงจร ตั้งแต่การระบุปัญหา → เข้าใจผู้ใช้งาน → สร้างแนวคิด → พัฒนาต้นแบบ → ทดสอบและรับ feedback พร้อมปรับปรุง ช่วยให้ทีมสามารถคิดเชิงนวัตกรรมและนำไอเดียไปใช้จริงได้ โดยผ่านกิจกรรมทำงานเป็นทีม การแลกเปลี่ยนมุมมอง และการทดลองใช้งานจริง",
          "type": "Workshop",
          "objectives": [
               "เข้าใจหลักการและกระบวนการของ Design Thinking",
               "ฝึกการเข้าใจผู้ใช้ผ่าน Empathy และสร้างแนวคิดเชิงนวัตกรรม",
               "เสริมการทำงานร่วมกันและการแก้ปัญหาเชิงสร้างสรรค์"
          ],
          "duration": "1 วัน",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f1","f2","f7"]
     },

     {
         "_id": "c2",
          "title": "Innovation Design Sprint (2 days)", 
          "family": "Innovation & Design Thinking", 
          "description": "เวิร์กช็อป 2 วัน ที่นำแนวทาง Design Thinking มาประยุกต์ใช้เพื่อช่วยทีมองค์กรเปลี่ยนไอเดียเป็นต้นแบบได้อย่างรวดเร็ว โดยเริ่มจากการเข้าใจปัญหาและผู้ใช้, ระดมแนวคิด, สร้างต้นแบบ, ทดสอบ และปรับปรุงตาม feedback พร้อมส่งเสริมการทำงานร่วมกันข้ามสายงาน ลด silo ภายในองค์กร และเพิ่มประสิทธิภาพการตัดสินใจ",
          "type": "Workshop",
          "objectives": [
               "แปลงแนวคิดให้เป็นต้นแบบ และพิสูจน์แนวคิด (POC)",
               "เสริมการทำงานร่วมกันแบบข้ามสายงานภายในองค์กร",
               "ปรับปรุงกระบวนการให้มีประสิทธิภาพและลดความซ้ำซ้อน"
          ],
          "duration": "2 วัน",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f1"]
     },

     {
         "_id": "c3",
          "title": "Hackathon",
          "family": "Innovation & Design Thinking",
          "description": "เวิร์กช็อป 3 วัน ที่เน้นให้ทีมองค์กรทำงานร่วมกันเพื่อสร้างนวัตกรรมจริง ผ่านกระบวนการ Design Thinking + Lean Startup ตั้งแต่การวิเคราะห์ปัญหา → ระดมแนวคิด → สร้างต้นแบบ → ทดลอง → ปรับปรุง → นำเสนอผลงานต่อผู้บริหาร พร้อมใช้แนวคิด MVP และ feedback loop เพื่อสนับสนุนการตัดสินใจลงทุนในนวัตกรรม",
          "type": "Workshop",
          "objectives": [
               "ฝึกการระดมแนวคิดและสร้างต้นแบบที่จับต้องได้ (Prototype)",
               "เรียนรู้การทดสอบสมมติฐานและรับ feedback จากผู้ใช้จริง",
               "สร้างนวัตกรรมที่สามารถนำเสนอให้ผู้บริหารใช้งานได้จริง"
          ],
          "duration": "3 วัน",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f1"]
     },

     {
          "_id": "c4",
          "title": "Practical Strategy", 
          "family": "Strategic Development", 
          "description": "เวิร์กช็อปเชิงกลยุทธ์ที่มุ่งให้ผู้เข้าร่วมวิเคราะห์ตลาด คู่แข่ง และแนวโน้มอุตสาหกรรม เพื่อสร้างกลยุทธ์ที่ใช้ได้จริงในองค์กร เสริมการตัดสินใจด้วยข้อมูล เพิ่มประสิทธิภาพในการใช้ทรัพยากร และสนับสนุนการเติบโตอย่างยั่งยืน",
          "objectives": [
               "ใช้เครื่องมือวิเคราะห์ตลาด คู่แข่ง และแนวโน้มอุตสาหกรรมเพื่อหาข้อมูลเชิงกลยุทธ์",
               "ประยุกต์ใช้เครื่องมือกลยุทธ์เพื่อสร้างแผนกลยุทธ์ที่ปฏิบัติได้",
               "เสริมทักษะการตัดสินใจเชิงกลยุทธ์และปรับตัวต่อการเปลี่ยนแปลง"
          ],
          "duration": "1 วัน",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": []
     },

     {
          "_id": "c5",
          "title": "Aligning Strategy", 
          "family": "Strategic Development", 
          "description": "เวิร์กช็อปที่มุ่งให้กลยุทธ์ต่าง ๆ ขององค์กรสอดคล้องกันอย่างเป็นระบบ เพื่อให้ทุกส่วนขององค์กรทำงานร่วมกันอย่างประสานสอดคล้อง ช่วยลดความซ้ำซ้อน เพิ่มประสิทธิภาพการดำเนินงาน และสนับสนุนการปรับตัวในยุคที่มีการเปลี่ยนแปลง",
          "type": "Workshop",
          "objectives": [
               "จัดแนวกลยุทธ์ขององค์กรให้ทุกหน่วยงานสอดคล้องกับเป้าหมายกลาง",
               "เสริมความเข้าใจร่วมกันและการสื่อสารระหว่างแผนก",
               "สร้างกลยุทธ์ที่ยืดหยุ่นและตอบสนองต่อการเปลี่ยนแปลงได้อย่างมีประสิทธิภาพ"
          ],
          "duration": "1 วัน",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": []
     },

     {
          "_id": "c6",
          "title": "Psychological Safety in Action", 
          "family": "Teambuilding Curriculum", 
          "description": "หลักสูตร/เวิร์กช็อปเน้นสร้างสภาพแวดล้อมที่คนในองค์กรรู้สึกปลอดภัย “กล้าแสดงความคิดเห็น ตั้งคำถาม ยอมรับข้อผิดพลาดได้ และลองไอเดียใหม่ๆโดยไม่กลัวถูกตัดสิน” ส่งเสริมการแลกเปลี่ยนความคิดเห็นอย่างเปิดกว้าง ฝึกให้สมาชิกในทีมแสดงความเปราะบาง (vulnerability) ได้อย่างไว้ใจซึ่งกันและกัน ช่วยเพิ่มความร่วมมือแบบ cross-functional, ลดความเสี่ยงจากการปิดกั้นข้อมูล และกระตุ้นนวัตกรรมผ่านการทดลองและเรียนรู้ (fail fast, learn fast) สร้างกลุ่มคนที่กล้าเสนอความเห็นท้าทาย ตั้งคำถาม และยอมรับ feedback โดยไม่กลัว “โดนลงโทษ” ช่วยให้ทีมเปลี่ยนจากการทำงานแบบปลอดภัย (risk-averse) ไปสู่การสร้างสรรค์เชิงรุก (risk-tolerant) ที่เน้นการเรียนรู้เป็นหลัก",
          "type": "Workshop",
          "objectives": [
               "เข้าใจหลักการและความสำคัญของ Psychological Safety ในการทำงานเป็นทีม",
               "สร้างทักษะการแสดงความคิดเห็น ทดลอง และยอมรับข้อผิดพลาดได้โดยไม่กลัว",
               "เสริมความร่วมมือในทีม ลด silo และกระตุ้นนวัตกรรมผ่านการเรียนรู้"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f5"]
     },

     {
          "_id": "c7",
          "title": "Building Team with MBTI", 
          "family": "Teambuilding Curriculum", 
          "description": "หลักสูตรที่ใช้เครื่องมือ MBTI (Myers-Briggs Type Indicator) เพื่อช่วยให้ผู้เข้าร่วมเข้าใจบุคลิกลักษณะของตัวเองและผู้อื่นช่วยเปิดมุมมองเรื่อง “สไตล์การทำงาน” ว่าใครชอบคิดแบบไหน ชอบสื่อสารอย่างไร และรับมือกับความขัดแย้งอย่างไรส่งเสริมการสร้างทีมที่มีความเข้าใจซึ่งกันและกัน โดยใช้จุดแข็งบุคลิกภาพให้เกิดประสิทธิภาพสูงสุดช่วยให้การสื่อสารภายในทีมดีขึ้น ลดความเข้าใจผิด และเสริมสร้างความร่วมมือที่ดีขึ้น",
          "type": "Workshop",
          "objectives": [
               "สำรวจบุคลิกภาพของตนเองและเข้าใจประเภท MBTI",
               "เข้าใจวิธีคิด การสื่อสาร และจุดแข็งของแต่ละบุคลิกภาพ",
               "ปรับวิธีการทำงานร่วมกันให้เหมาะสมกับบุคลิกภาพในทีม"
          ],
          "duration": "1 day",
          "price": "100 ,000 บาท",
          "facilitators_ids": ["f6","f7"]
     },

     {
          "_id": "c8",
          "title": "Effective Communication", 
          "family": "Communication", 
          "description": "หลักสูตร 1 วัน ที่มุ่งเพิ่มทักษะการสื่อสารให้ชัดเจน มีพลัง และเข้าใจผู้ฟัง ฝึกทั้งการฟังเชิงลึก (Active Listening) และการส่งสารที่มีประสิทธิภาพ (verbal & non-verbal) พร้อมเทคนิค Assertive Communication และ Nonviolent Communication เพื่อสร้างบรรยากาศที่ผู้เข้าร่วมกล้าแลกเปลี่ยนความเห็น รับ feedback และลดความขัดแย้งในองค์กร",
          "type": "E-learning",
          "objectives": [
               "ปรับสไตล์การสื่อสารให้เหมาะสมกับผู้ฟัง",
               "ฝึกใช้งาน Active Listening และ Nonverbal Communication",
               "ลดความขัดแย้งในองค์กร และส่งเสริมการสื่อสารแบบเปิด"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f3","f4","f5"]
     },

     {
          "_id": "c9",
          "title": "Negotiation & Persuasion Skill", 
          "family": "Communication", 
          "description": "เวิร์กช็อป 1 วัน ที่มุ่งพัฒนาทักษะการชักจูงและการเจรจาต่อรอง ด้วยเทคนิคและกลยุทธ์ เช่น การเตรียมตัวก่อนเจรจา, การตั้งคำถาม, การจัดการอารมณ์ และ framing เพื่อให้ผู้เรียนสามารถเจรจาได้อย่างมั่นใจและมีประสิทธิภาพแม้ในสถานการณ์ที่ท้าทาย", 
          "type": "E-learning",
          "objectives": [
               "เพิ่มความมั่นใจในการชักจูงและการเจรจาต่อรอง",
               "ฝึกการจัดการข้อโต้แย้งและการสื่อสารเมื่อเกิดความขัดแย้ง",
               "พัฒนาทักษะการเตรียมตัวและวางแผนก่อนการเจรจา"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": [""]
     },

     {
          "_id": "c10",
          "title": "Growth Mindset in Practice",
          "family": "Personal Mastery",
          "description": "เวิร์กช็อปที่มุ่งสร้างทัศนคติ “Growth Mindset” ที่เน้นการเรียนรู้ การพัฒนาอย่างต่อเนื่อง และการเห็นความสามารถว่าเป็นสิ่งที่สามารถปลูกฝังได้ ไม่ใช่แค่มีมาแต่กำเนิดช่วยให้ผู้เข้าร่วมปรับมุมมองจาก “ไม่ถนัด” เป็น “ยังไม่ถนัด” และกล้าทดลองเรียนรู้จากความล้มเหลว (fail forward)มีการออกแบบกิจกรรมเชิงปฏิบัติ ที่ฝึกให้ผู้เรียนตั้งเป้าหมายพัฒนา ติดตามความก้าวหน้า และสะท้อนบทเรียนที่ได้จากการลงมือทำจริงส่งเสริมให้ผู้เข้าร่วมมีความยืดหยุ่นทางจิตใจ (resilience) ต่อการเปลี่ยนแปลงและความท้าทายในงานเหมาะสำหรับองค์กรที่ต้องการเสริมสร้างบุคลากรให้มี mindset ที่พร้อมต่อการปรับตัว เรียนรู้ และสร้างนวัตกรรมอย่างต่อเนื่อง", 
          "type": "E-learning",
          "objectives": [
               "เข้าใจความแตกต่างระหว่าง Fixed Mindset และ Growth Mindset",
               "พัฒนาทัศนคติที่ยืดหยุ่น รับมือกับอุปสรรคและความล้มเหลว",
               "นำ Growth Mindset ไปใช้สร้างวัฒนธรรมการเรียนรู้และการทำงานที่ยั่งยืน"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f3","f4"]
     },

     {
          "_id": "c11",
          "title": "Problem Solving & Decision Making", 
          "family": "Personal Mastery", 
          "description": "เวิร์กช็อปที่มุ่งพัฒนาทักษะการแก้ปัญหาและการตัดสินใจอย่างมีประสิทธิภาพในสถานการณ์จริง ผู้เข้าร่วมจะได้เรียนรู้เครื่องมือและเทคนิคเชิงระบบ (systematic frameworks) ในการระบุปัญหา วิเคราะห์สาเหตุ และออกแบบแนวทางแก้ไขที่เหมาะสม ฝึกปฏิบัติการตัดสินใจโดยอิงข้อมูลและเกณฑ์ (data-driven decision making) เพื่อลดความเสี่ยงในการเลือกแนวทางแก้ไข มุ่งสร้าง mindset ที่มี logic และความลื่นไหลในการใช้เหตุผล เพื่อช่วยให้องค์กรสามารถปรับตัวและตัดสินใจได้รวดเร็วแม้ในสถานการณ์ที่ไม่แน่นอน", 
          "type": "E-learning",
          "objectives": [
               "เข้าใจเครื่องมือและกรอบแนวทางแก้ปัญหาแบบเป็นระบบ",
               "ฝึกการตัดสินใจโดยอิงข้อมูลและเกณฑ์เพื่อเลือกแนวทางที่เหมาะสม",
               "พัฒนามุมมองที่มีตรรกะ ยืดหยุ่น และสามารถปรับตัวในสถานการณ์ที่ไม่แน่นอนได้"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f3","f4"]
     },

     {    
          "_id": "c12",
          "title": "Agile Project Management", 
          "family": "Personal Mastery", 
          "description": "หลักสูตรที่ช่วยให้ผู้เรียนเข้าใจแนวคิดและกรอบการทำงานแบบ Agile เพื่อบริหารจัดการโครงการในยุคดิจิทัลที่มีการเปลี่ยนแปลงเร็วสอนการใช้ Scrum framework และเครื่องมือ Agile เพื่อแบ่งงานเป็นรอบสั้น ๆ (sprints) พร้อมปรับตัวตาม feedback อย่างรวดเร็วเน้นการทำงานแบบทีมร่วมมือสูง มีการสื่อสารชัดเจน ตอบสนองต่อการเปลี่ยนแปลงของลูกค้าหรือสภาพแวดล้อมได้ทันทีช่วยให้องค์กรสามารถลดความเสี่ยง ลดการสูญเสียจากการวางแผนที่ตายตัว และเพิ่มโอกาสสร้างมูลค่าได้เร็วขึ้น", 
          "type": "E-learning",
          "objectives": [
               "เข้าใจหลักการและกรอบการทำงานแบบ Agile / Scrum",
               "ฝึกวิธีแบ่งงานเป็น sprints พร้อมรับ feedback และปรับปรุง",
               "สร้างทีมที่ตอบสนองได้ดีและลดความเสี่ยงในการวางแผนตายตัว"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f2",]
     },

     {
          "_id": "c13",
          "title": "Leadership Mindset", 
          "family": "Leadership", 
          "description": "หลักสูตรที่มุ่งพัฒนากรอบความคิดผู้นำ (leader’s mindset) โดยเริ่มจากการพัฒนาตัวเองภายในก่อนสู่การนำทีมและขับเคลื่อนองค์กรสู่ความสำเร็จ ใช้แนวคิดจากผู้เชี่ยวชาญ เช่น Jack Canfield เพื่อสร้างวิธีคิดที่ก้าวหน้า กล้าเปลี่ยนแปลง และมุ่งเน้น “self-leadership” ส่งเสริมความเข้าใจในบุคลิกภาพของตัวเองและทีม (เชื่อมโยงกับ MBTI หรือ Leadership Intelligence) เพื่อสร้างสไตล์การเป็นผู้นำที่มีประสิทธิภาพตามธรรมชาติของแต่ละคน ช่วยให้ผู้นำเข้าใจวิธีสร้างแรงจูงใจทีม (“inspirational leadership”) และใช้ทักษะการสื่อสารและ feedback อย่างสร้างสรรค์เพื่อยกระดับศักยภาพทีม", 
          "type": "E-learning",
          "objectives": [
               "พัฒนาทัศนคติผู้นำ (Mindset) ที่พร้อมรับการเปลี่ยนแปลง",
               "สร้างทักษะในการจูงใจสื่อสารและให้ feedback อย่างมีประสิทธิภาพ",
               "เข้าใจบุคลิกภาพของตนเองและทีมเพื่อปรับสไตล์การนำที่เหมาะสม"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f4","f6","f7"]
     },

     {
          "_id": "c14",
          "title": "Consultative Selling",
          "family": "Sale School",
          "description": "เวิร์กช็อปที่ช่วยให้ผู้ขายกล้าที่จะเสนอขายเต็มที่ พร้อมรับมือกับ “คำว่าไม่” ได้อย่างเข้มแข็งและไม่สั่นคลอนฝึกสร้าง mindset แบบ “fail forward” เปลี่ยนการถูกปฏิเสธเป็นโอกาสเรียนรู้และปรับปรุงสอนเทคนิคและกลยุทธ์การรับมือกับ rejection อย่างมีระบบ และฟื้นตัวทางอารมณ์ได้รวดเร็วเสริมสร้างความมั่นใจและยืดหยุ่นทางใจ (resilience) โดยไม่ให้การปฏิเสธมาทำลายแรงจูงใจในการขายช่วยให้ทีมขายรักษาความต่อเนื่อง (persistence) และแปลงแนวคิด “โดนปฏิเสธ” มาเป็น “ข้อมูลเพื่อลับฝีมือ” ในการขายครั้งต่อไป",
          "type": "E-learning",
          "objectives": [
               "สร้างความมั่นใจในการเสนอขายและรับการปฏิเสธ",
               "ฝึกกลยุทธ์และเทคนิคการรับมือกับ rejection อย่างมีระบบ",
               "พัฒนาความยืดหยุ่นทางอารมณ์และแปลงข้อปฏิเสธเป็นบทเรียนในการขาย"
          ],
          "duration": "1 day",
          "price": "ติดต่อฝ่ายขาย",
          "facilitators_ids": ["f5"]
     }
]

course_result = courses_collection.insert_many(courses)

# ====== Facilitators ======
facilitators = [
     {
          "_id": "f1",
          "name": "Songpathara Snidvongs",
          "nickname": "อ.จี้",
          "expertise": ["Coporate Innovation & Creativity", "Change & Transformation", "Interactive Learning Design", "Strategic Facilitation", "Gen Y & Z Leadership Skills Development"], 
          "training_style": ["Result focused", "Fun", "Simple", "Energetic"]
     },

     {
          "_id": "f2",
          "name": "นายจีรวัฒน์ เยาวนิช",
          "nickname": "อ.ต้น",
          "expertise": ["Design Thinking", "Agile Project Management", "Team Synergy for Collaboration", "People Intelligence with MBTI"], 
          "workshop" : ["Design Thinking Workshop","Driving Innovation for Leader", "Agile Project Management", "Team Synergy for Collaboration", "People Intelligence with MBTI"],
          "training_style": ["สนุกสนาน", "เรียบง่าย", "มีพลัง"]
     },

     {
          "_id": "f3",
          "name": "นายวีรวัฒน์ พากเพียรกิจ", 
          "nickname": "อ.ปีโป้",
          "expertise": ["Communication", "Growth Mindset","Working Performance Team","Problem solving and decision making","Innovation and Design Thinking"], 
          "workshop" : ["Growth Mindset","Situational Leadership","Problem Solving and Decision Making","Train the Professional Trainer","Effective Communication"],
          "training_style": ["มีพลัง กระตือรือร้น", "เรียบง่าย เข้าใจง่าย", "โฟกัสเป้าหมายที่ชัดเจน", "สนุกสนาน"]
     },

     {
          "_id": "f4",
          "name": "นายบรรพต บุญธรรม", 
          "nickname": "อ.ปิง",
          "expertise": ["Design Thinking","Strategic Thinking","Storytelling","Presentation Design"],
          "workshop" : ["Growth Mindset","Situational Leadership","Problem Solving and Decision Making","Train the Professional Trainer","Effective Communication"],
          "training_style": ["เน้นกิจกรรม", "มีปฏิสัมพันธ์", "เรียบง่าย", "เข้าใจง่าย"]
     },

     {
          "_id": "f5",
          "name": "นายอุประจิตร รวมทรัพย์", 
          "nickname": "อ.มอส",
          "expertise": ["Communication", "Presentation Skills", "Learning Development","Soft Skills & Mindset"], 
          "workshop" : ["Effective Communication","Advance Presentation Skills","Train the Professional Trainer","Time Management & Effective Prioritization","Psychological Safety in Action"],
          "training_style": ["เน้นผลลัพธ์", "กระตือรือร้น มีพลัง", "เรียบง่าย เข้าใจง่าย", "สนุกสนาน"]
     },

     {
          "_id": "f6",
          "name": "นายธนโชติ มีกังวาล", 
          "nickname": "อ.โรเบิร์ต",
          "expertise": ["Team Synergy", "Leadership Psychology (MBTI, DISC)","Strategic Thinking", "Problem Solving & Decision Making"], 
          "workshop": ["Team Building & Collaboration","People Intelligence with MBTI","Leadership Bootcamp","Leading Self with MBTI","Enchancing Collaboration with MBTI"],
          "training_style": ["เรียนรู้ผ่านกิจกรรม", "โต้ตอบแบบมีส่วนร่วม", "สนุกสนาน มีพลัง"]
     },

     {
          "_id": "f7",
          "name": "นางสาวนฤมล ล้อมคง", 
          "nickname": "อ.เฟิร์น",
          "expertise": ["Design Thinking for business", "Project Management","Service Excellence","Communication"],
          "workshop" : ["Design Thinking Workshop","Project Management 101", "Service Design & Mindset", "Stakeholder Management 101", "Team Building & Collaboration"],
          "training_style": ["สร้างความสัมพันธ์", "เข้ากับคนง่าย", "เห็นความแตกต่าง", "เข้าใจคน", "เปิดใจรับคนอื่น"]
     }
]

fac_result = facilitators_collection.insert_many(facilitators)

print("✅ Seed สำเร็จ: Courses และ Facilitators ผูกกันแบบ Many-to-Many แล้ว")
