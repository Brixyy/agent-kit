"""Kontrola Vercelu: projekty nasazují jen produkci z main, náhledy jsou vypnuté (agent-kit#25, #53).

Použití: python -I <agent-kit>/scripts/vercel_kontrola.py [složka projektu ...]
         python -I <agent-kit>/scripts/vercel_kontrola.py --dnes
Bez argumentu projde všechny projekty ve složce, kde leží klon repozitáře agent-kit (Dev),
a všechny projekty na účtu Vercelu (přihlášené vercel CLI, jinak přes npx): u napojeného
repozitáře čte vercel.json v Root Directory přes gh api a nastavení projektu na Vercelu
(Root Directory, Ignored Build Step, produkční větev).
Se složkami jako argumenty čte jen jejich lokální kopie (aktualizuj je git pull) a každý
nalezený vercel.json; Vercel přitom čte jen ten v Root Directory projektu.
--dnes: počet nasazení na účtu za posledních 24 h po projektech a stavech
(od 60 VAROVÁNÍ, od 85 CHYBA s kódem 1; limit plánu Hobby je 100 za 24 h).

Projekt s Vercelem = má vercel.json (v kořeni nebo podsložce) nebo složku .vercel.
- CHYBA: náhledy nejsou ve vercel.json vypnuté (git.deploymentEnabled). Vzor „*“ nestačí,
  větve s lomítkem (claude/…) chytí jen „**“ (minimatch).
- VAROVÁNÍ: produkce z main se staví při každém push a chybí ignoreCommand (lokálně skript
  nastavení projektu na Vercelu nevidí, u účtu ano).
- NEOVĚŘENO: chybí přihlášení nebo přístup (vercel, gh); není to OK.
Konec s kódem 1, když je aspoň jedna CHYBA nebo NEOVĚŘENO.
"""
import collections
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

PRODUKCE = ("main", "master")
PRESKOCIT = {"node_modules", ".git", ".claude", ".next", "dist", "build", ".venv", "venv"}
HLOUBKA = 2
LIMIT_VAROVANI, LIMIT_CHYBA, LIMIT_UCTU = 60, 85, 100
DEN = 86400


class Neovereno(Exception):
    """Nástroj chybí, není přihlášený nebo nemá přístup."""


def spust(prikaz):
    """Spustí příkaz, vrátí (kód, stdout, stderr). V testech se nahrazuje."""
    try:
        v = subprocess.run(prikaz, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    except (OSError, subprocess.TimeoutExpired) as chyba:
        return 127, "", str(chyba)
    return v.returncode, v.stdout, v.stderr


def posledni_radek(text):
    return (text.strip().splitlines() or ["neznámá chyba"])[-1]


def vercel_prikaz():
    """Přihlášené vercel CLI (přihlášení sdílí i spuštění přes npx). Na Windows vždy přes npx.cmd:
    escapování pro cmd.exe je ověřené jen pro něj."""
    vercel = shutil.which("vercel")
    if vercel and os.name != "nt":
        return [vercel]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "vercel"]
    raise Neovereno("chybí vercel CLI i npx")


def vercel_api(cesta):
    prikaz = vercel_prikaz()
    # Na Windows jde npx.cmd přes cmd.exe dvakrát (příkazová řádka a %* uvnitř), „&“ by dělil příkaz.
    cesta_arg = cesta.replace("&", "^^^&") if prikaz[0].lower().endswith(".cmd") else cesta
    kod, vystup, chyba = spust(prikaz + ["api", cesta_arg, "--raw"])
    if kod != 0:
        raise Neovereno(f"vercel api {cesta.split('?')[0]}: {posledni_radek(chyba)} (přihlášení: vercel login)")
    try:
        return json.loads(vystup)
    except ValueError:
        raise Neovereno(f"vercel api {cesta.split('?')[0]}: odpověď není JSON")


def gh_soubor(vlastnik, repozitar, cesta, vetev):
    """Obsah souboru z GitHubu, None když neexistuje."""
    kod, vystup, chyba = spust(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                                f"repos/{vlastnik}/{repozitar}/contents/{cesta}?ref={vetev}"])
    if kod == 0:
        return vystup
    if "HTTP 404" in chyba:
        # 404 vrací GitHub i u repozitáře bez přístupu nebo chybějící větve: soubor chybí, jen když větev vidíme.
        if spust(["gh", "api", f"repos/{vlastnik}/{repozitar}/branches/{vetev}", "--jq", ".name"])[0] == 0:
            return None
        raise Neovereno(f"gh api {vlastnik}/{repozitar}: repozitář nebo větev {vetev} nedostupná")
    raise Neovereno(f"gh api {vlastnik}/{repozitar}: {posledni_radek(chyba)}")


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
    return zkontroluj_nastaveni(nastaveni)


def zkontroluj_nastaveni(nastaveni, ignore_na_vercelu=False):
    """Kontrola obsahu vercel.json; ignore_na_vercelu = Ignored Build Step je v nastavení projektu."""
    if not isinstance(nastaveni, dict):
        return [("CHYBA", "vercel.json není objekt")]
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
    elif not nastaveni.get("ignoreCommand") and not ignore_na_vercelu:
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


def zkontroluj_projekt_uctu(projekt):
    """Projekt z /v9/projects: nastavení na Vercelu + vercel.json v Root Directory na GitHubu."""
    odkaz = projekt.get("link") or {}
    if not odkaz:
        return [("OK", "bez napojeného repozitáře: z Gitu se nenasazuje")]
    if odkaz.get("type") != "github":
        return [("NEOVĚŘENO", f"repozitář na {odkaz.get('type')}, skript umí jen GitHub")]
    vetev = odkaz.get("productionBranch") or "main"
    vysledek = []
    if vetev not in PRODUKCE:
        vysledek.append(("VAROVÁNÍ", f"produkční větev je {vetev}, ne main"))
    koren = (projekt.get("rootDirectory") or "").strip("/")
    cesta = f"{koren}/vercel.json" if koren else "vercel.json"
    zdroj = f"{odkaz.get('org')}/{odkaz.get('repo')}:{cesta}"
    try:
        obsah = gh_soubor(odkaz.get("org"), odkaz.get("repo"), cesta, vetev)
    except Neovereno as chyba:
        return vysledek + [("NEOVĚŘENO", str(chyba))]
    if obsah is None:
        return vysledek + [("CHYBA", f"{zdroj} chybí: náhledy nejsou vypnuté (Vercel čte vercel.json v Root Directory)")]
    try:
        nastaveni = json.loads(obsah.lstrip("﻿"))
    except ValueError as chyba:
        return vysledek + [("CHYBA", f"{zdroj} nejde přečíst: {chyba}")]
    ignore = bool(projekt.get("commandForIgnoringBuildStep"))
    return vysledek + [(uroven, f"{zdroj}: {text}") for uroven, text in zkontroluj_nastaveni(nastaveni, ignore)]


def zkontroluj_ucet():
    """Vrátí seznam (název, výsledky) pro všechny projekty na účtu Vercelu."""
    try:
        odpoved = vercel_api("/v9/projects?limit=100")
    except Neovereno as chyba:
        return [("účet Vercelu", [("NEOVĚŘENO", str(chyba))])]
    projekty = sorted(odpoved.get("projects") or [], key=lambda p: p.get("name", ""))
    vysledek = [(p.get("name", "?"), zkontroluj_projekt_uctu(p)) for p in projekty]
    if (odpoved.get("pagination") or {}).get("next"):
        vysledek.append(("účet Vercelu", [("NEOVĚŘENO", "víc než 100 projektů, zbytek skript neprošel")]))
    return vysledek


def cas(nasazeni):
    return nasazeni.get("created") or nasazeni.get("createdAt") or 0


def nasazeni_za_den(ted):
    """Nasazení na účtu za posledních 24 h (stránkuje po 100, od nejnovějších)."""
    od = int((ted - DEN) * 1000)
    nasazeni, do = [], None
    while True:
        odpoved = vercel_api(f"/v6/deployments?since={od}&limit=100" + (f"&until={do}" if do else ""))
        stranka = odpoved.get("deployments") or []
        nasazeni += [n for n in stranka if cas(n) >= od]
        dalsi = (odpoved.get("pagination") or {}).get("next")
        if not dalsi or not stranka or min(cas(n) for n in stranka) < od:
            return nasazeni
        if do is not None and dalsi >= do:
            raise Neovereno("vercel api /v6/deployments: stránkování se nehýbe")
        do = dalsi


def dnes(ted=None):
    ted = time.time() if ted is None else ted
    try:
        nasazeni = nasazeni_za_den(ted)
    except Neovereno as chyba:
        print(f"NEOVĚŘENO {chyba}")
        return 1
    pocty = collections.defaultdict(collections.Counter)
    for n in nasazeni:
        druh = "produkce" if n.get("target") == "production" else "náhled"
        pocty[n.get("name", "?")][(druh, n.get("state") or n.get("readyState") or "?")] += 1
    print(f"Nasazení na účtu Vercelu za posledních 24 h (limit {LIMIT_UCTU}; počítají se i zrušená, pozorováno 19. 11. 2026):")
    for nazev in sorted(pocty, key=lambda k: (-sum(pocty[k].values()), k)):
        rozpis = " · ".join(f"{druh} {stav} {pocet}" for (druh, stav), pocet in sorted(pocty[nazev].items()))
        print(f"  {nazev:20}{sum(pocty[nazev].values()):4}   {rozpis}")
    celkem = len(nasazeni)
    print(f"  {'celkem':20}{celkem:4}")
    if celkem < LIMIT_VAROVANI:
        print("OK")
        return 0
    uvolni = datetime.datetime.fromtimestamp(min(cas(n) for n in nasazeni) / 1000 + DEN).strftime("%d. %m. %H:%M")
    uroven = "CHYBA" if celkem >= LIMIT_CHYBA else "VAROVÁNÍ"
    print(f"{uroven}: {celkem} z {LIMIT_UCTU}. PR se změnou frontendu slučuj po dávkách, ne po jednom; "
          f"nejstarší nasazení vypadne z 24h okna {uvolni}.")
    return 1 if uroven == "CHYBA" else 0


def vypis(nazev, vysledek):
    print(nazev)
    for uroven, text in vysledek:
        print(f"  {uroven:11}{text}")
    return sum(uroven in ("CHYBA", "NEOVĚŘENO") for uroven, _ in vysledek)


def main(argv):
    if argv == ["--dnes"]:
        return dnes()
    spatne = [a for a in argv if a.startswith("-") or not os.path.isdir(a)]
    if spatne:
        print("Neznámý přepínač nebo neexistující složka: " + " ".join(spatne))
        print("\n".join(__doc__.splitlines()[2:4]))
        return 2
    if argv:
        projekty = argv
    else:
        dev = dev_slozka()
        projekty = [os.path.join(dev, d) for d in sorted(os.listdir(dev))
                    if os.path.isdir(os.path.join(dev, d)) and not d.startswith((".", "_"))]
    chyby = 0
    for projekt in projekty:
        vysledek = zkontroluj_projekt(projekt)
        if vysledek is not None:
            chyby += vypis(os.path.basename(os.path.normpath(projekt)), vysledek)
    if not argv:
        print("\nÚčet Vercelu (nastavení projektů a vercel.json na GitHubu):")
        for nazev, vysledek in zkontroluj_ucet():
            chyby += vypis(nazev, vysledek)
    print("VŠE OK" if not chyby else f"{chyby} CHYB nebo NEOVĚŘENO")
    return 1 if chyby else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
