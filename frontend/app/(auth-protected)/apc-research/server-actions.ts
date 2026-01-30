import "server-only";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { generateCpts } from "@/lib/backendClient";
import { components } from "@/lib/api-types";

export const fetchCptCodes = async (topic: string, model: ResponsesModel) => {
  const response = await generateCpts(topic, model);
  if (response.error) {
    throw new Error(`CPT generation failed: ${response.error}`);
  }
  return response.data;
};

export type CptData = components["schemas"]["CptCodeResult"];
