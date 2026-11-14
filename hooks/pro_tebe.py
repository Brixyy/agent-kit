"""Stop: delší závěrečná zpráva musí začínat rámečkem „Pro tebe“ (output style `pro-tebe`).

Uživatel 14. 11. 2026 (Brixyy/agent-kit#31): v session je moc obsahu a část „pro mě“ zapadne.
Když zpráva delší než LIMIT znaků nezačíná rámečkem, hook ji jednou vrátí agentovi k přepsání.
Podruhé (stop_hook_active) už pustí, aby se agent nezacyklil. Při jakékoli chybě pustí.
Test: python -I tests/test_pro_tebe.py
"""
import json
import sys

LIMIT = 500  # kratší odpověď (krátká otázka, potvrzení) rámeček nepotřebuje

DUVOD = (
    "Závěrečná zpráva nezačíná rámečkem „Pro tebe“. Napiš ji znovu ve tvaru stylu „Pro tebe“: "
    "první řádek `> 📌 **Pro tebe:** …` (co má uživatel udělat, rozhodnout nebo vědět, nejvýš 3 body; "
    "když nic: `> ✅ **Pro tebe:** nic, běží to samo.`), pod ním čára `---` a pod ní „ℹ️ Pro informaci“ "
    "s podrobnostmi. Obsah neměň, jen tvar; nic dalšího nedělej."
)


def ma_ramecek(text):
    for radek in text.splitlines():
        radek = radek.strip()
        if radek:
            return "Pro tebe" in radek
    return False


def rozhodni(vstup):
    if vstup.get("stop_hook_active"):
        return None
    zprava = vstup.get("last_assistant_message")
    if not isinstance(zprava, str) or len(zprava) < LIMIT or ma_ramecek(zprava):
        return None
    return {"decision": "block", "reason": DUVOD}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        vysledek = rozhodni(json.load(sys.stdin))
        if vysledek:
            print(json.dumps(vysledek, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)
