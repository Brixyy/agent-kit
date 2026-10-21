"""SessionStart: vloží do každé session (lokální i cloudové) informace o uživateli a společný workflow."""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
with open(os.path.join(os.path.dirname(__file__), "..", "kontext.md"), encoding="utf-8") as f:
    text = f.read()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
