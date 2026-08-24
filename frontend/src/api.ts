const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`BASE{BASE}BASE{path}`, {
    headers: { "Content-Type": "application/json", ...opts?.headers },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    // FastAPI wraps our detail objects — surface structured error codes
    throw new ApiError(res.status, body?.detail ?? body);
  }
  return res.json();
}

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) { super(String(status)); }
  get code(): string | undefined {
    return typeof this.detail === "object" && this.detail !== null
      ? (this.detail as any).code : undefined;
  }
  get message(): string {
    return typeof this.detail === "object" && this.detail !== null
      ? (this.detail as any).message ?? "" : String(this.detail);
  }
}

export const api = {
  importThread: (label: string, rawText: string) =>
    request<{ thread_id: string; style_reliable: boolean; grief_redirect_required: boolean }>(
      "/threads", { method: "POST", body: JSON.stringify({ label, raw_text: rawText }) }),

  startSession: (threadId: string, mode: string) =>
    request<{ session_id: string; repeat_use_checkin: boolean }>(
      "/sessions/start", { method: "POST", body: JSON.stringify({ thread_id: threadId, mode }) }),

  send: (sessionId: string, text: string) =>
    request<{ reply: string; crisis_resources_shown: boolean; time_remaining_sec: number }>(
      "/sessions/send", { method: "POST", body: JSON.stringify({ session_id: sessionId, text }) }),

  deleteThread: (threadId: string) =>
    request<{ deleted: boolean; deletion_receipt: string }>(
      `/privacy/threads/${threadId}`, { method: "DELETE" }),
};
