const apiBase = process.env.BACKEND_API_URL || "http://localhost:8000";

const defaultHeaders = { "Content-Type": "application/json" } as const;

type FetchOpts = Omit<RequestInit, "body"> & { body?: unknown };

async function apiJson<T>(path: string, init?: FetchOpts): Promise<T> {
  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: { ...defaultHeaders, ...(init?.headers || {}) },
    body: init?.body !== undefined ? JSON.stringify(init.body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

async function apiBuffer(path: string): Promise<ArrayBuffer> {
  const res = await fetch(`${apiBase}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  return res.arrayBuffer();
}

// --------- Generators ---------
export const generateCpts = (topic: string, model = "gpt-4.1-mini") =>
  apiJson<{ code: string; description: string; source?: string }[]>("/cpt/generate", {
    method: "POST",
    body: { topic, model },
  });

export const fetchCptDescription = (code: string, useLlmFallback = false) =>
  apiJson<string>(`/cpt/${code}/description?use_llm_fallback=${useLlmFallback}`);

// --------- Research runs ---------
export const runSection = (
  sectionId: number,
  payload: {
    cpt: string;
    context?: string;
    model?: string;
    use_cache?: boolean;
  },
) => apiJson(`/research/sections/${sectionId}/run`, { method: "POST", body: payload });

export const runAllSections = (payload: {
  cpt: string;
  context?: string;
  model?: string;
  sections_to_run?: number[];
  use_cache?: boolean;
}) => apiJson("/research/run-all", { method: "POST", body: payload });

export const getSection1Cache = (cpt: string) =>
  apiJson(`/research/sections/1/cached?cpt=${encodeURIComponent(cpt)}`);

// --------- Chat per section ---------
export const sendSectionChat = (
  sectionId: string,
  payload: {
    session_id: string;
    cpt: string;
    section_id: string;
    question: string;
    model?: string;
  },
) => apiJson(`/research/sections/${sectionId}/chat`, { method: "POST", body: payload });

export const fetchSectionChat = (sectionId: string, sessionId: string, cpt: string) =>
  apiJson(
    `/research/sections/${sectionId}/chat?session_id=${encodeURIComponent(sessionId)}&cpt=${encodeURIComponent(cpt)}`,
  );

// --------- Sessions ---------
export const listSessions = () => apiJson("/sessions");

export const createSession = (payload: {
  session_id: string;
  topic: string;
  cpt: string;
  model: string;
  analysis_result: string;
}) => apiJson("/sessions", { method: "POST", body: payload });

export const fetchSession = (sessionId: string) =>
  apiJson(`/sessions/${encodeURIComponent(sessionId)}`);

export const updateSessionTopic = (sessionId: string, topic: string) =>
  apiJson(`/sessions/${encodeURIComponent(sessionId)}`, { method: "PATCH", body: { topic } });

export const deleteSession = (sessionId: string) =>
  apiJson(`/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" });

// --------- Notes ---------
export const fetchNotes = (sessionId: string, cpt: string) =>
  apiJson(`/notes?session_id=${encodeURIComponent(sessionId)}&cpt=${encodeURIComponent(cpt)}`);

export const saveNotes = (payload: { session_id: string; cpt: string; notes: string }) =>
  apiJson("/notes", { method: "PUT", body: payload });

// --------- Accuracy feedback ---------
export const saveAccuracyFeedback = (payload: {
  session_id: string;
  cpt: string;
  section_id: string;
  rating: string;
  reason?: string;
}) => apiJson("/feedback/accuracy", { method: "POST", body: payload });

export const fetchAccuracyFeedback = (sessionId: string, cpt: string, sectionId: string) =>
  apiJson(
    `/feedback/accuracy?session_id=${encodeURIComponent(sessionId)}&cpt=${encodeURIComponent(cpt)}&section_id=${encodeURIComponent(sectionId)}`,
  );

// --------- Exports ---------
export const fetchExcel = (sessionId: string) =>
  apiBuffer(`/export/excel?session_id=${encodeURIComponent(sessionId)}`);

export const fetchPdf = (sessionId: string) =>
  apiBuffer(`/export/pdf?session_id=${encodeURIComponent(sessionId)}`);
