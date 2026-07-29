"""
Research Agent — Streamlit UI (Light Theme)
Reuses run_model_tool_loop from chat.py. No second agent loop.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

# ── path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
load_lab_env(ROOT)

from chat import run_model_tool_loop, trim_history, write_transcript, safe_slug
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trợ Lý Tìm Nhà Trọ",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS — LIGHT THEME ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=SF+Pro+Display:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Apple Light Mode */
.stApp {
    background: #f5f5f7;
    color: #1d1d1f;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #d2d2d7;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    color: #86868b;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Header section */
.header-container {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 18px;
    padding: 30px 36px;
    margin-bottom: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
.header-container h1 {
    margin: 0 0 8px 0;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1d1d1f !important;
    letter-spacing: -0.02em;
}
.header-container p {
    margin: 0;
    font-size: 1rem;
    color: #86868b;
}

/* Version badge */
.version-badge {
    display: inline-block;
    background: #f5f5f7;
    color: #0071e3;
    border: 1px solid #d2d2d7;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: 'SF Pro Display', monospace;
    margin-bottom: 8px;
}

/* Chat messages */
.user-msg {
    background: #0071e3;
    color: #ffffff;
    border-radius: 18px 18px 4px 18px;
    padding: 14px 20px;
    margin: 12px 0;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(0, 113, 227, 0.2);
}

.agent-msg {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 4px 18px 18px 18px;
    padding: 14px 20px;
    margin: 12px 0;
    color: #1d1d1f;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* Tool event cards */
.tool-card {
    background: #fafafa;
    border: 1px solid #e5e5ea;
    border-left: 4px solid #0071e3;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 10px 0;
    font-family: 'SF Pro Display', monospace;
    font-size: 0.8rem;
    transition: all 0.2s ease;
}
.tool-card:hover {
    background: #ffffff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    border-color: #d2d2d7;
}

.tool-card.error {
    border-left-color: #ff3b30;
    background: #fff0f0;
}

.tool-card.success {
    border-left-color: #34c759;
    background: #f0fdf4;
}

.tool-name {
    color: #0071e3;
    font-weight: 600;
    font-size: 0.85rem;
}

.tool-args {
    color: #86868b;
    font-size: 0.75rem;
    margin-top: 6px;
    word-break: break-all;
}

/* Round label */
.round-label {
    background: #f5f5f7;
    border: 1px solid #d2d2d7;
    border-radius: 10px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: #1d1d1f;
    font-weight: 600;
    margin: 12px 0 8px 0;
    display: inline-block;
}

/* Status chips */
.chip-answered  { background: #e3f6e9; color: #1e873a; border-radius: 10px; padding: 4px 14px; font-size: 0.75rem; font-weight: 600; }
.chip-waiting   { background: #fff5e5; color: #bf6a02; border-radius: 10px; padding: 4px 14px; font-size: 0.75rem; font-weight: 600; }
.chip-error     { background: #ffebeb; color: #d92d20; border-radius: 10px; padding: 4px 14px; font-size: 0.75rem; font-weight: 600; }

/* Metric cards */
.metric-row {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin: 16px 0;
}
.metric-box {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 16px;
    padding: 16px 20px;
    flex: 1;
    min-width: 100px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}
.metric-box .val {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1d1d1f;
    letter-spacing: -0.02em;
}
.metric-box .lbl {
    font-size: 0.7rem;
    color: #86868b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 4px;
}

/* Section panels */
.panel {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 20px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}

/* Progress comparison */
.progress-row {
    display: flex; align-items: center; gap: 10px; margin: 8px 0;
}
.progress-row .label { width: 60px; font-size: 0.8rem; font-weight: 600; color: #1d1d1f; }
.progress-bar {
    flex: 1; height: 10px; background: #e5e5ea; border-radius: 5px; overflow: hidden;
}
.progress-fill {
    height: 100%; border-radius: 5px;
    background: #0071e3;
    transition: width 0.5s ease;
}
.progress-row .pct { width: 45px; font-size: 0.8rem; font-weight: 600; color: #0071e3; text-align: right; }

h1, h2, h3 { color: #1d1d1f !important; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_provider(provider_name: str):
    return make_provider(provider_name)


@st.cache_resource(show_spinner=False)
def get_tools():
    decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return to_openai_tools(decls)


def get_system_prompt() -> str:
    return (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")


def load_run_files() -> list[Path]:
    if not RUNS_DIR.exists():
        return []
    return sorted(RUNS_DIR.glob("*.json"), reverse=True)


def chip(status: str) -> str:
    cls = {"answered": "chip-answered", "waiting_for_user": "chip-waiting"}.get(status, "chip-error")
    return f'<span class="{cls}">{status}</span>'


def render_tool_event(event: dict[str, Any], idx: int):
    result = event.get("result", {})
    has_error = isinstance(result, dict) and result.get("error")
    card_cls = "tool-card error" if has_error else "tool-card success"
    args_str = json.dumps(event.get("args", {}), ensure_ascii=False)
    st.markdown(f"""
    <div class="{card_cls}">
        <span class="tool-name">🔧 {event.get('tool', '?')}</span>
        <div class="tool-args">args: {args_str}</div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander(f"📦 Result #{idx}", expanded=False):
        st.json(result)


def progress_bar(label: str, value: float) -> str:
    pct = int(value * 100)
    return f"""
    <div class="progress-row">
        <div class="label">{label}</div>
        <div class="progress-bar"><div class="progress-fill" style="width:{pct}%"></div></div>
        <div class="pct">{pct}%</div>
    </div>
    """


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    provider_name = st.selectbox(
        "Provider",
        ["nvidia", "openrouter", "openai", "anthropic", "gemini"],
        index=0,
    )

    version_label = st.text_input("Version", value="v3")
    max_tool_rounds = st.slider("Max tool rounds", 1, 8, 4)
    history_window = st.slider("History window", 0, 10, 5)

    st.divider()
    av = build_artifact_version(version_label, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
    st.markdown(f'<div class="version-badge">📌 {av.artifact_version}</div>', unsafe_allow_html=True)
    st.caption(f"🔑 prompt: `{av.prompt_hash[:12]}`")
    st.caption(f"🔧 tools: `{av.tools_hash[:12]}`")

    st.divider()
    st.markdown("### 📂 Run Files")
    run_files = load_run_files()
    if run_files:
        selected_run_name = st.selectbox(
            "Inspect a run",
            ["— select —"] + [f.name for f in run_files],
        )
    else:
        selected_run_name = "— select —"
        st.caption("No runs yet.")


# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <h1>🏠 Trợ Lý Tìm Nhà Trọ</h1>
    <p>Hỗ trợ tìm kiếm, xem chi tiết và đặt lịch xem nhà trọ/căn hộ</p>
</div>
""", unsafe_allow_html=True)

tab_chat, tab_runs, tab_prompt = st.tabs(["💬 Chat", "📊 Run Inspector", "📄 Artifacts"])


# ── TAB 1: CHAT ──────────────────────────────────────────────────────────────
with tab_chat:
    col_chat, col_trace = st.columns([3, 2])

    with col_chat:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### 💬 Conversation")

        if "history" not in st.session_state:
            st.session_state.history: list[dict] = []
        if "transcript_turns" not in st.session_state:
            st.session_state.transcript_turns: list[dict] = []

        for turn in st.session_state.transcript_turns:
            st.markdown(f'<div class="user-msg">👤 {turn["user"]}</div>', unsafe_allow_html=True)
            status_html = chip(turn.get("status", ""))
            st.markdown(f'<div class="agent-msg">🤖 {turn.get("assistant_text", "")} &nbsp;{status_html}</div>', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Message",
                placeholder="e.g. Tìm phòng trọ khu vực Cầu Giấy dưới 4 triệu...",
                label_visibility="collapsed",
            )
            cols = st.columns([5, 1])
            with cols[0]:
                send = st.form_submit_button("Send ▶", use_container_width=True)
            with cols[1]:
                pass

        if send and user_input.strip():
            with st.spinner("🔄 Agent thinking..."):
                try:
                    provider = get_provider(provider_name)
                    tools = get_tools()
                    system_prompt = get_system_prompt()

                    messages = [
                        {"role": "system", "content": system_prompt},
                        *trim_history(st.session_state.history, history_window),
                        {"role": "user", "content": user_input},
                    ]

                    result = run_model_tool_loop(
                        provider=provider,
                        messages=messages,
                        tools=tools,
                        model=None,
                        max_tool_rounds=max_tool_rounds,
                    )

                    turn_record = {
                        "turn_index": len(st.session_state.transcript_turns) + 1,
                        "user": user_input,
                        "artifact_version": av.artifact_version,
                        **result,
                    }
                    st.session_state.transcript_turns.append(turn_record)
                    st.session_state.history.append({"role": "user", "content": user_input})
                    st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})

                    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
                    tid = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{ts}"
                    tpath = TRANSCRIPTS_DIR / f"{tid}.transcript.json"
                    write_transcript(tpath, {
                        "transcript_id": tid,
                        **artifact_version_dict(av),
                        "provider": provider_name,
                        "turns": st.session_state.transcript_turns,
                    })
                except Exception as exc:
                    st.error(f"❌ Provider error: {exc}")

            st.rerun()

        if st.button("🗑️ Clear chat"):
            st.session_state.history = []
            st.session_state.transcript_turns = []
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_trace:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Tool Trace")

        if st.session_state.transcript_turns:
            latest = st.session_state.transcript_turns[-1]
            rounds = latest.get("rounds", [])
            total_rounds = len(rounds)
            total_tools = sum(len(r.get("tool_calls", [])) for r in rounds)

            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box"><div class="val">{total_rounds}</div><div class="lbl">Rounds</div></div>
                <div class="metric-box"><div class="val">{total_tools}</div><div class="lbl">Tools</div></div>
                <div class="metric-box"><div class="val">{latest.get('status','?')[:6]}</div><div class="lbl">Status</div></div>
            </div>
            """, unsafe_allow_html=True)

            for r in rounds:
                st.markdown(f'<div class="round-label">🔄 Round {r["round"]}</div>', unsafe_allow_html=True)
                if r.get("assistant_text"):
                    st.caption(f"💭 {r['assistant_text'][:150]}...")
                for i, event in enumerate(r.get("tool_results", []), 1):
                    render_tool_event(event, i)

            st.caption(f"🏷️ `{latest.get('artifact_version', '')}`")
        else:
            st.info("💡 Send a message to see the tool trace here.")

        st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 2: RUN INSPECTOR ─────────────────────────────────────────────────────
with tab_runs:
    if selected_run_name != "— select —":
        run_path = RUNS_DIR / selected_run_name
        try:
            run_data = json.loads(run_path.read_text(encoding="utf-8"))
            summary = run_data.get("summary", {})

            # Header
            st.markdown(f"""
            <div class="header-container" style="padding:20px 28px;">
                <h1 style="font-size:1.2rem;">📊 {run_data.get("version", "?")} — {run_data.get("provider", "?")} / {(run_data.get("model") or "?")[:25]}</h1>
                <p>🏷️ {run_data.get("artifact_version", "?")}</p>
            </div>
            """, unsafe_allow_html=True)

            # Visual progress bars
            ca = summary.get("case_accuracy", 0)
            tr = summary.get("tool_routing_accuracy", 0)
            aa = summary.get("argument_accuracy", 0)
            mt = summary.get("multiturn_accuracy", 0)

            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("#### Accuracy Metrics")
            st.markdown(
                progress_bar("Case", ca) +
                progress_bar("Route", tr) +
                progress_bar("Args", aa) +
                progress_bar("Multi", mt),
                unsafe_allow_html=True,
            )

            err_count = summary.get("provider_error_cases", 0)
            passed = summary.get("passed_cases", 0)
            total = summary.get("total_cases", 0)
            st.markdown(f"""
            <div class="metric-row">
                <div class="metric-box"><div class="val">{passed}/{total}</div><div class="lbl">Passed</div></div>
                <div class="metric-box"><div class="val">{err_count}</div><div class="lbl">Errors</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Failure counts
            fc = summary.get("failure_counts", {})
            if fc:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.markdown("#### Failure Breakdown")
                st.bar_chart(fc)
                st.markdown('</div>', unsafe_allow_html=True)

            # Per-case results
            st.markdown("#### Case Results")
            results = run_data.get("results", [])
            for r in results:
                res = r.get("result", {})
                passed_case = res.get("passed", False)
                icon = "✅" if passed_case else "❌"
                failures = res.get("failures", [])
                label = f"{icon} {r['id']}"
                if not passed_case and failures:
                    label += f" — {', '.join(failures[:2])}"
                with st.expander(label):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Expected**")
                        st.json(r.get("expect", {}))
                    with col_b:
                        st.markdown("**Actual**")
                        st.json(res.get("actual_tool_calls", []))
                    if failures:
                        st.error("⚠️ " + " | ".join(failures))

        except Exception as e:
            st.error(f"Error loading run: {e}")
    else:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### 📂 All Runs Overview")
        if run_files:
            rows = []
            for rf in run_files[:20]:
                try:
                    d = json.loads(rf.read_text(encoding="utf-8"))
                    s = d.get("summary", {})
                    rows.append({
                        "File": rf.name[:45],
                        "Ver": d.get("version", "?"),
                        "Provider": d.get("provider", "?"),
                        "Case %": f"{s.get('case_accuracy', 0):.0%}",
                        "Route %": f"{s.get('tool_routing_accuracy', 0):.0%}",
                        "Arg %": f"{s.get('argument_accuracy', 0):.0%}",
                        "Errors": s.get("provider_error_cases", 0),
                    })
                except Exception:
                    pass
            if rows:
                import pandas as pd
                st.dataframe(pd.DataFrame(rows), width="stretch")
        else:
            st.info("No run files found. Run an eval first.")
        st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 3: ARTIFACTS ─────────────────────────────────────────────────────────
with tab_prompt:
    col_p, col_t = st.columns(2)
    with col_p:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### 📝 system_prompt.md")
        prompt_content = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        st.code(prompt_content, language="markdown")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_t:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("#### 🔧 tools.yaml")
        tools_content = (ARTIFACTS_DIR / "tools.yaml").read_text(encoding="utf-8")
        st.code(tools_content, language="yaml")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### 📊 version_log.csv")
    version_log_path = ARTIFACTS_DIR / "version_log.csv"
    if version_log_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(version_log_path)
            st.dataframe(df, width="stretch")
        except Exception:
            st.code(version_log_path.read_text(encoding="utf-8"))
    st.markdown('</div>', unsafe_allow_html=True)
