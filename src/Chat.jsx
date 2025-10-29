import './styles/chat.css';
import React, { useEffect, useRef, useState, useMemo } from "react";

/** ===== Endpoints: ใช้สตรีมก่อน ถ้าไม่ได้ค่อย fallback ไป /chat ===== */
const BASE = "http://localhost:8000";
const API_STREAM = `${BASE}/chat-stream`;  // แบบสตรีม
const API_ONESHOT = `${BASE}/chat`;        // แบบตอบครั้งเดียว (fallback)

/* ====== Rich renderer: **bold**, **หัวข้อ**:, bullet -, ลำดับเลข 1., ย่อหน้า ====== */
function renderRich(src = "") {
  const esc = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // 1) escape ก่อน
  let s = esc(src);

  // 2) **bold**
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // 3) แยกเป็นบรรทัดและรวมลิสต์ให้เป็นก้อนเดียว
  const lines = s.split(/\r?\n/);
  const chunks = []; // เก็บเป็นสลับระหว่าง <ul>/<ol>/string
  let list = null;   // เก็บสถานะลิสต์ปัจจุบัน 

  const flushList = () => {
    if (!list) return;
    const tag = list.type === "ul" ? "ul" : "ol";
    chunks.push(`<${tag}>${list.items.map(x => `<li>${x}</li>`).join("")}</${tag}>`);
    list = null;
  };

  for (const raw of lines) { // ตัดบรรทัดว่าง
    const line = raw.replace(/\s+$/g, "");

    if (/^\s*$/.test(line)) {
      if (!list) chunks.push("\n");
      continue;
    }

    // bullet: - ...
    const mUl = line.match(/^\s*[-•]\s+(.*)$/);
    if (mUl) {
      if (!list || list.type !== "ul") list = { type: "ul", items: [] };
      list.items.push(mUl[1]);
      continue;
    }

    // ordered: 1. ... หรือ 1) ...
    const mOl = line.match(/^\s*(\d+)[\.\)]\s+(.*)$/);
    if (mOl) {
      if (!list || list.type !== "ol") list = { type: "ol", items: [] };
      list.items.push(mOl[2]);
      continue;
    }

    // ไม่ใช่ลิสต์ → ปิดลิสต์ก่อน แล้วเก็บเป็นข้อความปกติ
    flushList();
    chunks.push(line);
  }
  flushList();

  // 4) รวมข้อความธรรมดาเป็น <p> และแปลง **หัวข้อ**: เป็น <h4>
  const htmlParts = [];
  let buf = [];

  const pushParagraph = () => {
    if (!buf.length) return;
    const block = buf.join("\n");
    const mHead = block.match(/^\s*<strong>(.+?)<\/strong>\s*:\s*$/); // **หัวข้อ**:
    if (mHead) {
      htmlParts.push(`<h4>${mHead[1]}</h4>`);
    } else {
      htmlParts.push(`<p>${block.replace(/\n/g, "<br/>")}</p>`);
    }
    buf = [];
  };

  for (const ch of chunks) {
    if (typeof ch === "string" && ch !== "\n" && !/^<\/*(ul|ol)/.test(ch)) {
      buf.push(ch);
    } else {
      pushParagraph();
      if (typeof ch === "string" && /^<\/*(ul|ol)/.test(ch)) 
        htmlParts.push(ch);
    }
  }
  pushParagraph();

  return htmlParts.join("");
}

export default function Chat() {
  const GOLD_GRAD = "linear-gradient(45deg, #FFD600, #FFC107)";
  const DARK_BG  = "linear-gradient(to bottom, #111, #1a1a1a)";

  const initialMessages = useMemo(
    () => [{ sender: "bot", text: "สวัสดีค่ะ! มีอะไรให้ช่วยสำหรับวันนี้คะ?" }],
    []
  );
 // state: รายการห้องแชทและข้อความ
  const [chats, setChats] = useState([{ id: 1, name: "แชท #1", messages: initialMessages }]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  // textarea ref เพื่อทำ auto-resize และรีเซ็ตความสูงเวลาเคลียร์
  const taRef = useRef(null);

  // เก็บ AbortController ของคำขอล่าสุด ไว้ยกเลิกถ้าผู้ใช้สลับแชท/ออกหน้า
  const inflightController = useRef(null);

  // ปรับความสูงเริ่มต้น/เมื่อค่า input เปลี่ยน
  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    if (!input) {
      ta.style.height = "42px"; // match CSS .input min-height
    } else {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 240) + "px";
    }
  }, [input]);

  const currentChat = chats.find(c => c.id === currentChatId);
  const short = (s, n = 28) => (s.length > n ? s.slice(0, n) + "…" : s);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentChat?.messages, loading]);

  useEffect(() => {
    return () => inflightController.current?.abort(); // cleanup ตอน unmount
  }, []); 
//สร้างแชทใหม่
  const handleNewChat = () => {
    const newId = chats.length ? Math.max(...chats.map(c => c.id)) + 1 : 1;
    setChats([...chats, { id: newId, name: `แชท #${newId}`, messages: initialMessages }]); // เพิ่มรายการห้อง
    setCurrentChatId(newId);
    setInput("");
  };

  const handleSelectChat = (id) => { //เมื่อสลับไปแชทอื่น
    setCurrentChatId(id);
    setInput("");
    inflightController.current?.abort(); 
  };

  /** อ่านสตรีมทีละ chunk ถ้าไม่สำเร็จ → fallback ไป oneshot */
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);

    // 1) ใส่ข้อความผู้ใช้ + สร้างบัฟเฟอร์ว่างสำหรับบอท
    let localChatId = currentChatId;
    let historySnapshot;

    setChats(prev =>
      prev.map(c => {
        if (c.id !== localChatId) return c; // อัปเดตเฉพาะแชทปัจจุบัน
        const nextMsgs = [...c.messages, { sender: "user", text }, { sender: "bot", text: "" }];
        const userCount = nextMsgs.filter(m => m.sender === "user").length;
        const newName = (c.name.startsWith("แชท #") && userCount === 1) ? short(text) : c.name;
        historySnapshot = nextMsgs.slice(0, nextMsgs.length - 1); // ไม่รวมบอทว่าง
        return { ...c, name: newName, messages: nextMsgs };
      })
    );

    setInput("");

    const controller = new AbortController();
    inflightController.current = controller;

    // helper: เติมข้อความให้บับเบิลบอทตัวสุดท้าย
    const appendToLastBot = (chunk) => {
      setChats(prev =>
        prev.map(c => {
          if (c.id !== localChatId) return c; // อัปเดตเฉพาะแชทปัจจุบัน
          const msgs = c.messages.slice();
          const last = msgs[msgs.length - 1];
          if (last?.sender === "bot") {
            msgs[msgs.length - 1] = { ...last, text: last.text + chunk };
          }
          return { ...c, messages: msgs };
        })
      );
    };

    // ---------- 1) พยายามสตรีมจาก /chat-stream ----------
    try {
      const res = await fetch(API_STREAM, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, history: historySnapshot }),
        signal: controller.signal
      });

      // ถ้าไม่มี endpoint หรือสตรีมใช้ไม่ได้ → โยน error เพื่อไป fallback
      if (!res.ok || !res.body) throw new Error(`STREAM_UNAVAILABLE_${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      while (!done) {
        const { value, done: d } = await reader.read(); // อ่านทีละ chunk
        done = d;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          appendToLastBot(chunk);
        }
      }
    } catch (e) {
      // ---------- 2) Fallback ไป /chat แบบครั้งเดียว ----------
      if (e.name !== "AbortError") {
        try {
          const res2 = await fetch(API_ONESHOT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: text, history: historySnapshot })
          });
          const data = await res2.json();
          appendToLastBot(data?.response ?? "…");
        } catch {
          // ถ้ายังพัง แสดงข้อความผิดพลาด
          setChats(prev =>
            prev.map(c => {
              if (c.id !== localChatId) return c;
              const msgs = c.messages.slice();
              const last = msgs[msgs.length - 1];
              if (last?.sender === "bot" && last.text === "") {
                msgs[msgs.length - 1] = { ...last, text: "ขออภัย ระบบขัดข้อง ลองใหม่อีกครั้งนะคะ" };
              }
              return { ...c, messages: msgs };
            })
          );
        }
      }
    } finally {
      setLoading(false);
      inflightController.current = null;
    }
  };

  return (
    <div className="root" style={{ background: DARK_BG }}>
      {/* css ถูกนำเข้าเป็นไฟล์แล้ว: import './styles/chat.css'; */}

      {/* Sidebar */}
      <aside className="sidebar">
        <button className="btn btn-gold" onClick={handleNewChat}>+ New chat</button>

        <div className="side-head">CHATS</div>
        <div className="chat-list" role="list">
          {chats.map(c => {
            const active = c.id === currentChatId;
            return (
              <button
                key={c.id}
                className={`chat-tab ${active ? "active" : ""}`}
                onClick={() => handleSelectChat(c.id)}
                title={c.name}
                role="listitem"
              >
                <span className="dot" />
                <span className="truncate">💬 {c.name}</span>
              </button>
            );
          })}
        </div>

        <div className="sidebar-footer">
          <img src="/Logo.jpg" alt="Logo" className="footer-logo" />
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <section className="messages" aria-live="polite">
          {currentChat?.messages.map((m, i) => (
            <div key={i} className={`msg ${m.sender}`}>
              {m.sender === "user" ? (
                <span className="bubble gold">{m.text}</span>
              ) : (
                <span
                  className="bubble bot rich"
                  dangerouslySetInnerHTML={{ __html: renderRich(m.text) }}
                />
              )}
            </div>
          ))}
          {loading && <div className="loading">กำลังพิมพ์…</div>}
          <div ref={endRef} />
        </section>

        <form className="composer" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
          <textarea
            ref={taRef}
            className="input"
            value={input}
            placeholder="พิมพ์คำถาม… "
            rows={1}
            onChange={(e) => setInput(e.target.value)}
            onInput={(e) => {
              const ta = e.target;
              ta.style.height = "auto";
              ta.style.height = Math.min(ta.scrollHeight, 240) + "px";
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage(); // Enter = ส่ง
              }
              // Shift+Enter ให้เป็น newline (อย่า preventDefault)
            }}
            disabled={loading}
          />
           <button type="submit" className="btn btn-gold" disabled={loading || !input.trim()}>
             ส่ง
           </button>
         </form>
      </main>
    </div>
  );
}