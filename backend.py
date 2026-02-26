# backend.py
import os, json, re
import openai

import os

try:
    import streamlit as st
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
except Exception:
    OPENAI_API_KEY = None

if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY (set Streamlit secrets or environment variable).")

openai.api_key = OPENAI_API_KEY

def extract_block(text, start_marker, end_marker):
    s = text.find(start_marker); e = text.find(end_marker)
    return "" if s == -1 or e == -1 else text[s+len(start_marker):e].strip()

with open("prompts.md", "r", encoding="utf-8") as f:
    _txt = f.read()

# Existing plan prompts
PLAN_SYSTEM_PROMPT = extract_block(_txt, "### PLAN_SYSTEM_PROMPT", "### END_SYSTEM_PROMPT")
FEW_SHOT = extract_block(_txt, "### FEW_SHOT_EXAMPLES", "### END_FEW_SHOT")

# New report prompts
REPORT_SYSTEM_PROMPT = extract_block(_txt, "### REPORT_SYSTEM_PROMPT", "### END_REPORT_SYSTEM_PROMPT")
REPORT_FEW_SHOT = extract_block(_txt, "### REPORT_FEW_SHOT_EXAMPLES", "### END_REPORT_FEW_SHOT")

def is_valid_mitre(code: str) -> bool:
    return bool(re.fullmatch(r"T\d{4}", code.strip().upper()))

def clean_mitre_list(suggested):
    if not suggested:
        return []
    if isinstance(suggested, str):
        return list(dict.fromkeys(re.findall(r"T\d{4}", suggested.upper())))
    out = []
    for t in suggested:
        if isinstance(t, str):
            m = re.match(r"(T\d{4})", t.strip().upper())
            if m and is_valid_mitre(m.group(1)):
                out.append(m.group(1))
    return list(dict.fromkeys(out))

def _call_model(messages):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.0,
        max_tokens=2000,
        top_p=1.0
    )
    return resp.choices[0].message.content

def _parse_json(text: str):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON found in response")

    blob = text[start:end+1]
    try:
        return json.loads(blob), text
    except json.JSONDecodeError:
        # remove trailing commas before } or ]
        repaired = re.sub(r",\s*([}\]])", r"\1", blob)
        return json.loads(repaired), text
    
def generate_plan(user_text: str, include_examples: bool = True):
    messages = [{"role":"system","content": PLAN_SYSTEM_PROMPT}]
    if include_examples and FEW_SHOT:
        messages.append({"role":"system","content": FEW_SHOT})
    messages.append({"role":"user","content": user_text})

    raw = _call_model(messages)
    parsed, _ = _parse_json(raw)
    parsed["mitre_tags"] = clean_mitre_list(parsed.get("mitre_tags", []))
    return parsed, raw

def generate_report(assignment_text: str, notes_text: str, template: str = "Medium", include_examples: bool = True):
    """
    Generate a student-friendly lab report from assignment instructions (optional) and raw notes.
    """
    if not REPORT_SYSTEM_PROMPT:
        raise RuntimeError("REPORT_SYSTEM_PROMPT block missing from prompts.md")

    # Template guidance
    if template == "Short":
        template_instructions = (
            "Keep the report concise (approx 1–2 pages equivalent). "
            "Limit findings to the most critical issues. Executive summary should be brief."
        )
    elif template == "Long":
        template_instructions = (
            "Produce a detailed, professional-style report with expanded explanations, "
            "thorough impact analysis, and comprehensive remediation guidance."
        )
    else:
        template_instructions = (
            "Produce a balanced student assignment report. Moderate detail in methodology and findings. "
            "Suitable for most university submissions."
        )

    user_payload = f"""Report template: {template}

Template instructions:
{template_instructions}

Assignment / Rubric (may be empty):
{assignment_text.strip()}

Raw lab notes:
{notes_text.strip()}
"""

    messages = [{"role": "system", "content": REPORT_SYSTEM_PROMPT}]
    if include_examples and REPORT_FEW_SHOT:
        messages.append({"role": "system", "content": REPORT_FEW_SHOT})
    messages.append({"role": "user", "content": user_payload})

    raw = _call_model(messages)

    try:
        parsed, _ = _parse_json(raw)
    except Exception as e:
        # Return a safe error payload so Streamlit doesn't crash
        return {
            "report_title": "JSON parsing failed",
            "executive_summary": "The model returned invalid JSON. See raw output.",
            "scope": "",
            "methodology": "",
            "findings": [],
            "prioritized_remediation": [],
            "rubric_checklist": [],
            "conclusion": "",
            "references": [],
            "evidence_checklist": [],
            "assumptions": str(e)
        }, raw

    return parsed, raw