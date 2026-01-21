# CCV Research UI – Refactored (Backend + Frontend) 🚀

A modular APC (Ambulatory Payment Classification) research application with:

- Backend: Streamlit UI (legacy) plus new FastAPI endpoints for programmatic access
- Frontend: Next.js 16 portal (auth, chat UI, libsql/Drizzle persistence)

## ✨ Highlights

- **FastAPI layer** for the APC services (mirrors Streamlit flows)
- **Agent-ready services**: each section is independently runnable
- **Frontend portal** with Okta auth, chat, libsql/Drizzle
- **Organized data/output** directories; SQLite auto-created

git clone <repository-url>

## 🚀 Quick Start

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
```

Data prerequisite: place `CPT Codes with Long Descriptions 2025.xlsx` under `backend/data/`.

Run Streamlit UI (legacy):

```bash
cd backend
streamlit run app.py
```

Run FastAPI (new):

```bash
cd backend
uvicorn api:app --reload
```

Optional validation:

```bash
cd backend
python test_refactored_code.py
```

### Frontend (Next.js 16)

```bash
cd frontend
npm install
npm run dev
```

Env vars: `NEXT_PUBLIC_AUTH_OKTA_*`, `NEXT_PUBLIC_BASE_URL`, `NEXT_PUBLIC_POST_LOGOUT`, `DB_URL` (libsql file), Azure OpenAI keys.

## 📂 Project Structure (high level)

```
backend/
├── api.py                  # FastAPI entrypoint (uvicorn api:app --reload)
├── api_schemas.py          # Pydantic request models
├── app.py                  # Streamlit UI entry
├── llm_wrapper.py          # Azure OpenAI / MedGEMMA client config
├── db.py, feedback.py      # Legacy chat/feedback helpers
├── personas.py             # Legacy persona config
├── requirements.txt
├── data/                   # SQLite files (auto), CPT Excel
├── output/                 # Cached findings, exports
├── services/               # APC business logic (agentic sections)
│   ├── apc_orchestrator.py # conduct_section_research/run_all, chat helpers
│   ├── cpt_service.py      # CPT generation/parsing
│   ├── code_description_service.py ... (section 1)
│   ├── guideline_examination_service.py (section 2)
│   ├── payment_rate_service.py (section 3)
│   ├── device_code_service.py (section 4)
│   ├── ncci_compliance_service.py (section 5)
│   ├── reference_material_service.py (section 6)
│   ├── utils.py            # DB helpers (notes, chat, sessions, feedback)
│   └── common/             # Shared CPT description utilities, etc.
└── views/                  # Streamlit view components (legacy UI)

frontend/
├── app/                    # Next.js app router
├── components/             # UI components (chat, auth, notes, etc.)
├── lib/                    # db.ts (Drizzle/libsql), llm.ts, okta.ts, chat.ts
├── db/schemas.ts           # Drizzle schema
├── public/
├── package.json, tsconfig.json, etc.
└── data/                   # Frontend CPT descriptions JSON
```

## 🎯 Key Features

### Research Workflow

1. **Step 1: Topic Input**
   - Enter your research topic
   - Load previous sessions

2. **Step 1.5: CPT Code Selection**
   - AI-generated CPT code suggestions
   - Manual code selection
   - Code description lookup

3. **Step 2: Research Execution**
   - Six independent research sections
   - Each section with dedicated service and view
   - Final comprehensive assessment

4. **Step 3: Results & Export**
   - View detailed research results
   - Export to PDF or Excel
   - Chat with AI for clarifications
   - Provide accuracy feedback
   - Save notes for future reference

### Six Research Sections

1. **Code Description** - Detailed CPT code analysis
2. **Guideline Examination** - Policy and guideline review
3. **Payment Rate & Policy** - Reimbursement analysis
4. **Device Code** - Related device coding
5. **NCCI Compliance** - National Correct Coding Initiative checks
6. **Reference Material** - Supporting documentation

## 🧪 Architecture Principles

### Services Layer (Business Logic)

- **Pure Functions**: Testable, predictable business logic
- **Agent-Ready**: Each service can operate independently
- **Database Abstraction**: Centralized data operations
- **LLM Integration**: Unified prompt building and parsing

### Views Layer (UI Components)

- **Component-Based**: Modular, reusable UI elements
- **State Management**: Streamlit session_state integration
- **Shared Components**: Common UI patterns in utils
- **Clean Separation**: No business logic in views

## 🔧 Configuration

### LLM Models

Configure in `llm_wrapper.py`:

- Azure OpenAI (GPT-4.1, GPT-5 variants)
- Custom MedGEMMA model

### Database

All databases auto-initialize in `data/` directory:

- `apc_notes.db` - Research notes
- `apc_chat.db` - Chat history
- `apc_feedback.db` - User feedback
- `apc_research_sessions.db` - Research sessions
- `interactions2.db` - User interactions (legacy)
- `feedback.db` - General feedback (legacy)

## 📚 Documentation

- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Detailed refactoring documentation
- Code comments - Inline documentation in all modules
- Docstrings - Function-level documentation

## 🧪 Testing

Run the validation test:

```bash
python3 test_refactored_code.py
```

This will check:

- ✅ Module imports
- ✅ Directory structure
- ✅ Database path configuration
- ✅ Service layer functions
- ✅ View layer functions

## 🛠️ Development

### Adding a New Research Section

1. **Create Service Module**: `services/new_section_service.py`
   - Implement `run_section_X()` function
   - Build prompt with `build_section_X_prompt()`
   - Parse response with `parse_section_X_response()`

2. **Create View Module**: `views/new_section_view.py`
   - Implement `render_section_X()` function
   - Use shared components from `views/utils.py`

3. **Update Orchestrator**: `services/apc_orchestrator.py`
   - Add section to `run_all_sections()`
   - Implement `run_section_X()` method

4. **Update Main View**: `views/apc_main_view.py`
   - Add tab in `render_step3()`
   - Import and call new view function

### Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions
- Keep functions focused and testable

## 🚀 Future Enhancements

### Planned Features

- [ ] Unit tests for all service modules
- [ ] Agent-to-agent communication protocol
- [ ] Parallel section execution
- [ ] Advanced caching strategies
- [ ] Performance monitoring dashboard
- [ ] Multi-user support
- [ ] API endpoints for programmatic access

### Agentic Workflow

Each section service is designed to become an autonomous agent:

- Independent execution capability
- Standardized input/output interfaces
- Inter-agent communication ready
- Result aggregation support

## 📝 License

[Add your license information]

## 🤝 Contributing

[Add contribution guidelines]

## 📧 Contact

[Add contact information]

---

**Version**: 2.1  
**Last Updated**: 2026-01-19  
**Architecture**: Modular Services/Views with FastAPI layer
