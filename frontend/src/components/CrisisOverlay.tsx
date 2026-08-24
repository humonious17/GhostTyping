export function CrisisOverlay({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[100] bg-black/70 flex items-center justify-center p-4"
         role="alertdialog" aria-modal="true" aria-labelledby="crisis-title">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4">
        <h2 id="crisis-title" className="text-lg font-semibold">
          Stepping out of the exercise
        </h2>
        <p className="text-gray-700">
          What you wrote matters more than anything else right now. If you're thinking
          about hurting yourself, please reach out to real support:
        </p>
        <ul className="text-gray-800 space-y-2">
          <li>🇺🇸 Call or text <strong>988</strong> (Suicide &amp; Crisis Lifeline)</li>
          <li>🌍 <a href="https://findahelpline.com" target="_blank" rel="noreferrer"
                className="text-indigo-600 underline">findahelpline.com</a> for local options anywhere</li>
          <li>💬 Tell someone you trust, tonight</li>
        </ul>
        <button autoFocus onClick={onClose}
          className="w-full py-2.5 rounded-xl bg-indigo-600 text-white font-medium">
          I've seen this
        </button>
        <p className="text-xs text-gray-500 text-center">
          The session stays paused until you're ready. Nothing was sent anywhere.
        </p>
      </div>
    </div>
  );
}
