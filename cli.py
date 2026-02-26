# cli.py - simple command-line interface for RedMind
from backend import generate_plan
import json
import re

# Keywords that strongly imply malicious or unauthorized intent
BLOCKLIST = [
    r"\bhack\b",
    r"\bbreak[\s\-]?in\b",
    r"\bbackdoor\b",
    r"\bexploit\b",
    r"\bbypass\b",
    r"\btake\s+over\b",
    r"\bunpatched\b\s+production",
    r"\bwithout\s+authorization\b",
    r"\bprivately\s+owned\s+systems\b",
    r"\bcompromise\b",
    r"\boffensive\s+payload\b",
    r"\bzero[\s-]?day\b",
]

# Allow patterns (override blocklist when legitimate)
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

def is_blocked(user_text: str) -> bool:
    text = user_text.lower()

    # If user explicitly states it's authorized/training/lab → always allowed
    for allow in ALLOWLIST:
        if re.search(allow, text):
            return False

    # Block explicit malicious intent patterns
    for bad in BLOCKLIST:
        if re.search(bad, text):
            return True

    return False


def main():
    print("=== AI Red Team Assistant (CLI MVP) ===")
    print("This tool provides *conceptual, authorized, defensive* red-team analysis only.")
    print("It does NOT provide exploits, payloads, or unauthorized access methods.")
    print("You confirm all scenarios described are:")
    print("  1) Performed in a lab or controlled environment, OR")
    print("  2) Covered by explicit written authorization.\n")
    
    print("Describe your target and objective (or 'q' to quit):")
    while True:
        user = input("\nTarget & objective> ").strip()
        if user.lower() in ("q", "quit", "exit"):
            break
        if not user:
            continue

        # Safety filter
        if is_blocked(user):
            print("\n⚠️  Safety Warning: The request appears to describe")
            print("    *unauthorized access*, *real-world intrusion*, or")
            print("    *malicious intent* without proof of authorization.\n")
            print("    This assistant cannot process such queries.\n")
            print("    Please rephrase to clearly indicate:")
            print("      - Authorized testing, OR")
            print("      - Lab environment, OR")
            print("      - Educational/defensive analysis only.\n")
            continue

        # If allowed, generate the plan
        plan, raw = generate_plan(user)
        print("\n--- Parsed JSON plan ---")
        print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
