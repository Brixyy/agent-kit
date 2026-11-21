"""Jednotné štítky issues napříč repozitáři Brixyy: python -I scripts/stitky.py [repo ...]

Bez argumentu srovná všechny nearchivované repozitáře účtu s Issues (kromě VYNECHAT).
Standardní štítky zakládá a upravuje barvu a popis (jméno se nemění); u úpravy vypíše původní
hodnoty, aby šla vrátit. Maže jen výchozí anglické štítky GitHubu (SMAZAT, uživatel 21. 11. 2026).
`--nanecisto` jen vypíše plán. `--kontrola` nic nemění a vypíše otevřená issues, která nemají
právě jeden štítek stavu (návratový kód 1, když nějaké najde).
Pravidlo a význam štítků: global/PODROBNOSTI.md, oddíl „Štítky issues“.
"""
import json
import subprocess
import sys

UCET = "Brixyy"
# Úkoly mají jinde (robotika → Linear), štítky issues se tam nesrovnávají.
VYNECHAT = {"robotika"}

# Stav: každé otevřené issue má právě jeden.
STAVY = {
    "k práci": ("BFDADC", "Zadáno a připraveno, čeká ve frontě na zpracování"),
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
    "priorita": ("E4572E", "Další na řadě (pořadí práce)"),
    "naléhavé": ("B60205", "Má přednost před štítkem priorita"),
    "nesloučit": ("B60205", "PR se nesmí sloučit, dokud podmínka v popisu neplatí"),
    "riziko: nízké": ("C2E0C6", "Změna s nízkým rizikem"),
    "riziko: střední": ("FEF2C0", "Změna se středním rizikem"),
    "riziko: vysoké": ("F9D0C4", "Změna s vysokým rizikem"),
    "audit-projektu": ("5D6B7A", "Souhrnné issue auditu projektu (skill audit, 1. a 15. v měsíci)"),
}
STANDARD = {**STAVY, **OSTATNI}
# Oblast: názvy si určuje projekt („oblast: …“), barva je společná.
PREDPONA_OBLASTI = "oblast:"
BARVA_OBLASTI = "0E8A16"
VYHRAZENE_BARVY = {b for b, _p in STAVY.values()} | {BARVA_OBLASTI}
# Výchozí anglické štítky GitHubu: nahrazuje je český základ, mažou se.
SMAZAT = {"bug", "documentation", "duplicate", "enhancement", "good first issue", "help wanted",
          "invalid", "question", "wontfix", "accessibility"}


def plan(existujici):
    """Kroky (akce, jméno, barva, popis, původní) pro štítky repozitáře.

    akce = založit / upravit / smazat / varování; „původní“ je (barva, popis) před úpravou nebo
    smazáním, u varování vlastní štítek projektu v barvě vyhrazené stavu nebo oblasti (nic se
    s ním nedělá)."""
    podle_jmena = {s["name"]: s for s in existujici}
    kroky = []
    for jmeno, (barva, popis) in STANDARD.items():
        stary = podle_jmena.get(jmeno)
        if stary is None:
            kroky.append(("založit", jmeno, barva, popis, None))
        elif stary["color"].upper() != barva or (stary.get("description") or "") != popis:
            kroky.append(("upravit", jmeno, barva, popis, (stary["color"], stary.get("description") or "")))
    for jmeno, stary in podle_jmena.items():
        barva = stary["color"].upper()
        if jmeno in SMAZAT:
            kroky.append(("smazat", jmeno, None, None, (stary["color"], stary.get("description") or "")))
        elif jmeno.startswith(PREDPONA_OBLASTI):
            if barva != BARVA_OBLASTI:
                popis = stary.get("description") or ""
                kroky.append(("upravit", jmeno, BARVA_OBLASTI, popis, (stary["color"], popis)))
        elif jmeno not in STANDARD and barva in VYHRAZENE_BARVY:
            kroky.append(("varování", jmeno, barva, stary.get("description") or "", None))
    return kroky


def _gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def repozitare():
    data = json.loads(_gh("repo", "list", UCET, "--limit", "200", "--json", "name,isArchived,hasIssuesEnabled"))
    return sorted(r["name"] for r in data
                  if r["hasIssuesEnabled"] and not r["isArchived"] and r["name"] not in VYNECHAT)


def srovnej(repo, nanecisto):
    existujici = json.loads(_gh("label", "list", "-R", f"{UCET}/{repo}", "--limit", "200",
                                "--json", "name,color,description"))
    kroky = plan(existujici)
    for akce, jmeno, barva, popis, puvodni in kroky:
        if akce == "varování":
            print(f"{repo}: varování „{jmeno}“ #{barva} má barvu vyhrazenou stavu nebo oblasti, přebarvi ho v projektu")
            continue
        if akce == "smazat":
            print(f"{repo}: smazat „{jmeno}“ #{puvodni[0]} „{puvodni[1]}“")
            if not nanecisto:
                _gh("label", "delete", jmeno, "--yes", "-R", f"{UCET}/{repo}")
            continue
        if akce == "upravit":
            print(f"{repo}: upravit „{jmeno}“ #{puvodni[0]} „{puvodni[1]}“ → #{barva} „{popis}“")
        else:
            print(f"{repo}: založit „{jmeno}“ #{barva}")
        if not nanecisto:
            _gh("label", "create", jmeno, "--color", barva, "--description", popis, "--force",
                "-R", f"{UCET}/{repo}")
    if not kroky:
        print(f"{repo}: beze změny")


def chybny_stav(issues):
    """Otevřená issues, která nemají právě jeden štítek stavu: [(číslo, název, [stavy])]."""
    vysledek = []
    for i in issues:
        stavy = [s["name"] for s in i["labels"] if s["name"] in STAVY]
        if len(stavy) != 1:
            vysledek.append((i["number"], i["title"], stavy))
    return vysledek


def zkontroluj(repo):
    """Vypíše otevřená issues bez právě jednoho stavu; vrátí jejich počet."""
    issues = json.loads(_gh("issue", "list", "-R", f"{UCET}/{repo}", "--state", "open", "--limit", "1000",
                            "--json", "number,title,labels"))
    spatne = chybny_stav(issues)
    for cislo, nazev, stavy in spatne:
        print(f"{repo}#{cislo} {'bez stavu' if not stavy else 'víc stavů: ' + ', '.join(stavy)} – {nazev}")
    if not spatne:
        print(f"{repo}: stavy v pořádku")
    return len(spatne)


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    nanecisto = "--nanecisto" in argv
    kontrola = "--kontrola" in argv
    repa = [a for a in argv if not a.startswith("--")] or repozitare()
    chyby = 0
    nalezy = 0
    for repo in repa:
        try:
            if kontrola:
                nalezy += zkontroluj(repo)
                continue
            srovnej(repo, nanecisto)
        except subprocess.CalledProcessError as e:
            chyby += 1
            print(f"{repo}: CHYBA gh: {(e.stderr or '').strip()}")
    return 1 if chyby or nalezy else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
