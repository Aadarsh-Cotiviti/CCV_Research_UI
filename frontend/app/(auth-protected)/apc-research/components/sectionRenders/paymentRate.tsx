"use client";

import { AssistantRenderer } from "@/components/chatDisplay";
import { DollarSign, FileText, LinkIcon, TrendingUp, Table as TableIcon } from "lucide-react";
import { FC, ReactNode, useMemo, useState } from "react";
import { LEGEND, LegendCard } from "../legendCard";
import type { components } from "@/lib/api-types";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { markdownComponents } from "@/components/MarkdownComponents";

type PaymentRateResult = components["schemas"]["PaymentRateResult"];
type PaymentTable = components["schemas"]["PaymentTable"];
type CPTDescription = components["schemas"]["CPTDescription"];

type PaymentPayload =
  | { section_num: number; status: "success"; data: PaymentRateResult | string }
  | { section_num: number; status: "error"; error: string };

const isPaymentRateResult = (raw: unknown): raw is PaymentRateResult => {
  if (!raw || typeof raw !== "object") return false;
  const candidate = raw as PaymentRateResult;
  return (
    typeof candidate.analysis_content === "string" &&
    typeof candidate.target_cpt_payment_history === "object" &&
    candidate.target_cpt_payment_history !== null &&
    typeof candidate.cpt_descriptions === "object" &&
    candidate.cpt_descriptions !== null
  );
};

const parsePaymentContent = (content: string): PaymentRateResult | null => {
  const tryParse = (raw: unknown, allowNested = true): PaymentRateResult | null => {
    if (!raw || typeof raw !== "object") return null;

    if (isPaymentRateResult(raw)) return raw;

    const maybePayload = raw as Partial<PaymentPayload>;
    if ("status" in maybePayload) {
      if (maybePayload.status !== "success") return null;

      if (typeof maybePayload.data === "string" && allowNested) {
        try {
          return tryParse(JSON.parse(maybePayload.data), false);
        } catch (error) {
          console.warn("Failed to parse nested payment data", error);
          return null;
        }
      }

      if (maybePayload.data && typeof maybePayload.data === "object") {
        return isPaymentRateResult(maybePayload.data) ? maybePayload.data : null;
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
    console.warn("Failed to parse payment rate response", error);
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

const formatCurrency = (value: unknown): string => {
  if (value === null || value === undefined || value === "") return "N/A";
  const num = typeof value === "string" ? parseFloat(value) : Number(value);
  if (!Number.isFinite(num)) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
};

const formatPercent = (value: unknown): string => {
  if (value === null || value === undefined || value === "") return "N/A";
  const num = typeof value === "string" ? parseFloat(value) : Number(value);
  if (!Number.isFinite(num)) return "N/A";
  return `${num.toFixed(2)}%`;
};

interface PaymentDataTableProps {
  systemName: string;
  paymentTable: PaymentTable;
  systemColor: string;
}

const PaymentDataTable: FC<PaymentDataTableProps> = ({ systemName, paymentTable, systemColor }) => {
  const [showAllRecords, setShowAllRecords] = useState(false);

  const displayData = useMemo(() => {
    return showAllRecords ? paymentTable.data : paymentTable.data_filtered;
  }, [showAllRecords, paymentTable.data, paymentTable.data_filtered]);

  const columns = useMemo(() => {
    if (displayData.length === 0) return [];
    const firstRow = displayData[0];
    return Object.keys(firstRow);
  }, [displayData]);

  const hasFilteredData = paymentTable.record_count !== paymentTable.record_count_filtered;

  return (
    <div className="border border-muted rounded-lg overflow-hidden shadow-sm">
      <div className={`bg-${systemColor}/10 border-b border-muted px-4 py-3`}>
        <div className="flex items-center justify-between">
          <h5 className={`font-semibold text-${systemColor} text-base flex items-center gap-2`}>
            <TableIcon className="size-4" />
            {systemName} Payment History
          </h5>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-muted-foreground">
              {showAllRecords ? paymentTable.record_count : paymentTable.record_count_filtered}{" "}
              records
            </span>
            {hasFilteredData && (
              <button
                onClick={() => setShowAllRecords(!showAllRecords)}
                className="text-xs px-2 py-1 bg-background border border-muted rounded hover:bg-muted transition-colors"
              >
                {showAllRecords ? "Show Filtered" : "Show All"}
              </button>
            )}
          </div>
        </div>
        {hasFilteredData && !showAllRecords && paymentTable.excluded_cpt_codes.length > 0 && (
          <p className="text-xs text-muted-foreground mt-1">
            Excluded CPT codes: {paymentTable.excluded_cpt_codes.join(", ")}
          </p>
        )}
      </div>

      {displayData.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                {columns.map((col) => (
                  <th
                    key={col}
                    className="px-4 py-2 text-left font-semibold text-foreground border-b border-muted"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-muted">
              {displayData.map((row, idx) => (
                <tr
                  key={idx}
                  className="hover:bg-muted/30 transition-colors"
                >
                  {columns.map((col) => {
                    const value = row[col];
                    const displayValue = (() => {
                      // Format currency fields
                      if (
                        typeof col === "string" &&
                        (col.toLowerCase().includes("payment") ||
                          col.toLowerCase().includes("rate") ||
                          col.toLowerCase().includes("amount") ||
                          col.toLowerCase().includes("price"))
                      ) {
                        return formatCurrency(value);
                      }
                      // Format percentage fields
                      if (
                        typeof col === "string" &&
                        (col.toLowerCase().includes("percent") ||
                          col.toLowerCase().includes("change"))
                      ) {
                        return formatPercent(value);
                      }
                      // Default formatting
                      if (value === null || value === undefined) return "N/A";
                      return String(value);
                    })();

                    return (
                      <td key={col} className="px-4 py-2 text-foreground">
                        {displayValue}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="px-4 py-8 text-center text-muted-foreground">
          No payment data available for {systemName}
        </div>
      )}
    </div>
  );
};

const CPTCodesList: FC<{ cptDescriptions: Record<string, CPTDescription> }> = ({
  cptDescriptions,
}) => {
  const sortedCodes = useMemo(() => {
    const codes = Object.entries(cptDescriptions);
    return codes.sort(([codeA], [codeB]) => {
      const numA = Number(codeA);
      const numB = Number(codeB);
      if (Number.isFinite(numA) && Number.isFinite(numB)) return numA - numB;
      return codeA.localeCompare(codeB);
    });
  }, [cptDescriptions]);

  return (
    <div className="grid grid-cols-1 gap-3">
      {sortedCodes.map(([cptCode, description]) => {
        const sourceColor = LEGEND[description.source]?.color || "muted-foreground";
        return (
          <div
            key={cptCode}
            className="border border-muted rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors"
          >
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
      })}
    </div>
  );
};

const PaymentRateContent: FC<{ data: PaymentRateResult }> = ({ data }) => {
  const history = data.target_cpt_payment_history;

  return (
    <div className="select-text cursor-text">
      <LegendCard />

      {/* Analysis Section */}
      <SectionHeading id="payment-analysis">
        <span className="flex items-center gap-2">
          <TrendingUp className="size-5 text-muted-foreground" aria-hidden />
          <span>Payment Rate Analysis</span>
        </span>
      </SectionHeading>

      <div className="prose prose-sm max-w-none mt-3 mb-6">
        <div className="bg-muted/30 rounded-lg p-4 border border-muted">
          <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {data.analysis_content}
          </Markdown>
        </div>
      </div>

      {/* CPT Codes Analyzed */}
      {history.cpt_codes_analyzed.length > 0 && (
        <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <p className="text-sm font-semibold text-foreground mb-1">CPT Codes Analyzed:</p>
          <p className="text-sm text-foreground">{history.cpt_codes_analyzed.join(", ")}</p>
        </div>
      )}

      {/* Neighboring Codes */}
      {history.neighboring_codes.length > 0 && (
        <div className="mb-6 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
          <p className="text-sm font-semibold text-foreground mb-1">Neighboring Codes:</p>
          <p className="text-sm text-foreground">{history.neighboring_codes.join(", ")}</p>
        </div>
      )}

      <hr className="my-6 border-muted" />

      {/* Payment Tables */}
      <SectionHeading id="payment-systems">
        <span className="flex items-center gap-2">
          <DollarSign className="size-5 text-muted-foreground" aria-hidden />
          <span>Payment System Comparisons</span>
        </span>
      </SectionHeading>

      <div className="space-y-6 mt-4">
        <PaymentDataTable systemName="APC" paymentTable={history.apc} systemColor="blue-600" />
        <PaymentDataTable systemName="ASC" paymentTable={history.asc} systemColor="green-600" />
        <PaymentDataTable systemName="PNPP" paymentTable={history.pnpp} systemColor="purple-600" />
      </div>

      <hr className="my-6 border-muted" />

      {/* CPT Descriptions */}
      {Object.keys(data.cpt_descriptions).length > 0 && (
        <>
          <SectionHeading id="cpt-descriptions">
            <span className="flex items-center gap-2">
              <FileText className="size-5 text-muted-foreground" aria-hidden />
              <span>CPT Code Descriptions</span>
            </span>
          </SectionHeading>
          <p className="font-semibold text-foreground mb-3">
            {Object.keys(data.cpt_descriptions).length} code(s) referenced:
          </p>
          <CPTCodesList cptDescriptions={data.cpt_descriptions} />
        </>
      )}
    </div>
  );
};

const PaymentRateRenderer: AssistantRenderer = ({ message }) => {
  const parsedData = useMemo(() => parsePaymentContent(message.content), [message.content]);

  if (!parsedData) return <>{message.content}</>;

  return <PaymentRateContent data={parsedData} />;
};

export default PaymentRateRenderer;
