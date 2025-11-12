import streamlit as st
import uuid
from PIL import Image
from llm_wrapper import query_llm
from db import init_db, save_interaction, get_sessions, get_session_history, rename_session, delete_session, create_session
import apc_research
from feedback import init_feedback_db, render_feedback_page

# Initialize DBs
init_db()
init_feedback_db()

# Page config
st.set_page_config(page_title="CCV Research AI", layout="wide")

# Load Inter font and apply dark theme styling
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body, .stApp {
            background-color: #1e1e1e !important;
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
        }

        [data-testid="stHeader"] {
            background-color: #1e1e1e !important;
            border-bottom: 1px solid #333 !important;
        }

        [data-testid="stHeader"]::before {
            content: "🧠 CCV Research AI";
            font-size: 1.2rem;
            font-weight: 600;
            color: #e0e0e0;
            position: absolute;
            left: 1rem;
            top: 0.75rem;
        }

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
            background-color: #343541;
            color: white;
            margin-right: auto;
            text-align: left;
        }

        .bottom-input {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: #1e1e1e;
            padding: 1rem 2rem;
            box-shadow: 0 -1px 3px rgba(0,0,0,0.3);
            z-index: 999;
        }

        .stTextInput>div>input {
            padding: 0.75rem 1rem !important;
            border-radius: 1rem !important;
            font-size: 1rem !important;
            background-color: #2c2c2c !important;
            color: white !important;
            border: 1px solid #555 !important;
        }

        .stSidebar {
            background-color: #121212 !important;
            color: #e0e0e0 !important;
        }

        .stSidebar .stButton button,
        .stSidebar .stSelectbox div,
        .stSidebar .stTextInput input {
            background-color: #d3d3d3 !important;
            color: black !important;
            border: 1px solid #aaa !important;
        }
        
        /* Feedback button styling */
        .stSidebar button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
        }
        .stSidebar button[kind="secondary"]:hover {
            background-color: #f0f0f0 !important;
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
    st.session_state.app_mode = "Chat"

if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

# Sidebar: Logo + Navigation + Research topics + model + persona selector
with st.sidebar:
    st.markdown("<div style='text-align: center; padding-bottom: 10px;'>", unsafe_allow_html=True)
    try:
        logo = Image.open("logo.png")
        st.image(logo, width=180)
    except Exception as e:
        st.warning("Logo image not found or failed to load.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Navigation
    st.markdown("### 🧭 Navigation")
    
    # Add custom CSS for radio button labels
    st.markdown("""
        <style>
            .stRadio > label {
                color: #ffffff !important;
            }
            .stRadio div[role="radiogroup"] label {
                color: #ffffff !important;
            }
            .stRadio div[role="radiogroup"] label p {
                color: #ffffff !important;
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

# Main content area - switch between Chat, APC, and Feedback modes
if st.session_state.show_feedback:
    render_feedback_page()
elif st.session_state.app_mode == "APC":
    apc_research.render_apc_interface()
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
