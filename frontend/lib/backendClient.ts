import createClient from "openapi-fetch";
import type { components, paths } from "./api-types";

const apiBase = process.env.BACKEND_API_URL || "http://localhost:8000";

export type GenerateCptRequest = components["schemas"]["GenerateCptRequest"];
export type RunAllRequest = components["schemas"]["RunAllRequest"];
export type ChatRequest = components["schemas"]["ChatRequest"];
export type ApcChatRequest = components["schemas"]["ApcChatRequest"];
const client = createClient<paths>({ baseUrl: apiBase });

async function apiBuffer(path: string): Promise<ArrayBuffer> {
  const res = await fetch(`${apiBase}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status} ${await res.text()}`);
  return res.arrayBuffer();
}

// --------- Generators ---------
export const generateCpts = (
  topic: string,
  model: GenerateCptRequest["model"] = "gpt-4.1-mini",
) => {
  return client.POST("/cpt/generate", { body: { topic, model } });
};

// --------- Research runs ---------
export const runSection = (sectionId: number, payload: RunAllRequest) =>
  client.POST("/research/run/{section_id}", {
    params: { path: { section_id: sectionId } },
    body: payload,
  });
// --------- Chat per section ---------
export const sendSectionChat = (payload: ApcChatRequest) =>
  client.POST("/research/sections/chat", {
    body: payload,
  });

export const queryllmChatStream = (chatReq: ChatRequest) => {
  return client.POST("/chat", {
    body: chatReq,
    parseAs: "stream",
  });
};

// --------- Exports ---------
export const fetchExcel = (sessionId: string) =>
  apiBuffer(`/export/excel?session_id=${encodeURIComponent(sessionId)}`);

export const fetchPdf = (sessionId: string) =>
  apiBuffer(`/export/pdf?session_id=${encodeURIComponent(sessionId)}`);

// --------- Health ---------
export const health = () => client.GET("/health");
