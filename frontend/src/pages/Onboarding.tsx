import { useState } from "react";
import { api } from "../api";

const ACK_POINTS = [
  "Ghost Typing writes in a style learned from message patterns. It does not know what the real person thinks or would say.",
  "Nothing here is sent to anyone. It cannot be used to contact them.",
  "Sessions are time-limited on purpose. This tool works best when it helps you put things down, not pick them back up.",
];

export function Onboarding({ onAck }: { onAck: () => void }) {
  const [checked, setChecked] = useState(false);
  return (
    <div className="max-w-md mx-auto p-6 space-y-4">
      <h1 className="text-xl font-semibold">Before you begin</h1>
      {ACK_POINTS.map(p => (
        <p key={p} className="text-gray-700">• {p}</p>
      ))}
      <label className="flex gap-2 items-start">
        <input type="checkbox" checked={checked} onChange={e => setChecked(e.target.checked)} />
        <span className="text-sm">I understand this is a simulation based on my own saved messages.</span>
      </label>
      <button disabled={!checked} onClick={async () => { await api.updateGates({ acknowledge_onboarding: true }); onAck(); }}
        className="w-full py-2 rounded bg-indigo-600 text-white disabled:bg-gray-300">
        Continue
      </button>
    </div>
  );
}
