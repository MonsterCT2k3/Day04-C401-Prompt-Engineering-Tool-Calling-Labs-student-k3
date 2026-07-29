from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from chat import run_model_tool_loop, write_transcript, trim_history, now_iso, safe_slug
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

# Root paths
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent - Tool Calling Demo",
    page_icon="🤖",
    layout="wide"
)

# Page header
st.title("🤖 Research Agent UI — Evidence-Driven Tool Calling")
st.caption("Day 04 Lab — Interactive Agent with Full Live Tool Traces & Versioning")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Agent Settings")
    provider_name = st.selectbox(
        "Provider",
        options=["nvidia", "openrouter", "openai", "gemini", "anthropic"],
        index=0
    )
    version_label = st.selectbox(
        "Artifact Version",
        options=["v1", "v2", "v3", "v0"],
        index=0
    )
    model_override = st.text_input("Model Override (Optional)", value="")

    history_window = st.slider("History Window (turns)", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=8, value=4)

    # Build artifact version info
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    
    art_version_obj = build_artifact_version(
        version=version_label,
        system_prompt_path=system_prompt_path,
        tools_path=tools_path
    )
    art_info = artifact_version_dict(art_version_obj)
    
    st.divider()
    st.markdown("### 📌 Active Version Info")
    st.info(f"**Version:** `{art_info['artifact_version']}`")
    st.text(f"Prompt Hash: {art_info['prompt_hash'][:12]}...")
    st.text(f"Tools Hash:  {art_info['tools_hash'][:12]}...")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.transcript_history = []
        st.session_state.session_id = now_iso().replace(":", "-")
        st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript_history" not in st.session_state:
    st.session_state.transcript_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = now_iso().replace(":", "-")

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Tool Trace if available
        if "tool_events" in msg and msg["tool_events"]:
            with st.expander(f"🔍 Tool Trace ({len(msg['tool_events'])} tool call(s))", expanded=False):
                for idx, event in enumerate(msg["tool_events"], 1):
                    tool_name = event.get("tool", "unknown")
                    tool_args = event.get("args", {})
                    tool_result = event.get("result", {})
                    
                    st.markdown(f"**Call {idx}: `{tool_name}`**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption("Arguments")
                        st.code(json.dumps(tool_args, ensure_ascii=False, indent=2), language="json")
                    with col2:
                        st.caption("Result Output")
                        st.code(json.dumps(tool_result, ensure_ascii=False, indent=2), language="json")
                    st.divider()

# Chat input
user_input = st.chat_input("Hỏi gì đó (ví dụ: Thời tiết Hà Nội hôm nay thế nào?, Tin AI nổi bật hôm nay...)")

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.transcript_history.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process with Agent
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent đang suy nghĩ và thực thi tools..."):
            try:
                # Load configurations
                provider = make_provider(provider_name)
                system_prompt = system_prompt_path.read_text(encoding="utf-8")
                tool_declarations = load_tool_declarations(tools_path)
                openai_tools = to_openai_tools(tool_declarations)
                
                # Prepare messages payload
                history_subset = trim_history(st.session_state.transcript_history, history_window)
                full_messages = [{"role": "system", "content": system_prompt}] + history_subset

                # Run model tool loop
                loop_result = run_model_tool_loop(
                    provider=provider,
                    messages=full_messages,
                    tools=openai_tools,
                    model=model_override or None,
                    max_tool_rounds=max_tool_rounds
                )
                
                assistant_text = loop_result.get("assistant_text", "")
                tool_events = loop_result.get("tool_events", [])
                status = loop_result.get("status", "answered")

                # Display response
                st.markdown(assistant_text)

                # Display expandable Tool Trace
                if tool_events:
                    with st.expander(f"🔍 Tool Trace ({len(tool_events)} tool call(s))", expanded=True):
                        for idx, event in enumerate(tool_events, 1):
                            tool_name = event.get("tool", "unknown")
                            tool_args = event.get("args", {})
                            tool_result = event.get("result", {})

                            st.markdown(f"**Call {idx}: `{tool_name}`**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.caption("Arguments")
                                st.code(json.dumps(tool_args, ensure_ascii=False, indent=2), language="json")
                            with col2:
                                st.caption("Result Output")
                                st.code(json.dumps(tool_result, ensure_ascii=False, indent=2), language="json")
                            st.divider()

                # Save assistant message to session
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

                # Write transcript file
                transcript_data = {
                    "session_id": st.session_state.session_id,
                    "provider": provider_name,
                    "version": version_label,
                    "artifact_version": art_info["artifact_version"],
                    "messages": st.session_state.transcript_history,
                    "last_loop_result": loop_result
                }
                transcript_filename = f"{st.session_state.session_id}_{safe_slug(user_input[:20])}.transcript.json"
                write_transcript(TRANSCRIPTS_DIR / transcript_filename, transcript_data)

            except Exception as e:
                st.error(f"❌ Error during agent execution: {e}")
