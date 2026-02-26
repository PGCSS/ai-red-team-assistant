# app.py - Streamlit UI for AI Red Team Assistant
import os
import json
import time
import re
from pathlib import Path

KEYS_FILE = Path("keys.json")

import streamlit as st
from backend import generate_plan, generate_report

def load_valid_keys():
    # Prefer Streamlit secrets (Cloud)
    try:
        import streamlit as st
        keys = st.secrets.get("ACCESS_KEYS", None)
        if keys:
            return set(keys)
    except Exception:
        pass

    # Fallback to local keys.json (dev)
    if KEYS_FILE.exists():
        data = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        return set(data.get("valid_keys", []))

    return set()

def is_valid_key(user_key: str) -> bool:
    return user_key.strip() in load_valid_keys()

# ---------- Storage ----------
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

def list_sessions(limit: int = 10):
    """Return up to `limit` most recent session files."""
    files = sorted(
        SESSIONS_DIR.glob("session_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return files[:limit]

# ---------- Safety: blocklist / allowlist ----------
BLOCKLIST = [
    r"\bhack\b",
    r"\bbreak[\s\-]?in\b",
    r"\bbackdoor\b",
    r"\bexploit\b",
    r"\boffensive\s+payload\b",
    r"\bbypass\b",
    r"\btake\s+over\b",
    r"\bunpatched\b\s+production",
    r"\bcompromise\b",
    r"\bzero[\s-]?day\b",
    r"\bwithout\s+authorization\b",
]

ALLOWLIST = [
    r"\bauthorized\b",
    r"\bwith\s+authorization\b",
    r"\blab\b",
    r"\bcontrolled\s+environment\b",
    r"\btraining\b",
    r"\beducational\b",
    r"\bblue\s+team\b",
    r"\bdefensive\b",
    r"\bread-only\b",
]

# ---------- Preset scenarios ----------
PRESETS = {
    "External Web App (Auth & Session)": (
        "Target: external web application (staging). "
        "Objective: assess authentication, session management, and access control mechanisms to identify potential privilege escalation paths. "
        "Testing is authorized and limited to the staging environment."
    ),
    "Internal Network (Lateral Movement Lab)": (
        "Target: corporate internal LAN (isolated lab). "
        "Objective: simulate lateral movement scenarios, validate segmentation controls, and check for credential reuse issues. "
        "All accounts are test accounts and testing is authorized."
    ),
    "AWS Read-Only Audit": (
        "Target: AWS environment (authorized read-only audit). "
        "Objective: identify misconfigurations in IAM policies, S3 buckets, and serverless roles that could lead to data exposure or privilege escalation."
    ),
    "Public API (Abuse & Data Leakage)": (
        "Target: public API (beta environment with authorization). "
        "Objective: assess authentication, rate limiting, and access control handling for potential abuse or data leakage."
    ),
    "Defensive: Detect MFA Bypass": (
        "Objective: describe how defenders can detect attempts to bypass MFA on an enterprise login portal. "
        "Conceptual and defensive guidance only."
    ),
    "Educational: Explain Burp Suite": (
        "Explain the purpose of Burp Suite during authorized web application testing and outline conceptual use-cases in a lab environment."
    ),
}


def is_blocked(text: str) -> bool:
    t = text.lower()
    # If clearly stated as authorized / lab / educational -> allow
    for allow in ALLOWLIST:
        if re.search(allow, t):
            return False
    # Otherwise, if any obviously malicious pattern shows, block
    for bad in BLOCKLIST:
        if re.search(bad, t):
            return True
    return False

# ---------- Streamlit layout ----------
st.set_page_config(page_title="AI Red Team Assistant (MVP)", layout="wide")
st.title("AI Red Team Assistant — MVP")

st.markdown("""
This tool provides **conceptual, authorized** guidance for red teaming and security testing.

- It does **not** provide exploit code, payloads, or unauthorized access methods.  
- All scenarios must be **lab-only** or covered by **explicit written authorization**.  
""")

consent = st.checkbox(
    "I confirm that any scenarios I describe are in a lab or explicitly authorized.",
    value=False
)
if not consent:
    st.info("Check the box above to proceed.")
    st.stop()

with st.sidebar:
    st.header("Engagement Context")
    target_type = st.selectbox(
        "Target type",
        ["External web app", "Internal network", "Cloud infra", "Public API", "Other"]
    )
    notes = st.text_area("Engagement notes (optional)", height=120)
    if st.button("New Session", key="btn_new_session"):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.subheader("Previous sessions")

    session_files = list_sessions(limit=10)
    if session_files:
        # Build nice labels with timestamp
        options = ["(None)"]
        for f in session_files:
            ts = f.stem.replace("session_", "")
            try:
                ts_int = int(ts)
            except ValueError:
                ts_int = 0
            label_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts_int)) if ts_int else "unknown time"
            options.append(f"{f.name} — {label_time}")

        selected_label = st.selectbox("Load session", options, index=0)

        if selected_label != "(None)":
            idx = options.index(selected_label) - 1  # because "(None)" is first
            chosen_file = session_files[idx]
            try:
                loaded = json.loads(chosen_file.read_text(encoding="utf-8"))
                st.session_state["loaded_session"] = loaded
                st.session_state["loaded_session_file"] = chosen_file.name
            except Exception as e:
                st.warning(f"Failed to load {chosen_file.name}: {e}")
    else:
        st.caption("No previous sessions saved yet.")

st.markdown("### Access")

user_key = st.text_input(
    "Enter access key to unlock Report Generator",
    type="password",
    key="access_key"
)

# Always recompute access based on current input
st.session_state["access_granted"] = bool(user_key) and is_valid_key(user_key)

if user_key:
    if st.session_state["access_granted"]:
        st.success("Access granted. Report Generator unlocked.")
    else:
        st.error("Invalid access key.")

# ---- Mode selector FIRST ----
st.markdown("### Mode")
if st.session_state["access_granted"]:
    mode_options = ["Plan Generator", "Report Generator"]
else:
    mode_options = ["Plan Generator"]

mode = st.selectbox(
    "Choose what you want RedMind to do",
    mode_options,
    key="mode_select"
)

# ---- PLAN MODE ----
if mode == "Plan Generator":
    st.markdown("### Describe the target & objective")

    default_example = PRESETS["External Web App (Auth & Session)"]
    if "prompt_text" not in st.session_state:
        st.session_state["prompt_text"] = default_example

    st.markdown("You can start from a preset scenario or write your own:")

    preset_cols = st.columns(3)
    with preset_cols[0]:
        if st.button("Web App (Auth & Session)", key="preset_web_app"):
            st.session_state["prompt_text"] = PRESETS["External Web App (Auth & Session)"]
    with preset_cols[1]:
        if st.button("Internal Network Lab", key="preset_internal_lab"):
            st.session_state["prompt_text"] = PRESETS["Internal Network (Lateral Movement Lab)"]
    with preset_cols[2]:
        if st.button("AWS Audit", key="preset_aws_audit"):
            st.session_state["prompt_text"] = PRESETS["AWS Read-Only Audit"]

    preset_cols2 = st.columns(3)
    with preset_cols2[0]:
        if st.button("Public API", key="preset_public_api"):
            st.session_state["prompt_text"] = PRESETS["Public API (Abuse & Data Leakage)"]
    with preset_cols2[1]:
        if st.button("Defensive (MFA)", key="preset_defensive_mfa"):
            st.session_state["prompt_text"] = PRESETS["Defensive: Detect MFA Bypass"]
    with preset_cols2[2]:
        if st.button("Educational (Burp Suite)", key="preset_edu_burp"):
            st.session_state["prompt_text"] = PRESETS["Educational: Explain Burp Suite"]

    user_text = st.text_area(
        "Target & objective:",
        key="prompt_text",
        height=160
    )

    generate_clicked = st.button("Generate Plan", key="btn_generate_plan")

    if generate_clicked:
        if not user_text.strip():
            st.warning("Please enter a target and objective.")
        elif is_blocked(user_text):
            st.error("⚠️ The request appears unauthorized/malicious. Rephrase with lab/authorization/defensive intent.")
        else:
            with st.spinner("Generating conceptual plan..."):
                parsed, raw = generate_plan(user_text, include_examples=True)

            st.subheader("Structured Plan (JSON)")
            st.json(parsed)

            # Save session
            session_obj = {
                "timestamp": int(time.time()),
                "mode": "plan",
                "target_type": target_type,
                "notes": notes,
                "user_text": user_text,
                "plan": parsed,
            }
            fname = SESSIONS_DIR / f"session_{session_obj['timestamp']}.json"
            fname.write_text(json.dumps(session_obj, indent=2), encoding="utf-8")
            st.success(f"Session saved as {fname.name}")

# ---- REPORT MODE ----
elif mode == "Report Generator":

    if not st.session_state.get("access_granted", False):
        st.warning("Report Generator is locked. Enter a valid access key above.")
        st.stop()

    st.markdown("### Generate a student-ready lab report")
    st.caption("Paste the assignment/rubric (optional) and your raw lab notes.")

    template = st.selectbox(
        "Report Length / Style",
        ["Short", "Medium", "Long"],
        index=1,
        key="report_template"
    )

    assignment_text = st.text_area(
        "Assignment / Rubric (optional)",
        height=140,
        key="assignment_text"
    )

    notes_text = st.text_area(
        "Raw lab notes (required)",
        height=180,
        key="notes_text"
    )

    report_clicked = st.button("Generate Report", key="btn_generate_report")

    if report_clicked:
        if not notes_text.strip():
            st.warning("Please paste your raw lab notes.")
        else:
            if is_blocked(notes_text) and ("lab" not in notes_text.lower() and "authorized" not in notes_text.lower()):
                st.error("⚠️ Notes appear potentially unsafe. Add 'lab' or 'authorized' context and keep content conceptual.")
            else:
                with st.spinner("Generating report..."):
                    try:
                        report, raw = generate_report(assignment_text, notes_text, template=template, include_examples=True)

                    except Exception as e:
                        st.error(f"Error generating report: {e}")
                        #show raw output to debug JSON issues
                        st.subheader("Raw Model Output (for debugging)")
                        st.code(raw if "raw" in locals() else "No raw output captured.", language="text")
                        st.stop()

                # Readable render
                st.subheader("Report (Readable)")
                st.markdown(f"**Title:** {report.get('report_title','')}")
                st.markdown(f"**Executive Summary:** {report.get('executive_summary','')}")
                st.markdown(f"**Scope:** {report.get('scope','')}")
                st.markdown(f"**Methodology:** {report.get('methodology','')}")
                if report.get("report_title") == "JSON parsing failed":
                    st.subheader("Raw model output (debug)")
                    st.code(raw, language="text")
                    st.stop()

                rubric = report.get("rubric_checklist", [])
                if rubric:
                    st.markdown("## Rubric Checklist")
                    for r in rubric:
                        st.markdown(f"- {r}")

                findings = report.get("findings", [])
                if findings:
                    st.markdown("## Findings")
                    for i, f in enumerate(findings, 1):
                        st.markdown(f"### {i}. {f.get('title','')}")
                        st.markdown(f"**Severity:** {f.get('severity','')}")
                        st.markdown(f"**Description:** {f.get('description','')}")
                        st.markdown(f"**Impact:** {f.get('impact','')}")
                        ev = f.get("evidence", [])
                        if ev:
                            st.markdown("**Evidence:**")
                            for e in ev:
                                st.markdown(f"- {e}")
                        st.markdown(f"**Recommended fix:** {f.get('recommended_fix','')}")
                        mt = f.get("mitre_tags", [])
                        if mt:
                            st.markdown("**MITRE (optional):** " + ", ".join(mt))

                        cn = f.get("confidence_notes", "")
                        if cn:
                            st.caption(f"Confidence notes: {cn}")

                checklist = report.get("evidence_checklist", [])
                if checklist:
                    st.markdown("## Recommended Evidence to Include")
                    for item in checklist:
                        st.markdown(f"- {item}")

                prio = report.get("prioritized_remediation", [])
                if prio:
                    st.markdown("## Prioritized Remediation")
                    for item in prio:
                        st.markdown(f"- **{item.get('priority','')}**: {item.get('action','')}")
                        maps = item.get("maps_to_findings", [])
                        if maps:
                            st.caption("Maps to: " + ", ".join(maps))

                st.markdown(f"**Conclusion:** {report.get('conclusion','')}")
                refs = report.get("references", [])
                if refs:
                    st.markdown("**References:**")
                    for r in refs:
                        st.markdown(f"- {r}")
                st.markdown(f"**Assumptions:** {report.get('assumptions','')}")

                # Save session
                session_obj = {
                    "timestamp": int(time.time()),
                    "mode": "report",
                    "target_type": target_type,
                    "notes": notes,
                    "assignment_text": assignment_text,
                    "notes_text": notes_text,
                    "report": report,
                }
                fname = SESSIONS_DIR / f"session_{session_obj['timestamp']}.json"
                fname.write_text(json.dumps(session_obj, indent=2), encoding="utf-8")
                st.success(f"Session saved as {fname.name}")

                # Markdown export
                md = f"# {report.get('report_title','Cybersecurity Lab Report')}\n\n"
                md += f"## Executive Summary\n{report.get('executive_summary','')}\n\n"
                md += f"## Scope\n{report.get('scope','')}\n\n"
                md += f"## Methodology\n{report.get('methodology','')}\n\n"
                rubric = report.get("rubric_checklist", [])
                if rubric:
                    md += "## Rubric Checklist\n" + "".join([f"- {r}\n" for r in rubric]) + "\n"

                if checklist:
                    md += "## Recommended Evidence to Include\n"
                    md += "".join([f"- {item}\n" for item in checklist]) + "\n"

                md += "## Findings\n"
                for i, f in enumerate(findings, 1):
                    md += f"\n### {i}. {f.get('title','')}\n"
                    md += f"**Severity:** {f.get('severity','')}\n\n"
                    md += f"**Description:** {f.get('description','')}\n\n"
                    md += f"**Impact:** {f.get('impact','')}\n\n"
                    ev = f.get("evidence", [])
                    if ev:
                        md += "**Evidence:**\n" + "".join([f"- {e}\n" for e in ev]) + "\n"
                    md += f"**Recommended fix:** {f.get('recommended_fix','')}\n\n"
                    mt = f.get("mitre_tags", [])
                    if mt:
                        md += f"**MITRE:** {', '.join(mt)}\n\n"
                    cn = f.get("confidence_notes","")
                    if cn:
                        md += f"_Confidence notes:_ {cn}\n\n"

                prio = report.get("prioritized_remediation", [])
                if prio:
                    st.markdown("## Prioritized Remediation")
                    for item in prio:
                        st.markdown(f"- **{item.get('priority','')}**: {item.get('action','')}")
                        maps = item.get("maps_to_findings", [])
                        if maps:
                            st.caption("Maps to: " + ", ".join(maps))

                md += f"\n## Conclusion\n{report.get('conclusion','')}\n\n"
                if refs:
                    md += "## References\n" + "".join([f"- {r}\n" for r in refs]) + "\n"
                md += f"\n_Assumptions:_ {report.get('assumptions','')}\n"

                st.download_button(
                    "Download report (Markdown)",
                    md,
                    file_name="redmind_report.md",
                    mime="text/markdown"
                )


# ---------- Loaded session viewer ----------
if "loaded_session" in st.session_state:
    st.markdown("---")
    st.subheader("Loaded previous session")

    ls = st.session_state["loaded_session"]
    fname = st.session_state.get("loaded_session_file", "unknown file")

    st.markdown(f"**File:** `{fname}`")
    st.markdown(f"**Saved target type:** {ls.get('target_type', '')}")
    if ls.get("notes"):
        st.markdown(f"**Notes:** {ls.get('notes', '')}")
    st.markdown(f"**Original prompt:** {ls.get('user_text', '')}")

    plan = ls.get("plan", {})

    with st.expander("View loaded plan (JSON)", expanded=False):
        st.json(plan)

    st.markdown("**Loaded plan — readable view:**")
    st.markdown(f"- **Objective:** {plan.get('objective', '')}")
    st.markdown(f"- **Scope:** {plan.get('scope', '')}")

    vectors = plan.get("high_level_attack_vectors", [])
    if vectors:
        st.markdown("**High-level attack vectors:**")
        for v in vectors:
            st.markdown(f"- {v}")

    steps = plan.get("conceptual_test_steps", [])
    if steps:
        st.markdown("**Conceptual test steps:**")
        for s in steps:
            st.markdown(f"- {s}")

    det = plan.get("detection_points", [])
    if det:
        st.markdown("**Detection points:**")
        for d in det:
            st.markdown(f"- {d}")

    rem = plan.get("recommended_remediations", [])
    if rem:
        st.markdown("**Recommended remediations:**")
        for r in rem:
            st.markdown(f"- {r}")

    mitre = plan.get("mitre_tags", [])
    if mitre:
        st.markdown("**MITRE ATT&CK techniques:**")
        for t in mitre:
            st.markdown(f"- {t}")

    refs = plan.get("references", [])
    if refs:
        st.markdown("**References:**")
        for r in refs:
            st.markdown(f"- {r}")

    assumptions = plan.get("assumptions", "")
    if assumptions:
        st.markdown(f"**Assumptions:** {assumptions}")

