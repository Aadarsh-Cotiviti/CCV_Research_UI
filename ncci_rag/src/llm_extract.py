"""
NCCI RAG: LLM Analysis with Citations

Pipeline:
1. Load retrieved chunks from 06_retrieve.py
2. Format chunks as markdown with citation numbers [1] [2] [3]
3. Call LLM for NCCI compliance analysis with structured output (Pydantic)
4. Return markdown report with citations
"""
import argparse
import json
import os
import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from pydantic import BaseModel, Field

# Import llm_wrapper from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from llm_wrapper import query_llm

# Import retrieve module from same directory
try:
    from .retrieve import multi_stage_hybrid_rag
except ImportError:
    # Fallback for direct execution
    from retrieve import multi_stage_hybrid_rag

from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class NCCIAnalysis(BaseModel):
    """Structured NCCI compliance analysis output"""
    modifier_rules: List[str] = Field(
        description="List of modifier rules, each as a complete sentence with citation(s) at the end"
    )
    ptp_edit_rules: List[str] = Field(
        description="List of PTP edit rules, each as a complete sentence with citation(s) at the end"
    )
    compliance_risks: List[str] = Field(
        description="List of misuse opportunities and compliance risks, each as a complete sentence with citation(s) at the end"
    )
    clinical_context: List[str] = Field(
        description="List of clinical context and special rules, each as a complete sentence with citation(s) at the end"
    )

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 3000

# ============================================================================
# Step 1: Load Retrieved Chunks
# ============================================================================

def load_retrieved_chunks(cpt_code: int, output_dir: Optional[Path] = None) -> Tuple[Dict, List[Dict]]:
    """
    Load retrieved chunks from retrieve.py output.
    
    Args:
        cpt_code: CPT code
        output_dir: Optional custom output directory
    
    Returns:
        Tuple of (metadata, chunks list)
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'output'
    
    output_path = output_dir / f'retrieved_chunks_cpt_{cpt_code}.json'
    
    if not output_path.exists():
        raise FileNotFoundError(
            f"❌ Retrieved chunks not found: {output_path}\n\n"
        )
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"❌ Invalid JSON in {output_path}: {e}")
    
    chunks = data.get('chunks', [])
    
    if not chunks:
        raise ValueError(
            f"⚠️ No chunks found in {output_path}\n"
            f"The retrieval may have returned 0 results for CPT {cpt_code}"
        )

    return data, chunks


# ============================================================================
# Step 2: Format Chunks as Markdown
# ============================================================================

def format_chunks_as_markdown(chunks: List[Dict]) -> str:
    """
    Format chunks as markdown with citation numbers [1], [2], [3], etc.
    """
    markdown_parts = []
    
    for i, chunk in enumerate(chunks, 1):
        pages = chunk.get('pages', [])
        if pages:
            page_str = f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0])
        else:
            page_str = "Unknown"
        
        section = chunk.get('section') or 'General Policy'
        source = chunk.get('source', 'unknown')
        chunk_id = chunk.get('chunk_id', 'unknown')
        topic_tags = chunk.get('topic_tags', [])
        full_text = chunk.get('full_text', '')
        
        source_emoji = '🎯' if source == 'range_routing' else '📋'
        source_label = f"{source_emoji} {source}"
        
        citation_header = f"### [{i}] {section} (Pages {page_str})"
        metadata_line = f"**Chunk ID**: `{chunk_id}` | **Source**: {source_label}"
        
        if topic_tags:
            tags_display = ' '.join([f'`{tag}`' for tag in topic_tags[:5]])
            metadata_line += f"\n**Tags**: {tags_display}"
        
        chunk_block = f"""
{'='*70}
{citation_header}
{metadata_line}

{full_text.strip()}
"""
        markdown_parts.append(chunk_block)
    
    markdown_parts.append('=' * 70)
    
    return '\n'.join(markdown_parts)


# ============================================================================
# Step 3: Create LLM Analysis Prompt
# ============================================================================

def create_analysis_prompt(cpt_code: int, chunks_markdown: str, num_chunks: int) -> str:
    """
    Create LLM analysis prompt with strict citation requirements.
    """
    return f"""You are an expert medical coding compliance analyst specializing in CMS NCCI (National Correct Coding Initiative) policy interpretation.

# TASK OVERVIEW

Analyze the NCCI manual documentation below for **CPT {cpt_code}** and provide a comprehensive compliance analysis.

**CRITICAL INSTRUCTION ON CHUNK USAGE**: 
You have been provided with {num_chunks} candidate chunks as a reference pool. These are **candidates only** - you should carefully evaluate each one and **only cite the chunks that contain directly relevant, specific information about CPT {cpt_code}**. 

**Expected behavior**: Not all {num_chunks} chunks will be relevant to a specific CPT code - some may contain general policies or unrelated information. **Only cite chunks that contain specific, actionable information about CPT {cpt_code}**. Do NOT force citations from all chunks - be selective and only use what is genuinely applicable.

**Quality over quantity**: It's far better to cite 4 highly relevant chunks than to cite all {num_chunks} chunks with marginal relevance.

## Analysis Requirements

You MUST extract and analyze the following categories:

### 1. **Modifier Rules**
- Which modifiers (e.g., 25, 59, LT, RT, 76, 77, 91, XE, XS, XP, XU) are explicitly allowed or required?
- Under what clinical circumstances are these modifiers applicable?
- Are there NCCI-associated modifiers or modifier indicators (0, 1, 9)?
- Provide modifier-related rules found in RELEVANT chunks
- Include both general modifier policies and CPT-specific modifier rules
- **Only cite chunks that actually discuss modifiers relevant to CPT {cpt_code}**

### 2. **PTP Edit Rules (Procedure-to-Procedure Edits)**
- Column 1/Column 2 edit relationships - provide specific code pairs mentioned
- Which codes are mutually exclusive with CPT {cpt_code}?
- CCMI (CCI Modifier Indicator) values and bypass conditions for each edit pair
- Medically Unlikely Edits (MUE) if mentioned
- List PTP edits found in RELEVANT chunks
- Include effective dates and policy changes if mentioned
- **Only cite chunks that actually discuss PTP edits relevant to CPT {cpt_code}**

### 3. **Misuse Opportunities & Compliance Risks**
- Common billing errors or fraud patterns - provide examples found
- Unbundling risks (component codes vs comprehensive codes)
- Anatomic considerations (bilateral procedures, separate sites, separate sessions)
- Time-based restrictions or session limits
- List compliance risks and billing errors mentioned in RELEVANT chunks
- Include specific examples of improper billing practices if provided
- **Only cite chunks that actually discuss compliance risks relevant to CPT {cpt_code}**

### 4. **Clinical Context & Special Rules**
- Anatomic/procedural scope of CPT {cpt_code}
- Special policies (e.g., add-on codes, starred procedures)
- Documentation requirements
- Bundling/unbundling principles specific to this code
- **Only cite chunks that actually discuss special rules relevant to CPT {cpt_code}**

---

# CRITICAL CITATION RULES

⚠️ **YOU MUST FOLLOW THESE RULES STRICTLY**:

1. **Cite only relevant chunks**: Only reference chunks that contain information directly applicable to CPT {cpt_code}. **Most chunks in the candidate pool will NOT be relevant** - skip them without hesitation.
2. **Be selective**: Not all candidate chunks will be worth citing. Focus on chunks with specific information about CPT {cpt_code}. Quality citations are more valuable than quantity - cite only what is directly relevant.
3. **Use multiple citations sparingly**: Only when multiple chunks discuss the exact same specific rule. Avoid citing multiple general policy chunks.
4. **Every factual claim MUST have a citation**: Use ONLY [1], [2], [3], etc. (numbers only, no additional text)
5. **Relevance test**: Before citing a chunk, ask "Does this chunk specifically mention CPT {cpt_code} or a rule that directly applies to it?" If no, skip it.
6. **Only cite what's explicitly stated**: Do NOT infer beyond the text
7. **DO NOT mention missing information**: If something is not in the documentation, simply do not mention it. Do NOT include statements like "Evidence insufficient" or "Not mentioned in documentation"
8. **Quote exact language**: When discussing specific rules, quote verbatim from chunks
8. **Keep citations simple**: Use ONLY the number in brackets, e.g., [1] or [1][2], NOT [1, NCCI Policy Manual, Ch. 1]
9. **Be selective**: You are NOT required to use all {num_chunks} chunks. Only use the ones that are truly relevant to CPT {cpt_code}.
10. **Prioritize direct relevance**: Focus on chunks that directly mention CPT {cpt_code} or its specific code family, and applicable general NCCI policies

---

# OUTPUT FORMAT (Strict JSON)

You MUST respond with ONLY a valid JSON object matching this exact structure:

```json
{{
  "modifier_rules": [
    "Rule description with citation [1]",
    "Another rule with multiple citations [2][3]"
  ],
  "ptp_edit_rules": [
    "PTP edit rule with citation [1]"
  ],
  "compliance_risks": [
    "Risk description with citation [5]"
  ],
  "clinical_context": [
    "Clinical context rule with citation [1][2]"
  ]
}}
```

**CRITICAL JSON RULES**:
- Each array should contain strings (one rule per string)
- Each string MUST end with citation(s) in brackets like [1] or [2][3]
- Do NOT add any text before or after the JSON object
- Do NOT add markdown code fences (```) around the JSON
- Do NOT include summary, conclusion, or any other fields
- Ensure valid JSON syntax (proper quotes, commas, brackets)

**STOP HERE - DO NOT ADD ANY SUMMARY, CONCLUSION, OR ADDITIONAL SECTIONS**

---

# FINAL REMINDERS

- Be **specific and actionable** - this will be used for real compliance decisions
- **Always cite sources** - uncited claims will be rejected
- **Be highly selective with citations**: You have {num_chunks} candidate chunks - evaluate each one independently. Some will be genuinely relevant with specific information about CPT {cpt_code}, others may only provide general background.
- **Chunk evaluation**: Before citing any chunk, verify it contains specific information about CPT {cpt_code} or directly applicable rules
- **Skip general policies**: Unless they specifically apply to CPT {cpt_code}, don't cite chunks with only general NCCI background information
- **Use multiple citations rarely**: Only when 2+ chunks mention the exact same specific rule for CPT {cpt_code}
- Focus on **NCCI-specific rules** - ignore general CPT guidance unless relevant to edits
- If you quote text, use **exact quotes** from the chunks above
- Organize clearly with bullet points for easy reference
- **Quality over quantity**: Better to cite 4 highly relevant chunks than 12 marginally relevant ones
- **Do NOT mention gaps or missing information** - only report what is explicitly found
- **CRITICAL: Do NOT add any summary, conclusion, or closing statements after the "Clinical Context & Special Rules" section**
- **End your response immediately after the last bullet point in "Clinical Context & Special Rules"**

---

# RETRIEVED DOCUMENTATION ({num_chunks} candidate chunks - evaluate each for relevance)

**INSTRUCTION**: The chunks below are candidates retrieved by the search system. Many will not be directly relevant to CPT {cpt_code}. Review each one and only cite those with specific, actionable information about this CPT code.

{chunks_markdown}

---

**BEGIN YOUR ANALYSIS NOW** (Remember: Cite only chunks with specific, relevant information - not all {num_chunks} chunks will apply):
"""


# ============================================================================
# Step 4: Call LLM for Analysis
# ============================================================================

def call_llm_for_analysis(
    prompt: str, 
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> NCCIAnalysis:
    """
    Call LLM for analysis and return structured Pydantic model
    """
    # Build messages
    messages = [
        {
            "role": "system", 
            "content": (
                "You are an expert medical coding compliance analyst with deep expertise in "
                "CMS NCCI (National Correct Coding Initiative) policy interpretation. "
                "You provide precise, well-cited analyses for healthcare compliance decisions. "
                "CRITICAL: You MUST respond with ONLY valid JSON matching the specified structure. "
                "Do NOT add any text before or after the JSON object. Do NOT add markdown code fences. "
                "Do NOT add summary statements or conclusions within the JSON fields."
            )
        },
        {
            "role": "user", 
            "content": prompt
        }
    ]
    
    try:
        response_text = query_llm(messages, model="gpt-4.1")
        
        # Clean up response - remove markdown code fences if present
        response_text = response_text.strip()
        if response_text.startswith('```'):
            # Remove ```json or ``` from start
            response_text = response_text.split('\n', 1)[1] if '\n' in response_text else response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text.rsplit('\n', 1)[0] if '\n' in response_text else response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON and validate with Pydantic
        try:
            data = json.loads(response_text)
            analysis = NCCIAnalysis(**data)
            return analysis
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON response from LLM: {e}")
            print(f"Response text:\n{response_text[:500]}\n")
            raise ValueError(f"LLM did not return valid JSON: {e}")
        except Exception as e:
            print(f"\n❌ Error parsing response into NCCIAnalysis model: {e}")
            raise
        
    except Exception as e:
        print(f"\n❌ Error calling Azure OpenAI: {e}\n")
        raise


# ============================================================================
# Step 5: Save Analysis Output
# ============================================================================

def save_analysis_output(
    cpt_code: int, 
    analysis: NCCIAnalysis, 
    chunks: List[Dict], 
    metadata: Dict,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save structured analysis to markdown file.
    
    Args:
        cpt_code: CPT code
        analysis: Validated NCCIAnalysis Pydantic model
        chunks: List of retrieved chunks
        metadata: Metadata from retrieval
        output_dir: Output directory
        
    Returns:
        Path to saved markdown file
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'output'
    
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f'llm_analysis_cpt_{cpt_code}.md'
    
    import re
    
    # Build markdown content from structured data
    markdown_sections = []
    
    # Modifier Rules section
    markdown_sections.append(f"## Modifier Rules for CPT {cpt_code}\n")
    for rule in analysis.modifier_rules:
        markdown_sections.append(f"- {rule}")
    markdown_sections.append("")
    
    # PTP Edit Rules section
    markdown_sections.append("## PTP Edit Rules\n")
    for rule in analysis.ptp_edit_rules:
        markdown_sections.append(f"- {rule}")
    markdown_sections.append("")
    
    # Compliance Risks section
    markdown_sections.append("## Misuse Opportunities & Compliance Risks\n")
    for risk in analysis.compliance_risks:
        markdown_sections.append(f"- {risk}")
    markdown_sections.append("")
    
    # Clinical Context section
    markdown_sections.append("## Clinical Context & Special Rules\n")
    for context in analysis.clinical_context:
        markdown_sections.append(f"- {context}")
    
    analysis_markdown = "\n".join(markdown_sections)
    
    # Extract all cited numbers from the analysis
    cited_numbers = set()
    citation_pattern = r'\[(\d+)\]'
    for match in re.finditer(citation_pattern, analysis_markdown):
        cited_numbers.add(int(match.group(1)))
    
    # Build references list for cited chunks only
    references_list = []
    for i in sorted(cited_numbers):
        if i <= len(chunks):
            chunk = chunks[i-1]
            chunk_id = chunk.get('chunk_id', 'unknown')
            pages = chunk.get('pages', [])
            page_str = f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0]) if pages else "N/A"
            section = chunk.get('section') or 'General'
            
            references_list.append(f"{i}. `{chunk_id}` - Pages {page_str}, {section}")
    
    references_text = "\n".join(references_list) if references_list else "No citations used."
    
    full_output = f"""# 🎯 NCCI Compliance Analysis for CPT {cpt_code}

{analysis_markdown}

---

## References

{references_text}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_output)
    
    print(f"\n✓ Analysis saved to: {output_file}\n")
    return output_file
# ============================================================================
# Main Pipeline
# ============================================================================

def ncci_llm_analysis(
    cpt_code: int, 
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    auto_build: bool = False
) -> Path:
    """
    Run complete LLM analysis pipeline with citations.
    
    Args:
        cpt_code: CPT code (e.g. 97810)
        temperature: LLM generation temperature (0.0=strict, 1.0=creative)
        max_tokens: Maximum tokens to generate
        auto_build: If True, automatically build indices if missing (default: False)
    
    Returns:
        Path to output file
    """
    print(f"\n{'='*70}")
    print(f"🎯 NCCI LLM Analysis Pipeline for CPT {cpt_code}")
    print(f"{'='*70}\n")
    
    try:
        # Check if retrieved chunks exist, if not, run retrieval first
        output_dir = Path(__file__).parent.parent / 'output'
        chunks_path = output_dir / f'retrieved_chunks_cpt_{cpt_code}.json'
        
        if not chunks_path.exists():
            print(f"[➡️ Step 0/6] Retrieved chunks not found, running retrieval pipeline...\n")
            result = multi_stage_hybrid_rag(target_cpt_code=cpt_code, top_k=15, auto_build=auto_build)
            if result is None:
                raise RuntimeError("Retrieval failed - indices may be missing. Please run build_all.py first.")
            print(f"✓ Retrieval completed\n")
        
        print(f"[➡️ Step 1/6] Loading retrieved chunks for CPT {cpt_code}...\n")
        metadata, chunks = load_retrieved_chunks(cpt_code)
        print()
        
        print(f"[➡️ Step 2/6] Formatting {len(chunks)} chunks as markdown with citations...\n")
        chunks_markdown = format_chunks_as_markdown(chunks)
        print(f"✓ Generated markdown with citations [1] through [{len(chunks)}]\n")
        
        print(f"[➡️ Step 3/6] Creating LLM analysis prompt...\n")
        prompt = create_analysis_prompt(cpt_code, chunks_markdown, len(chunks))
        prompt_length = len(prompt)
        print(f"✓ Prompt created ({prompt_length:,} characters)\n")
        
        print(f"[➡️ Step 4/6] Calling LLM for analysis (may take 30-90 seconds)...")
        analysis = call_llm_for_analysis(prompt, temperature, max_tokens)
        
        print(f"[➡️ Step 5/6] Saving analysis with citation references...")
        
        from datetime import datetime
        metadata['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        output_file = save_analysis_output(
            cpt_code, 
            analysis, 
            chunks, 
            metadata
        )
        
        return output_file
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}\n")
        raise
    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    ncci_llm_analysis('97810')
