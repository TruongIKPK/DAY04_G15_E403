from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version
from chat import (
    run_model_tool_loop,
    trim_history,
    safe_slug,
    now_iso,
    write_transcript,
)

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

# Load environment variables
load_lab_env(ROOT)

# Page Configuration
st.set_page_config(
    page_title="Research Agent Tool Eval UI",
    page_icon="🔬",
    layout="wide",
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "transcript_path" not in st.session_state:
    st.session_state.transcript_path = None
if "turn_index" not in st.session_state:
    st.session_state.turn_index = 0

# Sidebar - Provider & API Key Setup
st.sidebar.title("🔬 Agent Config & Credentials")

provider_name = st.sidebar.selectbox(
    "Select Provider",
    options=["openrouter", "openai", "anthropic", "gemini", "perplexity"],
    index=0,
)

model_override_input = st.sidebar.text_input(
    "Model Name (Override)",
    value="",
    help="e.g. openai/gpt-4o-mini, gpt-4o-mini, claude-3-5-sonnet, gemini-2.5-flash. Leave blank for provider default.",
)
model_override = model_override_input.strip() if model_override_input.strip() else None

with st.sidebar.expander("API Key Settings", expanded=True):
    st.caption("Vui lòng nhập API Key của bạn trực tiếp tại đây:")
    openrouter_key = st.text_input("OPENROUTER_API_KEY", value="", type="password", placeholder="Nhập OpenRouter API Key...")
    openai_key = st.text_input("OPENAI_API_KEY", value="", type="password", placeholder="Nhập OpenAI API Key...")
    anthropic_key = st.text_input("ANTHROPIC_API_KEY", value="", type="password", placeholder="Nhập Anthropic API Key...")
    gemini_key = st.text_input("GEMINI_API_KEY", value="", type="password", placeholder="Nhập Gemini API Key...")
    perplexity_key = st.text_input("PERPLEXITY_API_KEY", value="", type="password", placeholder="Nhập Perplexity API Key...")

# Set or clear environment keys based strictly on UI user inputs
if openrouter_key.strip():
    os.environ["OPENROUTER_API_KEY"] = openrouter_key.strip()
else:
    os.environ.pop("OPENROUTER_API_KEY", None)

if openai_key.strip():
    os.environ["OPENAI_API_KEY"] = openai_key.strip()
else:
    os.environ.pop("OPENAI_API_KEY", None)

if anthropic_key.strip():
    os.environ["ANTHROPIC_API_KEY"] = anthropic_key.strip()
else:
    os.environ.pop("ANTHROPIC_API_KEY", None)

if gemini_key.strip():
    os.environ["GEMINI_API_KEY"] = gemini_key.strip()
else:
    os.environ.pop("GEMINI_API_KEY", None)

if perplexity_key.strip():
    os.environ["PERPLEXITY_API_KEY"] = perplexity_key.strip()
else:
    os.environ.pop("PERPLEXITY_API_KEY", None)



# Helper for secret redaction
def get_secret_strings() -> list[str]:
    """Collect API keys from env and UI inputs to ensure they are never displayed in UI/logs."""
    secrets = set()
    for key, val in os.environ.items():
        if ("KEY" in key or "TOKEN" in key or "SECRET" in key or "HOST" in key) and val and len(str(val)) > 5:
            secrets.add(str(val))
    for k in [openrouter_key, openai_key, anthropic_key, gemini_key]:
        if k and len(k.strip()) > 5:
            secrets.add(k.strip())
    return list(secrets)

def sanitize_value(value: Any, secrets: list[str]) -> Any:
    """Recursively scrub known secrets from UI output."""
    if isinstance(value, str):
        cleaned = value
        for secret in secrets:
            cleaned = cleaned.replace(secret, "[REDACTED_SECRET]")
        return cleaned
    elif isinstance(value, dict):
        return {k: sanitize_value(v, secrets) for k, v in value.items()}
    elif isinstance(value, list):
        return [sanitize_value(item, secrets) for item in value]
    return value

st.sidebar.markdown("---")

version_label = st.sidebar.text_input(
    "Artifact Version Label",
    value="v0",
    help="e.g. v0, v1, v2",
)

prompt_file_str = st.sidebar.text_input("System Prompt File", value="artifacts/system_prompt.md")
tools_file_str = st.sidebar.text_input("Tools Declaration File", value="artifacts/tools.yaml")

history_window = st.sidebar.number_input("History Window", min_value=1, max_value=20, value=5)
max_tool_rounds = st.sidebar.number_input("Max Tool Rounds", min_value=1, max_value=10, value=4)

system_prompt_path = ROOT / prompt_file_str
tools_path = ROOT / tools_file_str

# Compute Artifact Versioning
artifact_version_info = None
if system_prompt_path.exists() and tools_path.exists():
    try:
        artifact_version_info = build_artifact_version(version_label, system_prompt_path, tools_path)
    except Exception as e:
        st.sidebar.error(f"Version error: {e}")

if artifact_version_info:
    st.sidebar.subheader("📌 Current Artifact Version")
    st.sidebar.code(artifact_version_info.artifact_version, language="text")
    st.sidebar.caption(f"Prompt hash: `{artifact_version_info.prompt_hash[:16]}...`")
    st.sidebar.caption(f"Tools hash: `{artifact_version_info.tools_hash[:16]}...`")

if st.sidebar.button("🔄 Reset Chat Session"):
    st.session_state.messages = []
    st.session_state.history = []
    st.session_state.transcript = None
    st.session_state.transcript_path = None
    st.session_state.turn_index = 0
    st.rerun()

if st.session_state.transcript_path:
    st.sidebar.markdown("---")
    st.sidebar.caption(f"📝 Transcript File:\n`{st.session_state.transcript_path.name}`")

# Header
st.title("🧪 Research Agent Workspace")
st.markdown(
    "Interactive UI powered by `run_model_tool_loop`. Inspect detailed tool trace rounds, arguments, results, and versioning below."
)

secrets = get_secret_strings()

# Render Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("rounds"):
            sanitized_rounds = sanitize_value(msg["rounds"], secrets)
            with st.expander(f"⚙️ Tool Execution Trace ({len(sanitized_rounds)} round/s)", expanded=False):
                for r in sanitized_rounds:
                    st.markdown(f"**Round {r.get('round')}**")
                    if r.get("assistant_text"):
                        st.caption(f"Assistant Note: {r.get('assistant_text')}")
                    for tc in r.get("tool_calls", []):
                        st.markdown(f"🛠️ **Tool Call:** `{tc.get('name')}`")
                        st.json(tc.get("args", {}), expanded=False)
                    for tr in r.get("tool_results", []):
                        st.markdown(f"📊 **Tool Result:** `{tr.get('tool')}`")
                        res = tr.get("result", {})
                        if isinstance(res, dict) and res.get("error"):
                            st.error(f"Error: {res.get('error')} - {res.get('message')}")
                        else:
                            st.json(res, expanded=False)
                    st.divider()

        if msg.get("content"):
            st.markdown(sanitize_value(msg["content"], secrets))

# User Input
if user_prompt := st.chat_input("Hỏi agent điều gì đó (ví dụ: Tweet mới nhất của Sam Altman là gì?)..."):
    if not system_prompt_path.exists():
        st.error(f"File not found: {system_prompt_path}")
        st.stop()
    if not tools_path.exists():
        st.error(f"File not found: {tools_path}")
        st.stop()

    system_prompt_text = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)

    try:
        provider = make_provider(provider_name)
    except Exception as e:
        st.error(f"Failed to create provider '{provider_name}': {e}")
        st.stop()

    selected_model = model_override or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(version_label, system_prompt_path, tools_path)

    # Initialize Transcript if not started
    if st.session_state.transcript is None:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = "_".join([
            safe_slug(version_label),
            safe_slug(provider_name),
            timestamp,
        ])
        st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
        st.session_state.transcript = {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": selected_model,
            "system_prompt": str(system_prompt_path),
            "tools": str(tools_path),
            "history_window": history_window,
            "max_tool_rounds": max_tool_rounds,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }

    # Append User Message to UI State
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    # Prepare input for run_model_tool_loop
    messages = [
        {"role": "system", "content": system_prompt_text},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_prompt},
    ]

    st.session_state.turn_index += 1
    turn_record: dict[str, Any] = {
        "turn_index": st.session_state.turn_index,
        "started_at": now_iso(),
        "user": user_prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.spinner("🤖 Agent đang xử lý và thực thi tools..."):
        try:
            loop_result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model_override,
                max_tool_rounds=max_tool_rounds,
            )
            turn_record.update(loop_result)
            assistant_text = loop_result.get("assistant_text", "")
            rounds = loop_result.get("rounds", [])

            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "rounds": rounds,
            })
            st.session_state.history.append({"role": "user", "content": user_prompt})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})

        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            turn_record.update({
                "status": "provider_error",
                "error": error_msg,
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {error_msg}",
            })

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)

    st.rerun()
