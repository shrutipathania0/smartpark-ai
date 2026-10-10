import streamlit as st
import json
import config
from modules import parking_assistant
from assets import ui_theme

st.set_page_config(page_title="AI Assistant — SmartPark AI", page_icon="🤖", layout="wide")

ui_theme.inject_custom_theme()

st.markdown("""
<div class="smart-banner" style="padding: 20px 28px;">
    <h1>🤖 SmartPark Conversational Assistant</h1>
    <p>Ask questions, search for optimal parking spaces, and manage reservations using natural language.</p>
</div>
""", unsafe_allow_html=True)

user_name = st.sidebar.text_input("Your Name", value="Shruti", help="Used when making automated reservations.")

st.sidebar.markdown("### 💡 Quick Prompts")
sample_prompts = [
    "Find parking near the entrance for an SUV under ₹60 per hour",
    "Show available EV charging spaces",
    "Which parking zone is least crowded?",
    "Reserve slot A04 for 45 minutes",
    "Cancel my reservation",
    "Why is the parking lot almost full?",
    "Summarize parking activity"
]

for sp in sample_prompts:
    if st.sidebar.button(sp, key=f"btn_{hash(sp)}"):
        st.session_state["assistant_prompt_input"] = sp

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": "Hello! I am **SmartPark AI**, your intelligent parking assistant. How can I help you find or reserve a parking space today?",
            "structured": None
        }
    ]

for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("structured"):
            with st.expander("🔍 View Extracted Intent & Structured JSON Data"):
                st.json(msg["structured"])

default_prompt = st.session_state.pop("assistant_prompt_input", None)
prompt = st.chat_input("Ask SmartPark AI (e.g. 'Find an SUV spot near entrance under ₹50')...")

if default_prompt:
    prompt = default_prompt

if prompt:
    st.session_state["chat_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Processing intent and querying live parking database..."):
            response = parking_assistant.process_chat_message(prompt, user_name=user_name)
            
        st.markdown(response["text_content"])
        
        with st.expander("🔍 View Extracted Intent & Structured JSON Data"):
            st.json(response["structured_data"])
            
        if response.get("llm_used"):
            st.caption("✨ Response polished using Groq LLM (Llama 3.3 70B)")
            
    st.session_state["chat_messages"].append({
        "role": "assistant",
        "content": response["text_content"],
        "structured": response["structured_data"]
    })
