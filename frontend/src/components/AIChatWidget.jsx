import { useEffect, useState } from "react";

import { api } from "../api";
import { buildAssistantReply, defaultChatMessages } from "../utils/ui";

const quickPrompts = ["Suggest a phone under 25000", "Compare top electronics", "What is in my cart?", "How do payments work?"];

export default function AIChatWidget({ open, setOpen, products, cart, authUser }) {
  const [messages, setMessages] = useState(defaultChatMessages);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!authUser) {
      setMessages(defaultChatMessages);
      return;
    }
    api.chatHistory().then((history) => {
      if (history.items?.length) {
        setMessages(history.items.map((item) => ({ role: item.role, content: item.content })));
      }
    }).catch(() => {});
  }, [authUser?.id]);

  const sendPrompt = async (prompt) => {
    const clean = prompt.trim();
    if (!clean) return;
    setMessages((current) => [...current, { role: "user", content: clean }]);
    setDraft("");
    setBusy(true);
    try {
      const response = authUser ? await api.chat({ message: clean }) : { reply: buildAssistantReply(clean, products, cart) };
      setMessages((current) => [...current, { role: "assistant", content: response.reply }]);
    } catch (err) {
      setMessages((current) => [...current, { role: "assistant", content: err.message || "I could not answer right now." }]);
    } finally {
      setBusy(false);
    }
  };

  const clearHistory = async () => {
    if (authUser) {
      await api.clearChatHistory().catch(() => {});
    }
    setMessages(defaultChatMessages);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendPrompt(draft);
  };

  if (!open) {
    return <button type="button" className="chat-launcher" onClick={() => setOpen(true)}>Ask Cartium AI</button>;
  }

  return (
    <aside className="chat-shell">
      <div className="chat-head"><div><strong>Cartium AI</strong><span>Products, cart, payments, and orders.</span></div><div className="chat-head-actions"><button type="button" className="ghost-button" onClick={clearHistory}>Clear</button><button type="button" className="ghost-button" onClick={() => setOpen(false)}>Close</button></div></div>
      <div className="chat-body">{messages.map((message, index) => <article key={`${message.role}-${index}`} className={message.role === "assistant" ? "chat-message" : "chat-message user"}><span>{message.role === "assistant" ? "AI" : "You"}</span><p>{message.content}</p></article>)}</div>
      <div className="suggestion-row">{quickPrompts.map((prompt) => <button key={prompt} type="button" className="suggestion-chip" onClick={() => sendPrompt(prompt)}>{prompt}</button>)}</div>
      <form className="chat-input-row" onSubmit={handleSubmit}><input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about products, payment, or orders" /><button type="submit" className="primary-button" disabled={busy}>{busy ? "..." : "Send"}</button></form>
    </aside>
  );
}
