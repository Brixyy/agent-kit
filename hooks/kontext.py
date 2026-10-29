"""SessionStart: vloží do každé session (lokální i cloudové) jádro globálních pravidel z global/AGENTS.md.

Claude Code vloží z hooku nejvýš 10 000 znaků; delší text nahradí náhledem prvních 2 000.
Podrobnosti (global/PODROBNOSTI.md) se proto nevkládají, jen se předá jejich cesta.
Velikost hlídá tests/test_kontext.py.
"""
import json
import os
import sys

GLOBAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "global"))


def kontext():
    with open(os.path.join(GLOBAL, "AGENTS.md"), encoding="utf-8") as f:
        text = f.read()
    return text + f"\nPodrobnosti globálních pravidel: `{os.path.join(GLOBAL, 'PODROBNOSTI.md')}`\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": kontext()}}, ensure_ascii=False))
