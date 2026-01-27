import streamlit as st
import uuid
import os
import base64
from PIL import Image
from llm_wrapper import query_llm
from db import init_db, save_interaction, get_sessions, get_session_history, rename_session, delete_session, create_session
from views.apc_main_view import render_apc_interface
from feedback import init_feedback_db, render_feedback_page


# Initialize DBs
init_db()
init_feedback_db()

# Page config
st.set_page_config(page_title="CCV Research AI", layout="wide")

# Load Inter font and apply light theme styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* ===============================
           Base layout & typography
           =============================== */
        html, body, .stApp {
            background-color: #ffffff !important;
            color: #1f1f1f !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Hide Streamlit header elements */
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* Remove all top spacing */
        .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        .main {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        .stApp {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Main page logo styling */
        .main-logo-container {
            text-align: center;
            padding: 0 0 0.5rem 0;
            margin: 0 0 1rem 0;
            border-bottom: 1px solid #e0e0e0;
        }

        /* ===============================
           Text Colors - ALL BLACK
           =============================== */
        h1, h2, h3, h4, h5, h6 {
            color: #1f1f1f !important;
        }
        
        /* Force all markdown headings to be black */
        .main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4 {
            color: #1f1f1f !important;
        }

        /* Exception: Allow source-colored text to keep its color */
        .source-colored-text,
        .source-legend-item,
        .source-legend-container,
        [id*="src-"],
        [id*="legend-"] {
            /* Colors set via inline styles or embedded <style> - don't override */
        }

        p, span:not(.source-colored-text):not([id*="src-"]):not([id*="legend-"]), 
        div:not(.source-colored-text):not(.source-legend-container):not([id*="src-"]):not([id*="legend-"]), 
        label, a {
            color: #1f1f1f !important;
        }

        /* Streamlit specific text elements - except source-colored content */
        .stMarkdown, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown p, 
        .stMarkdown span:not(.source-colored-text):not([id*="src-"]):not([id*="legend-"]),
        .stMarkdown div:not(.source-colored-text):not(.source-legend-container):not([id*="src-"]):not([id*="legend-"]) {
            color: #1f1f1f !important;
        }

        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span:not(.source-colored-text):not([id*="src-"]):not([id*="legend-"]),
        [data-testid="stMarkdownContainer"] div:not(.source-colored-text):not(.source-legend-container):not([id*="src-"]):not([id*="legend-"]) {
            color: #1f1f1f !important;
        }

        /* ===============================
           Buttons - WHITE background, BLACK text
           =============================== */
        button,
        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        [data-testid="baseButton-primary"],
        [data-testid="baseButton-secondary"] {
            background-color: #ffffff !important;
            background: #ffffff !important;
            background-image: none !important;
            color: #1f1f1f !important;
            border: 1px solid #e8e8e8 !important;
            box-shadow: none !important;
        }

        /* Button hover */
        button:hover,
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="baseButton-secondary"]:hover {
            background-color: #f7f7f8 !important;
            background: #f7f7f8 !important;
            color: #1f1f1f !important;
            border: 1px solid #d0d0d0 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }

        /* Button text - force BLACK */
        button *, 
        .stButton > button *,
        .stDownloadButton > button *,
        .stFormSubmitButton > button *,
        button[kind="primary"] *,
        button[kind="secondary"] *,
        [data-testid="baseButton-primary"] *,
        [data-testid="baseButton-secondary"] * {
            color: #1f1f1f !important;
        }

        /* ===============================
           Remove button container borders
           =============================== */
        .stButton,
        .stDownloadButton,
        .stFormSubmitButton,
        div[data-testid="stButton"],
        div[data-testid="stDownloadButton"],
        div[data-testid="stFormSubmitButton"],
        .stButton > div,
        .stDownloadButton > div,
        .stFormSubmitButton > div {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        /* Remove ALL focus borders on forms and containers */
        .stForm,
        div[data-testid="stForm"],
        div[data-testid="stForm"]:focus,
        div[data-testid="stForm"]:focus-within,
        div[data-testid="stForm"]:hover,
        .element-container,
        .element-container:focus,
        .element-container:focus-within,
        .element-container:hover,
        div[data-testid="column"],
        div[data-testid="column"]:focus,
        div[data-testid="column"]:focus-within,
        div[data-testid="column"]:hover,
        [data-baseweb="card"],
        [data-baseweb="card"]:focus,
        [data-baseweb="card"]:focus-within,
        [data-baseweb="card"]:hover,
        .row-widget,
        .row-widget:focus,
        .row-widget:focus-within,
        .row-widget:hover {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
        }

        /* Remove focus-visible outline on all elements */
        *:focus,
        *:focus-within,
        *:focus-visible {
            outline: none !important;
            box-shadow: none !important;
            border-color: transparent !important;
        }

        /* Force remove any default Streamlit container styling */
        [class*="st-"] {
            border: none !important;
        }

        /* Specifically target form containers */
        form,
        form > div,
        form div {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        /* ===============================
           Sidebar styling
           =============================== */
        .stSidebar {
            background-color: #f7f7f8 !important;
            color: #1f1f1f !important;
        }

        .stSidebar h1, .stSidebar h2, .stSidebar h3, 
        .stSidebar p, .stSidebar span, .stSidebar label {
            color: #1f1f1f !important;
        }

        .stSidebar .stSelectbox div,
        .stSidebar .stTextInput input {
            background-color: #ffffff !important;
            color: #1f1f1f !important;
            border: 1px solid #d0d0d0 !important;
        }

        /* Radio buttons */
        .stRadio > label,
        .stRadio div[role="radiogroup"] label,
        .stRadio div[role="radiogroup"] label p {
            color: #1f1f1f !important;
        }

        /* ===============================
           Chat bubbles
           =============================== */
        .chat-bubble {
            padding: 1rem;
            border-radius: 1rem;
            margin: 0.5rem 0;
            max-width: 80%;
            font-size: 1rem;
        }

        .user-bubble {
            background-color: #10a37f;
            color: white;
            margin-left: auto;
            text-align: left;
        }

        .assistant-bubble {
            background-color: #f7f7f8;
            color: #1f1f1f;
            margin-right: auto;
            text-align: left;
            border: 1px solid #e0e0e0;
        }

        /* ===============================
           Other form elements
           =============================== */
        .stTextInput>div>input {
            padding: 0.75rem 1rem !important;
            border-radius: 1rem !important;
            font-size: 1rem !important;
            background-color: #f7f7f8 !important;
            color: #1f1f1f !important;
            border: 1px solid #d0d0d0 !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] button,
        .stTabs [data-baseweb="tab-list"] button * {
            color: #1f1f1f !important;
        }

        /* Selectbox */
        .stSelectbox label, .stSelectbox * {
            color: #1f1f1f !important;
        }

        /* Checkbox */
        .stCheckbox label, .stCheckbox * {
            color: #1f1f1f !important;
        }

        /* Tables */
        .stDataFrame, .stDataFrame *, .stTable, .stTable * {
            color: #1f1f1f !important;
        }

        /* Expanders */
        .streamlit-expanderHeader, .streamlit-expanderHeader * {
            color: #1f1f1f !important;
        }

        /* Alerts */
        .stAlert, .stAlert * {
            color: #1f1f1f !important;
        }
    </style>
""", unsafe_allow_html=True)


# Session setup
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.topic = "New Research"
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a helpful assistant with the persona of a CCV Researcher."
    }]

if "persona" not in st.session_state:
    st.session_state.persona = "Analysts"

if "model" not in st.session_state:
    st.session_state.model = "gpt-4.1-mini"

if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "APC"

if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

# Sidebar: Logo + Navigation + Research topics + model + persona selector
with st.sidebar:
    st.markdown("<div style='text-align: center; padding-bottom: 10px;'>", unsafe_allow_html=True)
    try:
        # Get absolute path to logo.png
        import pathlib
        logo_path = pathlib.Path(__file__).parent / "logo.png"
        if logo_path.exists():
            logo = Image.open(str(logo_path))
            st.image(logo, width=240)
        else:
            st.warning(f"Logo not found at: {logo_path}")
    except Exception as e:
        st.warning(f"Logo image failed to load: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Navigation
    st.markdown("### 🧭 Navigation")
    
    # Add custom CSS for radio button labels
    st.markdown("""
        <style>
            .stRadio > label {
                color: #1f1f1f !important;
            }
            .stRadio div[role="radiogroup"] label {
                color: #1f1f1f !important;
            }
            .stRadio div[role="radiogroup"] label p {
                color: #1f1f1f !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Determine the index for the radio button based on current mode
    if st.session_state.show_feedback:
        # When showing feedback, keep the previous selection highlighted
        current_index = 0 if st.session_state.app_mode == "Chat" else 1
    else:
        current_index = 0 if st.session_state.app_mode == "Chat" else 1
    
    app_mode = st.radio(
        "Select Mode",
        ["💬 Chat Research", "🏥 APC Research"],
        index=current_index,
        label_visibility="collapsed"
    )
    
    # Only update mode and close feedback if user actually changed the selection
    new_mode = "Chat" if app_mode == "💬 Chat Research" else "APC"
    if new_mode != st.session_state.app_mode:
        st.session_state.app_mode = new_mode
        st.session_state.show_feedback = False  # Close feedback when switching modes
        st.rerun()
    
    st.markdown("---")
    
    # Feedback button at the bottom of sidebar
    st.markdown("### 💭 Feedback")
    if st.button("📝 Give Feedback", use_container_width=True):
        st.session_state.show_feedback = True
        st.rerun()
    
    st.markdown("---")

    # Only show chat-specific sidebar content if in Chat mode
    if st.session_state.app_mode == "Chat":
        st.title("📚 Research Topics")
        # Button to add a new session
        if st.button("➕ New Research Session", key="add_new_session"):
            new_session_id = str(uuid.uuid4())
            new_topic = "New Research"
            create_session(new_session_id, new_topic, persona=st.session_state.get("persona", "Analysts"))
            st.session_state.session_id = new_session_id
            st.session_state.topic = new_topic
            st.session_state.messages = [{
                "role": "system",
                "content": "You are a helpful assistant with the persona of a CCV Researcher."
            }]
            st.rerun()

        sessions = get_sessions()

        for sid, topic in sessions:
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            if col1.button(topic, key=f"load_{sid}"):
                st.session_state.session_id = sid
                st.session_state.topic = topic
                st.session_state.messages = get_session_history(sid)

            if col2.button("✏️", key=f"rename_{sid}"):
                st.session_state.rename_target = sid
                st.session_state.rename_value = topic

            if col3.button("🗑️", key=f"delete_{sid}"):
                delete_session(sid)
                # If the deleted session is the current one, reset to a new session
                if st.session_state.session_id == sid:
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.topic = "New Research"
                    st.session_state.messages = [{
                        "role": "system",
                        "content": "You are a helpful assistant with the persona of a CCV Researcher."
                    }]
                st.rerun()

        if "rename_target" in st.session_state:
            with st.form(key="rename_form"):
                new_name = st.text_input("Rename topic to:", value=st.session_state.rename_value)
                submitted = st.form_submit_button("Save")
                if submitted:
                    rename_session(st.session_state.rename_target, new_name)
                    if st.session_state.session_id == st.session_state.rename_target:
                        st.session_state.topic = new_name
                    del st.session_state.rename_target
                    del st.session_state.rename_value
                    st.rerun()

        st.markdown("---")
        # Add gpt-5 models to the dropdown
        model_options = [
            "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.1",
            "gpt-5", "gpt-5-mini", "gpt-5-nano",
            "medgemma-27b-multimodal7"
        ]
        if st.session_state.model not in model_options:
            model_options.append(st.session_state.model)
        st.session_state.model = st.selectbox(
            "🧠 Model",
            model_options,
            index=model_options.index(st.session_state.model),
            help="Select the LLM model."
        )

        st.markdown("---")
        st.session_state.persona = st.selectbox("👤 User Persona", [
            "Analysts", "CDAs", "SMEs", "Product Owners", "Data Analysts",
            "Clinical Reviewers", "Audit Leads", "IT/Engineers"
        ], index=[
            "Analysts", "CDAs", "SMEs", "Product Owners", "Data Analysts",
            "Clinical Reviewers", "Audit Leads", "IT/Engineers"
        ].index(st.session_state.persona))

# Main content area - Add large logo at the top using pure HTML
try:
    # Get absolute path to logo.png
    import pathlib
    logo_path = pathlib.Path(__file__).parent / "logo.png"
    if logo_path.exists():
        with open(str(logo_path), "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div class="main-logo-container">
                <img src="data:image/png;base64,{logo_base64}" style="max-width: 500px; width: 50%; height: auto; display: block; margin: 0 auto;">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-logo-container"><div style="color: #e0e0e0; font-size: 2rem; font-weight: 600; text-align: center;">🧠 CCV Research AI</div></div>', unsafe_allow_html=True)
except Exception as e:
    st.markdown(f'<div class="main-logo-container"><div style="color: #e0e0e0; font-size: 2rem; font-weight: 600; text-align: center;">🧠 CCV Research AI</div><div style="color: #999; font-size: 0.8rem; text-align: center;">Logo error: {e}</div></div>', unsafe_allow_html=True)

# Main content area - switch between Chat, APC, and Feedback modes
if st.session_state.show_feedback:
    render_feedback_page()
elif st.session_state.app_mode == "APC":
    render_apc_interface()
else:
    # Topic display
    st.subheader(f"💬 Topic: {st.session_state.topic}")

    # Display chat history
    for msg in st.session_state.messages[1:]:  # Skip system prompt
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f'<div class="chat-bubble assistant-bubble">{msg["content"]}</div>', unsafe_allow_html=True)

    # Show pending user input and "Researching..." message
    if st.session_state.pending_user_input:
        st.markdown(f'<div class="chat-bubble user-bubble">{st.session_state.pending_user_input}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble assistant-bubble">Researching...</div>', unsafe_allow_html=True)

    # Input field at bottom (Enter to submit)
    st.markdown('<div class="bottom-input">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Type a message", key="temp_input", label_visibility="collapsed", placeholder="Type a message...")
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            st.session_state.pending_user_input = user_input
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # If pending input exists, process it
    if st.session_state.pending_user_input:
        st.session_state.messages.append({"role": "user", "content": st.session_state.pending_user_input})
        response = query_llm(st.session_state.messages, model=st.session_state.model)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_interaction(st.session_state.session_id, st.session_state.topic, st.session_state.persona, st.session_state.pending_user_input, response)
        st.session_state.pending_user_input = None
        st.rerun()
