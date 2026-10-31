"""Testy úklidu procesů: python -I tests/test_uklid.py

1. Výběr procesů a kontejnerů na smyšlené tabulce (běží všude, i v CI na Linuxu).
2. Na Windows ve složce projektů navíc živý test na neškodných procesech (python -c sleep)
   v dočasných složkách ~/Dev/.uklid-test-*: osiřelý proces ze složky se ukončí; proces jiné živé
   session, osiřelý proces ve složce s čerstvým přepisem session a proces mimo ~/Dev zůstanou.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8")
KOREN = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(KOREN, "scripts"))
import uklid  # noqa: E402

chyby = 0


def over(nazev, ok):
    global chyby
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev)


# --- 1. smyšlená tabulka ---------------------------------------------------------------
DEV = r"C:\Users\Admin\Dev"
STARY = 10_000_000  # vznik (FILETIME) dávno; rodiče vznikli dřív než potomci
APP = r"C:\Users\Admin\AppData\Local\AnthropicClaude\app-4.1\claude.exe"
CLI = r"C:\Users\Admin\AppData\Roaming\Claude\claude-code\2.1\claude.exe"


def proc(pid, ppid, jmeno, prikaz="", program="", vznik=None):
    return {"pid": pid, "ppid": ppid, "jmeno": jmeno, "prikaz": prikaz, "program": program,
            "vznik": STARY + pid if vznik is None else vznik}


W = r"C:\Users\Admin\Dev\trading\.claude\worktrees\a"
Z = r"C:\Users\Admin\Dev\prove\.claude\worktrees\ziva"  # složka s čerstvým přepisem session
HLAVNI = r"C:\Users\Admin\Dev\trading"
tabulka = {p["pid"]: p for p in [
    proc(1, 0, "explorer.exe"),
    proc(10, 1, "claude.exe", program=APP),                      # aplikace Claude
    proc(20, 10, "claude.exe", program=CLI),                     # končící session
    proc(21, 20, "bash.exe"),
    proc(22, 21, "node.exe", f'node "{W}\\node_modules\\vite\\bin\\vite.js"'),       # naše → ukončit
    proc(23, 22, "esbuild.exe", f"{W}\\node_modules\\esbuild.exe"),                  # potomek 22 (strom)
    proc(30, 10, "claude.exe", program=CLI),                     # jiná živá session
    proc(31, 30, "python.exe", f"python -m uvicorn --app-dir {W} api:app"),          # chráněný
    proc(40, 10, "cmd.exe"),                                     # náhled preview_start
    proc(41, 40, "node.exe", f"node {W}\\node_modules\\.bin\\vite"),                 # aplikace
    proc(45, 10, "powershell.exe"),                              # terminál v aplikaci Claude
    proc(46, 45, "node.exe", f"node {W}\\server.js"),            # server uživatele z terminálu
    proc(50, 999, "python.exe", "uvicorn api.main:app", W + r"\.venv\Scripts\python.exe"),  # sirotek
    proc(51, 999, "node.exe", "node /c/Users/Admin/Dev/trading/.claude/worktrees/a/x.js"),  # sirotek, Git Bash cesta
    proc(52, 999, "node.exe", r"node C:\Users\Admin\Dev\trading\.claude\worktrees\ab\x.js"),  # jiná složka (prefix)
    proc(53, 999, "Code.exe", f"Code.exe {W}"),                  # editor, není server
    proc(54, 999, "node.exe", r"node C:\Users\Admin\AppData\Local\Temp\x.js"),       # mimo Dev
    proc(55, 1, "node.exe", f"node {W}\\x.js"),                  # terminál uživatele (explorer)
    proc(56, 999, "node.exe", f"node {Z}\\node_modules\\vite\\bin\\vite.js"),        # server živé session na pozadí
    proc(60, 70, "node.exe", r"node C:\Users\Admin\Dev\prove\server.js"),            # rodič 70 je novější → sirotek
    proc(70, 1, "bash.exe", vznik=STARY + 10_000),
    proc(80, 999, "node.exe", r"node C:\Users\Admin\Dev\prove\mlady.js",
         vznik=int((time.time() + 11644473600) * 1e7)),          # sirotek právě vzniklý
]}
zive = {uklid.normalizuj(Z)}


def ziva(slozka, krome=None):
    return slozka in zive


def vyber(slozka=None, cli=None):
    return {p["pid"]: kdo for p, kdo in uklid.vyber(tabulka, DEV, slozka, cli, ziva=ziva)}


vybrane = vyber(W, (20, STARY + 20))
over(f"konec session: ukončí svůj server, náhled, sirotky ze složky (vybráno {sorted(vybrane)})",
     vybrane == {22: "nase", 41: "aplikace", 50: "sirotek", 51: "sirotek"})
over("konec session: nechá jinou živou session, editor, cizí složku, terminál uživatele (i v aplikaci)",
     not {31, 46, 52, 53, 55} & set(vybrane))
over("konec session: PID session přidělené jinému procesu (jiný čas vzniku) nic nedokazuje",
     22 not in vyber(W, (20, STARY + 999_999)))
sirotci = set(vyber())
over(f"sirotci: jen staří sirotci v ~/Dev (vybráno {sorted(sirotci)})", sirotci == {50, 51, 52, 60})
over("sirotci: nechá server živé session spuštěný na pozadí (bez rodiče, čerstvý přepis)", 56 not in sirotci)
over("sirotci: nesáhne na náhled aplikace, živé sessions, terminál, proces mimo Dev ani čerstvý proces",
     not {22, 31, 41, 46, 54, 80} & sirotci)
hlavni = set(vyber(HLAVNI, (20, STARY + 20)))
over(f"konec session v hlavním checkoutu: cizí worktree uvnitř jen s důkazem vlastnictví (vybráno {sorted(hlavni)})",
     hlavni == {22})
over("strom potomků: esbuild pod vite", [q["pid"] for q in uklid.potomci(tabulka[22], tabulka)] == [23])
over("pracovní složka z cesty procesu",
     uklid.koreny(uklid.text_procesu(tabulka[51]), DEV) == {uklid.normalizuj(W)})
beh = subprocess.run([sys.executable, "-I", os.path.join(KOREN, "scripts", "uklid.py"), "--slozka", DEV],
                     capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, AGENT_KIT_DEV=DEV))
over("celý kořen projektů jako složka session odmítne", os.name != "nt" or "nic neukončuji" in beh.stdout)
over("cesta z Git Bash se normalizuje", uklid.normalizuj("/c/Users/Admin/Dev/") == r"c:\users\admin\dev")

orchestr = dict(tabulka)
orchestr.update({p["pid"]: p for p in [
    proc(90, 999, "python.exe", f"python {W}\\run_agents.py"),   # osiřelý skript, který pustil session
    proc(91, 90, "claude.exe", program=CLI),
]})
over("skript se session (claude.exe) mezi potomky se neukončí",
     90 not in {p["pid"] for p, _ in uklid.vyber(orchestr, DEV, ziva=ziva)})

# Živost složky podle přepisů v dočasném ~/.claude/projects.
uklid.DEV = DEV
projekty = tempfile.mkdtemp()
uklid.PROJEKTY = projekty
ted = time.time()


def prepis(slozka, stari_s=0, jmeno="s.jsonl"):
    adresar = os.path.join(projekty, uklid.kod_slozky(slozka))
    os.makedirs(adresar, exist_ok=True)
    cesta = os.path.join(adresar, jmeno)
    open(cesta, "w").close()
    os.utime(cesta, (ted - stari_s, ted - stari_s))
    return cesta


prepis(DEV + r"\trading\.claude\worktrees\x")
prepis(DEV + r"\my folder")
prepis(DEV + r"\stary", stari_s=uklid.ZIVA_S + 60)
vlastni = prepis(DEV + r"\konci")
prepis(DEV + r"\.claude\worktrees\kd")
uklid._prepisy.clear()


def zije(slozka, krome=None):
    return uklid.ziva_slozka(DEV + slozka, krome, ted)


over("živost: hlavní checkout, jehož worktree má čerstvý přepis", zije(r"\trading"))
over("živost: podsložka worktree se session (štítek po cd backend)", zije(r"\trading\.claude\worktrees\x\backend"))
over("živost: neúplná cesta se mezerou (dev\\my → my folder)", zije(r"\my"))
over("živost: worktree přímo v ~/Dev (kořen dev\\.claude)", zije(r"\.claude"))
over("živost: jiný projekt, starý přepis ani vlastní přepis končící session nic nedokazují",
     not zije(r"\prove") and not zije(r"\stary") and not zije(r"\konci", vlastni))
prepis(DEV)
uklid._prepisy.clear()
over("živost: session spuštěná přímo v ~/Dev chrání vše pod ~/Dev", zije(r"\prove"))
shutil.rmtree(projekty, ignore_errors=True)

kont = [{"id": "a", "stav": "running", "slozka": W.replace("\\", "/"), "jmeno": "pg"},
        {"id": "b", "stav": "running", "slozka": W + "b", "jmeno": "pg2"},
        {"id": "c", "stav": "exited", "slozka": W, "jmeno": "pg3"},
        {"id": "d", "stav": "running", "slozka": HLAVNI + r"\db", "jmeno": "pg4"},
        {"id": "e", "stav": "running", "slozka": r"C:\jinde\x", "jmeno": "pg5"},
        {"id": "z", "stav": "running", "slozka": Z, "jmeno": "pg6"}]


def kontejnery(slozka=None, ziva_v=lambda slozka, krome=None: False):
    return [k["id"] for k in uklid.vyber_kontejnery(kont, DEV, slozka, ziva=ziva, ziva_v=ziva_v)]


over("kontejnery: konec session jen běžící se štítkem této složky", kontejnery(W) == ["a"])
over("kontejnery: hlavní checkout nezastaví kontejner vnořeného worktree", kontejnery(HLAVNI) == ["d"])
over("kontejnery: konec session nezastaví kontejner, který ve složce používá jiná živá session",
     kontejnery(W, ziva_v=lambda slozka, krome=None: True) == [])
over("kontejnery sirotci: v ~/Dev a složka nepatří živé session", kontejnery() == ["a", "b", "d"])

# --- 2. živý test (Windows, repozitář ve složce projektů) --------------------------------
dev = os.path.join(os.path.expanduser("~"), "Dev")
if os.name != "nt" or not uklid.normalizuj(KOREN).startswith(uklid.normalizuj(dev) + "\\"):
    print("PŘESKOČENO živý test (jen Windows a repozitář v ~/Dev)")
else:
    slozka = os.path.join(dev, f".uklid-test-{os.getpid()}")
    ziva_slozka = os.path.join(dev, f".uklid-ziva-{os.getpid()}")  # jiný prefix: shoda prefixem by chránila i slozka
    venku = os.path.join(tempfile.gettempdir(), f"uklid-test-{os.getpid()}")
    domov = tempfile.mkdtemp()
    for d in (slozka, ziva_slozka):
        os.makedirs(d)
    # Čerstvý přepis session pro ziva_slozka v dočasném ~/.claude (CLAUDE_CONFIG_DIR).
    prepisy = os.path.join(domov, ".claude", "projects",
                           "".join(c if c.isalnum() else "-" for c in uklid.normalizuj(ziva_slozka)))
    os.makedirs(prepisy)
    open(os.path.join(prepisy, "session.jsonl"), "w").close()
    spanek = "import sys, time; time.sleep(120)"
    PRIZNAKY = 0x08000000 | 0x00000200  # bez okna, vlastní skupina; rodič hned skončí = sirotek

    def sirotek(znacka):
        """Spustí spáče přes mezičlánek, který hned skončí: spáč zůstane bez živého rodiče."""
        kod = (f"import subprocess, sys; p = subprocess.Popen([sys.executable, '-c', {spanek!r}, {znacka!r}],"
               f" creationflags={PRIZNAKY}); print(p.pid)")
        return int(subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, check=True).stdout)

    def zije(pid):
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout

    def uklid_slozky(cil, *dalsi):
        beh = subprocess.run([sys.executable, "-I", os.path.join(KOREN, "scripts", "uklid.py"),
                              "--slozka", cil, "--provest", *dalsi],
                             capture_output=True, text=True, encoding="utf-8", env=prostredi)
        print("   ", (beh.stdout + beh.stderr).strip().replace("\n", "\n    "))

    pid_sirotek = sirotek(os.path.join(slozka, "server.py"))
    pid_ziva = sirotek(os.path.join(ziva_slozka, "server.py"))
    pid_venku = sirotek(os.path.join(venku, "server.py"))
    potomek = subprocess.Popen([sys.executable, "-c", spanek, os.path.join(slozka, "jina-session.py")])
    prostredi = dict(os.environ, AGENT_KIT_DEV=dev, USERPROFILE=domov, HOME=domov,
                     CLAUDE_CONFIG_DIR=os.path.join(domov, ".claude"))
    try:
        time.sleep(2)
        # Potomek tohoto testu patří pod session, která test spustila (claude.exe nad námi) = jiná živá session.
        for pokus in range(3):  # u čerstvého procesu Windows občas ještě nevrátí příkazovou řádku
            uklid_slozky(slozka)
            time.sleep(1)
            if not zije(pid_sirotek):
                break
        uklid_slozky(ziva_slozka)
        time.sleep(1)
        over("živě: osiřelý proces ze složky session je ukončený", not zije(pid_sirotek))
        over("živě: proces jiné živé session ze stejné složky běží dál", potomek.poll() is None)
        over("živě: osiřelý proces ve složce s čerstvým přepisem session běží dál", zije(pid_ziva))
        over("živě: osiřelý proces mimo ~/Dev běží dál", zije(pid_venku))
        over("živě: ukončení je zapsané v logu",
             os.path.isfile(os.path.join(domov, ".agents", "logs", "uklid.log")))
        # Stejný potomek se session = tento test (PID a čas vzniku): teď je „náš“ a ukončí se.
        uklid_slozky(slozka, "--cli", f"{os.getpid()}:{uklid.cas_vzniku(os.getpid())}")
        time.sleep(1)
        over("živě: proces vlastní session je ukončený", potomek.poll() is not None)
    finally:
        for pid in (pid_sirotek, pid_ziva, pid_venku, potomek.pid):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        for d in (slozka, ziva_slozka, domov):
            shutil.rmtree(d, ignore_errors=True)

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
