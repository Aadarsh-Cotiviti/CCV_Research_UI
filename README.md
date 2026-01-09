# CCV Research UI - Refactored Version 2.0 🚀

A modular, scalable APC (Ambulatory Payment Classification) research application built with Streamlit.

## ✨ What's New in V2.0

- **🏗️ Modular Architecture**: Complete separation of Services (business logic) and Views (UI components)
- **🤖 Agent-Ready**: Each research section is designed as an independent agent for future agentic workflows
- **📁 Organized Structure**: Clean directory layout with dedicated data/ and output/ folders
- **🔧 Better Maintainability**: Reusable components and single-responsibility modules
- **📊 Enhanced Testing**: Validation scripts to ensure code integrity

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd CCV_Research_UI_Dev

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Setup

Place the following file in the `data/` directory:
- `CPT Codes with Long Descriptions 2025.xlsx`

All database files will be automatically created on first run in the `data/` directory.

### 3. Run the Application

```bash
streamlit run app.py
```

### 4. Validate Installation (Optional)

```bash
python3 test_refactored_code.py
```

## 📂 Project Structure

```
CCV_Research_UI_Dev/
├── app.py                      # Main application entry point
├── llm_wrapper.py              # LLM integration wrapper
├── db.py                       # Database utilities (legacy)
├── feedback.py                 # Feedback system (legacy)
├── personas.py                 # Persona management (legacy)
├── requirements.txt            # Python dependencies
├── MIGRATION_GUIDE.md          # Detailed migration documentation
├── test_refactored_code.py     # Validation test script
│
├── data/                       # 📁 Data files directory
│   ├── *.db                    # SQLite databases (auto-created)
│   └── CPT Codes with Long Descriptions 2025.xlsx
│
├── output/                     # 📁 Generated reports directory
│   ├── *.pdf                   # PDF reports
│   └── *.xlsx                  # Excel reports
│
├── services/                   # ⚙️ Business Logic Layer
│   ├── __init__.py
│   ├── utils.py                       # Database operations & utilities
│   ├── cpt_service.py                 # CPT code generation
│   ├── code_description_service.py     # Section 1: Code Description
│   ├── guideline_examination_service.py # Section 2: Guideline Examination
│   ├── payment_rate_service.py         # Section 3: Payment Rate & Policy
│   ├── device_code_service.py          # Section 4: Device Code
│   ├── ncci_compliance_service.py      # Section 5: NCCI Compliance
│   ├── reference_material_service.py   # Section 6: Reference Material
│   ├── apc_orchestrator.py            # Workflow orchestration
│   └── report_service.py              # PDF/Excel report generation
│
└── views/                      # 🖥️ User Interface Layer
    ├── __init__.py
    ├── utils.py                       # Shared UI components
    ├── apc_main_view.py               # Main workflow interface
    ├── code_description_view.py       # Section 1 UI
    ├── guideline_examination_view.py  # Section 2 UI
    ├── payment_rate_view.py           # Section 3 UI
    ├── device_code_view.py            # Section 4 UI
    ├── ncci_compliance_view.py        # Section 5 UI
    ├── reference_material_view.py     # Section 6 UI
    └── final_assessment_view.py       # Final Assessment UI
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

**Version**: 2.0  
**Last Updated**: 2025.1.3  
**Architecture**: Modular Services/Views Pattern
