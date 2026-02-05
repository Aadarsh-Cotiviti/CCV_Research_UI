"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import {
  CheckCircle2,
  FileText,
  LinkIcon,
  Cpu,
  Shield,
  DollarSign,
  Calendar,
  Target,
} from "lucide-react";
import { FC, ReactNode, useMemo, useState } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";

type FinalAssessment = components["schemas"]["FinalAssessment"];
type DeviceDescription = components["schemas"]["DeviceDescription"];
type PaymentHistoryEntry = components["schemas"]["PaymentHistoryEntry"];

type FinalAssessmentPayload =
  | { section_num: number; status: "success"; data: FinalAssessment | string }
  | { section_num: number; status: "error"; error: string };

const isFinalAssessment = (raw: unknown): raw is FinalAssessment => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as FinalAssessment;
  return (
    typeof candidate.target_cpt === "string" &&
    typeof candidate.cpt_descriptions === "object" &&
    typeof candidate.ncci_results === "object" &&
    Array.isArray(candidate.device_codes) &&
    typeof candidate.payment_history === "object" &&
    typeof candidate.update_time === "string"
  );
};

const parseFinalAssessmentContent = (content: string): FinalAssessment | null => {
  const tryParse = (raw: unknown, allowNested = true): FinalAssessment | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isFinalAssessment(raw)) return raw;

    const maybePayload = raw as Partial<FinalAssessmentPayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested final assessment data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isFinalAssessment(maybePayload.data) ? maybePayload.data : null;
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
    console.warn("Failed to parse final assessment response", error);
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

const SubsectionHeading: FC<{ children: ReactNode }> = ({ children }) => (
  <h4 className="text-foreground text-lg font-semibold mb-2">{children}</h4>
);

interface CPTDescriptionsSectionProps {
  cptDescriptions: Record<string, Record<string, unknown>>;
}

const CPTDescriptionsSection: FC<CPTDescriptionsSectionProps> = ({ cptDescriptions }) => {
  const sortedCodes = useMemo(() => {
    const codes = Object.entries(cptDescriptions);
    return codes.sort(([codeA], [codeB]) => {
      const numA = Number(codeA);
      const numB = Number(codeB);
      if (Number.isFinite(numA) && Number.isFinite(numB)) return numA - numB;
      return codeA.localeCompare(codeB);
    });
  }, [cptDescriptions]);

  if (sortedCodes.length === 0) return null;

  return (
    <>
      <SectionHeading id="cpt-descriptions-summary">
        <span className="flex items-center gap-2">
          <FileText className="size-5 text-muted-foreground" aria-hidden />
          <span>CPT Code Descriptions</span>
        </span>
      </SectionHeading>

      <p className="font-semibold text-foreground mb-3">
        {sortedCodes.length} code(s) analyzed:
      </p>

      <div className="grid grid-cols-1 gap-3">
        {sortedCodes.map(([cptCode, data]) => {
          const description = (data.description as string) || "No description available";
          const source = (data.source as string) || "unknown";
          const sourceColor = LEGEND[source]?.color || "muted-foreground";

          return (
            <div
              key={cptCode}
              className="border border-muted rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-foreground">
                  <strong className={`text-${sourceColor}`}>CPT {cptCode}</strong>
                  <span className="ml-2">{description}</span>
                </p>
                <span
                  className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium shrink-0`}
                  title={`Source: ${source}`}
                >
                  {source}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};

interface DeviceCodesSectionProps {
  deviceCodes: DeviceDescription[];
}

const DeviceCodesSection: FC<DeviceCodesSectionProps> = ({ deviceCodes }) => {
  const sortedDevices = useMemo(() => {
    return [...deviceCodes].sort((a, b) => a.hcpcs_code.localeCompare(b.hcpcs_code));
  }, [deviceCodes]);

  if (sortedDevices.length === 0) return null;

  return (
    <>
      <hr className="my-6 border-muted" />
      <SectionHeading id="device-codes-summary">
        <span className="flex items-center gap-2">
          <Cpu className="size-5 text-muted-foreground" aria-hidden />
          <span>Device Codes</span>
        </span>
      </SectionHeading>

      <p className="font-semibold text-foreground mb-3">
        {sortedDevices.length} device code(s) identified:
      </p>

      <div className="grid grid-cols-1 gap-3">
        {sortedDevices.map((device, idx) => {
          const sourceColor = LEGEND[device.source]?.color || "muted-foreground";
          return (
            <div
              key={`${device.hcpcs_code}-${idx}`}
              className="border border-muted rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-start gap-2">
                <Cpu className="size-5 text-muted-foreground shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <h5 className="text-sm font-semibold text-foreground">
                      HCPCS {device.hcpcs_code}
                    </h5>
                    <span
                      className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium shrink-0`}
                      title={`Source: ${device.source}`}
                    >
                      {device.source}
                    </span>
                  </div>
                  <p className="text-sm text-foreground">{device.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};

interface NcciResultsSectionProps {
  ncciResults: Record<string, Record<string, unknown>>;
}

const NcciResultsSection: FC<NcciResultsSectionProps> = ({ ncciResults }) => {
  const [expandedCodes, setExpandedCodes] = useState<Set<string>>(new Set());

  const sortedCodes = useMemo(() => {
    const codes = Object.entries(ncciResults);
    return codes.sort(([codeA], [codeB]) => {
      const numA = Number(codeA);
      const numB = Number(codeB);
      if (Number.isFinite(numA) && Number.isFinite(numB)) return numA - numB;
      return codeA.localeCompare(codeB);
    });
  }, [ncciResults]);

  const toggleExpand = (cptCode: string) => {
    setExpandedCodes((prev) => {
      const next = new Set(prev);
      if (next.has(cptCode)) {
        next.delete(cptCode);
      } else {
        next.add(cptCode);
      }
      return next;
    });
  };

  if (sortedCodes.length === 0) return null;

  return (
    <>
      <hr className="my-6 border-muted" />
      <SectionHeading id="ncci-results-summary">
        <span className="flex items-center gap-2">
          <Shield className="size-5 text-muted-foreground" aria-hidden />
          <span>NCCI Compliance Results</span>
        </span>
      </SectionHeading>

      <p className="font-semibold text-foreground mb-3">
        {sortedCodes.length} code(s) evaluated for NCCI compliance:
      </p>

      <div className="space-y-3">
        {sortedCodes.map(([cptCode, data]) => {
          const isExpanded = expandedCodes.has(cptCode);
          const hasData = (data.has_data as boolean) || false;

          return (
            <div key={cptCode} className="border border-muted rounded-lg bg-muted/20">
              <button
                onClick={() => toggleExpand(cptCode)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Shield className="size-5 text-blue-500" />
                  <h5 className="font-semibold text-foreground">CPT {cptCode}</h5>
                  {!hasData && (
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-500 font-medium">
                      No conflicts
                    </span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {isExpanded ? "Collapse" : "Expand"}
                </span>
              </button>

              {isExpanded && (
                <div className="px-4 pb-4 border-t border-muted">
                  <div className="mt-3 bg-blue-500/10 border border-blue-500/30 rounded p-3">
                    <pre className="text-xs text-foreground whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};

interface PaymentHistorySectionProps {
  paymentHistory: Record<string, PaymentHistoryEntry>;
}

const PaymentHistorySection: FC<PaymentHistorySectionProps> = ({ paymentHistory }) => {
  const sortedSystems = useMemo(() => {
    return Object.entries(paymentHistory).sort(([a], [b]) => a.localeCompare(b));
  }, [paymentHistory]);

  if (sortedSystems.length === 0) return null;

  return (
    <>
      <hr className="my-6 border-muted" />
      <SectionHeading id="payment-history-summary">
        <span className="flex items-center gap-2">
          <DollarSign className="size-5 text-muted-foreground" aria-hidden />
          <span>Payment History Summary</span>
        </span>
      </SectionHeading>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sortedSystems.map(([system, entry]) => {
          const systemColors: Record<string, string> = {
            apc: "blue-500",
            asc: "green-500",
            pnpp: "purple-500",
          };
          const color = systemColors[system.toLowerCase()] || "gray-500";

          return (
            <div
              key={system}
              className={`border border-muted rounded-lg p-4 bg-${color}/5 hover:bg-${color}/10 transition-colors`}
            >
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className={`size-5 text-${color}`} />
                <h5 className="font-semibold text-foreground uppercase">{system}</h5>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Has Data:</span>
                  <span className="text-sm font-medium text-foreground">
                    {entry.has_data ? (
                      <CheckCircle2 className="size-4 text-green-500" />
                    ) : (
                      <span className="text-muted-foreground">No</span>
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Records:</span>
                  <span className="text-sm font-medium text-foreground">
                    {entry.data?.length || 0}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
};

const FinalAssessmentContent: FC<{ data: FinalAssessment }> = ({ data }) => {
  const formattedDate = useMemo(() => {
    try {
      return new Date(data.update_time).toLocaleString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      });
    } catch {
      return data.update_time;
    }
  }, [data.update_time]);

  return (
    <div className="select-text cursor-text">
      <LegendCard />

      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-muted rounded-lg p-6 mt-4">
        <div className="flex items-start gap-4">
          <div className="bg-blue-500/20 rounded-full p-3">
            <Target className="size-8 text-blue-500" />
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-foreground mb-2">Final Assessment</h2>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
              <Calendar className="size-4" />
              <span>Last Updated: {formattedDate}</span>
            </div>
            <div className="bg-muted/30 rounded px-3 py-2 inline-block">
              <p className="text-sm">
                <span className="text-muted-foreground">Target CPT Code: </span>
                <span className="font-bold text-blue-500 text-lg">{data.target_cpt}</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 my-6">
        <div className="border border-muted rounded-lg p-4 bg-muted/20">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="size-4 text-blue-500" />
            <p className="text-xs text-muted-foreground">CPT Codes</p>
          </div>
          <p className="text-2xl font-bold text-foreground">
            {Object.keys(data.cpt_descriptions).length}
          </p>
        </div>

        <div className="border border-muted rounded-lg p-4 bg-muted/20">
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="size-4 text-green-500" />
            <p className="text-xs text-muted-foreground">Device Codes</p>
          </div>
          <p className="text-2xl font-bold text-foreground">{data.device_codes.length}</p>
        </div>

        <div className="border border-muted rounded-lg p-4 bg-muted/20">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="size-4 text-purple-500" />
            <p className="text-xs text-muted-foreground">NCCI Checks</p>
          </div>
          <p className="text-2xl font-bold text-foreground">
            {Object.keys(data.ncci_results).length}
          </p>
        </div>

        <div className="border border-muted rounded-lg p-4 bg-muted/20">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="size-4 text-amber-500" />
            <p className="text-xs text-muted-foreground">Payment Systems</p>
          </div>
          <p className="text-2xl font-bold text-foreground">
            {Object.keys(data.payment_history).length}
          </p>
        </div>
      </div>

      {/* Detailed Sections */}
      <CPTDescriptionsSection cptDescriptions={data.cpt_descriptions} />
      <DeviceCodesSection deviceCodes={data.device_codes} />
      <NcciResultsSection ncciResults={data.ncci_results} />
      <PaymentHistorySection paymentHistory={data.payment_history} />
    </div>
  );
};

const FinalAssessmentRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(
    () => parseFinalAssessmentContent(message.content),
    [message.content]
  );

  if (!parsedData) return <>{message.content}</>;

  return <FinalAssessmentContent data={parsedData} />;
};

export default FinalAssessmentRenderer;
