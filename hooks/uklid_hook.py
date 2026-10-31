"""SessionEnd a SessionStart: úklid procesů a kontejnerů po sessions (jen Windows).

- SessionEnd: ukončí dev servery z pracovní složky končící session (její worktree) a zastaví
  kontejnery se štítkem agent-kit.slozka=<složka>.
- SessionStart: ukončí sirotky v celém ~/Dev (dev servery sessions, které skončily bez úklidu,
  např. po pádu nebo zavření aplikace).
Claude Code dává SessionEnd hookům pluginu dohromady jen 1,5 s, proto hook jen zjistí složku
a PID session (claude.exe nad tímto procesem) a samotný úklid (scripts/uklid.py) spustí na pozadí
jako odpojený proces. Výsledek je v ~/.agents/logs/uklid.log. Hook nikdy neblokuje ani neselže.
"""
import json
import os
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UKLID = os.path.join(KIT, "scripts", "uklid.py")


def rodice():
    """{pid: (ppid, jméno)} přes Toolhelp32 (rychlé, bez PowerShellu)."""
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snimek = k32.CreateToolhelp32Snapshot(0x2, 0)
    zaznam = PROCESSENTRY32W()
    zaznam.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    vysledek = {}
    ok = k32.Process32FirstW(snimek, ctypes.byref(zaznam))
    while ok:
        vysledek[zaznam.th32ProcessID] = (zaznam.th32ParentProcessID, zaznam.szExeFile.lower())
        ok = k32.Process32NextW(snimek, ctypes.byref(zaznam))
    k32.CloseHandle(snimek)
    return vysledek


def pid_session():
    """PID nejbližšího claude.exe nad tímto hookem (CLI session, ne aplikace Claude nad ní)."""
    tabulka = rodice()
    pid, videno = os.getpid(), set()
    while pid in tabulka and pid not in videno:
        videno.add(pid)
        pid, jmeno = tabulka[pid]
        if tabulka.get(pid, (0, ""))[1] == "claude.exe":
            return pid
    return 0


def pracovni_slozka(cwd):
    """Kořen worktree (git), jinak cwd. Session mohla během práce udělat cd do podsložky.
    Samotná složka projektů (~/Dev) je taky git repozitář; ten se za kořen nebere."""
    dev = os.path.normcase(os.path.normpath(os.environ.get("AGENT_KIT_DEV") or os.path.join(os.path.expanduser("~"), "Dev")))
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=0.8)
        koren = os.path.normpath(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else ""
        if koren and os.path.normcase(koren) != dev:
            return koren
    except (OSError, subprocess.TimeoutExpired):
        pass
    return cwd


def spust_na_pozadi(argumenty, prostredi):
    prikaz = [sys.executable, "-I", UKLID, "--provest", *argumenty]
    zaklad = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    logy = os.path.join(os.path.expanduser("~"), ".agents", "logs")
    os.makedirs(logy, exist_ok=True)
    with open(os.path.join(logy, "uklid-vystup.txt"), "w", encoding="utf-8") as vystup:  # poslední běh
        for priznaky in (zaklad | 0x01000000, zaklad):  # nejdřív CREATE_BREAKAWAY_FROM_JOB
            try:
                subprocess.Popen(prikaz, env=prostredi, creationflags=priznaky, close_fds=True,
                                 stdin=subprocess.DEVNULL, stdout=vystup, stderr=vystup)
                return
            except OSError:
                continue


def main():
    if os.name != "nt":
        return
    try:
        vstup = json.load(sys.stdin)
    except ValueError:
        vstup = {}
    prostredi = dict(os.environ)
    if vstup.get("hook_event_name") == "SessionEnd":
        prostredi["AGENT_KIT_UKLID_SLOZKA"] = pracovni_slozka(vstup.get("cwd") or os.getcwd())
        prostredi["AGENT_KIT_UKLID_CLI_PID"] = str(pid_session())
        spust_na_pozadi([], prostredi)
    else:
        spust_na_pozadi(["--sirotci"], prostredi)


if __name__ == "__main__":
    try:
        main()
    except Exception as chyba:  # úklid nesmí nikdy rozbít start ani konec session
        print(f"agent-kit úklid: {chyba}", file=sys.stderr)
    sys.exit(0)
