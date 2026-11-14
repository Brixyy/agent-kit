"""Stop: delší závěrečná zpráva musí začínat rámečkem „Pro tebe“ (output style `pro-tebe`).

Uživatel 14. 11. 2026 (Brixyy/agent-kit#31): v session je moc obsahu a část „pro mě“ zapadne.
Jen když je zapnutý styl STYL: zprávu delší než LIMIT znaků bez rámečku vrátí jednou agentovi,
aby rámeček doplnil (bez opakování podrobností). Zpráva začínající kódem nebo JSON projde.
Podruhé (stop_hook_active) už pustí, aby se agent nezacyklil. Při jakékoli chybě pustí.
Test: python -I tests/test_pro_tebe.py
"""
import json
import os
import sys

LIMIT = 500  # kratší odpověď (krátká otázka, potvrzení) rámeček nepotřebuje
STYL = "agent-kit:Pro tebe"  # hodnota outputStyle; jinde (cloudové rutiny, jiný styl) hook nic nevynucuje

DUVOD = (
    "Závěrečná zpráva nezačíná rámečkem „Pro tebe“. "
    "Napiš teď jen krátký doplněk: první řádek `> <🟢|🟠|🔴|🔵> **Pro tebe:** …` (co má uživatel udělat, rozhodnout "
    "nebo vědět, nejvýš 3 body; když nic: `> 🟢 **Pro tebe:** nic, běží to samo.`). Podrobnosti neopakuj, "
    "jsou výše. Nic dalšího nedělej."
)


def aktivni_styl(cwd):
    """outputStyle podle priority nastavení: projekt lokální > projekt > uživatel."""
    soubory = []
    if cwd:
        soubory += [os.path.join(cwd, ".claude", "settings.local.json"), os.path.join(cwd, ".claude", "settings.json")]
    soubory.append(os.path.join(os.path.expanduser("~"), ".claude", "settings.json"))
    for cesta in soubory:
        try:
            with open(cesta, encoding="utf-8") as f:
                hodnota = json.load(f).get("outputStyle")
        except Exception:
            continue
        if hodnota:
            return hodnota
    return None


def ma_ramecek(text):
    for radek in text.splitlines():
        radek = radek.strip()
        if radek:
            return "Pro tebe" in radek or radek.startswith(("```", "{", "["))
    return False


def rozhodni(vstup, styl=None):
    if vstup.get("stop_hook_active") or styl != STYL:
        return None
    zprava = vstup.get("last_assistant_message")
    if not isinstance(zprava, str) or len(zprava) < LIMIT or ma_ramecek(zprava):
        return None
    return {"decision": "block", "reason": DUVOD}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        vstup = json.load(sys.stdin)
        vysledek = rozhodni(vstup, aktivni_styl(vstup.get("cwd")))
        if vysledek:
            print(json.dumps(vysledek, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)
