"""Test jednotných štítků: python -I tests/test_stitky.py (bez sítě, podvržené gh)."""
import json
import os
import subprocess
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


def akce(kroky):
    return [(a, j) for a, j, _b, _p, _o in kroky]


# prázdný repozitář: založí všechny standardní štítky
kroky = stitky.plan([])
over("prázdné repo založí všechny standardní štítky",
     {j for a, j, *_ in kroky if a == "založit"} == set(stitky.STANDARD))

# repozitář se správnými štítky: nic
hotovo = [{"name": j, "color": b, "description": p} for j, (b, p) in stitky.STANDARD.items()]
over("srovnané repo je beze změny", stitky.plan(hotovo) == [])

# jiná barva a malá písmena v barvě; úprava nese původní hodnoty
jine = [dict(s) for s in hotovo]
jine[0]["color"] = "ededed"
jine[1]["color"] = jine[1]["color"].lower()
kroky = stitky.plan(jine)
over("jiná barva se upraví, malá písmena barvy ne",
     akce(kroky) == [("upravit", jine[0]["name"])] and kroky[0][4] == ("ededed", jine[0]["description"]))

# oblasti: přebarví na společnou barvu, popis zachová; cizí štítek v barvě stavu = varování
cizi = hotovo + [
    {"name": "oblast: Blitz", "color": "123456", "description": "Fasády"},
    {"name": "oblast: CAD", "color": stitky.BARVA_OBLASTI, "description": ""},
    {"name": "pilíř: fond", "color": "2da44e", "description": ""},
    {"name": "podnět", "color": "1d76db", "description": ""},
    {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
]
kroky = stitky.plan(cizi)
over("oblast se upraví s popisem, cizí štítek v barvě stavu je jen varování, anglický se smaže",
     akce(kroky) == [("upravit", "oblast: Blitz"), ("varování", "podnět"), ("smazat", "bug")]
     and kroky[0][2:4] == (stitky.BARVA_OBLASTI, "Fasády"))

# mazat se smí jen výchozí anglické štítky GitHubu, nikdy standardní ani vlastní štítek projektu
over("SMAZAT neobsahuje standardní štítky", not (stitky.SMAZAT & set(stitky.STANDARD)))
over("vlastní štítky projektu se nemažou",
     not [k for k in stitky.plan(hotovo + [{"name": "odloženo", "color": "C5A06A", "description": ""}])
          if k[0] == "smazat"])

# kontrola stavu: právě jeden štítek stavu
issues = [
    {"number": 1, "title": "ok", "labels": [{"name": "k práci"}, {"name": "oblast: CAD"}]},
    {"number": 2, "title": "bez", "labels": [{"name": "riziko: nízké"}]},
    {"number": 3, "title": "dva", "labels": [{"name": "rozpracováno"}, {"name": "čeká na zákazníka"}]},
]
over("kontrola najde issue bez stavu a s víc stavy",
     [(c, s) for c, _n, s in stitky.chybny_stav(issues)] == [(2, []), (3, ["rozpracováno", "čeká na zákazníka"])])

# stavy mají navzájem různé barvy (barva sama říká stav)
barvy = [b for b, _p in stitky.STAVY.values()]
over("každý stav má jinou barvu", len(set(barvy)) == len(barvy))

# podvržené gh: skript volá jen list a create --force, nanečisto nic nezapisuje
volani = []


def falesne_gh(*args):
    volani.append(args)
    if args[:2] == ("label", "list"):
        return json.dumps([{"name": "podnět", "color": "1D76DB", "description": ""}])
    if args[:2] == ("repo", "list"):
        return json.dumps([
            {"name": "a", "isArchived": False, "hasIssuesEnabled": True},
            {"name": "robotika", "isArchived": False, "hasIssuesEnabled": True},
            {"name": "stare", "isArchived": True, "hasIssuesEnabled": True},
        ])
    if args[:2] == ("issue", "list"):
        return json.dumps([{"number": 7, "title": "x", "labels": []}])
    return ""


stitky._gh = falesne_gh
stitky.srovnej("a", nanecisto=True)
over("nanečisto jen čte", all(v[:2] == ("label", "list") for v in volani))
volani.clear()
stitky.srovnej("a", nanecisto=False)
zapisy = [v for v in volani if v[:2] != ("label", "list")]
over("ostrý běh zakládá s --force, vlastní štítek nemaže ani nepřejmenuje",
     len(zapisy) == len(stitky.STANDARD)
     and all(v[:2] == ("label", "create") and "--force" in v and "--name" not in v for v in zapisy)
     and not any("delete" in v for v in volani))
over("výčet repozitářů zahrne robotiku, vynechá archivované", stitky.repozitare() == ["a", "robotika"])
volani.clear()
over("--kontrola jen čte a s nálezem vrátí 1",
     stitky.main(["a", "--kontrola"]) == 1 and all(v[:2] == ("issue", "list") for v in volani))


def gh_s_anglickym(*args):
    volani.append(args)
    if args[:2] == ("label", "list"):
        return json.dumps(hotovo + [{"name": "wontfix", "color": "ffffff", "description": ""}])
    return ""


stitky._gh = gh_s_anglickym
volani.clear()
stitky.srovnej("a", nanecisto=True)
over("nanečisto anglický štítek nesmaže", not any(v[:2] == ("label", "delete") for v in volani))
stitky.srovnej("a", nanecisto=False)
over("ostrý běh smaže anglický štítek s --yes",
     [v for v in volani if v[:2] == ("label", "delete")] == [("label", "delete", "wontfix", "--yes", "-R", "Brixyy/a")])


def padajici_gh(*args):
    raise subprocess.CalledProcessError(1, ["gh", *args], stderr="HTTP 403")


stitky._gh = padajici_gh
over("chyba gh u repozitáře se vypíše a vrátí kód 1", stitky.main(["x", "y"]) == 1)

# pravidlo je popsané v podrobnostech
with open(os.path.join(KOREN, "global", "PODROBNOSTI.md"), encoding="utf-8") as f:
    podrobnosti = f.read()
over("PODROBNOSTI mají oddíl o štítcích a odkaz na skript",
     "## Štítky issues" in podrobnosti and "scripts/stitky.py" in podrobnosti
     and all(f"`{j}`" in podrobnosti for j in stitky.STAVY))

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
