"""SessionStart: vloží do každé session (lokální i cloudové) jádro globálních pravidel z global/AGENTS.md.

Claude Code vloží z hooku nejvýš 10 000 znaků; delší text nahradí náhledem prvních 2 000.
Podrobnosti (global/PODROBNOSTI.md) se proto nevkládají, jen se předá jejich cesta.
Po zkrácení kontextu (zdroj `compact`) přidá navrch připomínku jazyka: agenti po souhrnu
kontextu opakovaně přecházeli do angličtiny, i když to pravidlo zakazuje (Brixyy/asistent#390).
Velikost a připomínku hlídá tests/test_kontext.py.
"""
import json
import os
import sys

GLOBAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "global"))


PO_ZKRACENI = (
    "Kontext byl právě zkrácen. Piš dál česky s plnou diakritikou: průběžné hlášky mezi nástroji "
    "i závěrečnou odpověď. Anglická věta je chyba (PODROBNOSTI, Formát hlášení, Jazyk).\n\n"
)


def zdroj():
    """Zdroj spuštění SessionStart (startup, resume, clear, compact); při chybě None."""
    try:
        return json.loads(sys.stdin.read() or "{}").get("source")
    except Exception:
        return None


def kontext(source=None):
    with open(os.path.join(GLOBAL, "AGENTS.md"), encoding="utf-8") as f:
        text = f.read()
    uvod = PO_ZKRACENI if source == "compact" else ""
    return uvod + text + f"\nPodrobnosti globálních pravidel: `{os.path.join(GLOBAL, 'PODROBNOSTI.md')}`\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": kontext(zdroj())}}, ensure_ascii=False))
