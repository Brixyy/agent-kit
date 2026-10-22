"""SessionStart: vloží do každé session (lokální i cloudové) globální pravidla z global/AGENTS.md."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
with open(os.path.join(os.path.dirname(__file__), "..", "global", "AGENTS.md"), encoding="utf-8") as f:
    text = f.read()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
