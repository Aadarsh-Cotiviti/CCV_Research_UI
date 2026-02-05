"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import { Cpu, CheckCircle2, LinkIcon, AlertCircle } from "lucide-react";
import { FC, ReactNode, useMemo } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";

type DeviceCodeResult = components["schemas"]["DeviceCodeResult"];
type DeviceDescription = components["schemas"]["DeviceDescription"];
type DeviceNoChange = components["schemas"]["DeviceNoChange"];

type DeviceCodePayload =
  | { section_num: number; status: "success"; data: DeviceCodeResult | string }
  | { section_num: number; status: "error"; error: string };

const isDeviceCodeResult = (raw: unknown): raw is DeviceCodeResult => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as DeviceCodeResult;
  return (
    Array.isArray(candidate.device_codes_with_desc) &&
    Array.isArray(candidate.internal_recoding_result) &&
    Array.isArray(candidate.no_change_results)
  );
};

const parseDeviceCodeContent = (content: string): DeviceCodeResult | null => {
  const tryParse = (raw: unknown, allowNested = true): DeviceCodeResult | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isDeviceCodeResult(raw)) return raw;

    const maybePayload = raw as Partial<DeviceCodePayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested device code data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isDeviceCodeResult(maybePayload.data) ? maybePayload.data : null;
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
    console.warn("Failed to parse device code response", error);
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

const DeviceCodeCard: FC<{ device: DeviceDescription }> = ({ device }) => {
  const sourceColor = LEGEND[device.source]?.color || "muted-foreground";

  return (
    <div className="border border-muted rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Cpu className="size-5 text-muted-foreground shrink-0" />
          <h5 className="text-base font-semibold text-foreground">HCPCS {device.hcpcs_code}</h5>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium shrink-0`}
          title={`Source: ${device.source}`}
        >
          {device.source}
        </span>
      </div>
      <p className="text-sm text-foreground leading-relaxed">{device.description}</p>
    </div>
  );
};

const NoChangeCard: FC<{ device: DeviceNoChange }> = ({ device }) => {
  const sourceColor = LEGEND[device.description_source]?.color || "muted-foreground";

  return (
    <div className="border border-muted rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="size-5 text-green-500 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h5 className="text-base font-semibold text-foreground">HCPCS {device.hcpcs_code}</h5>
            <div className="flex items-center gap-2 shrink-0">
              <span
                className={`text-xs px-2 py-1 rounded-full bg-${sourceColor}/10 text-${sourceColor} font-medium`}
                title={`Source: ${device.description_source}`}
              >
                {device.description_source}
              </span>
              <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-500 font-medium">
                {device.status}
              </span>
            </div>
          </div>
          <p className="text-sm text-foreground leading-relaxed">{device.description}</p>
        </div>
      </div>
    </div>
  );
};

const RecodingAnalysisCard: FC<{ entry: Record<string, unknown> }> = ({ entry }) => {
  const hcpcsCode = entry.hcpcs_code as string | undefined;
  const description = entry.description as string | undefined;
  const recodingAnalysis = entry.llm_recoding as Record<string, unknown> | undefined;
  const recodingPossibilities = recodingAnalysis?.recoding_possibilities as string | undefined;

  return (
    <div
      className="border border-muted rounded-lg p-4 bg-muted/20 hover:bg-muted/30 transition-colors"
      id={`hcpcs-${hcpcsCode ?? "unknown"}`}
    >
      <SubsectionHeading id={`hcpcs-${hcpcsCode ?? "unknown"}`}>
        HCPCS {hcpcsCode ?? "Unknown"}
      </SubsectionHeading>
      <p className="text-sm text-foreground mb-3">
        <strong>Description:</strong> <span>{description ?? "Description not available"}</span>
      </p>
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
        <p className="font-semibold text-foreground mb-2 flex items-center gap-2">
          <AlertCircle className="size-4" />
          Re-coding Analysis
        </p>
        <div className="whitespace-pre-wrap text-foreground text-sm leading-6">
          {recodingPossibilities ?? "No recoding analysis available."}
        </div>
      </div>
    </div>
  );
};

const DeviceCodeContent: FC<{ data: DeviceCodeResult }> = ({ data }) => {
  const sortedDeviceCodes = useMemo(() => {
    return [...data.device_codes_with_desc].sort((a, b) => {
      return a.hcpcs_code.localeCompare(b.hcpcs_code);
    });
  }, [data.device_codes_with_desc]);

  const sortedNoChangeCodes = useMemo(() => {
    return [...data.no_change_results].sort((a, b) => {
      return a.hcpcs_code.localeCompare(b.hcpcs_code);
    });
  }, [data.no_change_results]);

  const hasRecodingResults =
    data.internal_llm_recoding_result && data.internal_llm_recoding_result.length > 0;

  return (
    <div className="select-text cursor-text">
      <LegendCard />

      {/* Device Codes Section */}
      <SectionHeading id="device-codes">
        <span className="flex items-center gap-2">
          <Cpu className="size-5 text-muted-foreground" aria-hidden />
          <span>Device Codes Identified</span>
        </span>
      </SectionHeading>

      {sortedDeviceCodes.length > 0 ? (
        <>
          <p className="font-semibold text-foreground mb-3">
            {sortedDeviceCodes.length} device code(s) found:
          </p>
          <div className="grid grid-cols-1 gap-3">
            {sortedDeviceCodes.map((device, idx) => (
              <DeviceCodeCard key={`${device.hcpcs_code}-${idx}`} device={device} />
            ))}
          </div>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">No device codes identified.</p>
      )}

      {/* Re-coding Analysis Section */}
      {hasRecodingResults && (
        <>
          <hr className="my-6 border-muted" />
          <SectionHeading id="recoding-analysis">
            <span className="flex items-center gap-2">
              <AlertCircle className="size-5 text-muted-foreground" aria-hidden />
              <span>Re-coding and Change Analysis</span>
            </span>
          </SectionHeading>
          <p className="font-semibold text-foreground mb-3">
            Device codes with potential changes or recoding scenarios:
          </p>
          <div className="space-y-4">
            {(data.internal_llm_recoding_result || []).map((entry, idx) => (
              <RecodingAnalysisCard key={`recoding-${idx}`} entry={entry} />
            ))}
          </div>
        </>
      )}

      {/* No Change Results Section */}
      {sortedNoChangeCodes.length > 0 && (
        <>
          <hr className="my-6 border-muted" />
          <SectionHeading id="no-change-codes">
            <span className="flex items-center gap-2">
              <CheckCircle2 className="size-5 text-muted-foreground" aria-hidden />
              <span>Stable Device Codes (No Changes)</span>
            </span>
          </SectionHeading>
          <p className="font-semibold text-foreground mb-3">
            {sortedNoChangeCodes.length} device code(s) with no changes:
          </p>
          <div className="grid grid-cols-1 gap-3">
            {sortedNoChangeCodes.map((device, idx) => (
              <NoChangeCard key={`${device.hcpcs_code}-${idx}`} device={device} />
            ))}
          </div>
        </>
      )}

      {/* Summary Stats */}
      <div className="mt-6 p-4 bg-muted/30 border border-muted rounded-lg">
        <h4 className="font-semibold text-foreground mb-2">Summary</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Total Device Codes</p>
            <p className="text-lg font-semibold text-foreground">{sortedDeviceCodes.length}</p>
          </div>
          <div>
            <p className="text-muted-foreground">No Changes</p>
            <p className="text-lg font-semibold text-green-500">{sortedNoChangeCodes.length}</p>
          </div>
          {hasRecodingResults && (
            <div>
              <p className="text-muted-foreground">Requiring Analysis</p>
              <p className="text-lg font-semibold text-amber-500">
                {data.internal_llm_recoding_result?.length ?? 0}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const DeviceCodeRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(() => parseDeviceCodeContent(message.content), [message.content]);

  if (!parsedData) return <>{message.content}</>;

  return <DeviceCodeContent data={parsedData} />;
};

export default DeviceCodeRenderer;
