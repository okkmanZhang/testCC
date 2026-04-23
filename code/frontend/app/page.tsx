"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Calculator, MessageSquare, Loader2, ChevronDown } from "lucide-react";
import { toast } from "sonner";

const API = "http://localhost:8000/api/v1";

// ── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

interface Source {
  ref: string;
  page: number | null;
  similarity: number;
}

interface RateResult {
  classification: string;
  employment_type: string;
  age: number | null;
  work_date: string;
  day_type: string;
  start_time: string;
  end_time: string;
  hours_worked: number;
  rate_per_hour: number;
  rate_multiplier: number;
  total_pay: number;
  clause_ref: string;
  breakdown: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const CLASSIFICATIONS = [
  "retail_employee_level_1",
  "retail_employee_level_2",
  "retail_employee_level_3",
  "retail_employee_level_4",
  "retail_employee_level_5",
  "retail_employee_level_6",
  "retail_employee_level_7",
  "retail_employee_level_8",
];

const EMP_TYPES = ["full_time", "part_time", "casual"];

function formatLabel(s: string) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── Sub-components ───────────────────────────────────────────────────────────

function Tag({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span style={{ color: "var(--muted)", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", fontFamily: "var(--mono)" }}>
        {label}
      </span>
      <span style={{ color: "var(--text-dim)", fontFamily: "'IBM Plex Mono', monospace", fontSize: 12 }}>
        {value}
      </span>
    </div>
  );
}

function SourceBadge({ source }: { source: Source }) {
  const pct = Math.round(source.similarity * 100);
  const color = pct > 60 ? "var(--green)" : pct > 40 ? "var(--amber)" : "var(--muted)";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      background: "var(--bg)", border: "1px solid var(--border)",
      borderRadius: 4, padding: "2px 8px", fontSize: 11,
      fontFamily: "'IBM Plex Mono', monospace", color: "var(--text-dim)"
    }}>
      <span style={{ color, fontSize: 8 }}>●</span>
      {source.ref} {source.page ? `p.${source.page}` : ""} {pct}%
    </span>
  );
}

// ── Chat Panel ───────────────────────────────────────────────────────────────

function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Ask me anything about the General Retail Industry Award [MA000004]. I'll cite the relevant clauses.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendQuestion(question: string) {
    if (!question.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setMessages((m) => [...m, {
        role: "assistant",
        content: data.answer,
        sources: data.sources,
      }]);
    } catch {
      toast.error("Failed to reach the API");
      setMessages((m) => [...m, { role: "assistant", content: "Error: could not reach the API." }]);
    } finally {
      setLoading(false);
    }
  }

  async function send() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    await sendQuestion(question);
  }

  function handleCopy(text: string, idx: number) {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1500);
  }

  function handleRetry(text: string) {
    if (loading) return;
    sendQuestion(text);
  }

  const iconBtnStyle = (active?: boolean) => ({
    background: "none",
    border: "1px solid var(--border)",
    borderRadius: 4,
    padding: "3px 7px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: 4,
    fontSize: 10,
    color: active ? "var(--green)" : "var(--muted)",
    fontFamily: "'IBM Plex Mono', monospace",
    transition: "all 0.15s",
    whiteSpace: "nowrap" as const,
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 20px", display: "flex", flexDirection: "column", gap: 20 }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{
              maxWidth: "85%",
              background: msg.role === "user" ? "var(--amber)" : "var(--surface)",
              color: msg.role === "user" ? "#0e0f11" : "var(--text)",
              border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
              borderRadius: msg.role === "user" ? "12px 12px 2px 12px" : "2px 12px 12px 12px",
              padding: "10px 14px",
              fontSize: 13,
              lineHeight: 1.65,
              whiteSpace: "pre-wrap",
              fontWeight: msg.role === "user" ? 500 : 400,
            }}>
              {msg.content}
            </div>

            {/* Action buttons — only for user messages */}
            {msg.role === "user" && (
              <div style={{ display: "flex", gap: 4 }}>
                <button
                  style={iconBtnStyle(copiedIdx === i)}
                  onClick={() => handleCopy(msg.content, i)}
                  title="Copy question"
                >
                  {copiedIdx === i ? (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                  ) : (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  )}
                  {copiedIdx === i ? "copied" : "copy"}
                </button>
                <button
                  style={iconBtnStyle()}
                  onClick={() => handleRetry(msg.content)}
                  disabled={loading}
                  title="Re-send this question"
                >
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-4.95"/></svg>
                  retry
                </button>
              </div>
            )}

            {/* Source badges — only for assistant messages */}
            {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, maxWidth: "85%" }}>
                {msg.sources.slice(0, 5).map((s, j) => <SourceBadge key={j} source={s} />)}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--muted)" }}>
            <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} />
            <span style={{ fontSize: 12, fontFamily: "'IBM Plex Mono', monospace" }}>retrieving clauses...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="e.g. What rate applies to a 16yo on Sunday?"
          style={{
            flex: 1, background: "var(--bg)", border: "1px solid var(--border)",
            borderRadius: 6, padding: "8px 12px", color: "var(--text)",
            fontSize: 13, outline: "none",
          }}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            background: "var(--amber)", border: "none", borderRadius: 6,
            padding: "8px 14px", cursor: "pointer", display: "flex",
            alignItems: "center", justifyContent: "center",
            opacity: loading || !input.trim() ? 0.4 : 1,
            transition: "opacity 0.15s",
          }}
        >
          <Send size={14} color="#0e0f11" />
        </button>
      </div>
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Rate Calculator Panel ────────────────────────────────────────────────────

function RatePanel() {
  const [form, setForm] = useState({
    classification: "retail_employee_level_1",
    employment_type: "full_time",
    work_date: new Date().toISOString().split("T")[0],
    start_time: "08:00",
    end_time: "14:00",
    age: "",
  });
  const [result, setResult] = useState<RateResult | null>(null);
  const [loading, setLoading] = useState(false);

  function set(k: string, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function calculate() {
    setLoading(true);
    setResult(null);
    try {
      const body: Record<string, unknown> = {
        classification: form.classification,
        employment_type: form.employment_type,
        work_date: form.work_date,
        start_time: form.start_time,
        end_time: form.end_time,
      };
      if (form.age) body.age = parseInt(form.age);

      const res = await fetch(`${API}/rate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      toast.error("Calculation failed — check inputs");
    } finally {
      setLoading(false);
    }
  }

  const selectStyle = {
    width: "100%", background: "var(--bg)", border: "1px solid var(--border)",
    borderRadius: 6, padding: "7px 10px", color: "var(--text)", fontSize: 13,
    outline: "none", appearance: "none" as const,
  };

  const inputStyle = { ...selectStyle };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflowY: "auto" }}>
      <div style={{ padding: "20px 20px 0" }}>

        {/* Form grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div style={{ gridColumn: "1 / -1" }}>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Classification
            </label>
            <div style={{ position: "relative" }}>
              <select value={form.classification} onChange={(e) => set("classification", e.target.value)} style={selectStyle}>
                {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{formatLabel(c)}</option>)}
              </select>
              <ChevronDown size={12} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", color: "var(--muted)", pointerEvents: "none" }} />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Employment Type
            </label>
            <div style={{ position: "relative" }}>
              <select value={form.employment_type} onChange={(e) => set("employment_type", e.target.value)} style={selectStyle}>
                {EMP_TYPES.map((t) => <option key={t} value={t}>{formatLabel(t)}</option>)}
              </select>
              <ChevronDown size={12} style={{ position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)", color: "var(--muted)", pointerEvents: "none" }} />
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Age (blank = adult)
            </label>
            <input type="number" min={14} max={20} value={form.age} onChange={(e) => set("age", e.target.value)} placeholder="e.g. 16" style={inputStyle} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Work Date
            </label>
            <input type="date" value={form.work_date} onChange={(e) => set("work_date", e.target.value)} style={inputStyle} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              Start Time
            </label>
            <input type="time" value={form.start_time} onChange={(e) => set("start_time", e.target.value)} style={inputStyle} />
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              End Time
            </label>
            <input type="time" value={form.end_time} onChange={(e) => set("end_time", e.target.value)} style={inputStyle} />
          </div>
        </div>

        <button
          onClick={calculate}
          disabled={loading}
          style={{
            width: "100%", background: loading ? "var(--border)" : "var(--green)",
            color: "#0e0f11", border: "none", borderRadius: 6,
            padding: "9px", fontWeight: 600, fontSize: 13, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
            transition: "background 0.15s",
          }}
        >
          {loading ? <Loader2 size={14} style={{ animation: "spin 1s linear infinite" }} /> : <Calculator size={14} />}
          {loading ? "Calculating..." : "Calculate Pay"}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div style={{ margin: "16px 20px", background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
          {/* Total */}
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Total Pay</span>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 26, fontWeight: 500, color: "var(--green)" }}>
              ${result.total_pay.toFixed(2)}
            </span>
          </div>

          {/* Details grid */}
          <div style={{ padding: "14px 20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Tag label="Rate / hr" value={`$${result.rate_per_hour.toFixed(4)}`} />
            <Tag label="Hours" value={`${result.hours_worked}h`} />
            <Tag label="Multiplier" value={`${result.rate_multiplier}×`} />
            <Tag label="Day Type" value={formatLabel(result.day_type)} />
          </div>

          {/* Clause ref */}
          <div style={{ padding: "10px 20px", borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 10, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Award ref</span>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "var(--amber)" }}>{result.clause_ref}</span>
          </div>
        </div>
      )}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Home() {
  const [tab, setTab] = useState<"chat" | "rate">("chat");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", maxWidth: 1100, margin: "0 auto", padding: "0 16px" }}>

      {/* Header */}
      <header style={{ borderBottom: "1px solid var(--border)", padding: "16px 0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "var(--amber)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: 2 }}>
            MA000004
          </div>
          <h1 style={{ fontSize: 16, fontWeight: 600, color: "var(--text)", letterSpacing: "-0.01em" }}>
            General Retail Industry Award
          </h1>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {(["chat", "rate"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "6px 14px", borderRadius: 6, border: "1px solid",
                borderColor: tab === t ? "var(--amber)" : "var(--border)",
                background: tab === t ? "rgba(245,166,35,0.08)" : "transparent",
                color: tab === t ? "var(--amber)" : "var(--muted)",
                fontSize: 12, fontWeight: 500, cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              {t === "chat" ? <MessageSquare size={13} /> : <Calculator size={13} />}
              {t === "chat" ? "Ask Award" : "Rate Calc"}
            </button>
          ))}
        </div>
      </header>

      {/* Panel */}
      <main style={{ flex: 1, overflow: "hidden" }}>
        {tab === "chat" ? <ChatPanel /> : <RatePanel />}
      </main>
    </div>
  );
}