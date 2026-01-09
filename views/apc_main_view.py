"""
APC Main View - Primary Interface

This module handles the main APC research workflow including:
- Step 1: Topic input and CPT code generation
- Step 1.5: CPT code selection
- Step 2: Research parameter configuration
- Step 3: Results display with tabs
- Sidebar: Session management and notes
"""

import streamlit as st
from datetime import datetime
from services.cpt_service import get_cpt_codes_for_topic
from services.apc_orchestrator import (
    conduct_comprehensive_research, 
    parse_structured_research,
    conduct_all_sections_research,
    SECTION_SERVICES
)
from services.utils import (
    init_all_databases,
    get_all_research_sessions,
    get_research_session,
    save_research_session,
    delete_research_session,
    update_research_topic,
    get_notes,
    save_notes
)
from .utils import apply_custom_css, format_text_with_source, render_source_legend
from . import (
    code_description_view,
    guideline_examination_view,
    payment_rate_view,
    device_code_view,
    ncci_compliance_view,
    reference_material_view,
    final_assessment_view
)


# Map section numbers to view modules
SECTION_VIEWS = {
    1: code_description_view,
    2: guideline_examination_view,
    3: payment_rate_view,
    4: device_code_view,
    5: ncci_compliance_view,
    6: reference_material_view
}


def convert_agentic_result_to_section_data(section_num, agentic_section_result, metadata):
    """
    Convert agentic research result to section_data format for view rendering
    
    Args:
        section_num: Section number (1-6)
        agentic_section_result: Result from conduct_section_research() or conduct_all_sections_research()
        metadata: Section metadata from get_section_metadata()
        
    Returns:
        Dictionary in format expected by view's render_section()
    """
    # Section 1 returns structured dict - pass it directly to view
    if section_num == 1 and isinstance(agentic_section_result, dict):
        return {
            'num': str(section_num),
            'name': metadata['title'],
            'title': f"SECTION {section_num} - {metadata['title']}",
            'data': agentic_section_result  # Structured data for new format
        }
    
    # Other sections return string - use legacy format
    else:
        content = agentic_section_result if isinstance(agentic_section_result, str) else str(agentic_section_result)
        return {
            'num': str(section_num),
            'name': metadata['title'],
            'title': f"SECTION {section_num} - {metadata['title']}",
            'content': content  # String content for legacy format
        }


def initialize_session_state():
    """Initialize all session state variables"""
    if "apc_step" not in st.session_state:
        st.session_state.apc_step = 1
    if "generated_cpts" not in st.session_state:
        st.session_state.generated_cpts = []
    if "selected_cpt" not in st.session_state:
        st.session_state.selected_cpt = None
    if "topic_description" not in st.session_state:
        st.session_state.topic_description = ""
    if "show_notes" not in st.session_state:
        st.session_state.show_notes = False
    if "section_chat_history" not in st.session_state:
        st.session_state.section_chat_history = {}
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "current_research_session_id" not in st.session_state:
        st.session_state.current_research_session_id = None
    if "editing_topic" not in st.session_state:
        st.session_state.editing_topic = {}


def render_sidebar():
    """Render sidebar with session management and notes"""
    with st.sidebar:
        st.markdown("### 🔬 Research Sessions")
        
        # New Research button
        if st.button("➕ New Research", use_container_width=True, key="new_research_btn"):
            st.session_state.apc_step = 1
            st.session_state.generated_cpts = []
            st.session_state.selected_cpt = None
            st.session_state.topic_description = ""
            st.session_state.section_chat_history = {}
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.current_research_session_id = None
            st.rerun()
        
        st.markdown("---")
        
        # Display previous research sessions
        sessions = get_all_research_sessions()
        
        if sessions:
            st.markdown("**Previous Research:**")
            for session_id, topic, cpt_code, created_at, updated_at in sessions:
                with st.container():
                    col1, col2, col3 = st.columns([6, 1, 1])
                    
                    with col1:
                        if st.session_state.editing_topic.get(session_id, False):
                            new_topic = st.text_input(
                                "Topic",
                                value=topic,
                                key=f"topic_input_{session_id}",
                                label_visibility="collapsed"
                            )
                        else:
                            display_text = f"{topic} - CPT {cpt_code}"
                            if st.button(display_text, key=f"load_{session_id}", use_container_width=True):
                                loaded_session = get_research_session(session_id)
                                if loaded_session:
                                    st.session_state.current_research_session_id = session_id
                                    st.session_state.session_id = session_id
                                    st.session_state.topic_description = loaded_session["topic"]
                                    st.session_state.selected_cpt = loaded_session["cpt_code"]
                                    st.session_state.apc_step = 3
                                    
                                    st.session_state.apc_analysis = {
                                        "cpt_code": loaded_session["cpt_code"],
                                        "context": "",
                                        "model": loaded_session["model"],
                                        "result": loaded_session["result"],
                                        "timestamp": loaded_session["updated_at"],
                                        "topic": loaded_session["topic"]
                                    }
                                    
                                    st.session_state.section_chat_history = {}
                                    st.rerun()
                    
                    with col2:
                        if st.session_state.editing_topic.get(session_id, False):
                            if st.button("💾", key=f"save_edit_{session_id}"):
                                new_topic = st.session_state.get(f"topic_input_{session_id}", topic)
                                if new_topic and new_topic != topic:
                                    update_research_topic(session_id, new_topic)
                                st.session_state.editing_topic[session_id] = False
                                st.rerun()
                        else:
                            if st.button("✏️", key=f"edit_{session_id}"):
                                st.session_state.editing_topic[session_id] = True
                                st.rerun()
                    
                    with col3:
                        if st.button("🗑️", key=f"delete_{session_id}"):
                            delete_research_session(session_id)
                            if st.session_state.current_research_session_id == session_id:
                                st.session_state.apc_step = 1
                                st.session_state.current_research_session_id = None
                            st.rerun()
                    
                    st.markdown("---")
        
        st.markdown("---")
        
        # Notes Section
        st.markdown("### 📝 Research Notes")
        
        if st.button("✏️ Open Notes", use_container_width=True):
            st.session_state.show_notes = not st.session_state.show_notes
        
        if st.session_state.show_notes:
            current_cpt = st.session_state.selected_cpt if st.session_state.selected_cpt else "general"
            session_id = st.session_state.get("session_id", "default")
            
            existing_notes = get_notes(session_id, current_cpt)
            
            st.markdown(f"**Notes for:** {current_cpt}")
            
            notes_text = st.text_area(
                "Your Notes",
                value=existing_notes,
                height=300,
                placeholder="Add your research notes here...",
                help="These notes will be saved for this CPT code",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Notes", use_container_width=True):
                    save_notes(session_id, current_cpt, notes_text)
                    st.success("✅ Notes saved!")
            with col2:
                if st.button("❌ Close", use_container_width=True):
                    st.session_state.show_notes = False
                    st.rerun()


def render_step1():
    """Step 1: Topic Input and CPT Code Generation"""
    
    # Header row with title and generate button side by side
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📋 Step 1: Enter Topic and Generate CPT Codes")
    
    # Input fields
    topic_input = st.text_input(
        "Medical Procedure or Condition Topic",
        placeholder="e.g., Bronchial Biopsy, Knee Replacement, Cardiac Catheterization",
        help="Enter a medical procedure or condition to find relevant CPT codes",
        key="topic_input_field"
    )
    
    model_for_generation = st.selectbox(
        "Model for CPT Generation",
        ["gpt-4.1", "gpt-4.1-mini", "gpt-5", "gpt-5-mini"],
        index=1,
        help="Select the AI model for generating CPT codes",
        key="model_select_field"
    )
    
    # Generate button in the header column
    with col2:
        st.write("")  # Add spacing to align with subheader
        generate_btn = st.button("🔍 Generate CPT Codes", use_container_width=True, key="generate_cpt_btn")
    
    if generate_btn and topic_input:
        with st.spinner("Generating relevant CPT codes..."):
            parsed_codes = get_cpt_codes_for_topic(topic_input, model=model_for_generation)
            
            if parsed_codes:
                st.session_state.generated_cpts = parsed_codes
                st.session_state.topic_description = topic_input
                st.session_state.apc_step = 1.5
                st.rerun()
            else:
                st.error("⚠️ No relevant CPT codes found. Please try a different topic or be more specific.")
    
    elif generate_btn and not topic_input:
        st.error("⚠️ Please enter a medical topic to generate CPT codes.")


def render_step1_5():
    """Step 1.5: Display Generated CPT Codes for Selection"""
    st.subheader("📋 Step 1: Select a CPT Code")
    st.info(f"Topic: **{st.session_state.topic_description}**")
    
    # Show source legend
    render_source_legend()
    
    st.markdown("### Generated CPT Codes")
    st.markdown("Click on a CPT code to proceed with research:")
    
    for idx, cpt_info in enumerate(st.session_state.generated_cpts):
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(cpt_info['code'], key=f"cpt_btn_{idx}", use_container_width=True):
                st.session_state.selected_cpt = cpt_info['code']
                st.session_state.apc_step = 2
                st.rerun()
        with col2:
            # Get source and format description with appropriate color
            source = cpt_info.get('source', 'llm')  # Default to 'llm' if no source specified
            formatted_desc = format_text_with_source(cpt_info['description'], source)
            st.markdown(f"<div style='padding: 10px 20px; font-size: 1rem;'>{formatted_desc}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("← Back to Topic Input"):
        st.session_state.apc_step = 1
        st.session_state.generated_cpts = []
        st.rerun()


def render_step2():
    """Step 2: Research Parameters and Analysis"""
    st.subheader("📋 Step 2: Conduct APC Research")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**Selected CPT Code:** {st.session_state.selected_cpt}")
    with col_info2:
        st.info(f"**Topic:** {st.session_state.topic_description}")
    
    with st.form("apc_research_form"):
        default_context = f"Related to {st.session_state.topic_description}"
        
        additional_context = st.text_area(
            "Additional Context",
            value=default_context,
            placeholder="Provide any specific details: surrounding codes, known issues, claim examples, etc.",
            height=100,
            help="Context has been pre-filled with your topic. You can modify or add more details."
        )
        
        selected_model = st.selectbox(
            "Analysis Model",
            ["gpt-4.1", "gpt-4.1-mini", "gpt-5", "gpt-5-mini"],
            help="Select the AI model for comprehensive analysis"
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            back_btn = st.form_submit_button("← Back")
        with col_btn2:
            submit_btn = st.form_submit_button("🔍 Start Research", use_container_width=True)
    
    if back_btn:
        st.session_state.apc_step = 1.5
        st.rerun()
    
    if submit_btn:
        # Initialize empty results structure - sections will be loaded/run individually in their tabs
        st.session_state.apc_analysis = {
            "cpt_code": st.session_state.selected_cpt,
            "context": additional_context,
            "model": selected_model,
            "result": {
                "sections": {
                    f"section_{i}": {"status": "pending", "data": None}
                    for i in range(1, 7)
                }
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": st.session_state.topic_description
        }
        
        st.session_state.apc_step = 3
        st.rerun()


def render_step3():
    """Step 3: Display Results with Tabs"""
    if "apc_analysis" not in st.session_state:
        st.error("No analysis data found. Please start a new research.")
        return
    
    analysis_data = st.session_state.apc_analysis
    
    # Display Topic and CPT Code at the top
    st.markdown(f"### 📋 {analysis_data.get('topic', 'Research Topic')} - CPT {analysis_data['cpt_code']}")
    st.markdown("---")
    
    # Apply custom CSS
    apply_custom_css()
    
    # Get section metadata for tab labels
    section_tabs = []
    for i in range(1, 7):
        metadata = SECTION_SERVICES[i].get_section_metadata()
        section_tabs.append(f"Section {i}: {metadata['title']}")
    section_tabs.append("Final Assessment")
    
    # Create tabs
    tabs = st.tabs(section_tabs)
    
    # Render each section in its tab - let each view handle its own data loading/display
    for i in range(1, 7):
        with tabs[i-1]:
            view_module = SECTION_VIEWS.get(i)
            if view_module:
                view_module.render_section(
                    cpt_code=analysis_data['cpt_code'],
                    model=analysis_data.get('model', 'gpt-4.1-mini'),
                    session_id=st.session_state.session_id,
                    idx=i-1
                )
    
    # Render Final Assessment
    with tabs[-1]:
        final_assessment_view.render_section(
            cpt_code=analysis_data['cpt_code'],
            session_id=st.session_state.session_id
        )
    
    # Display section accuracy summary if any sections were rated
    if "section_accuracy" in st.session_state and st.session_state.section_accuracy:
        st.markdown("---")
        st.subheader("📊 Section Accuracy Summary")
        
        summary_cols = st.columns(6)
        for idx, (section_num, rating) in enumerate(st.session_state.section_accuracy.items()):
            with summary_cols[idx % 6]:
                st.metric(f"Section {section_num}", rating)
    
    # Option to start new research
    st.markdown("---")
    if st.button("🔄 Start New Research"):
        st.session_state.apc_step = 1
        st.session_state.generated_cpts = []
        st.session_state.selected_cpt = None
        st.session_state.topic_description = ""
        if "apc_analysis" in st.session_state:
            del st.session_state.apc_analysis
        st.rerun()


def render_apc_interface():
    """Main function to render the complete APC Research interface"""
    st.title("🏥 APC Target Code Research")
    st.markdown("---")
    
    # Apply custom CSS for inputs and buttons
    st.markdown("""
        <style>
            .stSidebar .stTextArea textarea {
                background-color: #2c2c2c !important;
                color: #ffffff !important;
                border: 1px solid #555 !important;
                border-radius: 6px !important;
                font-size: 0.9rem !important;
                line-height: 1.5 !important;
            }
            .stSidebar .stTextArea label {
                color: #ffffff !important;
            }
            
            /* Light colored buttons */
            .stButton > button,
            .stDownloadButton > button,
            .stFormSubmitButton > button,
            .stSidebar .stButton > button,
            button[kind="primary"],
            button[kind="secondary"] {
                background-color: #ffffff !important;
                color: #1f1f1f !important;
                border: 1px solid #e8e8e8 !important;
            }
            
            .stButton > button:hover,
            .stDownloadButton > button:hover,
            .stFormSubmitButton > button:hover,
            .stSidebar .stButton > button:hover,
            button[kind="primary"]:hover,
            button[kind="secondary"]:hover {
                background-color: #f7f7f8 !important;
                color: #1f1f1f !important;
                border: 1px solid #d0d0d0 !important;
            }
            
            .stAlert {
                margin-top: 0.25rem !important;
                margin-bottom: 0.25rem !important;
                padding: 0.5rem 1rem !important;
            }
            
            hr {
                margin-top: 0.25rem !important;
                margin-bottom: 0.25rem !important;
            }
            
            h3 {
                margin-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
                color: #1f1f1f !important;
            }
            
            .main .stTextInput input,
            .main .stTextArea textarea,
            .main .stSelectbox select,
            .main .stSelectbox div[data-baseweb="select"] > div,
            div[data-testid="stTextInput"] input,
            div[data-testid="stTextArea"] textarea,
            div[data-testid="stSelectbox"] select,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
            div[data-baseweb="select"] > div {
                background-color: #f7f7f8 !important;
                color: #1f1f1f !important;
                border: 1px solid #d0d0d0 !important;
                border-radius: 6px !important;
            }
            
            .main .stTextInput input:focus,
            .main .stTextArea textarea:focus,
            .main .stSelectbox select:focus {
                border: 2px solid #1f1f1f !important;
                background-color: #ffffff !important;
            }
            
            .stForm label {
                color: #1f1f1f !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize databases
    init_all_databases()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render appropriate step based on workflow state
    if st.session_state.apc_step == 1:
        render_step1()
    elif st.session_state.apc_step == 1.5:
        render_step1_5()
    elif st.session_state.apc_step == 2:
        render_step2()
    elif st.session_state.apc_step == 3:
        render_step3()
