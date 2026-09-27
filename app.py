"""AgentLint — Streamlit dashboard placeholder (Phase 0).

Phase 9 will implement the full dashboard.
This file must not import any agentlint submodule — pure Streamlit only.
"""

import streamlit as st

st.set_page_config(
    page_title="AgentLint",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 AgentLint")
st.caption("One repo. Many AI coding agents. One source of truth.")

st.info(
    "**Dashboard coming soon.** "
    "Run `agentlint scan <repo-path>` from the CLI once Phase 1 is complete.",
    icon="ℹ️",
)

st.divider()

pages = [
    ("📊 Overview", "Scan summary, severity breakdown, and health score."),
    ("📄 Instruction Sources", "All discovered agent instruction files and their metadata."),
    ("🐛 Findings", "Detected conflicts, stale references, and missing context."),
    ("🗂️ Repository Truth", "Facts extracted directly from the repository."),
    ("📋 Canonical Contract", "The recommended canonical agent policy."),
    ("🔧 Repair Preview", "Proposed diff to fix each finding."),
    ("✅ Verification", "Evidence-backed verification of each repair."),
]

for title, description in pages:
    with st.expander(title):
        st.write(f"_{description}_")
        st.write("**Not yet implemented** — available after Phase 9.")

st.divider()
st.caption("AgentLint v0.1.0 · IBM Bob 2.0 Hackathon · MIT License")
