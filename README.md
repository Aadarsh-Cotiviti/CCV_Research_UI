# CCV Research UI – Medical Coding Analysis Platform

A comprehensive medical coding research and analysis platform for CPT code analysis across multiple payment systems (APC, ASC, PNPP) and compliance frameworks. The application consists of a Python backend (FastAPI + legacy Streamlit) and a Next.js 16 frontend.

## ✨ Highlights

- **FastAPI layer** for programmatic access to APC services
- **Agent-ready services**: Each section is independently runnable
- **Frontend portal** with Okta auth, chat UI, and libsql/Drizzle persistence
- **Streamlit UI** (legacy) for direct interaction
- **Organized data/output** directories with auto-initialized SQLite databases

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│        Streamlit UI (Legacy) | FastAPI | Next.js 16          │
└──────────────┬────────────────────────────────┬──────────────┘
               │                                │
        ┌──────▼──────┐                  ┌──────▼──────┐
        │    Views    │                  │  Services   │
        │   (UI Layer)│◄─────────────────┤(Logic Layer)│
        └──────┬──────┘                  └──────┬──────┘
               │                                │
        ┌──────▼──────────────────────────────┬─▼──────┐
        │                                     │        │
   ┌────▼─────┐  ┌─────────┐  ┌───────┐  ┌──▼───┐  ┌─▼────┐
   │  SQLite  │  │  Excel  │  │  PDF  │  │ LLM  │  │ RAG  │
   │  Storage │  │  Data   │  │  Docs │  │ API  │  │System│
   └──────────┘  └─────────┘  └───────┘  └──────┘  └──────┘
```

### Three-Tier Architecture

#### 1. **Presentation Layer** (Views)
- **Location**: `views/` directory
- **Purpose**: User interface components and data visualization
- **Technology**: Streamlit components, Pandas DataFrames, Markdown rendering
- **Key Files**:
  - `apc_main_view.py` - Main workflow and orchestration UI
  - `code_description_view.py` - Section 1: CPT code description analysis
  - `guideline_examination_view.py` - Section 2: Clinical guidelines review
  - `payment_rate_view.py` - Section 3: Payment rate comparison (APC/ASC/PNPP)
  - `device_code_view.py` - Section 4: Device code analysis
  - `ncci_compliance_view.py` - Section 5: NCCI compliance checking
  - `reference_material_view.py` - Section 6: Reference material collection
  - `final_assessment_view.py` - Consolidated findings report

#### 2. **Business Logic Layer** (Services)
- **Location**: `services/` directory
- **Purpose**: Data processing, LLM orchestration, and business rules
- **Design Pattern**: Service-oriented architecture with modular components
- **Agentic Architecture**: Each section service operates independently with its own knowledge retrieval and LLM analysis
- **Key Components**:

  **Core Services**:
  - `code_description_service.py` - CPT description change tracking
  - `guideline_examination_service.py` - Guideline extraction and analysis
  - `payment_rate_service.py` - Multi-system payment comparison
  - `device_code_service.py` - Device code tracking and description
  - `ncci_compliance_service.py` - PTP edit checking via RAG
  - `reference_material_service.py` - Reference document aggregation
  - `final_assessment_service.py` - Cross-section data consolidation

  **Utility Services**:
  - `apc_orchestrator.py` - Workflow orchestration and state management
  - `cpt_service.py` - CPT code generation and validation
  - `report_service.py` - PDF/Excel report generation
  - `utils.py` - Database operations and shared utilities

  **Common Utilities** (`services/common/`):
  - `apc_payment_comparison.py` - APC payment data loader
  - `asc_payment_comparison.py` - ASC payment data loader
  - `pnpp_payment_comparison.py` - PNPP payment data loader
  - `cms_exclusions.py` - CMS exclusion list management
  - `cpt_utils.py` - CPT code utility functions
  - `device_utils.py` - HCPCS device code utilities

  **Data Preprocessing** (`services/data_preprocessing/`):
  - `cpt_change_preprocessing.py` - CPT code change tracking
  - `device_change_preprocessing.py` - Device code change tracking
  - `ptp_table_preprocessing.py` - NCCI PTP table processing

#### 3. **Data Layer**
- **Location**: `data/` directory and `ncci_rag/` system
- **Storage Systems**:

  **SQLite Databases** (Auto-created on first run):
  - `apc_notes.db` - Research notes and annotations
  - `apc_chat.db` - Chat conversation history
  - `apc_feedback.db` - User feedback and ratings
  - `apc_research_sessions.db` - Research session state

  **Excel Data Files**:
  - `CPT Codes with Long Descriptions 2025.xlsx` - CPT code master list
  - `apc_payment_changes_quarterly.xlsx` - APC payment rate history (2024-2026)
  - `asc_payment_changes_quarterly.xlsx` - ASC payment rate history (2024-2026)
  - `pnpp_payment_changes_quarterly.xlsx` - PNPP payment rate history (2024-2026)
  - `hcpcs_codes_all.csv` - HCPCS device code descriptions

  **Preprocessed Data** (`data/`):
  - `preprocessed_cpt_change_tracking.csv` - CPT description changes over time
  - `preprocessed_device_code_change_tracking.csv` - Device code changes over time
  - `ptp_edit_table_mod_0_*.csv` - NCCI PTP Modifier 0 edit tables
  - `ptp_edit_table_mod_1_*.csv` - NCCI PTP Modifier 1 edit tables

### NCCI RAG System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              NCCI RAG Pipeline (Section 5)                   │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────▼──────┐
    │   Query     │ (User CPT Code + Context)
    └──────┬──────┘
           │
    ┌──────▼──────────────────────────────────────┐
    │   Hybrid Retrieval Engine                   │
    │   ┌──────────────┐    ┌──────────────┐     │
    │   │ BM25 Search  │    │ChromaDB Vec  │     │
    │   │  (Lexical)   │    │  (Semantic)  │     │
    │   └──────┬───────┘    └──────┬───────┘     │
    │          └─────────┬──────────┘             │
    │                    │                        │
    │            ┌───────▼────────┐               │
    │            │  Top-k Chunks  │               │
    │            │   (k=15)       │               │
    │            └────────────────┘               │
    └──────────────────────┬──────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  LLM Agent  │
                    │  Analysis   │
                    └──────┬──────┘
                           │
                    ┌──────▼─────────┐
                    │  NCCI Result   │
                    │  with Citations│
                    └────────────────┘
```

**NCCI RAG Components** (`ncci_rag/src/`):
- `extract_pdf.py` - PDF text extraction with page metadata
- `extract_toc.py` - Table of contents structure parsing
- `chunk_and_tag.py` - Semantic chunking with metadata tagging
- `build_bm25.py` - BM25 lexical index construction
- `build_embeddings_chroma.py` - ChromaDB semantic embeddings
- `build_range_index.py` - CPT code range routing index
- `retrieve.py` - Hybrid retrieval orchestration
- `llm_extract.py` - LLM-based analysis with citation

**Auto-build System**:
- Detects missing indices on first run
- Builds all required indices automatically (10-15 minutes)
- Stores indices in `ncci_rag/build/` directory
- Supports manual pre-build via `build_all.py`

### Frontend Architecture (Next.js 16)

**Tech Stack**:
- Next.js 16 App Router
- React 19
- TypeScript
- Drizzle ORM with libsql (SQLite)
- Hono for API routes
- Okta authentication

**Key Directories**:
- `app/` - Next.js app router pages and API routes
- `components/` - React UI components
- `lib/` - Core utilities:
  - `backendClient.ts` - Type-safe backend API client using openapi-fetch
  - `db.ts` - Drizzle database client and queries
  - `session.ts` - JWT session management
  - `chat.ts` - Chat utilities
- `db/schemas.ts` - Drizzle database schemas

**Database Schema** (`db/schemas.ts`):
- `users` - User accounts with Okta integration
- `sessions` - Research sessions (type: "chat" | "apc")
- `sections` - Session sections/conversations
- `messages` - Chat messages with LLM responses
- `message_feedback` - User feedback (positive/negative)
- `highlighted_text` - User text highlights with annotations
- `general_feedback` - App-wide feedback

## 🔄 Research Workflow

```
Step 1: Topic Input
    │
    ▼
Step 1.5: CPT Code Selection
    │  ├─ LLM generates relevant CPT codes
    │  └─ User selects/confirms codes
    ▼
Step 2: Multi-Section Analysis
    │
    ├─► Section 1: Code Description
    │       └─ Compare 2024 vs 2025 descriptions
    │       └─ Flag changes, output "No changes" for unchanged codes
    │
    ├─► Section 2: Guideline Examination
    │       └─ Extract relevant clinical guidelines
    │       └─ LLM analysis of guideline updates
    │
    ├─► Section 3: Payment Rate Comparison
    │       ├─ APC: Historical payment rates + APC codes
    │       ├─ ASC: Historical payment rates
    │       └─ PNPP: Facility vs Non-Facility rates
    │
    ├─► Section 4: Device Code Analysis
    │       └─ Track device code changes
    │       └─ Flag changes, output "No changes" for unchanged codes
    │
    ├─► Section 5: NCCI Compliance
    │       ├─ Query NCCI RAG system
    │       ├─ Retrieve top-15 relevant chunks
    │       └─ LLM cites only relevant chunks
    │
    └─► Section 6: Reference Materials
            └─ Aggregate supporting documents
    │
    ▼
Final Assessment
    │  └─ Consolidate findings from Sections 1-6
    │  └─ Generate comprehensive summary
    │
    ▼
Step 3: Export & Feedback
    ├─ PDF/Excel report generation
    ├─ Chat interface for Q&A
    └─ Accuracy feedback collection
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure OpenAI API access (or compatible LLM API)

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run legacy Streamlit UI
streamlit run app.py

# Run FastAPI server (preferred for new development)
uvicorn api:app --reload

# Test refactored code
python test_refactored_code.py

# Build NCCI RAG indices (first-time setup, takes 10-15 minutes)
python ncci_rag/src/build_all.py
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Generate TypeScript types from backend OpenAPI schema
npm run gen:api-types
```

**Important**: Run `npm run gen:api-types` after any changes to backend API schemas to regenerate `lib/api-types.ts`.

### Data Setup

1. **Place required Excel files in `backend/data/` directory**:
   - `CPT Codes with Long Descriptions 2025.xlsx`
   - `apc_payment_changes_quarterly.xlsx`
   - `asc_payment_changes_quarterly.xlsx`
   - `pnpp_payment_changes_quarterly.xlsx`
   - `hcpcs_codes_all.csv`

2. **NCCI Manual for Section 5**:
   ```bash
   # Download NCCI Manual PDF
   # Save as: backend/ncci_rag/data/ncci_manual.pdf

   # Install RAG dependencies
   pip install pymupdf regex rank_bm25 chromadb pydantic

   # Indices will auto-build on first use (or manually pre-build):
   python backend/ncci_rag/src/build_all.py
   ```

3. **Preprocessed data will auto-generate in `backend/data/` on first run**

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# Azure OpenAI (GPT-4.1 series)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=

# Azure OpenAI (GPT-5 series)
AZURE_OPENAI_API_KEY_GPT_5=
AZURE_OPENAI_ENDPOINT_GPT_5=
AZURE_OPENAI_API_KEY_GPT_5_MINI=
AZURE_OPENAI_ENDPOINT_GPT_5_MINI=
AZURE_OPENAI_API_KEY_GPT_5_NANO=
AZURE_OPENAI_ENDPOINT_GPT_5_NANO=

# Optional: Custom MedGEMMA model
MEDGEMMA_MODEL_URL=
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```bash
# Okta Authentication
NEXT_PUBLIC_AUTH_OKTA_ISSUER=
NEXT_PUBLIC_AUTH_OKTA_CLIENT_ID=
OKTA_CLIENT_SECRET=
NEXT_PUBLIC_BASE_URL=
NEXT_PUBLIC_POST_LOGOUT=

# Database
DB_URL=data/app.db

# Session
SESSION_JWT_SECRET=

# Backend API
BACKEND_API_URL=http://localhost:8000

# Azure OpenAI (frontend LLM calls)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
```

### LLM Configuration

Edit `backend/llm_wrapper.py`:
- **Supported Models**: Azure OpenAI (`gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`), Custom (`medgemma-27b-multimodal7`)
- **Functions**: `query_llm(messages, model)` - Synchronous, `stream_llm(messages, model)` - Streaming
- Configurable parameters: temperature, max_tokens, top_p

## 📂 Project Structure

```
backend/
├── api.py                  # FastAPI entrypoint (uvicorn api:app --reload)
├── api_schemas.py          # Pydantic request models
├── app.py                  # Streamlit UI entry
├── llm_wrapper.py          # Azure OpenAI / MedGEMMA client config
├── requirements.txt
├── data/                   # SQLite files (auto), CPT Excel
├── output/                 # Cached findings, exports
├── services/               # APC business logic (agentic sections)
│   ├── apc_orchestrator.py
│   ├── cpt_service.py
│   ├── code_description_service.py
│   ├── guideline_examination_service.py
│   ├── payment_rate_service.py
│   ├── device_code_service.py
│   ├── ncci_compliance_service.py
│   ├── reference_material_service.py
│   ├── final_assessment_service.py
│   ├── utils.py
│   ├── common/             # Shared utilities
│   └── data_preprocessing/ # Data preprocessing scripts
├── views/                  # Streamlit view components
└── ncci_rag/              # NCCI RAG system

frontend/
├── app/                    # Next.js app router
├── components/             # UI components
├── lib/                    # Core utilities (db, api client, session)
├── db/schemas.ts           # Drizzle schema
└── data/                   # Frontend data files
```

## 📊 Output Structure

```
backend/output/
└── services_findings/
    └── {CPT_CODE}/
        ├── section_1_results.json   # Code descriptions
        ├── section_2_results.json   # Guidelines
        ├── section_3_results.json   # Payment rates (APC/ASC/PNPP)
        ├── section_4_results.json   # Device codes
        ├── section_5_results.json   # NCCI compliance
        ├── section_6_results.json   # References
        └── final_assessment.json    # Consolidated report
```

## 🎯 Key Features

### Cost Optimization
- **LLM call reduction**: Sections 1 & 4 skip LLM for unchanged codes
- **Caching**: Preprocessed data stored locally
- **Selective retrieval**: RAG system retrieves top-k only

### NCCI RAG Quality
- **Hybrid search**: BM25 (lexical) + ChromaDB (semantic)
- **Selective citation**: LLM cites only relevant chunks (not all 15)
- **Prompt optimization**: Emphasizes quality over quantity

### Multi-Payment System Support
- **APC**: Hospital Outpatient Prospective Payment System
- **ASC**: Ambulatory Surgical Center Payment System
- **PNPP**: Physician Non-Facility Payment Practice (Facility/Non-Facility rates)

### User Experience
- **Auto-build system**: Missing indices built automatically
- **Loading indicators**: Clear progress messages
- **Error handling**: Graceful degradation for missing data
- **Feedback system**: Accuracy ratings and notes

## 🐛 Troubleshooting

### Common Issues

1. **Missing indices error in Section 5**:
   - Ensure `backend/ncci_rag/data/ncci_manual.pdf` exists
   - Wait for auto-build (10-15 minutes on first run)
   - Or manually run: `python backend/ncci_rag/src/build_all.py`

2. **Payment data showing "N/A"**:
   - Check Excel files are in `backend/data/` directory
   - Verify column names match expected format
   - Check CPT code exists in payment tables

3. **LLM errors**:
   - Verify Azure OpenAI API credentials
   - Check API quota and rate limits
   - Ensure deployment name matches configuration

4. **Frontend API types out of sync**:
   - Run `npm run gen:api-types` to regenerate from backend OpenAPI schema
   - Ensure backend is running at `http://localhost:8000`

5. **Database migrations not applied**:
   - Frontend: Drizzle migrations auto-run on app start
   - Backend: SQLite databases auto-initialize in `backend/data/`

## 📝 Development Guide

### Adding New Features

1. **New Research Section**:
   - Create service in `services/new_section_service.py`
   - Implement `run_section_X()` function with `build_section_X_prompt()` and `parse_section_X_response()`
   - Create view in `views/new_section_view.py`
   - Update orchestrator in `services/apc_orchestrator.py`
   - Update API in `api.py` (add to `SECTION_FUNCS`)
   - Add tab in `views/apc_main_view.py`

2. **New Payment System**:
   - Create loader in `services/common/new_payment_comparison.py`
   - Update `payment_rate_service.py` to include new system
   - Update views and final assessment to display new payment type

3. **New Data Source**:
   - Add loader in `services/data_preprocessing/`
   - Update relevant service to consume data
   - Add preprocessing step in orchestrator

### Code Standards
- Follow PEP 8 style guidelines (backend), TypeScript strict mode (frontend)
- Use type hints for function signatures
- Add docstrings (Google style) to all public functions
- Keep functions focused (single responsibility)
- Separate UI logic (views/components) from business logic (services)
- **Agentic pattern**: Services should be independently executable with standard interfaces
- **Database abstraction**: Use utility functions in `services/utils.py` or `lib/db.ts`

## 🔮 Future Roadmap

- [ ] Unit tests for all service modules
- [ ] Multi-user authentication and authorization
- [ ] Parallel section execution for faster processing
- [ ] Agent-to-agent communication protocol
- [ ] Advanced caching strategies (Redis)
- [ ] Performance monitoring dashboard
- [ ] REST API enhancements for programmatic access
- [ ] Batch processing mode for multiple CPT codes
- [ ] Custom RAG models for specialized medical domains
- [ ] Export templates customization
- [ ] Real-time collaboration features

## 📚 Documentation

- **Architecture**: This README
- **Project Instructions**: `CLAUDE.md`
- **NCCI RAG System**: `backend/ncci_rag/README.md`
- **Migration Guide**: `MIGRATION_GUIDE.md` (if available)
- **Inline Documentation**: Docstrings in all modules

---

**Version**: 2.1
**Last Updated**: February 5, 2026
**Architecture**: Three-Tier Services/Views/Data Pattern with FastAPI + Next.js 16
**License**: [Add License]
**Contact**: [Add Contact]
