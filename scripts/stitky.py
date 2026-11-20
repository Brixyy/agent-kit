"""Jednotné štítky issues napříč repozitáři Brixyy: python -I scripts/stitky.py [repo ...]

Bez argumentu srovná všechny nearchivované repozitáře účtu s Issues. Štítky jen zakládá
a přebarvuje (jméno se nemění, nic se nemaže), takže je to vratné. `--nanecisto` jen vypíše plán.
Pravidlo a význam štítků: global/PODROBNOSTI.md, oddíl „Štítky issues“.
"""
import json
import subprocess
import sys

UCET = "Brixyy"

# Stav: každé otevřené issue má právě jeden.
STAVY = {
    "rozpracováno": ("1D76DB", "Agent na tom právě pracuje (session, PR)"),
    "čeká na uživatele": ("FBCA04", "Čeká na rozhodnutí nebo krok uživatele (otázka v komentáři)"),
    "čeká na zákazníka": ("D93F0B", "Čeká na podklad od zákazníka nebo jiné třetí strany"),
    "čeká na termín": ("C5DEF5", "Pokračuje až k danému datu"),
    "stálé": ("5319E7", "Stálé issue, zůstává otevřené záměrně (předávky, přehledy)"),
    "myšlenka": ("D4C5F9", "Nápad pro kontext, nic se nedělá bez zadání"),
    "pozastaveno": ("BFBFBF", "Téma je pozastavené, nepracuje se na něm"),
}
# Zvláštní štítky PR a issues, společné všem projektům.
OSTATNI = {
    "nesloučit": ("B60205", "PR se nesmí sloučit, dokud podmínka v popisu neplatí"),
    "riziko: nízké": ("C2E0C6", "Změna s nízkým rizikem"),
    "riziko: střední": ("FEF2C0", "Změna se středním rizikem"),
    "riziko: vysoké": ("F9D0C4", "Změna s vysokým rizikem"),
}
STANDARD = {**STAVY, **OSTATNI}
# Oblast: názvy si určuje projekt („oblast: …“), barva je společná.
PREDPONA_OBLASTI = "oblast:"
BARVA_OBLASTI = "0E8A16"


def plan(existujici):
    """Seznam (akce, jméno, barva, popis) pro štítky repozitáře; akce = založit / přebarvit."""
    podle_jmena = {s["name"]: s for s in existujici}
    kroky = []
    for jmeno, (barva, popis) in STANDARD.items():
        stary = podle_jmena.get(jmeno)
        if stary is None:
            kroky.append(("založit", jmeno, barva, popis))
        elif stary["color"].upper() != barva or (stary.get("description") or "") != popis:
            kroky.append(("přebarvit", jmeno, barva, popis))
    for jmeno, stary in podle_jmena.items():
        if jmeno.startswith(PREDPONA_OBLASTI) and stary["color"].upper() != BARVA_OBLASTI:
            kroky.append(("přebarvit", jmeno, BARVA_OBLASTI, stary.get("description") or ""))
    return kroky


def _gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def repozitare():
    data = json.loads(_gh("repo", "list", UCET, "--limit", "200", "--json", "name,isArchived,hasIssuesEnabled"))
    return sorted(r["name"] for r in data if r["hasIssuesEnabled"] and not r["isArchived"])


def srovnej(repo, nanecisto):
    existujici = json.loads(_gh("label", "list", "-R", f"{UCET}/{repo}", "--limit", "200",
                                "--json", "name,color,description"))
    kroky = plan(existujici)
    for akce, jmeno, barva, popis in kroky:
        print(f"{repo}: {akce} „{jmeno}“ #{barva}")
        if not nanecisto:
            _gh("label", "create", jmeno, "--color", barva, "--description", popis, "--force",
                "-R", f"{UCET}/{repo}")
    if not kroky:
        print(f"{repo}: beze změny")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    nanecisto = "--nanecisto" in argv
    repa = [a for a in argv if not a.startswith("--")] or repozitare()
    for repo in repa:
        srovnej(repo, nanecisto)


if __name__ == "__main__":
    main(sys.argv[1:])
