"""Úklid procesů a kontejnerů Dockeru, které po sobě nechaly sessions agentů (Windows).

Použití (bez --provest jen vypíše, co by ukončil):
  python -I scripts/uklid.py --sirotci [--provest]
      osiřelé dev servery: proces běží ze složky projektů (~/Dev), ale žádný jeho předek
      už není živá session (claude.exe, codex.exe) ani okno uživatele (terminál, editor, Průzkumník);
      kontejnery se štítkem agent-kit.slozka, jejichž složka už neexistuje.
  python -I scripts/uklid.py --slozka <pracovní složka> [--cli-pid <PID session>] [--provest]
      konec session: procesy, jejichž příkazová řádka nebo program je v dané složce a patří této
      session nebo už nikomu; kontejnery se štítkem agent-kit.slozka=<složka>.
Složku lze předat i proměnnou AGENT_KIT_UKLID_SLOZKA (hook ji tak předává, aby nebyla
v příkazové řádce úklidu). Kořen projektů mění AGENT_KIT_DEV (výchozí ~/Dev).

Pojistky: ukončuje jen programy dev serverů (SERVERY), nikdy nic mimo kořen projektů, nikdy proces,
jehož předkem je jiná živá session nebo okno uživatele, nikdy sebe a své předky. Sirotky mladší
než MIN_STARI_S nechá být (právě startující proces ještě může mít rodiče v pohybu).
Záznam o každém ukončení jde do ~/.agents/logs/uklid.log. Hlavní volání: hooks/uklid_hook.py.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

SERVERY = {
    "node.exe", "bun.exe", "deno.exe", "esbuild.exe",
    "python.exe", "pythonw.exe", "python3.exe", "uv.exe",
    "uvicorn.exe", "gunicorn.exe", "hypercorn.exe", "celery.exe", "pytest.exe",
    "postgres.exe", "redis-server.exe",
}
SESSION = {"claude.exe", "codex.exe"}
UZIVATEL = {"explorer.exe", "windowsterminal.exe", "code.exe", "cursor.exe",
            "services.exe", "wininit.exe", "svchost.exe"}
MIN_STARI_S = 600
STITEK = "agent-kit.slozka"
LOG = os.path.join(os.path.expanduser("~"), ".agents", "logs", "uklid.log")

# JSON jde na stdout přímo jako bajty UTF-8: v kódování konzole by se uvozovky „“ z příkazových
# řádek změnily na " a rozbily JSON (Windows PowerShell 5.1 nastavení OutputEncoding ignoruje).
PS_PROCESY = (
    "$j = Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{"
    "pid=$_.ProcessId; ppid=$_.ParentProcessId; jmeno=$_.Name; prikaz=$_.CommandLine;"
    "program=$_.ExecutablePath; vznik=$(if ($_.CreationDate) { $_.CreationDate.ToFileTimeUtc() } else { 0 })"
    "} } | ConvertTo-Json -Compress; $b = [Text.Encoding]::UTF8.GetBytes($j);"
    "$o = [Console]::OpenStandardOutput(); $o.Write($b, 0, $b.Length); $o.Flush()"
)


def normalizuj(cesta):
    """Cesta k porovnání: malá písmena, zpětná lomítka, Git Bash /c/... → c:\\..."""
    c = (cesta or "").strip().strip('"').replace("/", "\\").lower().rstrip("\\")
    m = re.match(r"^\\([a-z])(\\|$)", c)
    if m:
        c = m.group(1) + ":" + c[2:]
    return c


def vzor_slozky(slozka, pokracovani=r"(?=$|[\\\"' ;:,])"):
    """Regex na výskyt složky v textu (i v podobě /c/... z Git Bash), ne jako prefix jiného jména."""
    c = normalizuj(slozka)
    varianty = [re.escape(c), re.escape("\\" + c[0] + c[2:])] if re.match(r"^[a-z]:", c) else [re.escape(c)]
    return re.compile("(?:" + "|".join(varianty) + ")" + pokracovani)


def nacti_procesy(pokusu=3):
    for pokus in range(pokusu):  # WMI občas dotaz odmítne (přetížení), pak to zkusí znovu
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_PROCESY],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        try:
            data = json.loads(r.stdout) if r.returncode == 0 else None
        except ValueError:
            data = None
        if data:
            break
        if pokus == pokusu - 1:
            raise RuntimeError(f"seznam procesů se nepodařilo načíst: {r.stderr.strip()[:300]}")
    if isinstance(data, dict):
        data = [data]
    return {p["pid"]: p for p in data}


def predkove(p, procesy):
    """Živí předkové procesu; řetěz končí u mrtvého rodiče (nebo PID přiděleného později jinému)."""
    videno = {p["pid"]}
    while True:
        rodic = procesy.get(p["ppid"])
        if not rodic or rodic["pid"] in videno or (rodic["vznik"] and p["vznik"] and rodic["vznik"] > p["vznik"]):
            return
        videno.add(rodic["pid"])
        yield rodic
        p = rodic


def vlastnik(p, procesy, cli_pid):
    """'nase' (předkem je tato session), 'aplikace' (náhledový server nebo terminál spuštěný přímo
    aplikací Claude), 'ziva' (jiná session nebo okno uživatele), 'sirotek'."""
    for a in predkove(p, procesy):
        if cli_pid and a["pid"] == cli_pid:
            return "nase"
        jmeno = (a["jmeno"] or "").lower()
        if jmeno == "claude.exe" and "\\anthropicclaude\\" in normalizuj(a["program"]):
            return "aplikace"
        if jmeno in SESSION or jmeno in UZIVATEL:
            return "ziva"
    return "sirotek"


def je_server(p):
    jmeno = (p["jmeno"] or "").lower()
    return jmeno in SERVERY or bool(re.fullmatch(r"python3\.\d+\.exe", jmeno))


def text_procesu(p):
    return (p["prikaz"] or "").replace("/", "\\").lower() + "\n" + normalizuj(p["program"])


def stari_s(p):
    if not p["vznik"]:
        return 0
    return (datetime.datetime.now(datetime.timezone.utc).timestamp() - (p["vznik"] / 1e7 - 11644473600))


def vyber(procesy, dev, slozka=None, cli_pid=None, min_stari=MIN_STARI_S):
    """Procesy k ukončení. Bez složky hledá sirotky v celém kořeni projektů."""
    ja = os.getpid()
    chranene = {ja} | {a["pid"] for a in predkove(procesy[ja], procesy)} if ja in procesy else {ja}
    vzor_dev, vzor = vzor_slozky(dev), vzor_slozky(slozka or dev)
    # Worktree jiné session uvnitř složky (hlavní checkout → .claude\worktrees\…) bez důkazu
    # vlastnictví nepatří končící session.
    vnoreny = vzor_slozky(slozka, r"\\\.claude\\worktrees\\") if slozka else None
    vysledek = []
    for p in procesy.values():
        if p["pid"] in chranene or not je_server(p):
            continue
        text = text_procesu(p)
        if not (vzor_dev.search(text) and vzor.search(text)):
            continue
        kdo = vlastnik(p, procesy, cli_pid)
        if vnoreny and kdo != "nase" and vnoreny.search(text):
            continue
        # Náhledové servery (preview_start) spouští aplikace Claude, ne session: u konce session
        # se ukončí ty z její složky; mezi sirotky nepatří, živá aplikace je pořád jejich rodič.
        if (kdo in ("nase", "aplikace") and slozka) or (kdo == "sirotek" and (slozka or stari_s(p) >= min_stari)):
            vysledek.append((p, kdo))
    # Ukončuje se celý strom (taskkill /T): potomka vybraného procesu není třeba ukončovat zvlášť.
    vybrane = {p["pid"] for p, _ in vysledek}
    return [(p, kdo) for p, kdo in vysledek if not any(a["pid"] in vybrane for a in predkove(p, procesy))]


def docker_kontejnery():
    try:
        r = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"label={STITEK}",
             "--format", '{{.ID}}\t{{.State}}\t{{.Label "' + STITEK + '"}}\t{{.Names}}'],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if r.returncode:
        return []
    kontejnery = []
    for radek in r.stdout.splitlines():
        casti = radek.split("\t")
        if len(casti) == 4:
            kontejnery.append(dict(zip(("id", "stav", "slozka", "jmeno"), casti)))
    return kontejnery


def vyber_kontejnery(kontejnery, slozka=None, dev=None):
    vysledek = []
    for k in kontejnery:
        if k["stav"] != "running":
            continue
        cil = normalizuj(k["slozka"])
        if slozka:
            if cil == normalizuj(slozka) or cil.startswith(normalizuj(slozka) + "\\"):
                vysledek.append(k)
        elif cil and (not dev or cil.startswith(normalizuj(dev) + "\\")) and not os.path.isdir(cil):
            vysledek.append(k)
    return vysledek


def zapis(radek):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {radek}\n")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sirotci", action="store_true", help="osiřelé procesy v celém kořeni projektů")
    ap.add_argument("--slozka", default=os.environ.get("AGENT_KIT_UKLID_SLOZKA"), help="pracovní složka končící session")
    ap.add_argument("--cli-pid", type=int, default=int(os.environ.get("AGENT_KIT_UKLID_CLI_PID") or 0))
    ap.add_argument("--provest", action="store_true", help="opravdu ukončit (jinak jen výpis)")
    ap.add_argument("--min-stari", type=int, default=MIN_STARI_S, help="sirotci mladší než N sekund se nechají")
    a = ap.parse_args(argv)
    if os.name != "nt":
        print("Úklid procesů je jen pro Windows; cloudová session končí i se svým strojem.")
        return 0
    if bool(a.sirotci) == bool(a.slozka):
        ap.error("zadej právě jedno: --sirotci, nebo --slozka")

    dev = normalizuj(os.environ.get("AGENT_KIT_DEV") or os.path.join(os.path.expanduser("~"), "Dev"))
    slozka = normalizuj(a.slozka) if a.slozka else None
    if slozka and not slozka.startswith(dev + "\\"):
        print(f"Složka {slozka} není uvnitř {dev} (celý kořen projektů je moc široký); nic neukončuji.")
        return 0

    rezim = f"konec session {slozka}" if slozka else "sirotci"
    procesy = nacti_procesy()
    k_ukonceni = vyber(procesy, dev, slozka, a.cli_pid or None, a.min_stari)
    kontejnery = vyber_kontejnery(docker_kontejnery(), slozka, dev)
    if not k_ukonceni and not kontejnery:
        print(f"Úklid ({rezim}): nic k ukončení.")
        return 0
    for p, kdo in k_ukonceni:
        popis = f"proces {p['pid']} {p['jmeno']} ({kdo}): {(p['prikaz'] or p['program'] or '')[:300]}"
        if a.provest:
            r = subprocess.run(["taskkill", "/PID", str(p["pid"]), "/T", "/F"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            stav = "ukončen" if r.returncode == 0 else f"selhalo: {(r.stderr or r.stdout).strip()}"
            zapis(f"[{rezim}] {popis} → {stav}")
            print(f"{stav}: {popis}")
        else:
            print(f"ukončil bych: {popis}")
    for k in kontejnery:
        popis = f"kontejner {k['jmeno']} ({k['id']}, {STITEK}={k['slozka']})"
        if a.provest:
            r = subprocess.run(["docker", "stop", k["id"]], capture_output=True, text=True, timeout=60)
            stav = "zastaven" if r.returncode == 0 else f"selhalo: {r.stderr.strip()}"
            zapis(f"[{rezim}] {popis} → {stav}")
            print(f"{stav}: {popis}")
        else:
            print(f"zastavil bych: {popis}")
    if not a.provest:
        print("Jen výpis. Opravdu ukončit: přidej --provest.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as chyba:  # běží i na pozadí bez konzole: chyba musí skončit v logu
        zapis(f"[chyba] {type(chyba).__name__}: {chyba}")
        raise
