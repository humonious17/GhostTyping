import { useEffect, useState } from "react";
import { api } from "./api";
import { AgeGate } from "./components/AgeGate";
import { Onboarding } from "./pages/Onboarding";

type Gates = { age_confirmed_18_plus: boolean; onboarded: boolean };

export function App() {
  const [gates, setGates] = useState<Gates | null>(null);
  useEffect(() => { api.gates().then(setGates).catch(() => setGates({ age_confirmed_18_plus: false, onboarded: false })); }, []);
  if (!gates) return <p className="p-6">Loading...</p>;
  if (!gates.age_confirmed_18_plus) return <AgeGate onConfirm={() => setGates({ ...gates, age_confirmed_18_plus: true })} />;
  if (!gates.onboarded) return <Onboarding onAck={() => setGates({ ...gates, onboarded: true })} />;
  return <main className="p-6"><h1 className="text-xl font-semibold">Ghost Typing</h1></main>;
}