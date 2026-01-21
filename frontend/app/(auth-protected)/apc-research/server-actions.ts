import "server-only";
import { queryllm } from "@/lib/llm";
import OpenAI from "openai";
import { zodResponseFormat } from "openai/helpers/zod.mjs";
import { ResponsesModel } from "openai/resources/shared.mjs";
import { z } from "zod/v4";
import { generateCpts } from "@/lib/backendClient";

// const generateCptCodeFromTopic = (topic: string) => {
//   const prompt = `
// You are a medical coding expert. Given the following medical procedure or condition topic, provide the top 5 most relevant CPT codes.
// Topic: ${topic}

// For each CPT code, provide:
// 1. The CPT code number
// 2. A brief description (one line)
// 3. A title for the CPT code. Keep it concise.

// Provide exactly 5 CPT codes. If the topic is too vague or unclear, provide the most commonly associated codes.
// `;

//   const messages = [
//     {
//       role: "system",
//       content: "You are an expert medical coding specialist with deep knowledge of CPT codes.",
//     },
//     { role: "user", content: prompt },
//   ];
//   return messages as OpenAI.Chat.Completions.ChatCompletionMessageParam[];
// };

// export type CptData = z.infer<typeof topicChoices>["cpt_codes_and_descriptions"][number];

export const fetchCptCodes = async (topic: string, model: ResponsesModel) => {
  return await generateCpts(topic, model);
};

const computeAuditWindow = () => {
  // """Compute the audit window for claims (3 years back from today)"""
  const current_date = new Date();
  const currentYear = current_date.getFullYear();
  const start_date = new Date();
  start_date.setFullYear(currentYear - 3);
  return [start_date.toISOString().split("T")[0], current_date.toISOString().split("T")[0]];
};

const createResearchPrompt = (target_cpt: string, context_details: string) => {
  // """Build comprehensive research prompt for APC analysis"""
  const [window_start, window_end] = computeAuditWindow();

  const research_query = `
As a medical coding specialist focused on APC analysis, perform a thorough evaluation for CPT code: ${target_cpt}

Audit Window: ${window_start} through ${window_end}

Context Information: {${context_details} or "Not specified"}

Complete the following analysis sections. 

<SECTION_1>
<TITLE>Code Description Analysis</TITLE>
<CONTENT>
- Review detailed descriptions for ${target_cpt} and neighboring codes
- List neighboring codes in ASCENDING ORDER (from lowest to highest code number)
- Detect re-coding possibilities considering:
  • Procedural approach variations (open, percutaneous, laparoscopic)
  • Anatomical location differences
  • Intervention technique specifics
  • Potential bundling scenarios
</CONTENT>
</SECTION_1>

<SECTION_2>
<TITLE>Guideline Examination</TITLE>
<CONTENT>
- Extract instructional notes specific to ${target_cpt}
- Summarize applicable chapter-level guidelines
- Note parenthetical references and code relationships
</CONTENT>
</SECTION_2>

<SECTION_3>
<TITLE>Payment Rate Comparison</TITLE>
<CONTENT>
- Evaluate APC assignments and payment rates for ${target_cpt} and related codes
- Present the comparison in a TABLE format with the following columns:
  | CPT Code | APC Code | Payment Rate | Status | Notes |
- Categorize findings:
  • Matching rates → No audit opportunity
  • Differing rates → Investigate further
- Track rate consistency across quarters/years within audit window
- Flag potential underpayment or overpayment patterns
- Use markdown table format for clear presentation
</CONTENT>
</SECTION_3>

<SECTION_4>
<TITLE>Device Code Analysis</TITLE>
<CONTENT>
- Confirm if ${target_cpt} involves medical devices
- List relevant HCPCS device codes
- Highlight common errors:
  • Procedure without device code
  • Device-procedure mismatch
  • Incorrect device type selection
</CONTENT>
</SECTION_4>

<SECTION_5>
<TITLE>NCCI Compliance Check</TITLE>
<CONTENT>
- Reference NCCI Edit Manual for ${target_cpt}
- Examine PTP (Procedure-to-Procedure) edits
- Detect modifier abuse patterns:
  • Inappropriate modifier 59 usage
  • Modifier 25 misapplication
  • Other unbundling indicators
</CONTENT>
</SECTION_5>

<SECTION_6>
<TITLE>Reference Material Review</TITLE>
<CONTENT>
- Locate CPT Assistant guidance for ${target_cpt}
- Find applicable HCPCS Coding Clinic articles
- Document special coding considerations
</CONTENT>
</SECTION_6>

<FINAL_ASSESSMENT>
<TITLE>Final Assessment</TITLE>
<CONTENT>
- Consolidate findings and opportunities
- Assign priority level (Critical/Moderate/Low)
- Recommend validation steps
</CONTENT>
</FINAL_ASSESSMENT>

CRITICAL:Use markdown formatting within the content sections, including tables where specified. Convert the analysis to the given structure.
`;
  return research_query;
};

const sectionStructure = z.object({
  sections: z.array(
    z.object({
      title: z.string(),
      content: z.string(),
    }),
  ),
});

export type ResearchSection = z.infer<typeof sectionStructure>["sections"][number];

export const createResearch = async (
  targetCpt: string,
  contextDetails: string,
  model: ResponsesModel,
) => {
  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    {
      role: "system",
      content: "You are an expert medical coding analyst specializing in APC research.",
    },
    { role: "user", content: createResearchPrompt(targetCpt, contextDetails) },
  ];
  const response = await queryllm<z.infer<typeof sectionStructure>>(
    messages,
    model,
    zodResponseFormat(sectionStructure, "sections"),
  );
  return response.sections;
};
