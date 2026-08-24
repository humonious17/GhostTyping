export function RepeatUseCheckinModal({ open, onClose, personLabel }: {
  open: boolean; onClose: () => void; personLabel: string;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[90] bg-black/40 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4">
        <h2 className="text-lg font-semibold">Quick check-in</h2>
        <p className="text-gray-700">
          This is your third-ish session with {personLabel}. No judgment — just worth asking:
        </p>
        <ul className="text-gray-700 space-y-2 text-sm">
          <li>• After each session, do things feel a little lighter, or heavier?</li>
          <li>• Is this helping you put it down, or keeping it alive?</li>
        </ul>
        <p className="text-sm text-gray-600">
          If talking with a real person would help, that's not failure — that's what this
          exercise can't be. Consider sharing your saved summary with your therapist,
          or a friend.
        </p>
        <div className="flex gap-2">
          <button onClick={onClose}
            className="flex-1 py-2.5 rounded-xl bg-indigo-600 text-white font-medium">
            Thanks, continue
          </button>
        </div>
        <a href="https://www.psychologytoday.com/us/therapists"
           target="_blank" rel="noreferrer"
           className="block text-center text-sm text-indigo-600 underline">
          Find a therapist near me →
        </a>
      </div>
    </div>
  );
}
