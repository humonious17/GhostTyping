import { useState } from "react";
import { api } from "../api";

export function AgeGate({ onConfirm }: { onConfirm: () => void }) {
  const [ok, setOk] = useState(false);
  return (
    <div className="max-w-sm mx-auto p-6 space-y-4">
      <h1 className="text-lg font-semibold">One thing first</h1>
      <p className="text-gray-700">Ghost Typing handles emotionally intense material and is not designed for anyone under 18.</p>
      <label className="flex gap-2 items-center">
        <input type="checkbox" checked={ok} onChange={e => setOk(e.target.checked)} />
        <span className="text-sm">I confirm I am 18 or older.</span>
      </label>
      <button disabled={!ok} onClick={async () => { await api.updateGates({ age_confirmed_18_plus: true }); onConfirm(); }}
        className="w-full py-2 rounded bg-indigo-600 text-white disabled:bg-gray-300">Continue</button>
    </div>
  );
}