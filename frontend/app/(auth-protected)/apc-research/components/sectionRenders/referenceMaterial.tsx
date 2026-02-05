"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import { Library, FileText, LinkIcon } from "lucide-react";
import { FC, ReactNode, useMemo } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownComponents } from "@/components/MarkdownComponents";

type ReferenceMaterialResult = components["schemas"]["ReferenceMaterialResult"];
type CPTDescription = components["schemas"]["CPTDescription"];

type ReferenceMaterialPayload =
  | { section_num: number; status: "success"; data: ReferenceMaterialResult | string }
  | { section_num: number; status: "error"; error: string };

const isReferenceMaterialResult = (raw: unknown): raw is ReferenceMaterialResult => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as ReferenceMaterialResult;
  return (
    typeof candidate.analysis_content === "string" &&
    typeof candidate.cpt_descriptions === "object" &&
    candidate.cpt_descriptions !== null
  );
};

const parseReferenceMaterialContent = (content: string): ReferenceMaterialResult | null => {
  const tryParse = (raw: unknown, allowNested = true): ReferenceMaterialResult | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isReferenceMaterialResult(raw)) return raw;

    const maybePayload = raw as Partial<ReferenceMaterialPayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested reference material data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isReferenceMaterialResult(maybePayload.data) ? maybePayload.data : null;
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
    console.warn("Failed to parse reference material response", error);
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

const CPTCodeCard: FC<{ cptCode: string; description: CPTDescription }> = ({
  cptCode,
  description,
}) => {
  const sourceColor = LEGEND[description.source]?.color || "muted-foreground";

  return (
    <div
      className="border border-muted rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors"
      id={`cpt-${cptCode}`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-lg font-semibold text-foreground">CPT {description.cpt_code}</h4>
        <span
          className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium`}
          title={`Source: ${description.source}`}
        >
          {description.source}
        </span>
      </div>
      <p className="text-sm text-foreground leading-relaxed">{description.description}</p>
    </div>
  );
};

const ReferenceMaterialContent: FC<{ data: ReferenceMaterialResult }> = ({ data }) => {
  const sortedCptCodes = useMemo(() => {
    const codes = Object.entries(data.cpt_descriptions || {});
    return codes.sort(([codeA], [codeB]) => {
      const numA = Number(codeA);
      const numB = Number(codeB);

      if (Number.isFinite(numA) && Number.isFinite(numB)) {
        return numA - numB;
      }
      return codeA.localeCompare(codeB);
    });
  }, [data.cpt_descriptions]);

  return (
    <div className="select-text cursor-text">
      <LegendCard />

      {/* Reference Analysis Section */}
      <SectionHeading id="reference-material-analysis">
        <span className="flex items-center gap-2">
          <Library className="size-5 text-muted-foreground" aria-hidden />
          <span>Reference Material Review</span>
        </span>
      </SectionHeading>

      <div className="prose prose-sm max-w-none mt-3 mb-6">
        <div className="bg-muted/30 rounded-lg p-4 border border-muted">
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {data.analysis_content}
          </Markdown>
        </div>
      </div>

      <hr className="my-6 border-muted" />

      {/* CPT Codes Section */}
      <SectionHeading id="referenced-cpt-codes">
        <span className="flex items-center gap-2">
          <FileText className="size-5 text-muted-foreground" aria-hidden />
          <span>Referenced CPT Codes</span>
        </span>
      </SectionHeading>

      <p className="font-semibold text-foreground mb-3">
        {sortedCptCodes.length} {sortedCptCodes.length === 1 ? "code" : "codes"} referenced in analysis:
      </p>

      {sortedCptCodes.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 mt-3">
          {sortedCptCodes.map(([cptCode, description]) => (
            <CPTCodeCard key={cptCode} cptCode={cptCode} description={description} />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground mt-2">No CPT codes available.</p>
      )}

      {/* Source Information */}
      <div className="mt-6 p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <Library className="size-4 text-indigo-400" />
          <h4 className="font-semibold text-foreground text-sm">Analysis Source</h4>
        </div>
        <p className="text-sm text-muted-foreground">
          This analysis was generated from reference materials and supporting documentation related to
          the specified CPT codes. The information is synthesized to provide context and insights for
          medical coding decisions.
        </p>
      </div>
    </div>
  );
};

const ReferenceMaterialRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(
    () => parseReferenceMaterialContent(message.content),
    [message.content]
  );

  if (!parsedData) return <>{message.content}</>;

  return <ReferenceMaterialContent data={parsedData} />;
};

export default ReferenceMaterialRenderer;
