# prompt_test.py (replace your existing file with this)
import os
import openai
import json
import re

openai.api_key = os.environ.get("OPENAI_API_KEY")

# --------- load prompts ----------
with open("prompts.md", "r", encoding="utf-8") as f:
    prompts_text = f.read()

# extract system prompt and few-shot using markers
def extract_block(text, start_marker, end_marker):
    s = text.find(start_marker)
    e = text.find(end_marker)
    if s == -1 or e == -1:
        return ""
    return text[s + len(start_marker): e].strip()

system_prompt = extract_block(prompts_text, "### SYSTEM_PROMPT", "### END_SYSTEM_PROMPT")
few_shot = extract_block(prompts_text, "### FEW_SHOT_EXAMPLES", "### END_FEW_SHOT")

# --------- helper: clean MITRE tags ----------
def is_valid_mitre(code: str) -> bool:
    return bool(re.fullmatch(r"T\d{4}", code.strip().upper()))

def clean_mitre_list(suggested):
    if not suggested:
        return []
    out = []
    # if it's a string, extract codes
    if isinstance(suggested, str):
        codes = re.findall(r"T\d{4}", suggested.upper())
        return list(dict.fromkeys(codes))
    # if it's a list, normalize each item
    for t in suggested:
        if isinstance(t, str):
            t_up = t.strip().upper()
            m = re.match(r"(T\d{4})", t_up)
            if m and is_valid_mitre(m.group(1)):
                out.append(m.group(1))
    return list(dict.fromkeys(out))

# --------- query function ----------
def query_model(user_text, include_few_shot=True):
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    if include_few_shot and few_shot:
        # include few-shot examples as system content to stabilize output
        messages.append({"role": "system", "content": few_shot})
    messages.append({"role": "user", "content": user_text})

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",   # change if you want another model
        messages=messages,
        temperature=0.0,      # deterministic
        max_tokens=700,
        top_p=1.0
    )
    return resp.choices[0].message.content

# --------- JSON extract & parse helper ----------
def try_parse_json(text: str):
    # try direct load
    try:
        return json.loads(text), text
    except Exception:
        # fallback: extract first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1]), text
            except Exception:
                return None, text
        return None, text

# --------- main ----------
if __name__ == "__main__":
    user_prompt = "Target: external web app. Objective: assess authentication & session handling."
    print("User prompt:", user_prompt)
    out_text = query_model(user_prompt, include_few_shot=True)
    print("\nModel output:\n")
    print(out_text)

    parsed, raw = try_parse_json(out_text)
    if parsed is None:
        print("\nFailed to parse JSON. Raw output above.")
    else:
        # sanitize mitre tags
        parsed['mitre_tags'] = clean_mitre_list(parsed.get('mitre_tags', []))
        print("\nParsed JSON (cleaned):\n")
        print(json.dumps(parsed, indent=2))
