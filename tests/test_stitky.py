"""Test jednotných štítků: python -I tests/test_stitky.py (bez sítě, smyšlené repozitáře)."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
KOREN = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(KOREN, "scripts"))
import stitky  # noqa: E402

chyby = 0


def over(nazev, ok):
    global chyby
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev)


# prázdný repozitář: založí všechny standardní štítky
kroky = stitky.plan([])
over("prázdné repo založí všechny standardní štítky",
     {j for a, j, _b, _p in kroky if a == "založit"} == set(stitky.STANDARD))

# repozitář se správnými štítky: nic
hotovo = [{"name": j, "color": b, "description": p} for j, (b, p) in stitky.STANDARD.items()]
over("srovnané repo je beze změny", stitky.plan(hotovo) == [])

# jiná barva a malá písmena v barvě
jine = [dict(s) for s in hotovo]
jine[0]["color"] = "ededed"
jine[1]["color"] = jine[1]["color"].lower()
kroky = stitky.plan(jine)
over("jiná barva se přebarví, malá písmena barvy ne",
     [(a, j) for a, j, _b, _p in kroky] == [("přebarvit", jine[0]["name"])])

# oblasti: přebarví na společnou barvu, popis zachová, cizí štítky nechá
cizi = hotovo + [
    {"name": "oblast: Blitz", "color": "123456", "description": "Fasády"},
    {"name": "oblast: CAD", "color": stitky.BARVA_OBLASTI, "description": ""},
    {"name": "pilíř: fond", "color": "2da44e", "description": ""},
    {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
]
kroky = stitky.plan(cizi)
over("oblast se přebarví a popis zůstane, cizí štítky nechá",
     kroky == [("přebarvit", "oblast: Blitz", stitky.BARVA_OBLASTI, "Fasády")])

# stavy mají navzájem různé barvy (barva sama říká stav)
barvy = [b for b, _p in stitky.STAVY.values()]
over("každý stav má jinou barvu", len(set(barvy)) == len(barvy))

# pravidlo je popsané v podrobnostech
with open(os.path.join(KOREN, "global", "PODROBNOSTI.md"), encoding="utf-8") as f:
    podrobnosti = f.read()
over("PODROBNOSTI mají oddíl o štítcích a odkaz na skript",
     "## Štítky issues" in podrobnosti and "scripts/stitky.py" in podrobnosti
     and all(f"`{j}`" in podrobnosti for j in stitky.STAVY))

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
