"""Úklid procesů a kontejnerů Dockeru, které po sobě nechaly sessions agentů (Windows).

Použití (bez --provest jen vypíše, co by ukončil):
  python -I scripts/uklid.py --sirotci [--provest]
      osiřelé dev servery v ~/Dev: nad procesem už není živá session ani okno uživatele
      a jeho pracovní složka nepatří živé session (viz ZIVA_S); kontejnery se štítkem
      agent-kit.slozka, jejichž složka neexistuje nebo nepatří živé session.
  python -I scripts/uklid.py --slozka <pracovní složka> [--provest]
      konec session: dev servery z dané složky, které patří této session (AGENT_KIT_UKLID_CLI),
      náhledu aplikace Claude nebo už nikomu; kontejnery se štítkem agent-kit.slozka=<složka>.
Hook předává složku, session a přepis proměnnými AGENT_KIT_UKLID_SLOZKA, AGENT_KIT_UKLID_CLI
(„pid:čas vzniku“) a AGENT_KIT_UKLID_PREPIS. Kořen projektů mění AGENT_KIT_DEV (výchozí ~/Dev).

Živá session se pozná dvojím způsobem, protože ani jeden sám nestačí:
- strom procesů: nad procesem je claude.exe (CLI) nebo codex.exe, okno uživatele (terminál, editor,
  Průzkumník) nebo terminál v aplikaci Claude;
- přepis: v ~/.claude/projects je přepis změněný v posledních ZIVA_S sekundách od session spuštěné
  v té složce, v její podsložce nebo v nadřazené složce uvnitř ~/Dev (viz ziva_slozka).
  Server spuštěný na pozadí totiž přijde o rodiče (shell skončí), i když session dál běží.
Pojistky: jen programy dev serverů (SERVERY), nic mimo kořen projektů, nikdy sebe a své předky;
ukončuje se přesné PID s ověřeným časem vzniku (ne strom podle PID, které mohl dostat jiný proces).
Záznam o každém ukončení jde do ~/.agents/logs/uklid.log. Hlavní volání: hooks/uklid_hook.py.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

SERVERY = {
    "node.exe", "bun.exe", "deno.exe", "esbuild.exe",
    "python.exe", "pythonw.exe", "python3.exe", "uv.exe",
    "uvicorn.exe", "gunicorn.exe", "hypercorn.exe", "celery.exe", "pytest.exe",
    "postgres.exe", "redis-server.exe",
}
SESSION = {"claude.exe", "codex.exe"}
UZIVATEL = {"explorer.exe", "windowsterminal.exe", "code.exe", "cursor.exe",
            "services.exe", "wininit.exe", "svchost.exe"}
TERMINAL = {"powershell.exe", "pwsh.exe"}  # terminál, který aplikace Claude otevírá uživateli
MIN_STARI_S = 600
ZIVA_S = 6 * 3600  # session nečinná déle se bere jako skončená (její servery už nejsou potřeba)
STITEK = "agent-kit.slozka"
LOG = os.path.join(os.path.expanduser("~"), ".agents", "logs", "uklid.log")
PROJEKTY = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude"),
                        "projects")
DEV = os.environ.get("AGENT_KIT_DEV") or os.path.join(os.path.expanduser("~"), "Dev")
BEZ_OKNA = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: úklid na pozadí nesmí blikat konzolí

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


def _varianty(slozka):
    c = normalizuj(slozka)
    return [re.escape(c), re.escape("\\" + c[0] + c[2:])] if re.match(r"^[a-z]:", c) else [re.escape(c)]


def vzor_slozky(slozka):
    """Regex na výskyt složky v textu (i v podobě /c/... z Git Bash), ne jako prefix jiného jména."""
    return re.compile("(?:" + "|".join(_varianty(slozka)) + r")(?=$|[\\\"' ;:,=)\n])")


def koreny(text, dev):
    """Pracovní složky, na které text procesu odkazuje: ~/Dev/<projekt>[/.claude/worktrees/<jméno>]."""
    jmeno = r"[^\\\"' ;:,=)\n]+"
    worktree = r"\\\.claude\\worktrees\\" + jmeno
    vzor = re.compile("(?:" + "|".join(_varianty(dev)) + ")(" + worktree + r"|\\" + jmeno + "(?:" + worktree + ")?)")
    return {normalizuj(dev) + m.group(1) for m in vzor.finditer(text)}


def kod_slozky(slozka):
    """Jméno adresáře přepisů v ~/.claude/projects (Claude Code nahrazuje vše mimo a-z0-9 pomlčkou)."""
    return re.sub(r"[^a-z0-9]", "-", normalizuj(slozka))


_prepisy = {}


def cerstve_prepisy(krome=None, ted=None):
    """{adresář přepisů: čas poslední změny} pro adresáře s přepisem mladším než ZIVA_S (mimo `krome`)."""
    klic = (normalizuj(krome) if krome else None, ted)
    if klic in _prepisy:
        return _prepisy[klic]
    hranice, vysledek = (ted or time.time()) - ZIVA_S, {}
    try:
        adresare = [d for d in os.scandir(PROJEKTY) if d.is_dir()]
    except OSError:
        adresare = []
    for d in adresare:
        try:
            casy = [e.stat().st_mtime for e in os.scandir(d.path)
                    if e.name.endswith(".jsonl") and normalizuj(e.path) != klic[0]]
        except OSError:  # přepis smazaný během procházení
            continue
        if casy and max(casy) >= hranice:
            vysledek[d.name.lower()] = max(casy)
    _prepisy[klic] = vysledek
    return vysledek


def ziva_slozka(slozka, krome=None, ted=None):
    """Složku používá živá session: čerstvý přepis má session spuštěná v ní, v její podsložce
    (worktree, frontend…) nebo v nadřazené složce až po ~/Dev (hlavní checkout, ~/Dev).
    Shoda prefixem občas označí za živou i sousední složku (trading-old), to je bezpečný směr."""
    c, dev = normalizuj(slozka), normalizuj(DEV)
    predci, x = set(), c
    while x.startswith(dev):
        predci.add(kod_slozky(x))
        x = x.rsplit("\\", 1)[0]
    kod = kod_slozky(c)
    return any(d in predci or d.startswith(kod + "-") for d in cerstve_prepisy(krome, ted))


def ziva_v_slozce(slozka, krome=None, ted=None):
    """Čerstvý přepis jiné session přímo v té složce nebo v její podsložce (bez nadřazených)."""
    kod = kod_slozky(slozka)
    return any(d == kod or d.startswith(kod + "-") for d in cerstve_prepisy(krome, ted))


def nacti_procesy(pokusu=3):
    for pokus in range(pokusu):  # WMI občas dotaz odmítne (přetížení), pak to zkusí znovu
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_PROCESY],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
            creationflags=BEZ_OKNA,
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


def potomci(p, procesy):
    """Všichni živí potomci (dítě musí vzniknout po rodiči, jinak má jen recyklované PPID)."""
    deti = {}
    for q in procesy.values():
        deti.setdefault(q["ppid"], []).append(q)
    vysledek, fronta = [], [p]
    while fronta:
        rodic = fronta.pop()
        for q in deti.get(rodic["pid"], []):
            if q is not rodic and q not in vysledek and (not q["vznik"] or q["vznik"] >= rodic["vznik"]):
                vysledek.append(q)
                fronta.append(q)
    return vysledek


def vlastnik(p, procesy, cli=None):
    """'nase' (předkem je tato session), 'aplikace' (náhledový server spuštěný aplikací Claude),
    'ziva' (jiná session, okno nebo terminál uživatele), 'sirotek'."""
    pod = p
    for a in predkove(p, procesy):
        if cli and a["pid"] == cli[0] and (not cli[1] or abs(a["vznik"] - cli[1]) <= 20_000):  # WMI má µs
            return "nase"
        jmeno = (a["jmeno"] or "").lower()
        if jmeno == "claude.exe" and "\\anthropicclaude\\" in normalizuj(a["program"]):
            return "ziva" if (pod["jmeno"] or "").lower() in TERMINAL else "aplikace"
        if jmeno in SESSION or jmeno in UZIVATEL:
            return "ziva"
        pod = a
    return "sirotek"


def je_server(p):
    jmeno = (p["jmeno"] or "").lower()
    return jmeno in SERVERY or bool(re.fullmatch(r"python3\.\d+\.exe", jmeno))


def text_procesu(p):
    return (p["prikaz"] or "").replace("/", "\\").lower() + "\n" + normalizuj(p["program"])


def stari_s(p, ted=None):
    if not p["vznik"]:
        return 0
    return (ted or time.time()) - (p["vznik"] / 1e7 - 11644473600)


def vyber(procesy, dev, slozka=None, cli=None, krome=None, ziva=ziva_slozka, min_stari=MIN_STARI_S):
    """Procesy k ukončení. Bez složky hledá sirotky v celém kořeni projektů."""
    slozka = normalizuj(slozka) if slozka else None
    ja = os.getpid()
    chranene = {ja} | ({a["pid"] for a in predkove(procesy[ja], procesy)} if ja in procesy else set())
    vzor_dev, vzor = vzor_slozky(dev), vzor_slozky(slozka or dev)
    vysledek = []
    for p in procesy.values():
        if p["pid"] in chranene or not je_server(p):
            continue
        text = text_procesu(p)
        if not (vzor_dev.search(text) and vzor.search(text)):
            continue
        kdo = vlastnik(p, procesy, cli)
        if kdo == "ziva" or (kdo == "aplikace" and not slozka):
            continue
        # Skript, který spustil session (claude -p, codex), se neukončuje i s ní.
        if any((q["jmeno"] or "").lower() in SESSION for q in potomci(p, procesy)):
            continue
        if kdo != "nase":
            slozky = koreny(text, dev)
            # Worktree jiné session uvnitř složky (hlavní checkout → .claude\worktrees\…).
            if slozka and any(k.startswith(slozka + "\\") for k in slozky):
                continue
            if any(ziva(k, krome) for k in slozky):
                continue
            if not slozka and stari_s(p) < min_stari:
                continue
        vysledek.append((p, kdo))
    vybrane = {p["pid"] for p, _ in vysledek}
    return [(p, kdo) for p, kdo in vysledek if not any(a["pid"] in vybrane for a in predkove(p, procesy))]


def _kernel32():
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    return k32


def _vznik_handle(k32, h):
    from ctypes import byref
    from ctypes.wintypes import FILETIME
    casy = [FILETIME() for _ in range(4)]
    if not k32.GetProcessTimes(h, *[byref(c) for c in casy]):
        return None
    return (casy[0].dwHighDateTime << 32) | casy[0].dwLowDateTime


def cas_vzniku(pid):
    """Čas vzniku procesu (FILETIME) přímo z Windows, nebo None, když proces neběží."""
    k32 = _kernel32()
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return None
    try:
        return _vznik_handle(k32, h)
    finally:
        k32.CloseHandle(h)


def ukonci(p):
    """Ukončí proces jen tehdy, když PID pořád patří témuž procesu (stejný čas vzniku)."""
    import ctypes
    k32 = _kernel32()
    h = k32.OpenProcess(0x1001, False, p["pid"])  # PROCESS_TERMINATE | QUERY_LIMITED_INFORMATION
    if not h:
        chyba = ctypes.get_last_error()
        return "už neběží" if chyba == 87 else f"nelze otevřít (chyba {chyba})"  # 87 = neplatné PID
    try:
        skutecny = _vznik_handle(k32, h)
        if skutecny is None or not p["vznik"] or abs(skutecny - p["vznik"]) > 20_000:  # tolerance 2 ms (WMI)
            return "PID mezitím patří jinému procesu, nechávám"
        return "ukončen" if k32.TerminateProcess(h, 1) else f"selhalo (chyba {ctypes.get_last_error()})"
    finally:
        k32.CloseHandle(h)


def docker_kontejnery():
    try:
        r = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"label={STITEK}",
             "--format", '{{.ID}}\t{{.State}}\t{{.Label "' + STITEK + '"}}\t{{.Names}}'],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
            creationflags=BEZ_OKNA,
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


def vyber_kontejnery(kontejnery, dev, slozka=None, krome=None, ziva=ziva_slozka, ziva_v=None):
    """Běžící kontejnery se štítkem: při konci session přesně její složky (podsložky kromě
    vnořených worktree), pokud je tam nepoužívá jiná živá session; mezi sirotky ty, jejichž
    složka v ~/Dev nepatří živé session."""
    ziva_v = ziva_v or ziva_v_slozce
    slozka = normalizuj(slozka) if slozka else None
    vysledek = []
    for k in kontejnery:
        cil = normalizuj(k["slozka"])
        if k["stav"] != "running" or not cil.startswith(normalizuj(dev) + "\\"):
            continue
        if slozka:
            nalezi = cil == slozka or (cil.startswith(slozka + "\\") and "\\.claude\\worktrees\\" not in cil[len(slozka):])
            if nalezi and not ziva_v(cil, krome):
                vysledek.append(k)
        elif not ziva(cil, krome):
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
    ap.add_argument("--cli", default=os.environ.get("AGENT_KIT_UKLID_CLI", ""), help="session: pid[:čas vzniku]")
    ap.add_argument("--prepis", default=os.environ.get("AGENT_KIT_UKLID_PREPIS"), help="přepis končící session")
    ap.add_argument("--provest", action="store_true", help="opravdu ukončit (jinak jen výpis)")
    ap.add_argument("--min-stari", type=int, default=MIN_STARI_S, help="sirotci mladší než N sekund se nechají")
    a = ap.parse_args(argv)
    if os.name != "nt":
        print("Úklid procesů je jen pro Windows; cloudová session končí i se svým strojem.")
        return 0
    if bool(a.sirotci) == bool(a.slozka):
        ap.error("zadej právě jedno: --sirotci, nebo --slozka")

    dev = normalizuj(DEV)
    slozka = normalizuj(a.slozka) if a.slozka else None
    if slozka and not slozka.startswith(dev + "\\"):
        print(f"Složka {slozka} není uvnitř {dev} (celý kořen projektů je moc široký); nic neukončuji.")
        return 0
    casti = [int(x) for x in a.cli.split(":") if x.strip().isdigit()]
    cli = (casti[0], casti[1] if len(casti) > 1 else 0) if casti and casti[0] else None

    rezim = f"konec session {slozka}" if slozka else "sirotci"
    procesy = nacti_procesy()
    k_ukonceni = vyber(procesy, dev, slozka, cli, a.prepis, min_stari=a.min_stari)
    kontejnery = vyber_kontejnery(docker_kontejnery(), dev, slozka, a.prepis)
    if not k_ukonceni and not kontejnery:
        print(f"Úklid ({rezim}): nic k ukončení.")
        return 0
    for p, kdo in k_ukonceni:
        strom = potomci(p, procesy)
        popis = (f"proces {p['pid']} {p['jmeno']} ({kdo}, potomků {len(strom)}): "
                 f"{(p['prikaz'] or p['program'] or '')[:300]}")
        if a.provest:
            stav = ukonci(p)
            for q in strom:
                ukonci(q)
            zapis(f"[{rezim}] {popis} → {stav}")
            print(f"{stav}: {popis}")
        else:
            print(f"ukončil bych: {popis}")
    for k in kontejnery:
        popis = f"kontejner {k['jmeno']} ({k['id']}, {STITEK}={k['slozka']})"
        if a.provest:
            r = subprocess.run(["docker", "stop", k["id"]], capture_output=True, text=True, timeout=60,
                               creationflags=BEZ_OKNA)
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
