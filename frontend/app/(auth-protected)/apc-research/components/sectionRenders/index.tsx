import CodeDescriptionRenderer from "./codeDescription";
import GuidelineExaminationRenderer from "./guidelineExamination";
import PaymentRateRenderer from "./paymentRate";
import DeviceCodeRenderer from "./deviceCode";
import NcciComplianceRenderer from "./ncciCompliance";
import ReferenceMaterialRenderer from "./referenceMaterial";
import FinalAssessmentRenderer from "./finalAssessment";
import type { AssistantRenderer } from "@/components/chatDisplay";

export const sectionRenderers: AssistantRenderer[] = [
  CodeDescriptionRenderer,
  GuidelineExaminationRenderer,
  PaymentRateRenderer,
  DeviceCodeRenderer,
  NcciComplianceRenderer,
  ReferenceMaterialRenderer,
  FinalAssessmentRenderer,
];
