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
  let list = null;   // {type:'ul'|'ol', items:[]}

  const flushList = () => {
    if (!list) return;
    const tag = list.type === "ul" ? "ul" : "ol";
    chunks.push(`<${tag}>${list.items.map(x => `<li>${x}</li>`).join("")}</${tag}>`);
    list = null;
  };

  for (const raw of lines) {
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
      if (typeof ch === "string" && /^<\/*(ul|ol)/.test(ch)) htmlParts.push(ch);
    }
  }
  pushParagraph();

  return htmlParts.join("");
}

export default function Chat() {
  const GOLD_GRAD = "linear-gradient(45deg, #FFD600, #FFC107)";
  const DARK_BG  = "linear-gradient(to bottom, #111, #1a1a1a)";

  const initialMessages = useMemo(
    () => [{ sender: "bot", text: "สวัสดีค่ะ! มีอะไรให้ช่วยถามเกี่ยวกับสินค้าไหมคะ?" }],
    []
  );

  const [chats, setChats] = useState([{ id: 1, name: "แชท #1", messages: initialMessages }]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  // เก็บ AbortController ของคำขอล่าสุด ไว้ยกเลิกถ้าผู้ใช้สลับแชท/ออกหน้า
  const inflightController = useRef(null);

  const currentChat = chats.find(c => c.id === currentChatId);
  const short = (s, n = 28) => (s.length > n ? s.slice(0, n) + "…" : s);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentChat?.messages, loading]);

  useEffect(() => {
    return () => inflightController.current?.abort(); // cleanup ตอน unmount
  }, []);

  const handleNewChat = () => {
    const newId = chats.length ? Math.max(...chats.map(c => c.id)) + 1 : 1;
    setChats([...chats, { id: newId, name: `แชท #${newId}`, messages: initialMessages }]);
    setCurrentChatId(newId);
    setInput("");
  };

  const handleSelectChat = (id) => {
    setCurrentChatId(id);
    setInput("");
    inflightController.current?.abort(); // ถ้ากำลังสตรีมอยู่ ให้ยกเลิกเพื่อไม่ให้ปนกัน
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
        if (c.id !== localChatId) return c;
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
          if (c.id !== localChatId) return c;
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
        const { value, done: d } = await reader.read();
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
      <style>{css}</style>

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
          <input
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="พิมพ์คำถาม…"
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
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

/* ---------- CSS: Gold/Black + bubble-fit + เน้นหัวข้อสำคัญ ---------- */
const css = `
:root{
  --gold-1:#FFD600;
  --gold-2:#FFC107;
  --gold-grad: linear-gradient(45deg, var(--gold-1), var(--gold-2));
  --bg:#111; --bg2:#1a1a1a; --card:#141414; --text:#fff;
  --muted:#bdbdbd; --bot:#1f1f1f; --stroke:#333;
}

*{ box-sizing:border-box; }
html, body, #root{ height:100%; width:100%; margin:0; padding:0; }
body{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Arial; color:var(--text); }

.root{ display:flex; height:100vh; width:100vw; overflow:hidden; }

/* Sidebar */
.sidebar{
  width:280px; height:100%; flex-shrink:0;
  padding:20px; padding-bottom:90px; /* เว้นที่ให้โลโก้ */
  background:var(--bg2);
  border-right:2px solid var(--gold-1);
  box-shadow:2px 0 10px rgba(255,214,0,.18);
  display:flex; flex-direction:column; gap:14px;
  position:relative; /* ให้ footer วาง absolute ได้ */
}
.side-head{ color:var(--gold-1); font-weight:800; font-size:12px; letter-spacing:.1em; }

.chat-list{ overflow:auto; display:flex; flex-direction:column; gap:8px; padding-right:4px; }
.chat-tab{
  display:flex; align-items:center; gap:10px; width:100%;
  padding:12px 14px; border-radius:12px;
  background:#181818; border:1px solid var(--stroke);
  color:var(--text); text-align:left; cursor:pointer;
  transition: transform .12s ease, box-shadow .2s ease, border-color .2s ease, background .2s ease;
}
.chat-tab .dot{ width:8px; height:8px; border-radius:50%; background:var(--gold-1); box-shadow:0 0 8px rgba(255,214,0,.6); }
.chat-tab:hover{ border-color:var(--gold-1); background:#1d1d1d; box-shadow:0 4px 12px rgba(0,0,0,.25); transform:translateY(-1px); }
.chat-tab:active{ transform:translateY(0); }
.chat-tab.active{
  background: radial-gradient(120% 120% at 0% 0%, rgba(255,214,0,.14), transparent 50%), #161616;
  border-color:var(--gold-1);
}
.truncate{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* Sidebar footer logo (fixed bottom) */
.sidebar-footer{
  position:absolute; left:20px; right:20px; bottom:20px;
  display:flex; align-items:center; justify-content:center;
}
.footer-logo{
  width:64px; height:64px; object-fit:contain;
  border-radius:50%; background:#000;
  border:2px solid var(--gold-1);
  padding:6px;
  box-shadow:0 0 12px rgba(255,214,0,.25);
  transition: transform .2s ease, box-shadow .2s ease, filter .2s ease;
}
.footer-logo:hover{ transform:scale(1.05); box-shadow:0 0 18px rgba(255,214,0,.6); filter:saturate(1.1); }

/* Main */
.main{ flex:1; height:100%; display:flex; flex-direction:column; padding:20px; gap:14px; }

.messages{
  flex:1; overflow:auto;
  background: linear-gradient(180deg, rgba(255,214,0,.04), transparent 120%), var(--card);
  border:1px solid var(--stroke); border-radius:16px; padding:18px;
  box-shadow: 0 8px 24px rgba(0,0,0,.25);
}

/* แถวของข้อความ */
.msg{ display:flex; margin:10px 0; align-items:flex-end; }
.msg.user{ justify-content:flex-end; }   /* ผู้ใช้ชิดขวา */
.msg.bot{  justify-content:flex-start; } /* บอทชิดซ้าย */

/* บับเบิล */
.bubble{
  display:inline-block;
  max-width: min(680px, 72%);
  padding:8px 14px;
  margin:4px 0;
  border-radius:16px;
  line-height:1.5;
  font-size:15px;
  box-shadow:0 4px 12px rgba(0,0,0,.25);
  word-break:break-word;
  overflow-wrap:anywhere;
  white-space:pre-wrap;
  transition: transform .12s ease, box-shadow .2s ease;
}
.bubble:hover{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.32); }

.bubble.gold{ background:var(--gold-grad); color:#111; border:none; }
.bubble.bot{  background:var(--bot); color:#f4f4f4; border:1px solid rgba(255,214,0,.25); }

.loading{ color:var(--gold-1); font-size:13px; margin-top:6px; }

/* ===== อ่านง่าย + เน้นหัวข้อสำคัญสำหรับบอท ===== */
.bubble.rich{
  background:var(--bot);
  border:1px solid rgba(255,214,0,.25);
  max-width:min(720px, 90%);
  line-height:1.85;
  font-size:16px;
  white-space:normal;
  text-align:left;
}
.bubble.rich p{ margin:0 0 12px; }
.bubble.rich h4{
  margin:14px 0 8px;
  font-size:18px;
  font-weight:900;
  color:#ffe071;
  display:inline-block;
  position:relative;
  padding-bottom:2px;
}
.bubble.rich h4::after{
  content:"";
  position:absolute;
  left:0; right:0; bottom:-2px;
  height:2px;
  background:linear-gradient(90deg, var(--gold-1), transparent 70%);
  opacity:.9;
}
.bubble.rich ul, .bubble.rich ol{
  margin:8px 0 12px 1.25em;
  padding:0;
}
.bubble.rich ul{ list-style:disc; }
.bubble.rich ol{ list-style:decimal; }
.bubble.rich li{ margin:6px 0; }
.bubble.rich strong{ font-weight:800; color:#ffe071; }

/* Composer */
.composer{
  display:flex; gap:10px; padding:12px; border:1px solid var(--stroke); border-radius:14px; background:#121212; align-items:center;
}
.input{
  flex:1; padding:12px 14px; border-radius:10px; border:1px solid rgba(255,214,0,.5);
  background:#0f0f0f; color:var(--text); font-size:15px;
  transition: box-shadow .2s ease, border-color .2s ease, background .2s ease;
}
.input::placeholder{ color:#9a9a9a; }
.input:focus{ outline:none; border-color:var(--gold-1); box-shadow:0 0 0 3px rgba(255,214,0,.25); background:#101010; }

/* ปรับสำหรับหน้าจอเล็ก */
@media (max-width: 640px){
  .messages{ padding:16px; }
  .bubble{ max-width: calc(100% - 56px); }
  .bubble.rich{ max-width: calc(100% - 56px); }
}

/* Buttons */
.btn{ border:none; border-radius:10px; padding:10px 16px; font-weight:800; cursor:pointer;
  transition: transform .12s ease, box-shadow .2s ease, filter .2s ease, opacity .2s ease; user-select:none; }
.btn:disabled{ opacity:.6; cursor:not-allowed; }
.btn:active{ transform:translateY(1px); }
.btn-gold{ background:var(--gold-grad); color:#111; box-shadow:0 8px 16px rgba(0,0,0,.35); }
.btn-gold:hover{ filter:brightness(1.02); box-shadow:0 10px 20px rgba(0,0,0,.45); }

/* Scrollbars */
.messages::-webkit-scrollbar, .chat-list::-webkit-scrollbar{ width:10px; }
.messages::-webkit-scrollbar-thumb, .chat-list::-webkit-scrollbar-thumb{ background:rgba(255,214,0,.35); border-radius:20px; }

/* Reduce motion */
@media (prefers-reduced-motion: reduce){ .btn, .bubble, .chat-tab, .footer-logo{ transition:none !important; } }
`;
