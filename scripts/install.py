"""Nainstaluje agent-kit na tento počítač pro agenty mimo Claude Code (Codex a další).

Použití (z kořene agent-kitu): python -I scripts/install.py
- globální pravidla  global/AGENTS.md → ~/.agents/AGENTS.md a ~/.codex/AGENTS.md
- skills             skills/*         → ~/.agents/skills/ (sdílené umístění pro Codex a další agenty)
- pojistka           hooks/pojistka.py → ~/.agents/hooks/pojistka.py + PreToolUse v ~/.codex/hooks.json
Claude Code dostává totéž přes plugin agent-kit@agent-kit (marketplace Brixyy/agent-kit).
Existující soubory s jiným obsahem nejdřív zazálohuje jako *.bak. Opakované spuštění je bezpečné.
"""
import filecmp
import json
import os
import shutil
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
AGENTS = os.path.join(HOME, ".agents")
CODEX = os.path.join(HOME, ".codex")


def kopiruj(zdroj, cil):
    os.makedirs(os.path.dirname(cil), exist_ok=True)
    if os.path.exists(cil) and not filecmp.cmp(zdroj, cil, shallow=False) and os.path.getsize(cil) > 0:
        shutil.copy2(cil, cil + ".bak")
    shutil.copy2(zdroj, cil)
    print("  ", cil)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Globální pravidla:")
    kopiruj(os.path.join(KIT, "global", "AGENTS.md"), os.path.join(AGENTS, "AGENTS.md"))
    if os.path.isdir(CODEX):
        kopiruj(os.path.join(KIT, "global", "AGENTS.md"), os.path.join(CODEX, "AGENTS.md"))

    print("Skills:")
    for nazev in sorted(os.listdir(os.path.join(KIT, "skills"))):
        cil = os.path.join(AGENTS, "skills", nazev)
        shutil.copytree(os.path.join(KIT, "skills", nazev), cil, dirs_exist_ok=True)
        print("  ", cil)

    print("Pojistka:")
    pojistka = os.path.join(AGENTS, "hooks", "pojistka.py")
    kopiruj(os.path.join(KIT, "hooks", "pojistka.py"), pojistka)
    if os.path.isdir(CODEX):
        cesta = os.path.join(CODEX, "hooks.json")
        try:
            with open(cesta, encoding="utf-8") as f:
                nastaveni = json.load(f)
        except (OSError, ValueError):
            nastaveni = {}
        prikaz = f'python -I "{pojistka}" --exit-code'
        skupiny = nastaveni.setdefault("hooks", {}).setdefault("PreToolUse", [])
        if not any("pojistka.py" in json.dumps(s) for s in skupiny):
            skupiny.append({"matcher": ".*", "hooks": [{"type": "command", "command": prikaz, "timeout": 10}]})
            with open(cesta, "w", encoding="utf-8", newline="\n") as f:
                json.dump(nastaveni, f, ensure_ascii=False, indent=2)
                f.write("\n")
        print("  ", cesta, "(Codex se při dalším spuštění zeptá, jestli hooku důvěřuje)")
    print("Hotovo. Claude Code: plugin agent-kit@agent-kit.")


main()
