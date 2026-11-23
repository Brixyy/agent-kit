"""Test hooku nové verze agent-kitu: python -I tests/test_verze.py

Na dočasné cache pluginu (složky <verze>/.claude-plugin/plugin.json) ověří: session si při
startu zapamatuje verzi, na novější verzi upozorní jednou, na starší ani stejnou ne, chyby
skončí potichu s kódem 0. Hook se spouští stejně jako v Claude Code (stdin JSON, proměnné).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "verze.py")
TMP = tempfile.mkdtemp()
CACHE = os.path.join(TMP, "cache", "agent-kit", "agent-kit")
STAV = os.path.join(TMP, "stav")


def verze(nazev, s_manifestem=True):
    slozka = os.path.join(CACHE, nazev)
    os.makedirs(os.path.join(slozka, ".claude-plugin"), exist_ok=True)
    if s_manifestem:
        with open(os.path.join(slozka, ".claude-plugin", "plugin.json"), "w", encoding="utf-8") as f:
            json.dump({"name": "agent-kit", "version": nazev}, f)
    return slozka


def spust(vstup, root):
    data = vstup if isinstance(vstup, str) else json.dumps(vstup)
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": root, "AGENT_KIT_STAV": STAV}
    p = subprocess.run([sys.executable, "-I", HOOK], input=data, capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=5)
    return p.returncode, p.stdout.strip()


def start(sid, root):
    return spust({"hook_event_name": "SessionStart", "session_id": sid, "source": "startup"}, root)


def zprava(sid, root):
    kod, out = spust({"hook_event_name": "UserPromptSubmit", "session_id": sid, "prompt": "ahoj"}, root)
    if kod != 0:
        return "KÓD %d" % kod
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


chyby = 0


def over(nazev, ok):
    global chyby
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev)


try:
    stara = verze("2.9.0")
    over("start session nic nevypíše", start("s1", stara) == (0, ""))
    over("bez nové verze žádné upozornění", zprava("s1", stara) == "")

    verze("2.10.0", s_manifestem=False)  # rozbalovaná / neúplná složka se nepočítá
    verze("neni-verze")
    over("neúplná složka ani cizí název nevadí", zprava("s1", stara) == "")

    nova = verze("2.10.1")  # 2.10.1 > 2.9.0 číselně, ne podle abecedy
    text = zprava("s1", stara)
    over("novější verze → upozornění s verzemi",
         "agent-kitu 2.10.1" in text and "běží na 2.9.0" in text)
    over("upozornění ukazuje na nové jádro a podrobnosti",
         os.path.join(nova, "global", "AGENTS.md") in text and "PODROBNOSTI.md" in text)
    over("upozornění žádá ohlásit uživateli", "ohlas uživateli" in text)
    over("stejná verze podruhé neupozorní", zprava("s1", stara) == "")

    verze("2.11.0")
    over("další nová verze upozorní znovu", "agent-kitu 2.11.0" in zprava("s1", stara))
    over("a zase jen jednou", zprava("s1", stara) == "")

    open(os.path.join(verze("3.0.0"), ".orphaned_at"), "w").close()  # odinstalovaná verze
    over("verze se značkou .orphaned_at se nepočítá", zprava("s1", stara) == "")

    over("session startovaná na nejnovější verzi nic nedostane",
         start("s2", os.path.join(CACHE, "2.11.0")) == (0, "") and zprava("s2", os.path.join(CACHE, "2.11.0")) == "")
    over("resume na nové verzi vynuluje stav (pravidla vložena znovu)",
         start("s1", os.path.join(CACHE, "2.11.0")) == (0, "") and zprava("s1", stara) == "")

    over("session bez záznamu ze startu bere verzi hooku",
         "běží na 2.9.0" in zprava("s3", stara))
    over("zvláštní znaky v session_id nezapíšou mimo složku stavu",
         zprava("../../ven", stara) != "KÓD 1" and not os.path.exists(os.path.join(TMP, "ven.json")))

    over("rozbitý vstup → tichý konec", spust("není json", stara) == (0, ""))
    over("chybí session_id → tichý konec", spust({"hook_event_name": "UserPromptSubmit"}, stara) == (0, ""))
    over("neexistující plugin → tichý konec",
         spust({"hook_event_name": "UserPromptSubmit", "session_id": "s4"}, os.path.join(TMP, "nic", "1.0.0")) == (0, ""))
    over("jiná událost → nic", spust({"hook_event_name": "Stop", "session_id": "s1"}, stara) == (0, ""))
finally:
    shutil.rmtree(TMP, ignore_errors=True)

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
