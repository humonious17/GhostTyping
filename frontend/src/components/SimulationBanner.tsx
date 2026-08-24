export function SimulationBanner({ name }: { name: string }) {
  return (
    <div
      role="status"
      className="sticky top-0 z-50 bg-amber-100 border-b-2 border-amber-500
                 px-4 py-2 text-sm font-medium text-amber-900 select-none"
    >
      Simulated style — not {name}. This is a writing exercise, not a real conversation.
    </div>
  );
}
