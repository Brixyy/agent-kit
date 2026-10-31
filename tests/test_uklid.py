"""Testy úklidu procesů: python -I tests/test_uklid.py

1. Výběr procesů na smyšlené tabulce (běží všude, i v CI na Linuxu).
2. Na Windows ve složce projektů navíc živý test na neškodných procesech (python -c sleep):
   osiřelý proces ze složky se ukončí, proces jiné živé session a proces mimo ~/Dev zůstanou.
"""
import os
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
tabulka = {p["pid"]: p for p in [
    proc(1, 0, "explorer.exe"),
    proc(10, 1, "claude.exe", program=APP),                      # aplikace Claude
    proc(20, 10, "claude.exe", program=CLI),                     # končící session
    proc(21, 20, "bash.exe"),
    proc(22, 21, "node.exe", f'node "{W}\\node_modules\\vite\\bin\\vite.js"'),       # naše → ukončit
    proc(23, 22, "esbuild.exe", f"{W}\\node_modules\\esbuild.exe"),                  # potomek 22, stačí strom
    proc(30, 10, "claude.exe", program=CLI),                     # jiná živá session
    proc(31, 30, "python.exe", f"python -m uvicorn --app-dir {W} api:app"),          # chráněný
    proc(40, 10, "cmd.exe"),                                     # náhled preview_start
    proc(41, 40, "node.exe", f"node {W}\\node_modules\\.bin\\vite"),                 # aplikace
    proc(50, 999, "python.exe", "uvicorn api.main:app", W + r"\.venv\Scripts\python.exe"),  # sirotek
    proc(51, 999, "node.exe", "node /c/Users/Admin/Dev/trading/.claude/worktrees/a/x.js"),  # sirotek, Git Bash cesta
    proc(52, 999, "node.exe", r"node C:\Users\Admin\Dev\trading\.claude\worktrees\ab\x.js"),  # jiná složka (prefix)
    proc(53, 999, "Code.exe", f"Code.exe {W}"),                  # editor, není server
    proc(54, 999, "node.exe", r"node C:\Users\Admin\AppData\Local\Temp\x.js"),       # mimo Dev
    proc(55, 1, "node.exe", f"node {W}\\x.js"),                  # terminál uživatele (explorer)
    proc(60, 70, "node.exe", r"node C:\Users\Admin\Dev\prove\server.js"),            # rodič 70 je novější → sirotek
    proc(70, 1, "bash.exe", vznik=STARY + 10_000),
    proc(80, 999, "node.exe", r"node C:\Users\Admin\Dev\prove\mlady.js",
         vznik=int((time.time() + 11644473600) * 1e7)),          # sirotek právě vzniklý
]}

vybrane = {p["pid"]: kdo for p, kdo in uklid.vyber(tabulka, DEV, W, cli_pid=20)}
over(f"konec session: ukončí svůj server, náhled, sirotky ze složky (vybráno {sorted(vybrane)})",
     vybrane == {22: "nase", 41: "aplikace", 50: "sirotek", 51: "sirotek"})
over("konec session: nechá jinou živou session, editor, cizí složku, terminál uživatele",
     not {31, 52, 53, 55} & set(vybrane))
sirotci = {p["pid"] for p, _ in uklid.vyber(tabulka, DEV)}
over(f"sirotci: jen staří sirotci v ~/Dev (vybráno {sorted(sirotci)})", sirotci == {50, 51, 52, 60})
over("sirotci: nesáhne na náhled aplikace, živé sessions, proces mimo Dev ani čerstvý proces",
     not {22, 31, 41, 54, 80} & sirotci)
HLAVNI = r"C:\Users\Admin\Dev\trading"
hlavni = {p["pid"] for p, _ in uklid.vyber(tabulka, DEV, HLAVNI, cli_pid=20)}
over(f"konec session v hlavním checkoutu: cizí worktree uvnitř jen s důkazem vlastnictví (vybráno {sorted(hlavni)})",
     hlavni == {22})
beh = subprocess.run([sys.executable, "-I", os.path.join(KOREN, "scripts", "uklid.py"), "--slozka", DEV],
                     capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, AGENT_KIT_DEV=DEV))
over("celý kořen projektů jako složka session odmítne", os.name != "nt" or "nic neukončuji" in beh.stdout)
over("cesta z Git Bash se normalizuje", uklid.normalizuj("/c/Users/Admin/Dev/") == r"c:\users\admin\dev")
kont = [{"id": "a", "stav": "running", "slozka": W.replace("\\", "/"), "jmeno": "pg"},
        {"id": "b", "stav": "running", "slozka": W + "b", "jmeno": "pg2"},
        {"id": "c", "stav": "exited", "slozka": W, "jmeno": "pg3"}]
over("kontejnery: jen běžící se štítkem této složky",
     [k["id"] for k in uklid.vyber_kontejnery(kont, W)] == ["a"])
kont += [{"id": "d", "stav": "running", "slozka": DEV + r"\neexistuje-xyz", "jmeno": "pg4"},
         {"id": "e", "stav": "running", "slozka": r"C:\jinde\neexistuje-xyz", "jmeno": "pg5"}]
over("kontejnery sirotci: běžící se štítkem neexistující složky, jen v ~/Dev",
     [k["id"] for k in uklid.vyber_kontejnery(kont, dev=DEV)] == ["a", "b", "d"])

# --- 2. živý test (Windows, repozitář ve složce projektů) --------------------------------
dev = os.path.join(os.path.expanduser("~"), "Dev")
if os.name != "nt" or not uklid.normalizuj(KOREN).startswith(uklid.normalizuj(dev) + "\\"):
    print("PŘESKOČENO živý test (jen Windows a repozitář v ~/Dev)")
else:
    slozka = os.path.join(KOREN, f".uklid-test-{os.getpid()}")
    venku = os.path.join(tempfile.gettempdir(), f"uklid-test-{os.getpid()}")
    spanek = "import sys, time; time.sleep(120)"
    PRIZNAKY = 0x00000008 | 0x00000200  # odpojený proces bez rodiče = sirotek

    def sirotek(znacka):
        """Spustí spáče přes mezičlánek, který hned skončí: spáč zůstane bez živého rodiče."""
        kod = (f"import subprocess, sys; p = subprocess.Popen([sys.executable, '-c', {spanek!r}, {znacka!r}],"
               f" creationflags={PRIZNAKY}); print(p.pid)")
        return int(subprocess.run([sys.executable, "-c", kod], capture_output=True, text=True, check=True).stdout)

    def zije(pid):
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout

    pid_sirotek = sirotek(os.path.join(slozka, "server.py"))
    pid_venku = sirotek(os.path.join(venku, "server.py"))
    potomek = subprocess.Popen([sys.executable, "-c", spanek, os.path.join(slozka, "jina-session.py")])
    domov = tempfile.mkdtemp()
    prostredi = dict(os.environ, AGENT_KIT_DEV=dev, USERPROFILE=domov, HOME=domov)
    try:
        time.sleep(2)
        # Potomek tohoto testu patří pod session, která test spustila (claude.exe nad námi) = jiná živá session.
        # Windows u čerstvě spuštěného procesu občas ještě nevrátí příkazovou řádku; proto až 3 pokusy.
        for pokus in range(3):
            beh = subprocess.run([sys.executable, "-I", os.path.join(KOREN, "scripts", "uklid.py"),
                                  "--slozka", slozka, "--provest"],
                                 capture_output=True, text=True, encoding="utf-8", env=prostredi)
            print(f"    pokus {pokus + 1}:", (beh.stdout + beh.stderr).strip().replace("\n", "\n    "))
            time.sleep(1)
            if not zije(pid_sirotek):
                break
        over("živě: osiřelý proces ze složky session je ukončený", not zije(pid_sirotek))
        over("živě: proces jiné živé session ze stejné složky běží dál", potomek.poll() is None)
        over("živě: osiřelý proces mimo ~/Dev běží dál", zije(pid_venku))
        over("živě: ukončení je zapsané v logu",
             os.path.isfile(os.path.join(domov, ".agents", "logs", "uklid.log")))
        # Stejný potomek s PID session = tento test: teď je „náš“ a ukončí se.
        beh = subprocess.run([sys.executable, "-I", os.path.join(KOREN, "scripts", "uklid.py"),
                              "--slozka", slozka, "--cli-pid", str(os.getpid()), "--provest"],
                             capture_output=True, text=True, encoding="utf-8", env=prostredi)
        print("    vlastní session:", (beh.stdout + beh.stderr).strip().replace("\n", "\n    "))
        time.sleep(1)
        over("živě: proces vlastní session je ukončený", potomek.poll() is not None)
    finally:
        for pid in (pid_sirotek, pid_venku, potomek.pid):
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
