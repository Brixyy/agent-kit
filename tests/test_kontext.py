"""Test vkládaných pravidel: python -I tests/test_kontext.py

Claude Code vloží z hooku nejvýš 10 000 znaků; delší text nahradí náhledem prvních 2 000
a zbytek agent neuvidí (29. 10. 2026 tak zapadlo pravidlo o vykreslování diagramů).
Jádro pravidel proto musí zůstat pod limitem s rezervou, lokálně (hook) i v cloudu.
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOREN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIMIT = 10_000  # https://code.claude.com/docs/en/hooks (additionalContext a stdout)
REZERVA = 9_000
CLOUD_HLAVICKA = 600  # úvodní řádky, odkaz na podrobnosti a na výtah o uživateli z cloud-bootstrap.sh

vystup = subprocess.run(
    [sys.executable, "-I", os.path.join(KOREN, "hooks", "kontext.py")],
    capture_output=True, text=True, encoding="utf-8", check=True,
).stdout
text = json.loads(vystup)["hookSpecificOutput"]["additionalContext"]
with open(os.path.join(KOREN, "global", "AGENTS.md"), encoding="utf-8") as f:
    jadro = f.read()

chyby = 0
for nazev, ok in [
    (f"hook vloží {len(text)} znaků, rezerva {REZERVA}", len(text) <= REZERVA),
    (f"cloud vypíše asi {len(jadro) + CLOUD_HLAVICKA} znaků, limit {LIMIT}", len(jadro) + CLOUD_HLAVICKA <= LIMIT),
    ("hook předá cestu k podrobnostem, soubor existuje",
     "PODROBNOSTI.md" in text and os.path.isfile(os.path.join(KOREN, "global", "PODROBNOSTI.md"))),
    ("pravidlo o vykreslování diagramů je v jádru", "vykresli jako obrázek" in jadro),
    # 20. 11. 2026: pod-session 2,5 h stála na „čekám na doběhnutí testů“
    ("pravidlo „žádné čekám bez budíku“ je v podrobnostech i ve skillu koordinátora",
     "čekám“ bez budíku" in open(os.path.join(KOREN, "global", "PODROBNOSTI.md"), encoding="utf-8").read()
     and "čekám bez budíku" in open(os.path.join(KOREN, "skills", "koordinator", "SKILL.md"), encoding="utf-8").read()),
]:
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev)

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
