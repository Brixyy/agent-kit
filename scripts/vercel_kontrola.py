"""Kontrola Vercelu: projekty nasazují jen produkci z main, náhledy jsou vypnuté (agent-kit#25).

Použití: python -I <agent-kit>/scripts/vercel_kontrola.py [složka projektu ...]
Bez argumentu projde všechny projekty ve složce, kde leží klon repozitáře agent-kit (Dev).
Čte lokální kopie projektů (aktualizuj je git pull) a každý nalezený vercel.json; Vercel
přitom čte jen ten v Root Directory projektu.

Projekt s Vercelem = má vercel.json (v kořeni nebo podsložce) nebo složku .vercel.
- CHYBA: náhledy nejsou ve vercel.json vypnuté (git.deploymentEnabled). Vzor „*“ nestačí,
  větve s lomítkem (claude/…) chytí jen „**“ (minimatch).
- VAROVÁNÍ: produkce z main se staví při každém push a vercel.json nemá ignoreCommand
  (Ignored Build Step může být nastavený v projektu na Vercelu, to skript nevidí).
Konec s kódem 1, když je aspoň jedna CHYBA.
"""
import json
import os
import subprocess
import sys

PRODUKCE = ("main", "master")
PRESKOCIT = {"node_modules", ".git", ".claude", ".next", "dist", "build", ".venv", "venv"}
HLOUBKA = 2


def dev_slozka():
    """Složka projektů: rodič hlavního repozitáře agent-kit (funguje i z worktree)."""
    tady = os.path.dirname(os.path.abspath(__file__))
    vysledek = subprocess.run(["git", "-C", tady, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                              capture_output=True, text=True)
    if vysledek.returncode != 0:
        sys.exit("Skript neleží v klonu agent-kitu (např. cache pluginu): zadej složky projektů jako argumenty.")
    return os.path.dirname(os.path.dirname(vysledek.stdout.strip()))


def najdi_vercel_json(projekt):
    nalezene = []
    for koren, slozky, soubory in os.walk(projekt):
        hloubka = os.path.relpath(koren, projekt).count(os.sep) + (koren != projekt)
        slozky[:] = [s for s in slozky if s not in PRESKOCIT and hloubka < HLOUBKA]
        if "vercel.json" in soubory:
            nalezene.append(os.path.join(koren, "vercel.json"))
    return nalezene


def zkontroluj_soubor(cesta):
    """Vrátí seznam (úroveň, text) pro jeden vercel.json."""
    try:
        with open(cesta, encoding="utf-8-sig") as f:  # -sig: soubory z PowerShellu mívají BOM
            nastaveni = json.load(f)
    except (OSError, ValueError) as chyba:
        return [("CHYBA", f"vercel.json nejde přečíst: {chyba}")]
    git = nastaveni.get("git") or {}
    povoleno = git.get("deploymentEnabled", None)
    if povoleno is False or (nastaveni.get("github") or {}).get("enabled") is False:
        return [("OK", "Git nasazení vypnutá (nasazuje se jinak, náhledy nevznikají)")]
    vzor = '({"main": true, "*": false, "**": false})'
    if povoleno is True:
        return [("CHYBA", f"git.deploymentEnabled je true, nasazuje každou větev jako náhled {vzor}")]
    if not isinstance(povoleno, dict):
        return [("CHYBA", f"náhledy nejsou vypnuté: chybí git.deploymentEnabled {vzor}")]
    # Vercel větev nasadí, když ji povolí aspoň jedno pravidlo; „**“ chytí i větve s lomítkem.
    vysledek = [("CHYBA", f'pravidlo "{vetev}": true nasazuje náhledy') for vetev, hodnota in povoleno.items()
                if hodnota is True and vetev not in PRODUKCE]
    if povoleno.get("**") is not False:
        vysledek.append(("CHYBA", 'náhledy větví nejsou vypnuté: chybí "**": false v git.deploymentEnabled '
                                  "(samotné „*“ nechytí větve s lomítkem, claude/…)"))
    if not any(povoleno.get(vetev) is True for vetev in PRODUKCE):
        vysledek.append(("VAROVÁNÍ", 'chybí "main": true, z Gitu se nenasadí ani produkce'))
    elif not nastaveni.get("ignoreCommand"):
        vysledek.append(("VAROVÁNÍ", "chybí ignoreCommand: produkce se staví při každém push do main; "
                                     "nastav Ignored Build Step (změna frontendu), ve vercel.json nebo na Vercelu"))
    return vysledek or [("OK", "jen produkce z main, build jen při změně")]


def zkontroluj_projekt(projekt):
    """Vrátí None (projekt bez Vercelu) nebo seznam (úroveň, text)."""
    soubory = najdi_vercel_json(projekt)
    if not soubory:
        if os.path.isdir(os.path.join(projekt, ".vercel")):
            return [("CHYBA", "projekt je napojený na Vercel (.vercel), ale nemá vercel.json s vypnutými náhledy")]
        return None
    vysledek = []
    for cesta in soubory:
        relativni = os.path.relpath(cesta, projekt).replace(os.sep, "/")
        vysledek += [(uroven, f"{relativni}: {text}") for uroven, text in zkontroluj_soubor(cesta)]
    return vysledek


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if argv:
        projekty = argv
    else:
        dev = dev_slozka()
        projekty = [os.path.join(dev, d) for d in sorted(os.listdir(dev))
                    if os.path.isdir(os.path.join(dev, d)) and not d.startswith((".", "_"))]
    chyby = 0
    for projekt in projekty:
        vysledek = zkontroluj_projekt(projekt)
        if vysledek is None:
            continue
        print(os.path.basename(os.path.normpath(projekt)))
        for uroven, text in vysledek:
            chyby += uroven == "CHYBA"
            print(f"  {uroven:9}{text}")
    print("VŠE OK" if not chyby else f"{chyby} CHYB")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
