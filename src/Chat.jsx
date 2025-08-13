import React, { useEffect, useRef, useState } from "react";
import logo from '/public/logo.jpg';
const API_URL = "http://localhost:8000/chat";

export default function Chat() {
  // ---- Theme tokens ----
  const GOLD_GRAD = "linear-gradient(45deg, #FFD600, #FFC107)";
  const DARK_BG = "linear-gradient(to bottom, #111, #1a1a1a)";

  // ---- State ----
  const initialMessages = [
    { sender: "bot", text: "สวัสดีค่ะ! มีอะไรให้ช่วยถามเกี่ยวกับสินค้าไหมคะ?" }
  ];
  const [chats, setChats] = useState([{ id: 1, name: "แชท #1", messages: initialMessages }]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  const currentChat = chats.find(c => c.id === currentChatId);
  const short = (s, n = 28) => (s.length > n ? s.slice(0, n) + "…" : s);

  // ---- Effects ----
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [currentChat?.messages, loading]);

  // ---- Actions ----
  const handleNewChat = () => {
    const newId = chats.length ? Math.max(...chats.map(c => c.id)) + 1 : 1;
    setChats([...chats, { id: newId, name: `แชท #${newId}`, messages: initialMessages }]);
    setCurrentChatId(newId);
    setInput("");
  };

  const handleSelectChat = (id) => {
    setCurrentChatId(id);
    setInput("");
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);

    // optimistic: push user message + auto-rename if first user message
    setChats(prev =>
      prev.map(c => {
        if (c.id !== currentChatId) return c;
        const next = { ...c, messages: [...c.messages, { sender: "user", text }] };
        const userCount = next.messages.filter(m => m.sender === "user").length;
        if (c.name.startsWith("แชท #") && userCount === 1) next.name = short(text);
        return next;
      })
    );
    setInput("");

    try {
      const history = (currentChat?.messages ?? []).concat({ sender: "user", text });
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, history })
      });
      const data = await res.json();
      const botText = data?.response ?? "(no response)";

      setChats(prev =>
        prev.map(c =>
          c.id === currentChatId
            ? { ...c, messages: [...c.messages, { sender: "bot", text: botText }] }
            : c
        )
      );
    } catch {
      setChats(prev =>
        prev.map(c =>
          c.id === currentChatId
            ? { ...c, messages: [...c.messages, { sender: "bot", text: "ขออภัย ระบบขัดข้อง ลองใหม่อีกครั้งนะคะ" }] }
            : c
        )
      );
    } finally {
      setLoading(false);
    }
  };

  // ---- Render ----
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

        {/* Footer Logo (fixed at bottom-left of sidebar) */}
        <div className="sidebar-footer">
          <img src="/public/Logo.jpg" alt="Logo" className="footer-logo" />
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <section className="messages" aria-live="polite">
          {currentChat?.messages.map((m, i) => (
            <div key={i} className={`msg ${m.sender}`}>
              <span className={`bubble ${m.sender === "user" ? "gold" : "bot"}`}>{m.text}</span>
            </div>
          ))}
          {loading && <div className="loading">กำลังค้นหาข้อมูล…</div>}
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

/* ---------- CSS: Fullscreen + Gold/Black gradient theme + interactions + footer logo ---------- */
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
.footer-logo:hover{
  transform:scale(1.05);
  box-shadow:0 0 18px rgba(255,214,0,.6);
  filter:saturate(1.1);
}

/* Main */
.main{ flex:1; height:100%; display:flex; flex-direction:column; padding:20px; gap:14px; }

.messages{
  flex:1; overflow:auto;
  background: linear-gradient(180deg, rgba(255,214,0,.04), transparent 120%), var(--card);
  border:1px solid var(--stroke); border-radius:16px; padding:18px;
  box-shadow: 0 8px 24px rgba(0,0,0,.25);
}

.msg{ display:flex; margin:10px 0; }
.msg.user{ justify-content:flex-end; }

.bubble{
  max-width:72%; padding:12px 16px; border-radius:16px; line-height:1.45; font-size:15px;
  box-shadow: 0 4px 12px rgba(0,0,0,.25);
  transition: transform .12s ease, box-shadow .2s ease;
}
.bubble:hover{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.32); }

.bubble.gold{ background:var(--gold-grad); color:#111; border:none; }
.bubble.bot{ background:var(--bot); color:#f4f4f4; border:1px solid rgba(255,214,0,.25); }

.loading{ color:var(--gold-1); font-size:13px; margin-top:6px; }

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
