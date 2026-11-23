"""SessionStart a UserPromptSubmit: upozorní dlouho běžící session na novou verzi agent-kitu.

Jádro pravidel vkládá hooks/kontext.py jen při SessionStart, takže session běžící dny drží
pravidla ze svého startu (Brixyy/asistent#344).
- SessionStart (i resume, clear, compact; kontext.py tehdy vloží pravidla znovu): zapamatuje si
  verzi pluginu, se kterou session běží (`.claude-plugin/plugin.json` v CLAUDE_PLUGIN_ROOT).
- UserPromptSubmit: najde nejnovější nainstalovanou verzi (sousední složky v cache pluginu
  `~/.claude/plugins/cache/agent-kit/agent-kit/<verze>/`). Když je novější než verze session,
  vloží jednou na každou novou verzi krátké upozornění přes additionalContext.
Stav je v ${CLAUDE_PLUGIN_DATA}/verze/<session_id>.json (bez té proměnné ~/.agents/stav/verze;
AGENT_KIT_STAV mění složku pro testy). Starou verzi drží Claude Code po aktualizaci 14 dní
(značka .orphaned_at), takže hook ze staré složky session do té doby běží.
Hook nikdy neblokuje ani neselže: při jakékoli chybě skončí potichu.
Test: python -I tests/test_verze.py
"""
import json
import os
import re
import sys
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERZE = re.compile(r"^\d+(\.\d+)*$")
STARI = 30 * 24 * 3600  # stav sessions starší 30 dní se při SessionStart smaže


def slozka_stavu():
    data = os.environ.get("CLAUDE_PLUGIN_DATA")  # trvalá složka pluginu, přežije aktualizace
    return (os.environ.get("AGENT_KIT_STAV") or (data and os.path.join(data, "verze"))
            or os.path.join(os.path.expanduser("~"), ".agents", "stav", "verze"))


def koren():
    return os.environ.get("CLAUDE_PLUGIN_ROOT") or KIT


def verze_pluginu(slozka):
    with open(os.path.join(slozka, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        return str(json.load(f)["version"])


def klic(verze):
    return tuple(int(c) for c in verze.split("."))


def nejnovejsi(root):
    """(verze, složka) nejvyšší platné verze v cache vedle root (s plugin.json a jádrem, bez .orphaned_at); jinak None."""
    cache = os.path.dirname(os.path.normpath(root))
    nalezene = []
    for nazev in os.listdir(cache):
        cesta = os.path.join(cache, nazev)
        if (VERZE.match(nazev) and os.path.isfile(os.path.join(cesta, ".claude-plugin", "plugin.json"))
                and os.path.isfile(os.path.join(cesta, "global", "AGENTS.md"))  # ne rozbalovaná
                and not os.path.exists(os.path.join(cesta, ".orphaned_at"))):  # odinstalovaná verze
            nalezene.append((klic(nazev), nazev, cesta))
    if not nalezene:
        return None
    _, nazev, cesta = max(nalezene)
    return nazev, cesta


def soubor_stavu(session_id):
    bezpecne = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    return os.path.join(slozka_stavu(), bezpecne + ".json")


def nacti(session_id):
    try:
        with open(soubor_stavu(session_id), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def uloz(session_id, stav):
    os.makedirs(slozka_stavu(), exist_ok=True)
    with open(soubor_stavu(session_id), "w", encoding="utf-8") as f:
        json.dump(stav, f)


def uklid_stary():
    hranice = time.time() - STARI
    for nazev in os.listdir(slozka_stavu()):
        cesta = os.path.join(slozka_stavu(), nazev)
        try:
            if nazev.endswith(".json") and os.path.getmtime(cesta) < hranice:
                os.remove(cesta)
        except OSError:
            pass


def upozorneni(nova, slozka, stara):
    globalni = os.path.join(slozka, "global")
    return (
        f"Vyšla nová verze agent-kitu {nova} (session běží na {stara}). Přečti si nové jádro "
        f"`{os.path.join(globalni, 'AGENTS.md')}` a změny v podrobnostech "
        f"`{os.path.join(globalni, 'PODROBNOSTI.md')}`, řiď se jimi a jednou větou to ohlas uživateli."
    )


def zpracuj(vstup):
    """Vrátí JSON výstupu hooku (dict) nebo None."""
    session_id = vstup.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return None
    udalost = vstup.get("hook_event_name")
    if udalost == "SessionStart":
        uloz(session_id, {"start": verze_pluginu(koren()), "oznameno": None})
        uklid_stary()
        return None
    if udalost != "UserPromptSubmit":
        return None
    stav = nacti(session_id)
    if not stav or not stav.get("start"):  # session bez záznamu: běží na verzi tohoto hooku
        stav = {"start": verze_pluginu(koren()), "oznameno": None}
        uloz(session_id, stav)
    nalez = nejnovejsi(koren())
    if not nalez:
        return None
    nova, slozka = nalez
    zname = max((v for v in (stav["start"], stav.get("oznameno")) if v), key=klic)
    if klic(nova) <= klic(zname):
        return None
    stav["oznameno"] = nova
    uloz(session_id, stav)
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                   "additionalContext": upozorneni(nova, slozka, stav["start"])}}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
        vysledek = zpracuj(json.load(sys.stdin))
        if vysledek:
            print(json.dumps(vysledek, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)
