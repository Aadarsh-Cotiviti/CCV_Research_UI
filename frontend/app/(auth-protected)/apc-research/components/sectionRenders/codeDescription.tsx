"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import { LinkIcon, RefreshCcw, Search } from "lucide-react";
import { FC, ReactNode, useMemo } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";

type CodeDescriptionResult = components["schemas"]["CodeDescriptionResult"];
type CodeDescriptionNeighbor = CodeDescriptionResult["neighbouring_codes"][number];
type CodeDescriptionRecodingEntry = {
  cpt_code?: string;
  description?: string;
  description_source?: string;
  llm_recoding?: {
    recoding_possibilities?: string;
  };
};
type CodeDescriptionPayload =
  | { section_num: number; status: "success"; data: CodeDescriptionResult | string }
  | { section_num: number; status: "error"; error: string };

const isCodeDescriptionResult = (raw: unknown): raw is CodeDescriptionResult => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as CodeDescriptionResult;
  return (
    Array.isArray(candidate.neighbouring_codes) &&
    Array.isArray(candidate.internal_recoding_result) &&
    Array.isArray(candidate.no_change_results)
  );
};

const parseCodeDescriptionContent = (content: string): CodeDescriptionResult | null => {
  const tryParse = (raw: unknown, allowNested = true): CodeDescriptionResult | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isCodeDescriptionResult(raw)) return raw;

    const maybePayload = raw as Partial<CodeDescriptionPayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested code description data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isCodeDescriptionResult(maybePayload.data) ? maybePayload.data : null;
      }
    }

    return null;
  };

  try {
    const parsed = JSON.parse(content) as unknown;
    const result = tryParse(parsed);
    if (result) return result;

    if (typeof parsed === "string") {
      return tryParse(JSON.parse(parsed), false);
    }
  } catch (error) {
    console.warn("Failed to parse code description response", error);
    return null;
  }

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

const CodeLine: FC<{ code: CodeDescriptionNeighbor }> = ({ code }) => (
  <p className="leading-relaxed text-base text-foreground">
    <strong className={`text-${LEGEND[code.source].color}`}>{`CPT ${code.cpt_code}`}</strong>:
    <span className="ml-1 text-foreground" title={`Source: ${code.source}`}>
      {code.description}
    </span>
  </p>
);

const RecodingCard: FC<{ entry: CodeDescriptionRecodingEntry }> = ({ entry }) => (
  <div
    className="border border-muted rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors"
    id={`cpt-${entry.cpt_code ?? "unknown"}`}
  >
    <SubsectionHeading id={`cpt-${entry.cpt_code ?? "unknown"}`}>
      CPT {entry.cpt_code ?? "Unknown"}
    </SubsectionHeading>
    <p className="text-sm text-foreground">
      <strong>Description:</strong> <span>{entry.description ?? "Description not available"}</span>
    </p>
    <p className="mt-3 font-semibold text-foreground">Potential Re-coding/Bundling Scenarios:</p>
    <div className="mt-1 whitespace-pre-wrap text-foreground text-sm leading-6">
      {entry.llm_recoding?.recoding_possibilities ?? "No recoding analysis available."}
    </div>
  </div>
);

const CodeDescriptionContent: FC<{ data: CodeDescriptionResult }> = ({ data }) => {
  const neighbouringCodes = useMemo(
    () =>
      [...((data.neighbouring_codes as CodeDescriptionNeighbor[] | undefined) || [])].sort(
        (a, b) => {
          const aCode = String(a?.cpt_code ?? "");
          const bCode = String(b?.cpt_code ?? "");
          const aNum = Number(aCode);
          const bNum = Number(bCode);

          if (Number.isFinite(aNum) && Number.isFinite(bNum)) return aNum - bNum;
          return aCode.localeCompare(bCode);
        },
      ),
    [data.neighbouring_codes],
  );

  const recodingEntries = useMemo(
    () =>
      [...((data.internal_llm_recoding_result as CodeDescriptionRecodingEntry[]) || [])].sort(
        (a, b) => {
          const aCode = String(a?.cpt_code ?? "");
          const bCode = String(b?.cpt_code ?? "");
          const aNum = Number(aCode);
          const bNum = Number(bCode);

          if (Number.isFinite(aNum) && Number.isFinite(bNum)) return aNum - bNum;
          return aCode.localeCompare(bCode);
        },
      ),
    [data.internal_llm_recoding_result],
  );

  return (
    <div className="select-text cursor-text">
      <LegendCard />
      <SectionHeading id="neighboring-cpt-codes-with-target-cpt-code">
        <span className="flex items-center gap-2">
          <Search className="size-5 text-muted-foreground" aria-hidden />
          <span>Neighboring CPT Codes with Target CPT Code</span>
        </span>
      </SectionHeading>
      <p className="font-semibold text-foreground">
        Identified {neighbouringCodes.length} related codes (in ascending order):
      </p>
      <div className="space-y-3 mt-2">
        {neighbouringCodes.map((code) => (
          <CodeLine key={`${code.cpt_code}-${code.source}`} code={code} />
        ))}
      </div>

      <hr className="my-6 border-muted" />

      <SectionHeading id="re-coding-and-bundling-analysis">
        <span className="flex items-center gap-2">
          <RefreshCcw className="size-5 text-muted-foreground" aria-hidden />
          <span>Re-coding and Bundling Analysis</span>
        </span>
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

const CodeDescriptionRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(() => parseCodeDescriptionContent(message.content), [message.content]);
  console.log("Parsed Code Description Data:", parsedData);
  if (!parsedData) return <>{message.content}</>;

  return <CodeDescriptionContent data={parsedData} />;
};

export default CodeDescriptionRenderer;
