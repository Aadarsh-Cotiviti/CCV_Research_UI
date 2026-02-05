# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CCV Research UI is a full-stack medical coding research and analysis platform for CPT code analysis across multiple payment systems (APC, ASC, PNPP) and compliance frameworks. The application consists of a Python backend (FastAPI + legacy Streamlit) and a Next.js 16 frontend.

## Development Commands

### Backend (Python)

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

### Frontend (Next.js)

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

**Important**: Run `npm run gen:api-types` after any changes to backend API schemas to regenerate [lib/api-types.ts](frontend/lib/api-types.ts).

## Architecture

### Three-Tier Backend Architecture

The backend follows a strict separation between Presentation (views), Business Logic (services), and Data layers:

**1. Presentation Layer** ([views/](backend/views/))
- Streamlit UI components (legacy)
- Each view corresponds to a research section
- No business logic - only display and user interaction

**2. Business Logic Layer** ([services/](backend/services/))
- Core application logic organized by research sections
- **Agentic architecture**: Each section service operates independently with its own knowledge retrieval and LLM analysis
- Section services (1-6): code_description, guideline_examination, payment_rate, device_code, ncci_compliance, reference_material
- [services/apc_orchestrator.py](backend/services/apc_orchestrator.py) - Workflow orchestration and section coordination
- [services/final_assessment_service.py](backend/services/final_assessment_service.py) - Consolidates findings from all sections
- [services/utils.py](backend/services/utils.py) - Database operations, session management
- [services/common/](backend/services/common/) - Shared utilities for CPT descriptions, payment data loaders

**3. Data Layer**
- SQLite databases (auto-created in [backend/data/](backend/data/)):
  - `apc_notes.db` - Research notes and annotations
  - `apc_chat.db` - Chat conversation history
  - `apc_feedback.db` - User feedback
  - `apc_research_sessions.db` - Research session state
- Excel data files (required in [backend/data/](backend/data/)):
  - `CPT Codes with Long Descriptions 2025.xlsx`
  - `apc_payment_changes_quarterly.xlsx`
  - `asc_payment_changes_quarterly.xlsx`
  - `pnpp_payment_changes_quarterly.xlsx`
  - `hcpcs_codes_all.csv`
- Preprocessed CSV files (auto-generated):
  - `preprocessed_cpt_change_tracking.csv`
  - `preprocessed_device_code_change_tracking.csv`
  - `ptp_edit_table_mod_*.csv`

### NCCI RAG System

Located in [backend/ncci_rag/](backend/ncci_rag/), this system provides NCCI compliance checking via hybrid retrieval:

- **Hybrid Search**: BM25 (lexical) + ChromaDB (semantic embeddings)
- **Pipeline**: PDF extraction → chunking → indexing → retrieval → LLM analysis
- **Auto-build**: Indices auto-generate on first use (or manually via `build_all.py`)
- **Indices stored in**: [backend/ncci_rag/build/](backend/ncci_rag/build/)
- **Source PDF required**: [backend/ncci_rag/data/ncci_manual.pdf](backend/ncci_rag/data/ncci_manual.pdf)

Key files:
- [ncci_rag/src/retrieve.py](backend/ncci_rag/src/retrieve.py) - Hybrid retrieval orchestration
- [ncci_rag/src/llm_extract.py](backend/ncci_rag/src/llm_extract.py) - LLM-based analysis with citations
- [ncci_rag/src/build_all.py](backend/ncci_rag/src/build_all.py) - Index builder

### Frontend Architecture (Next.js 16)

**Tech Stack**:
- Next.js 16 App Router
- React 19
- TypeScript
- Drizzle ORM with libsql (SQLite)
- Hono for API routes
- Okta authentication

**Key Directories**:
- [app/](frontend/app/) - Next.js app router pages and API routes
- [components/](frontend/components/) - React UI components
- [lib/](frontend/lib/) - Core utilities:
  - [lib/backendClient.ts](frontend/lib/backendClient.ts) - Type-safe backend API client using openapi-fetch
  - [lib/db.ts](frontend/lib/db.ts) - Drizzle database client and queries
  - [lib/session.ts](frontend/lib/session.ts) - JWT session management
  - [lib/chat.ts](frontend/lib/chat.ts) - Chat utilities
- [db/schemas.ts](frontend/db/schemas.ts) - Drizzle database schemas

**Database Schema** ([db/schemas.ts](frontend/db/schemas.ts)):
- `users` - User accounts with Okta integration
- `sessions` - Research sessions (type: "chat" | "apc")
- `sections` - Session sections/conversations
- `messages` - Chat messages with LLM responses
- `message_feedback` - User feedback (positive/negative)
- `highlighted_text` - User text highlights with annotations
- `general_feedback` - App-wide feedback

### Backend API Structure

The FastAPI backend ([api.py](backend/api.py)) exposes endpoints for:

1. **CPT Generation**: `POST /cpt/generate` - Generate relevant CPT codes for a research topic
2. **Section Research**: `POST /research/run/{section_id}` - Run individual research sections (0-6)
3. **Section Chat**: `POST /research/sections/chat` - Chat about section results with context
4. **General Chat**: `POST /chat` - Streaming LLM chat
5. **Export**: `GET /export/pdf`, `GET /export/excel` - Export research results

Section IDs map to:
- 0: Code Description Analysis
- 1: Guideline Examination
- 2: Payment Rate Comparison
- 3: Device Code Analysis
- 4: NCCI Compliance
- 5: Reference Material Review
- 6: Final Assessment (consolidates all sections)

### LLM Integration

[llm_wrapper.py](backend/llm_wrapper.py) provides a unified interface for multiple LLM models:

**Supported Models**:
- Azure OpenAI: `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
- Custom: `medgemma-27b-multimodal7`

**Functions**:
- `query_llm(messages, model)` - Synchronous LLM call
- `stream_llm(messages, model)` - Streaming LLM response

**Configuration**: Each model requires specific environment variables for API keys and endpoints.

## Research Workflow

The application follows a six-section research workflow for CPT code analysis:

1. **Topic Input** → 2. **CPT Code Selection** (LLM-generated) → 3. **Multi-Section Analysis**:
   - Section 1: Code Description Analysis (compare 2024 vs 2025)
   - Section 2: Guideline Examination (extract clinical guidelines)
   - Section 3: Payment Rate Comparison (APC/ASC/PNPP historical rates)
   - Section 4: Device Code Analysis (track device code changes)
   - Section 5: NCCI Compliance (RAG-based PTP edit checking)
   - Section 6: Reference Material Review (supporting documentation)
4. **Final Assessment** → 5. **Export & Feedback** (PDF/Excel, chat Q&A, accuracy ratings)

Results are cached in [backend/output/services_findings/{CPT_CODE}/](backend/output/services_findings/) as JSON files.

## Key Implementation Patterns

### Adding a New Research Section

1. Create service module: [services/new_section_service.py](backend/services/new_section_service.py)
   - Implement `run_section_X(cpt_code, model, use_cache)` function
   - Build prompt with `build_section_X_prompt()`
   - Parse LLM response with `parse_section_X_response()`

2. Update orchestrator: [services/apc_orchestrator.py](backend/services/apc_orchestrator.py)
   - Add to `SECTION_SERVICES` registry

3. Update API: [api.py](backend/api.py)
   - Add service function to `SECTION_FUNCS` list

4. Create view (if using Streamlit): [views/new_section_view.py](backend/views/new_section_view.py)
   - Implement `render_section_X()` function

### Adding a New Payment System

1. Create loader: [services/common/new_payment_comparison.py](backend/services/common/new_payment_comparison.py)
2. Update [services/payment_rate_service.py](backend/services/payment_rate_service.py) to include new system
3. Update display logic in views and final assessment

### Database Operations

Backend uses direct SQLite operations via [services/utils.py](backend/services/utils.py).
Frontend uses Drizzle ORM via [lib/db.ts](frontend/lib/db.ts).

Example backend pattern:
```python
from services.utils import save_research_session, get_research_session
session_id = save_research_session(topic, cpt_codes, metadata)
session = get_research_session(session_id)
```

Example frontend pattern:
```typescript
import { db } from "@/lib/db";
import { sessions } from "@/db/schemas";
const session = await db.query.sessions.findFirst({
  where: eq(sessions.id, sessionId)
});
```

## Environment Variables

### Backend ([backend/.env](backend/.env))

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

### Frontend ([frontend/.env.local](frontend/.env.local))

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

## Common Issues & Solutions

### NCCI RAG indices missing
- Ensure [backend/ncci_rag/data/ncci_manual.pdf](backend/ncci_rag/data/ncci_manual.pdf) exists
- Run `python ncci_rag/src/build_all.py` (10-15 minutes)
- Or wait for auto-build on first Section 5 execution

### Payment data showing "N/A"
- Verify all Excel files exist in [backend/data/](backend/data/)
- Check CPT code exists in payment tables
- Verify column names match expected format

### Frontend API types out of sync
- Run `npm run gen:api-types` to regenerate from backend OpenAPI schema
- Ensure backend is running at `http://localhost:8000`

### Database migrations not applied
- Frontend: Drizzle migrations in [frontend/drizzle/](frontend/drizzle/) auto-run on app start
- Backend: SQLite databases auto-initialize in [backend/data/](backend/data/)

## Code Standards

- **Backend**: Follow PEP 8, use type hints, add docstrings (Google style)
- **Frontend**: TypeScript strict mode, use type inference where possible
- **Separation of concerns**: Keep business logic in services, UI logic in views/components
- **Agentic pattern**: Services should be independently executable with standard interfaces
- **Database abstraction**: Use utility functions in [services/utils.py](backend/services/utils.py) or [lib/db.ts](frontend/lib/db.ts)
