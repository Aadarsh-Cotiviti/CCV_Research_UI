"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import {
  Shield,
  FileText,
  LinkIcon,
  Table as TableIcon,
  BookOpen,
  AlertTriangle,
} from "lucide-react";
import { FC, ReactNode, useMemo, useState } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownComponents } from "@/components/MarkdownComponents";

type NcciResult = components["schemas"]["NcciResult"];
type PtpTablesForCpt = components["schemas"]["PtpTablesForCpt"];
type PtpTable = components["schemas"]["PtpTable"];
type CPTDescription = components["schemas"]["CPTDescription"];

type NcciPayload =
  | { section_num: number; status: "success"; data: NcciResult | string }
  | { section_num: number; status: "error"; error: string };

const isNcciResult = (raw: unknown): raw is NcciResult => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as NcciResult;
  return (
    typeof candidate.analysis_content === "string" &&
    typeof candidate.ptp_tables_by_cpt === "object" &&
    typeof candidate.ncci_manual_by_cpt === "object" &&
    typeof candidate.cpt_descriptions === "object" &&
    Array.isArray(candidate.neighboring_codes)
  );
};

const parseNcciContent = (content: string): NcciResult | null => {
  const tryParse = (raw: unknown, allowNested = true): NcciResult | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isNcciResult(raw)) return raw;

    const maybePayload = raw as Partial<NcciPayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested NCCI data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isNcciResult(maybePayload.data) ? maybePayload.data : null;
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
    console.warn("Failed to parse NCCI compliance response", error);
    return null;
  }

  return null;
};

const SectionHeading: FC<{ id: string; children: ReactNode }> = ({ id, children }) => (
  <div className="flex items-center gap-2 mt-6 mb-3" id={id}>
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
  <div className="flex items-center gap-2 mt-4 mb-2" id={id}>
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

interface PtpTableDisplayProps {
  modifierLabel: string;
  ptpTable: PtpTable | null | undefined;
}

const PtpTableDisplay: FC<PtpTableDisplayProps> = ({ modifierLabel, ptpTable }) => {
  if (!ptpTable || ptpTable.data.length === 0) {
    return (
      <div className="p-4 bg-muted/20 border border-muted rounded-lg text-center text-muted-foreground text-sm">
        No PTP edits found for {modifierLabel}
      </div>
    );
  }

  const columns = Object.keys(ptpTable.data[0]);

  return (
    <div className="border border-muted rounded-lg overflow-hidden">
      <div className="border-b border-muted px-4 py-2">
        <h6 className="font-semibold  text-sm flex items-center gap-2">
          <TableIcon className="size-4" />
          {modifierLabel} ({ptpTable.record_count} records)
        </h6>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left font-semibold text-foreground border-b border-muted"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-muted">
            {ptpTable.data.map((row, idx) => (
              <tr key={idx} className="hover:bg-muted/30 transition-colors">
                {columns.map((col) => {
                  const value = row[col];
                  const displayValue =
                    value === null || value === undefined ? "N/A" : String(value);
                  return (
                    <td key={col} className="px-3 py-2 text-foreground">
                      {displayValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

interface CptPtpSectionProps {
  cptCode: string;
  ptpData: PtpTablesForCpt;
}

const CptPtpSection: FC<CptPtpSectionProps> = ({ cptCode, ptpData }) => {
  const sourceColor = LEGEND[ptpData.source]?.color || "muted-foreground";

  return (
    <div className="border border-muted rounded-lg p-4 bg-muted/20" id={`ptp-${cptCode}`}>
      <div className="flex items-center justify-between mb-3">
        <SubsectionHeading id={`ptp-${cptCode}`}>CPT {cptCode}</SubsectionHeading>
        <span
          className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium`}
          title={`Source: ${ptpData.source}`}
        >
          {ptpData.source}
        </span>
      </div>

      {ptpData.has_data ? (
        <div className="space-y-3">
          <PtpTableDisplay modifierLabel="Modifier 0" ptpTable={ptpData.modifier_0} />
          <PtpTableDisplay modifierLabel="Modifier 1" ptpTable={ptpData.modifier_1} />
        </div>
      ) : (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg text-center">
          <p className="text-sm text-foreground font-semibold">No PTP Edits Found</p>
          <p className="text-xs text-muted-foreground mt-1">
            This CPT code has no documented NCCI PTP edit conflicts
          </p>
        </div>
      )}
    </div>
  );
};

interface NcciManualSectionProps {
  cptCode: string;
  manualData: Record<string, unknown>;
}

const NcciManualSection: FC<NcciManualSectionProps> = ({ cptCode, manualData }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const hasContent = Object.keys(manualData).length > 0;

  if (!hasContent) return null;

  return (
    <div className="border border-muted rounded-lg bg-muted/20">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen className="size-5 text-blue-500" />
          <h5 className="font-semibold text-foreground">NCCI Manual Excerpts - CPT {cptCode}</h5>
        </div>
        <span className="text-xs text-muted-foreground">{isExpanded ? "Collapse" : "Expand"}</span>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-muted">
          <div className="mt-3 space-y-3">
            {Object.entries(manualData).map(([key, value]) => (
              <div key={key} className="bg-blue-500/10 border border-blue-500/30 rounded p-3">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-1">
                  {key}
                </p>
                <div className="text-sm text-foreground whitespace-pre-wrap">
                  {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const CPTDescriptionCard: FC<{ cptCode: string; description: CPTDescription }> = ({
  cptCode,
  description,
}) => {
  const sourceColor = LEGEND[description.source]?.color || "muted-foreground";

  return (
    <div className="border border-muted rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-foreground">
          <strong className={`text-${sourceColor}`}>CPT {description.cpt_code}</strong>
          <span className="ml-2">{description.description}</span>
        </p>
        <span
          className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium shrink-0`}
          title={`Source: ${description.source}`}
        >
          {description.source}
        </span>
      </div>
    </div>
  );
};

const NcciComplianceContent: FC<{ data: NcciResult }> = ({ data }) => {
  const sortedPtpCptCodes = useMemo(() => {
    return Object.keys(data.ptp_tables_by_cpt).sort((a, b) => {
      const numA = Number(a);
      const numB = Number(b);
      if (Number.isFinite(numA) && Number.isFinite(numB)) return numA - numB;
      return a.localeCompare(b);
    });
  }, [data.ptp_tables_by_cpt]);

  const sortedCptDescriptions = useMemo(() => {
    const codes = Object.entries(data.cpt_descriptions);
    return codes.sort(([codeA], [codeB]) => {
      const numA = Number(codeA);
      const numB = Number(codeB);
      if (Number.isFinite(numA) && Number.isFinite(numB)) return numA - numB;
      return codeA.localeCompare(codeB);
    });
  }, [data.cpt_descriptions]);

  const hasManualData = Object.keys(data.ncci_manual_by_cpt).length > 0;

  return (
    <div className="select-text cursor-text">
      <LegendCard />

      {/* Analysis Section */}
      <SectionHeading id="ncci-analysis">
        <span className="flex items-center gap-2">
          <Shield className="size-5 text-muted-foreground" aria-hidden />
          <span>NCCI Compliance Analysis</span>
        </span>
      </SectionHeading>

      <div className="prose prose-sm max-w-none mt-3 mb-6">
        <div className="bg-muted/30 rounded-lg p-4 border border-muted">
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {data.analysis_content}
          </Markdown>
        </div>
      </div>

      {/* Neighboring Codes */}
      {data.neighboring_codes.length > 0 && (
        <div className="mb-6 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <p className="text-sm font-semibold text-foreground mb-1">Neighboring Codes Analyzed:</p>
          <p className="text-sm text-foreground">{data.neighboring_codes.join(", ")}</p>
        </div>
      )}

      <hr className="my-6 border-muted" />

      {/* PTP Edit Tables */}
      <SectionHeading id="ptp-edits">
        <span className="flex items-center gap-2">
          <AlertTriangle className="size-5 text-muted-foreground" aria-hidden />
          <span>PTP Edit Tables</span>
        </span>
      </SectionHeading>

      <p className="text-sm text-muted-foreground mb-4">
        Procedure-to-Procedure (PTP) edits identify code pairs that should not be billed together.
      </p>

      {sortedPtpCptCodes.length > 0 ? (
        <div className="space-y-4">
          {sortedPtpCptCodes.map((cptCode) => (
            <CptPtpSection
              key={cptCode}
              cptCode={cptCode}
              ptpData={data.ptp_tables_by_cpt[cptCode]}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">No PTP edit data available.</p>
      )}

      {/* NCCI Manual Excerpts */}
      {hasManualData && (
        <>
          <hr className="my-6 border-muted" />
          <SectionHeading id="ncci-manual">
            <span className="flex items-center gap-2">
              <BookOpen className="size-5 text-muted-foreground" aria-hidden />
              <span>NCCI Manual Excerpts</span>
            </span>
          </SectionHeading>
          <p className="text-sm text-muted-foreground mb-4">
            Relevant sections from the NCCI Policy Manual retrieved via RAG.
          </p>
          <div className="space-y-3">
            {Object.entries(data.ncci_manual_by_cpt).map(([cptCode, manualData]) => (
              <NcciManualSection key={cptCode} cptCode={cptCode} manualData={manualData} />
            ))}
          </div>
        </>
      )}

      {/* CPT Descriptions */}
      {sortedCptDescriptions.length > 0 && (
        <>
          <hr className="my-6 border-muted" />
          <SectionHeading id="cpt-descriptions">
            <span className="flex items-center gap-2">
              <FileText className="size-5 text-muted-foreground" aria-hidden />
              <span>CPT Code Descriptions</span>
            </span>
          </SectionHeading>
          <p className="font-semibold text-foreground mb-3">
            {sortedCptDescriptions.length} code(s) referenced:
          </p>
          <div className="grid grid-cols-1 gap-3">
            {sortedCptDescriptions.map(([cptCode, description]) => (
              <CPTDescriptionCard key={cptCode} cptCode={cptCode} description={description} />
            ))}
          </div>
        </>
      )}
    </div>
  );
};

const NcciComplianceRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(() => parseNcciContent(message.content), [message.content]);

  if (!parsedData) return <>{message.content}</>;

  return <NcciComplianceContent data={parsedData} />;
};

export default NcciComplianceRenderer;
