import { useState } from "react";
import { SimulationBanner } from "./SimulationBanner";
import { api } from "../api";

type Msg = { role: "user" | "assistant"; content: string };
type Props = { sessionId: string; personLabel: string; onEnded: (data: { reason: "completed"; messages: Msg[] }) => void };

export function GoodbyeChat({ sessionId, personLabel, onEnded }: Props) {
  const [phase, setPhase] = useState<"writing" | "final_ready" | "closed">("writing");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");

  const send = async () => {
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    const next = [...messages, { role: "user" as const, content: text }];
    const response = await api.send(sessionId, text);
    setMessages([...next, { role: "assistant", content: response.reply }]);
    if (response.phase === "final_ready") setPhase("final_ready");
  };

  const receiveFinal = async () => {
    const response = await api.deliverFinal(sessionId);
    const next = [...messages, { role: "assistant" as const, content: response.final_message }];
    setMessages(next);
    setPhase("closed");
    onEnded({ reason: "completed", messages: next });
  };

  return <div className="flex flex-col h-screen bg-stone-50">
    <SimulationBanner name={personLabel} />
    <div className="flex-1 overflow-y-auto p-4 space-y-3">
      {messages.map((message, index) => <p key={index} className="max-w-[75%] rounded-xl border p-3 whitespace-pre-wrap">{message.content}</p>)}
    </div>
    {phase === "writing" && <div className="p-4 border-t flex gap-2">
      <textarea value={draft} onChange={e => setDraft(e.target.value)} rows={2} className="flex-1 border rounded p-3" />
      <button onClick={send} disabled={!draft.trim()} className="self-end px-5 py-2 rounded bg-indigo-600 text-white disabled:bg-gray-300">Send</button>
    </div>}
    {phase === "final_ready" && <div className="p-6 text-center border-t bg-amber-50 space-y-3">
      <p className="text-sm">You have said what you came to say. The last step comes once, then this conversation closes.</p>
      <button onClick={receiveFinal} className="px-6 py-3 rounded bg-indigo-600 text-white">Receive the goodbye</button>
    </div>}
  </div>;
}