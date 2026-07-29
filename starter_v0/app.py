from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop, safe_slug, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def init_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("turns", [])


def transcript_path(version: str, provider: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    name = "_".join([safe_slug(version), safe_slug(provider), stamp])
    return TRANSCRIPTS_DIR / f"{name}.transcript.json"


def main() -> None:
    st.set_page_config(page_title="Research Agent", layout="wide")
    init_state()

    st.title("Research Agent")
    st.caption("Day04 tool eval UI")

    with st.sidebar:
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"])
        version = st.text_input("Artifact version", "v3")
        model = st.text_input("Model override", "")
        max_tool_rounds = st.slider("Max tool rounds", 1, 6, 4)
        history_window = st.slider("History turns", 0, 8, 5)
        if st.button("Reset chat"):
            st.session_state.history = []
            st.session_state.turns = []
            st.rerun()

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(declarations)
    artifact = build_artifact_version(version, system_prompt_path, tools_path)

    st.write(f"Artifact version: `{artifact.artifact_version}`")

    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.write(turn["user"])
        with st.chat_message("assistant"):
            st.write(turn.get("assistant_text") or "")
            events = turn.get("tool_events") or []
            if events:
                with st.expander("Tool trace", expanded=True):
                    for event in events:
                        st.markdown(f"**{event.get('tool')}**")
                        st.code(compact_json({"args": event.get("args"), "result": event.get("result")}), language="json")

    user_text = st.chat_input("Ask for web, social, policy, paper, or source-quality research")
    if not user_text:
        return

    with st.chat_message("user"):
        st.write(user_text)

    recent_history = st.session_state.history[-history_window * 2:] if history_window else []
    messages = [
        {"role": "system", "content": system_prompt},
        *recent_history,
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "user": user_text,
        "status": "started",
        "assistant_text": "",
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        try:
            provider = make_provider(provider_name)
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model or None,
                max_tool_rounds=max_tool_rounds,
            )
            turn_record.update(result)
            st.write(result["assistant_text"])
            if result.get("tool_events"):
                with st.expander("Tool trace", expanded=True):
                    for event in result["tool_events"]:
                        st.markdown(f"**{event.get('tool')}**")
                        st.code(compact_json({"args": event.get("args"), "result": event.get("result")}), language="json")
            st.session_state.history.append({"role": "user", "content": user_text})
            st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn_record.update({
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {exc}",
                "assistant_text": "Provider error. Check API key, quota, and selected model.",
            })
            st.error(turn_record["error"])

    turn_record["ended_at"] = datetime.now().isoformat(timespec="seconds")
    st.session_state.turns.append(turn_record)
    payload = {
        "transcript_id": f"{safe_slug(version)}_{safe_slug(provider_name)}_streamlit",
        **artifact_version_dict(artifact),
        "provider": provider_name,
        "model": model or None,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "turns": st.session_state.turns,
    }
    path = transcript_path(version, provider_name)
    write_transcript(path, payload)
    st.caption(f"Transcript saved: {path}")


if __name__ == "__main__":
    main()
