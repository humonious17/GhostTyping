import { useEffect, useRef, useState, useCallback } from "react";
import { SimulationBanner } from "./SimulationBanner";
import { CrisisOverlay } from "./CrisisOverlay";
import { RepeatUseCheckinModal } from "./RepeatUseCheckinModal";
import { api, ApiError } from "../api";
import type { SessionEndData } from "./SessionEnd";

interface Props {
  sessionId: string;
  personLabel: string;
  mode: string;
  showRepeatCheckin: boolean;
  onEnded: (data: SessionEndData) => void;
}

type Msg = { role: "user" | "assistant"; content: string };

export function ChatView({ sessionId, personLabel, mode, showRepeatCheckin, onEnded }: Props) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [timeLeft, setTimeLeft] = useState(20 * 60);
  const [crisis, setCrisis] = useState(false);
  const [checkinOpen, setCheckinOpen] = useState(showRepeatCheckin);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  // Local mirror of the server-side timebox so the user isn't surprised by a 409.
  // Server remains authoritative — client timer is UX only.
  useEffect(() => {
    if (timeLeft <= 0) return;
    const t = setInterval(() => setTimeLeft(s => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, [timeLeft > 0]);

  const endSession = useCallback(async (reason: SessionEndData["reason"]) => {
    onEnded({ reason, messages });
  }, [messages, onEnded]);

  const send = async () => {
    const text = draft.trim();
    if (!text || sending || timeLeft <= 0) return;
    setSending(true);
    setDraft("");
    setMessages(m => [...m, { role: "user", content: text }]);
    try {
      const r = await api.send(sessionId, text);
      setMessages(m => [...m, { role: "assistant", content: r.reply }]);
      setTimeLeft(Math.floor(r.time_remaining_sec));
      if (r.crisis_resources_shown) setCrisis(true);
    } catch (e) {
      if (e instanceof ApiError && e.code === "timebox_reached") {
        setTimeLeft(0);
        endSession("timebox");
        return;
      }
      setMessages(m => [...m, {
        role: "assistant",
        content: "(Something went wrong on our side. Your words are still here.)",
      }]);
    } finally {
      setSending(false);
    }
  };

  const mins = Math.floor(timeLeft / 60), secs = timeLeft % 60;

  return (
    <div className="flex flex-col h-screen bg-stone-50">
      {/* PRD 5.5 — non-dismissible. No conditional rendering. */}
      <SimulationBanner name={personLabel} />

      <div className="px-4 py-2 text-xs text-stone-500 flex justify-between items-baseline">
        <span>
          Guided session:{" "}
          {{ unsaid: "Say the unsaid thing", question: "Ask the question",
             replay: "Replay an exchange", goodbye: "Say goodbye", free: "Free writing" }[mode]}
        </span>
        <span aria-label={`${mins} minutes remaining`} className="tabular-nums">
          {timeLeft > 0 ? `mins:{mins}:mins:{String(secs).padStart(2, "0")} left in this session` :
            "Session time reached"}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <p className="max-w-[75%] rounded-2xl rounded-br-sm bg-white border border-stone-300
                            px-4 py-2 whitespace-pre-wrap">{m.content}</p>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              {/* Deliberately NOT a standard chat bubble: dashed amber border
                  keeps the simulated nature visually unmistakable (5.5) */}
              <p className="max-w-[75%] rounded-2xl rounded-bl-sm bg-amber-50
                            border-2 border-dashed border-amber-400
                            px-4 py-2 whitespace-pre-wrap">{m.content}</p>
            </div>
          )
        )}
        <div ref={bottomRef} />
      </div>

      {timeLeft > 0 ? (
        <div className="p-4 border-t border-stone-200 flex gap-2">
          <textarea
            value={draft} onChange={e => setDraft(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            rows={2}
            placeholder="Write what you need to say…"
            className="flex-1 resize-none rounded-xl border border-stone-300 p-3 focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          <button onClick={send} disabled={sending || !draft.trim()}
            className="self-end px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-medium disabled:bg-stone-300">
            Send
          </button>
        </div>
      ) : (
        <div className="p-6 text-center">
          <button onClick={() => endSession("completed")}
            className="px-6 py-3 rounded-xl bg-indigo-600 text-white font-medium">
            Close this session and reflect →
          </button>
        </div>
      )}

      {crisis && <CrisisOverlay onClose={() => setCrisis(false)} />}
      <RepeatUseCheckinModal open={checkinOpen} onClose={() => setCheckinOpen(false)}
                             personLabel={personLabel} />
    </div>
  );
}
