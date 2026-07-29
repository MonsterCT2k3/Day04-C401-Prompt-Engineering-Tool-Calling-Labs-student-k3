from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from chat import run_model_tool_loop, write_transcript, trim_history, now_iso, safe_slug
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

# Root paths & env load
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

# Page configuration
st.set_page_config(
    page_title="AI Research Agent — Evidence-Driven Tool Calling",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Modern Styling (Glassmorphism + Dynamic Gradients)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Gradient Hero Header */
    .hero-title {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* Custom Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* Badge Tags */
    .badge-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-pass { background-color: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
    .badge-info { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
    .badge-warn { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }

    /* Tool Event Container */
    .tool-box {
        background: #0f172a;
        border-left: 4px solid #8b5cf6;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin: 0.5rem 0;
    }
    .tool-title {
        color: #a78bfa;
        font-weight: 700;
        font-size: 0.95rem;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<div class="hero-title">⚡ AI Research Agent — Tool Calling Studio</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Evidence-Driven Prompt Optimization • Dynamic Tool Execution & Real-Time Traces</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### 🎛️ Agent Control Panel")
    
    provider_name = st.selectbox(
        "🧠 Model Provider",
        options=["nvidia", "openrouter", "openai", "gemini", "anthropic"],
        index=0
    )
    
    version_label = st.selectbox(
        "🎯 Optimized Version",
        options=["v1", "v2", "v3", "v0"],
        index=0,
        help="v1 (Best baseline - 70% Acc), v2 (News cleaning), v3 (Integer limit enforcement), v0 (Baseline 30%)"
    )
    
    model_override = st.text_input("🤖 Model Identifier", value="", placeholder="meta/llama-3.1-70b-instruct")

    with st.expander("⚙️ Execution Tuning", expanded=False):
        history_window = st.slider("Context History Window (turns)", min_value=1, max_value=10, value=5)
        max_tool_rounds = st.slider("Max Tool Execution Rounds", min_value=1, max_value=8, value=4)
        show_raw_json = st.checkbox("Show Raw JSON in Tool Trace", value=True)

    # Calculate Version Signatures
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    
    art_version_obj = build_artifact_version(
        version=version_label,
        system_prompt_path=system_prompt_path,
        tools_path=tools_path
    )
    art_info = artifact_version_dict(art_version_obj)

    st.markdown("---")
    st.markdown("### 🏷️ Active Artifact Signatures")
    st.markdown(f'<span class="badge-status badge-pass">{art_info["artifact_version"]}</span>', unsafe_allow_html=True)
    st.caption(f"**Prompt Hash:** `{art_info['prompt_hash'][:12]}...`")
    st.caption(f"**Tools Hash:** `{art_info['tools_hash'][:12]}...`")

    st.markdown("---")
    if st.button("🔄 Clear Conversation Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript_history = []
        st.session_state.session_id = now_iso().replace(":", "-")
        st.rerun()

# Sample Prompts Showcase Bar
st.markdown("##### 🚀 Quick Demo Shortcuts (Click to Test):")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

selected_shortcut = None
if col_s1.button("🌤️ Thời tiết Hà Nội"):
    selected_shortcut = "Thời tiết Hà Nội hôm nay thế nào?"
if col_s2.button("📰 Tin tức AI Hôm Nay"):
    selected_shortcut = "Tin tức AI hôm nay có gì nổi bật trên web?"
if col_s3.button("🐤 Tweet của Sam Altman"):
    selected_shortcut = "Tweet mới nhất của Sam Altman là gì?"
if col_s4.button("🛡️ Telegram Boundary Test"):
    selected_shortcut = "Đăng bản tin thời tiết này lên Telegram giúp mình"

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript_history" not in st.session_state:
    st.session_state.transcript_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = now_iso().replace(":", "-")

# Render Conversation Timeline
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])
            
            # Interactive Collapsible & Toggleable Tool Trace Section
            tool_events = msg.get("tool_events", [])
            if tool_events:
                with st.expander(f"⚙️ **Interactive Tool Trace** ({len(tool_events)} tool call(s) executed)", expanded=False):
                    for idx, event in enumerate(tool_events, 1):
                        tool_name = event.get("tool", "unknown")
                        tool_args = event.get("args", {})
                        tool_result = event.get("result", {})
                        
                        st.markdown(
                            f'<div class="tool-box">'
                            f'<span class="tool-title">🔧 Call #{idx}: {tool_name}()</span>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                        
                        t_col1, t_col2 = st.columns(2)
                        with t_col1:
                            st.caption("📥 Tool Input Arguments")
                            st.json(tool_args, expanded=False)
                        with t_col2:
                            st.caption("📤 Tool Execution Result Output")
                            st.json(tool_result, expanded=False)
                        st.markdown("---")

# Handle User Input (from Chat Bar or Quick Shortcut Button)
user_prompt = st.chat_input("Nhập câu hỏi hoặc chọn phím tắt mẫu bên trên...")
if selected_shortcut:
    user_prompt = selected_shortcut

if user_prompt:
    # Append & Render User Message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    st.session_state.transcript_history.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # Process Assistant Response & Tool Calling Loop
    with st.chat_message("assistant", avatar="🤖"):
        status_placeholder = st.empty()
        status_placeholder.markdown('<span class="badge-status badge-info">🔄 Agent is reasoning and executing tools...</span>', unsafe_allow_html=True)
        
        try:
            # Load Provider & System Configuration
            provider = make_provider(provider_name)
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
            tool_declarations = load_tool_declarations(tools_path)
            openai_tools = to_openai_tools(tool_declarations)
            
            # Prepare trimmed message history
            history_subset = trim_history(st.session_state.transcript_history, history_window)
            full_messages = [{"role": "system", "content": system_prompt}] + history_subset

            # Run Autonomous Tool Execution Loop
            loop_result = run_model_tool_loop(
                provider=provider,
                messages=full_messages,
                tools=openai_tools,
                model=model_override or None,
                max_tool_rounds=max_tool_rounds
            )
            
            status_placeholder.empty()
            assistant_text = loop_result.get("assistant_text", "")
            tool_events = loop_result.get("tool_events", [])
            status = loop_result.get("status", "answered")

            # Render Main Text Response
            st.markdown(assistant_text)

            # Render Interactive Tool Execution Trace
            if tool_events:
                with st.expander(f"⚙️ **Interactive Tool Trace** ({len(tool_events)} tool call(s) executed)", expanded=False):
                    st.caption("Chi tiết quá trình suy luận và kết quả thực thi Tool của Agent:")
                    for idx, event in enumerate(tool_events, 1):
                        tool_name = event.get("tool", "unknown")
                        tool_args = event.get("args", {})
                        tool_result = event.get("result", {})

                        st.markdown(
                            f'<div class="tool-box">'
                            f'<span class="tool-title">🔧 Call #{idx}: {tool_name}()</span>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                        
                        t_col1, t_col2 = st.columns(2)
                        with t_col1:
                            st.caption("📥 Tool Input Arguments")
                            st.json(tool_args, expanded=False)
                        with t_col2:
                            st.caption("📤 Tool Execution Result Output")
                            st.json(tool_result, expanded=False)
                        st.markdown("---")

            # Update Session History & Save Transcript
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "tool_events": tool_events,
                "status": status
            })
            st.session_state.transcript_history.append({
                "role": "assistant",
                "content": assistant_text
            })

            transcript_data = {
                "session_id": st.session_state.session_id,
                "provider": provider_name,
                "version": version_label,
                "artifact_version": art_info["artifact_version"],
                "messages": st.session_state.transcript_history,
                "last_loop_result": loop_result
            }
            transcript_filename = f"{st.session_state.session_id}_{safe_slug(user_prompt[:20])}.transcript.json"
            write_transcript(TRANSCRIPTS_DIR / transcript_filename, transcript_data)

        except Exception as e:
            status_placeholder.empty()
            st.error(f"❌ Error during agent execution: {e}")
