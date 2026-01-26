"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import type { components } from "@/lib/api-types";
import { LinkIcon } from "lucide-react";
import { FC, ReactNode, useMemo } from "react";

type Section1Data = components["schemas"]["Section1Data"];
type InternalLlmRecodingResult = components["schemas"]["InternalLlmRecodingResult"];
type NeighbouringCode = components["schemas"]["NeighbouringCode"];

type Section1Payload =
  | { section_num: number; status: "success"; data: Section1Data | string }
  | { section_num: number; status: "error"; error: string }
  | Section1Data;

const isSection1Data = (value: unknown): value is Section1Data => {
  if (!value || typeof value !== "object") return false;
  const data = value as Partial<Section1Data>;

  return (
    Array.isArray(data.neighbouring_codes) &&
    Array.isArray(data.internal_recoding_result) &&
    Array.isArray(data.internal_llm_recoding_result) &&
    Array.isArray(data.external_full_llm_result)
  );
};

const parseSection1Content = (content: string): Section1Data | null => {
  const stripCodeFence = (raw: string) => {
    const fenceMatch = raw.match(/^```[a-zA-Z]*\n([\s\S]*?)\n```$/);
    if (fenceMatch) return fenceMatch[1];
    return raw;
  };

  const tryParse = (raw: unknown, allowNested = true): Section1Data | null => {
    if (isSection1Data(raw)) return raw;
    if (!raw || typeof raw !== "object") return null;

    const maybePayload = raw as Partial<Section1Payload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (isSection1Data(maybePayload.data)) return maybePayload.data;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested section 1 data", error);
          return null;
        }
      }
    }

    return null;
  };

  const attemptJson = (raw: string, allowNested = true): Section1Data | null => {
    try {
      const parsed = JSON.parse(raw) as unknown;
      const result = tryParse(parsed, allowNested);
      if (result) return result;

      if (typeof parsed === "string") {
        return attemptJson(parsed, false);
      }
    } catch (error) {
      return null;
    }
    return null;
  };

  const normalized = stripCodeFence(content.trim());

  const direct = attemptJson(normalized);
  if (direct) return direct;

  const firstBrace = normalized.indexOf("{");
  const lastBrace = normalized.lastIndexOf("}");
  if (firstBrace >= 0 && lastBrace > firstBrace) {
    const slice = normalized.slice(firstBrace, lastBrace + 1);
    const sliced = attemptJson(slice);
    if (sliced) return sliced;
  }

  console.warn("Failed to parse section 1 response", content);
  return null;
};

const SectionHeading: FC<{ id: string; children: ReactNode }> = ({ id, children }) => (
  <div className="flex items-center gap-2 mt-4 mb-2" id={id}>
    <h3 className="text-foreground text-xl font-semibold">{children}</h3>
    <a
      href={`#${id}`}
      className="text-muted-foreground hover:text-foreground"
      aria-label="Link to this section"
    >
      <LinkIcon className="size-4" />
    </a>
  </div>
);

const SubsectionHeading: FC<{ id: string; children: ReactNode }> = ({ id, children }) => (
  <div className="flex items-center gap-2 mt-3 mb-1" id={id}>
    <h4 className="text-foreground text-lg font-semibold">{children}</h4>
    <a
      href={`#${id}`}
      className="text-muted-foreground hover:text-foreground"
      aria-label="Link to this subsection"
    >
      <LinkIcon className="size-4" />
    </a>
  </div>
);

const CodeLine: FC<{ code: NeighbouringCode }> = ({ code }) => (
  <p className="leading-relaxed text-base text-foreground">
    <strong>{`CPT ${code.cpt_code}`}</strong>:
    <span className="ml-1 text-primary" title={`Source: ${code.source}`}>
      {code.description}
    </span>
  </p>
);

const RecodingCard: FC<{ entry: InternalLlmRecodingResult }> = ({ entry }) => (
  <div
    className="border border-border rounded-lg p-4 shadow-sm bg-card"
    id={`cpt-${entry.cpt_code}`}
  >
    <SubsectionHeading id={`cpt-${entry.cpt_code}`}>CPT {entry.cpt_code}</SubsectionHeading>
    <p className="text-sm text-foreground">
      <strong>Description:</strong> <span className="text-primary">{entry.description}</span>
    </p>
    <p className="mt-3 font-semibold text-foreground">Potential Re-coding/Bundling Scenarios:</p>
    <div className="mt-1 whitespace-pre-wrap text-foreground text-sm leading-6">
      {entry.llm_recoding.recoding_possibilities}
    </div>
  </div>
);

const SectionOneContent: FC<{ data: Section1Data }> = ({ data }) => {
  const neighbouringCodes = useMemo(
    () =>
      [...(data.neighbouring_codes || [])].sort((a, b) => {
        const aNum = Number(a.cpt_code);
        const bNum = Number(b.cpt_code);

        if (Number.isFinite(aNum) && Number.isFinite(bNum)) return aNum - bNum;
        return a.cpt_code.localeCompare(b.cpt_code);
      }),
    [data.neighbouring_codes],
  );

  const recodingEntries = useMemo(
    () =>
      [...(data.internal_llm_recoding_result || [])].sort((a, b) => {
        const aNum = Number(a.cpt_code);
        const bNum = Number(b.cpt_code);

        if (Number.isFinite(aNum) && Number.isFinite(bNum)) return aNum - bNum;
        return a.cpt_code.localeCompare(b.cpt_code);
      }),
    [data.internal_llm_recoding_result],
  );

  return (
    <div className="px-0 rounded-sm select-text cursor-text">
      <SectionHeading id="neighboring-cpt-codes-with-target-cpt-code">
        Neighboring CPT Codes with Target CPT Code
      </SectionHeading>
      <p className="font-semibold text-foreground">
        Identified {neighbouringCodes.length} related codes (in ascending order):
      </p>
      <div className="space-y-3 mt-2">
        {neighbouringCodes.map((code) => (
          <CodeLine key={`${code.cpt_code}-${code.source}`} code={code} />
        ))}
      </div>

      <hr className="my-6 border-border" />

      <SectionHeading id="re-coding-and-bundling-analysis">
        Re-coding and Bundling Analysis
      </SectionHeading>
      <p className="font-semibold text-foreground">
        Codes with local descriptions and LLM-generated recoding analysis:
      </p>

      {recodingEntries.length > 0 ? (
        <div className="space-y-5 mt-3">
          {recodingEntries.map((entry) => (
            <RecodingCard key={`${entry.cpt_code}-${entry.description_source}`} entry={entry} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground mt-2">No recoding analysis available.</p>
      )}
    </div>
  );
};

const SectionOneRenderer: AssistantRenderer = ({ message, defaultRenderer }) => {
  const parsedData = useMemo(() => parseSection1Content(message.content), [message.content]);

  if (!parsedData) return <>{defaultRenderer()}</>;

  return (
    <div className="flex gap-2 mt-4 w-full" data-message-id={message.id}>
      <div className="flex flex-col w-full">
        <SectionOneContent data={parsedData} />
      </div>
    </div>
  );
};

export const sectionRenderers: AssistantRenderer[] = [SectionOneRenderer];
