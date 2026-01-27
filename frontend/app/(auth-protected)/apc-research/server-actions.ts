import "server-only";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { generateCpts, runAllSections } from "@/lib/backendClient";
import { components } from "@/lib/api-types";

export type ResearchSections = components["schemas"]["ResearchRunResult"]["sections"];

export const createResearch = async (
  targetCpt: string,
  contextDetails: string,
  model: ResponsesModel,
) => {
  console.log(
    `Creating research for CPT: ${targetCpt} with model: ${model} and context: ${contextDetails}`,
  );
  const response = await runAllSections({
    context: contextDetails,
    cpt: targetCpt,
    model: model,
    use_cache: true,
  });
  console.log(JSON.stringify(response));
  if (response.error) {
    throw new Error(`Research run failed: ${response.error}`);
  }
  return response.data;
};

export const fetchCptCodes = async (topic: string, model: ResponsesModel) => {
  const response = await generateCpts(topic, model);
  if (response.error) {
    throw new Error(`CPT generation failed: ${response.error}`);
  }
  return response.data;
};

export type CptData = components["schemas"]["CptCodeResult"];
