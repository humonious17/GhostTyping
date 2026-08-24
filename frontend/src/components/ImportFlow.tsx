import { useState } from "react";
import { api } from "../api";

export function ImportFlow({ onImported }: { onImported: (threadId: string) => void }) {
	const [label, setLabel] = useState("");
	const [rawText, setRawText] = useState("");
	const [error, setError] = useState<string | null>(null);
	const [saving, setSaving] = useState(false);

	const submit = async () => {
		setSaving(true);
		setError(null);
		try {
			const result = await api.importThread(label, rawText);
			onImported(result.thread_id);
		} catch (cause) {
			setError(cause instanceof Error ? cause.message : "Import failed");
		} finally {
			setSaving(false);
		}
	};

	return <form className="max-w-xl mx-auto p-6 space-y-4" onSubmit={e => { e.preventDefault(); void submit(); }}>
		<h1 className="text-xl font-semibold">Start a writing exercise</h1>
		<input value={label} onChange={e => setLabel(e.target.value)} maxLength={40} required placeholder="Person label" className="w-full border rounded p-3" />
		<textarea value={rawText} onChange={e => setRawText(e.target.value)} required rows={14} placeholder="Paste the conversation here" className="w-full border rounded p-3" />
		{error && <p role="alert" className="text-red-700">{error}</p>}
		<button disabled={saving || !label.trim() || !rawText.trim()} className="px-5 py-2 rounded bg-indigo-600 text-white disabled:bg-gray-300">
			{saving ? "Importing..." : "Import conversation"}
		</button>
	</form>;
}
