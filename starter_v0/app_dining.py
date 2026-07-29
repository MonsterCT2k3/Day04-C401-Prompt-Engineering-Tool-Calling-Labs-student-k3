from __future__ import annotations

import html
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

SYSTEM_PROMPT_PATH = ARTIFACTS_DIR / "system_prompt_dining.md"
TOOLS_PATH = ARTIFACTS_DIR / "tools_dining.yaml"

st.set_page_config(
    page_title="Dining & Hangout Finder",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    .hero-title {
        background: linear-gradient(135deg, #f97316 0%, #ef4444 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle { color: #94a3b8; font-size: 1.05rem; margin-bottom: 1.5rem; }

    .place-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 0.9rem;
        margin: 0.6rem 0 1rem 0;
    }
    .place-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-left: 4px solid #f97316;
        border-radius: 14px;
        padding: 1rem 1.1rem;
    }
    .place-name { font-weight: 700; font-size: 1.02rem; color: #fdba74; margin-bottom: 0.3rem; }
    .place-meta { color: #94a3b8; font-size: 0.85rem; margin: 0.15rem 0; }
    .place-distance {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.15rem 0.6rem;
        border-radius: 9999px;
        background: rgba(249, 115, 22, 0.15);
        color: #fb923c;
        font-size: 0.78rem;
        font-weight: 700;
    }

    .ticket-card {
        background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(219, 39, 119, 0.12));
        border: 1px solid rgba(249, 115, 22, 0.4);
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        margin: 0.6rem 0 1rem 0;
    }
    .ticket-title { font-weight: 800; font-size: 1.1rem; color: #fdba74; }
    .ticket-code {
        font-family: monospace;
        font-weight: 700;
        color: #4ade80;
        background: rgba(74, 222, 128, 0.12);
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
    }

    .badge-status { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .badge-info { background-color: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">🍜 Dining & Hangout Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Tìm quán ăn, cafe, chỗ vui chơi quanh bạn & đặt chỗ — dữ liệu thật từ OpenStreetMap</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎛️ Cấu hình")
    provider_name = st.selectbox("🧠 Model Provider", options=["nvidia", "openrouter", "openai", "gemini", "anthropic"], index=0)
    model_override = st.text_input("🤖 Model Identifier", value="", placeholder="meta/llama-3.1-70b-instruct")

    with st.expander("⚙️ Execution Tuning", expanded=False):
        history_window = st.slider("Context History Window (turns)", min_value=1, max_value=10, value=5)
        max_tool_rounds = st.slider("Max Tool Execution Rounds", min_value=1, max_value=8, value=4)

    art_version_obj = build_artifact_version(version="dining-v1", system_prompt_path=SYSTEM_PROMPT_PATH, tools_path=TOOLS_PATH)
    art_info = artifact_version_dict(art_version_obj)

    st.markdown("---")
    st.markdown("### 🏷️ Artifact Signature")
    st.markdown(f'<span class="badge-status badge-info">{art_info["artifact_version"]}</span>', unsafe_allow_html=True)
    st.caption(f"**Prompt Hash:** `{art_info['prompt_hash'][:12]}...`")
    st.caption(f"**Tools Hash:** `{art_info['tools_hash'][:12]}...`")

    st.markdown("---")
    if st.button("🔄 Xóa hội thoại", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript_history = []
        st.session_state.session_id = now_iso().replace(":", "-")
        st.rerun()

st.markdown("##### 🚀 Thử nhanh:")
col_s1, col_s2, col_s3, col_s4 = st.columns(4)

selected_shortcut = None
if col_s1.button("🍜 Quán ăn gần VinUni"):
    selected_shortcut = "Tìm giúp mình vài quán ăn gần VinUni"
if col_s2.button("☕ Cafe gần Bách Khoa"):
    selected_shortcut = "Có quán cafe nào gần Bách Khoa Hà Nội không?"
if col_s3.button("🎬 Vui chơi ở Hồ Gươm"):
    selected_shortcut = "Gợi ý chỗ vui chơi giải trí gần Hồ Gươm"
if col_s4.button("📅 Đặt chỗ tối nay"):
    selected_shortcut = "Đặt chỗ cho 4 người tối nay 7 giờ"


def render_place_cards(results: list[dict]) -> None:
    cards = []
    for place in results:
        name = html.escape(str(place.get("name", "")))
        category = html.escape(str(place.get("category", "")))
        cuisine = html.escape(str(place.get("cuisine", "")))
        address = html.escape(str(place.get("address", "")))
        distance = place.get("distance_km", "")
        meta_lines = "".join([
            f'<div class="place-meta">📍 {address}</div>' if address else "",
            f'<div class="place-meta">🍽️ {cuisine}</div>' if cuisine else "",
            f'<div class="place-meta">🏷️ {category}</div>' if category else "",
        ])
        cards.append(
            f'<div class="place-card">'
            f'<div class="place-name">{name}</div>'
            f'{meta_lines}'
            f'<span class="place-distance">{distance} km</span>'
            f'</div>'
        )
    st.markdown(f'<div class="place-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_reservation_ticket(result: dict) -> None:
    place_name = html.escape(str(result.get("place_name", "")))
    when = html.escape(str(result.get("when", "")))
    party_size = html.escape(str(result.get("party_size", "")))
    code = html.escape(str(result.get("confirmation_code", "")))
    st.markdown(
        f'<div class="ticket-card">'
        f'<div class="ticket-title">✅ Đã đặt chỗ — {place_name}</div>'
        f'<div class="place-meta">🕒 {when} · 👥 {party_size} người</div>'
        f'<div style="margin-top:0.5rem;">Mã xác nhận: <span class="ticket-code">{code}</span></div>'
        f'<div class="place-meta" style="margin-top:0.4rem;">Đây là booking mô phỏng cho demo.</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def render_tool_events(tool_events: list[dict]) -> None:
    for event in tool_events:
        tool_name = event.get("tool", "unknown")
        result = event.get("result", {})
        if tool_name == "place_search" and result.get("status") == "success":
            render_place_cards(result.get("results", []))
        elif tool_name == "book_reservation" and result.get("status") == "reserved":
            render_reservation_ticket(result)

    with st.expander(f"⚙️ Tool Trace ({len(tool_events)} call(s))", expanded=False):
        for idx, event in enumerate(tool_events, 1):
            st.markdown(f"**#{idx} `{event.get('tool', 'unknown')}()`**")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.caption("📥 Input")
                st.json(event.get("args", {}), expanded=False)
            with t_col2:
                st.caption("📤 Output")
                st.json(event.get("result", {}), expanded=False)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "transcript_history" not in st.session_state:
    st.session_state.transcript_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = now_iso().replace(":", "-")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🍽️"):
            st.markdown(msg["content"])
            tool_events = msg.get("tool_events", [])
            if tool_events:
                render_tool_events(tool_events)

user_prompt = st.chat_input("Hỏi về quán ăn, cafe, chỗ vui chơi, hoặc đặt chỗ...")
if selected_shortcut:
    user_prompt = selected_shortcut

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    st.session_state.transcript_history.append({"role": "user", "content": user_prompt})

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🍽️"):
        status_placeholder = st.empty()
        status_placeholder.markdown('<span class="badge-status badge-info">🔄 Đang tìm & xử lý...</span>', unsafe_allow_html=True)

        try:
            provider = make_provider(provider_name)
            system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
            tool_declarations = load_tool_declarations(TOOLS_PATH)
            openai_tools = to_openai_tools(tool_declarations)

            history_subset = trim_history(st.session_state.transcript_history, history_window)
            full_messages = [{"role": "system", "content": system_prompt}] + history_subset

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

            st.markdown(assistant_text)
            if tool_events:
                render_tool_events(tool_events)

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "tool_events": tool_events,
                "status": status
            })
            st.session_state.transcript_history.append({"role": "assistant", "content": assistant_text})

            transcript_data = {
                "session_id": st.session_state.session_id,
                "provider": provider_name,
                "version": "dining-v1",
                "artifact_version": art_info["artifact_version"],
                "messages": st.session_state.transcript_history,
                "last_loop_result": loop_result
            }
            transcript_filename = f"dining_{st.session_state.session_id}_{safe_slug(user_prompt[:20])}.transcript.json"
            write_transcript(TRANSCRIPTS_DIR / transcript_filename, transcript_data)

        except Exception as e:
            status_placeholder.empty()
            st.error(f"❌ Lỗi khi xử lý: {e}")
