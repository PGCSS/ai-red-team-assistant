# RedMind — AI Red Team Assistant (MVP)

RedMind is a **conceptual, authorization-first** AI assistant for cybersecurity professionals, students, and defenders.  
It helps generate **structured red team and security assessment plans** for **authorized engagements and lab environments**.

This is an early MVP intended for **testing, feedback, and iteration**.

---

## What RedMind does

RedMind generates a structured assessment plan that includes:

- Objective and scope
- High-level attack vectors (conceptual, non-operational)
- Conceptual test steps (explicitly framed as lab or authorized)
- Detection points (blue-team perspective)
- Recommended remediations
- Optional MITRE ATT&CK technique IDs
- References and assumptions

The UI also provides:
- Preset testing scenarios
- A readable report view (not just raw JSON)
- Session history (load previous runs)
- Markdown export for reports

---

## What RedMind does NOT do

RedMind **does not**:
- Provide exploit code or payloads
- Give step-by-step hacking instructions
- Assist with unauthorized access
- Generate malware or weaponized content

Prompts that appear malicious or unauthorized are blocked.

---

## Requirements

- **Python 3.11 recommended**
- Windows, macOS, or Linux
- An **OpenAI API key** (your own)

---

## Installation

Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd ai-red-team-assistant
pip install -r requirements.txt
OpenAI API Key Setup
RedMind uses the environment variable OPENAI_API_KEY.
Your API key is never stored in the code.

Option 1 — Set in your shell (recommended)
Windows (PowerShell)

powershell
Copy code
setx OPENAI_API_KEY "sk-your-key-here"
Restart PowerShell after running this.

macOS / Linux

bash
Copy code
export OPENAI_API_KEY="sk-your-key-here"
Option 2 — Use a .env file (recommended for local development)
Create a file called .env in the project root:

env
Copy code
OPENAI_API_KEY=sk-your-key-here
Do not commit this file. It should be in .gitignore.

Running the UI (Streamlit)
Activate your virtual environment (if using one), then run:

bash
Copy code
python -m streamlit run app.py
Streamlit will print a local URL, typically:

arduino
Copy code
http://localhost:8501
Open it in your browser.

Using RedMind
Confirm the authorization checkbox

Choose a preset scenario or write your own target & objective

Click Generate Plan

Review:

Structured JSON output

Readable report view

Download the plan as Markdown if needed

Reload previous sessions from the sidebar

All generated sessions are saved locally in the sessions/ directory.

Running the CLI (optional)
A simple CLI interface is also available:

bash
Copy code
python cli.py
This is useful for quick testing without the UI.

Project Structure
graphql
Copy code
ai-red-team-assistant/
├── app.py            # Streamlit UI
├── backend.py        # Model call, parsing, safety logic
├── cli.py            # CLI interface
├── prompts.md        # System prompt and few-shot examples
├── requirements.txt  # Locked dependencies
├── sessions/         # Saved session outputs
└── README.md
Safety & Acceptable Use
RedMind is designed for:

Authorized security testing

Lab environments

Defensive planning

Education and training

You are responsible for ensuring you have explicit permission to test any real systems described.

Early Tester Feedback
If you’re an early tester, feedback is hugely appreciated:

What is your background? (student, pentester, blue team, etc.)

Which presets did you use?

What felt useful or confusing?

What would you want added next?

You can collect feedback via:

GitHub Issues

A private message

A feedback form (recommended)

Roadmap (Early)
Planned improvements include:

Mode selection (Offensive / Defensive / Educational)

Better MITRE mapping controls

Hosted demo (no local setup)

Authentication and usage limits

Expanded cloud and API scenarios

Disclaimer
This tool is provided for educational and authorized use only.
The author is not responsible for misuse.