import OpenAI, { AzureOpenAI } from "openai";
import { AzureClientOptions } from "openai/azure";
import { AutoParseableResponseFormat } from "openai/lib/parser.mjs";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { ChatRequest, queryllmChatStream } from "./backendClient";

const MODEL_CONFIGS: Partial<Record<ResponsesModel, AzureClientOptions>> = {
  "gpt-4.1": {
    deployment: "gpt-4.1",
    apiKey: process.env["AZURE_OPENAI_API_KEY"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT"],
    apiVersion: "2024-12-01-preview",
  },
  "gpt-4.1-mini": {
    deployment: "gpt-4.1-mini",
    apiKey: process.env["AZURE_OPENAI_API_KEY"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT"],
    apiVersion: "2024-12-01-preview",
  },
  "gpt-4.1-nano": {
    deployment: "gpt-4.1-nano",
    apiKey: process.env["AZURE_OPENAI_API_KEY"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT"],
    apiVersion: "2024-12-01-preview",
  },
  "gpt-5": {
    deployment: "gpt-5",
    apiKey: process.env["AZURE_OPENAI_API_KEY_GPT_5"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT_GPT_5"],
    apiVersion: "2025-01-01-preview",
  },
  "gpt-5-mini": {
    deployment: "gpt-5-mini",
    apiKey: process.env["AZURE_OPENAI_API_KEY_GPT_5_MINI"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT_GPT_5_MINI"],
    apiVersion: "2025-04-01-preview",
  },
  "gpt-5-nano": {
    deployment: "gpt-5-nano",
    apiKey: process.env["AZURE_OPENAI_API_KEY_GPT_5_NANO"],
    endpoint: process.env["AZURE_OPENAI_ENDPOINT_GPT_5_NANO"],
    apiVersion: "2025-01-01-preview",
  },
  "medgemma-27b-multimodal7": {
    baseURL: process.env["MEDGEMMA_MODEL_URL"],
    apiKey: "",
  },
};

export const AVAILABLE_MODELS: ResponsesModel[] = Object.keys(MODEL_CONFIGS);

export const queryllmStream = async (messages: ChatRequest["messages"], model: ResponsesModel) => {
  if (!AVAILABLE_MODELS.includes(model)) throw new Error("Model is not available");
  // const client = new AzureOpenAI(MODEL_CONFIGS[model]);
  // const responseStream = await client.chat.completions.create({
  //   model,
  //   messages,
  //   stream: true,
  // });

  const resp = await queryllmChatStream({
    model,
    messages,
  });
  if (resp.error) {
    throw new Error(`LLM query failed: ${resp.error}`);
  }
  if (!resp.data) {
    throw new Error("LLM query returned no data");
  }

  return resp.data;
};

export const queryllm = async <T = unknown>(
  messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[],
  model: ResponsesModel,
  textFormat?: AutoParseableResponseFormat<T>,
): Promise<T> => {
  if (!AVAILABLE_MODELS.includes(model)) throw new Error("Model is not available");
  const client = new AzureOpenAI(MODEL_CONFIGS[model]);

  const response = await client.chat.completions.parse({
    model,
    messages,
    response_format: textFormat,
  });

  return response.choices[0].message.parsed as T;
};
