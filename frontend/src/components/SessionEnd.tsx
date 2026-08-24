export interface SessionEndData {
  reason: "completed" | "timebox" | "user_exit";
  messages: { role: string; content: string }[];
}

const MOOD_LABELS = ["Much worse", "A bit worse", "About the same", "A bit better", "Much better"];

export function SessionEnd({ data, threadId }: { data: SessionEndData; threadId: string }) {
  const [summary, setSummary] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editedSummary, setEditedSummary] = useState("");
  const [mood, setMood] = useState<number | null>(null);
  const [saved, setSaved] = useState(false);

  // Fetch generated summary once (US-4)
  useEffect(() => {
    fetch(`BASE/sessions/{BASE}/sessions/BASE/sessions/{data.sessionId}/summary`).then(r => r.json())
      .then(d => { setSummary(d.summary); setEditedSummary(d.summary); })
      .catch(() => setSummary("We couldn't generate a summary — your transcript is still saved."));
  }, []);

  const moodSelected = mood !== null;

  return (
    <div className="max-w-lg mx-auto p-6 space-y-6">
      <h1 className="text-xl font-semibold">What did saying that feel like?</h1>

      {/* Reflection prompt (5.3) */}
      <textarea rows={4} placeholder="Take a moment before you go…"
        className="w-full rounded-xl border border-stone-300 p-3" />

      {/* Mood check-in (5.3 / 3.2 metric) */}
      <fieldset>
        <legend className="font-medium mb-2">How do you feel now, vs. before this session?</legend>
        <div className="grid grid-cols-5 gap-1 text-center text-xs">
          {MOOD_LABELS.map((label, i) => (
            <button key={label}
              onClick={() => setMood(i + 1)}
              className={`py-3 px-1 rounded-lg border ${mood === i + 1
                ? "border-indigo-500 bg-indigo-50 font-semibold"
                : "border-stone-300 hover:border-indigo-300"}`}>
              {label}
            </button>
          ))}
        </div>
      </fieldset>

      {/* Editable summary (US-4) — journal-shaped, ghost's words excluded per summary.py */}
      {summary && !editing && (
        <div className="rounded-xl border border-stone-200 bg-white p-4">
          <p className="whitespace-pre-wrap text-gray-700">{editedSummary}</p>
          <button onClick={() => setEditing(true)} className="mt-3 text-sm text-indigo-600 underline">
            Edit this
          </button>
        </div>
      )}
      {editing && (
        <div className="space-y-2">
          <textarea rows={8} value={editedSummary} onChange={e => setEditedSummary(e.target.value)}
            className="w-full rounded-xl border border-stone-300 p-3" />
          <button onClick={() => setEditing(false)} className="text-sm text-indigo-600 underline">
            Done editing
          </button>
        </div>
      )}

      {/* Save locally as a private letter — no share/send affordances exist */}
      <button disabled={!moodSelected || saved}
        onClick={() => { downloadLetter(editedSummary); setSaved(true); }}
        className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium disabled:bg-stone-300">
        {saved ? "Saved ✓" : "Save my reflection"}
      </button>
      <p className="text-xs text-gray-500 text-center">
        Saved privately to your device. It can't be sent to anyone.
      </p>
    </div>
  );
}

// Plain-text file download — deliberately NOT image/screenshot format (7.3)
function downloadLetter(text: string) {
  const blob = new Blob([`My Ghost Typing reflection
${new Date().toLocaleDateString()}

${text}`],
    { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "my-reflection.txt";
  a.click();
}
