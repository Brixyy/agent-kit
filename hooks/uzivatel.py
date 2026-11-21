"""SessionStart: vloží do session výtah z paměti osobního asistenta (fakta o uživateli).

Výtah žije v soukromém repozitáři Brixyy/asistent (`pamet/pro-agenty.md`), agent-kit je veřejný
a drží jen tento kód (Brixyy/agent-kit#89). Pořadí zdrojů: `gh api` (vždy aktuální), místní
kopie `~/Dev/asistent/pamet/pro-agenty.md`. Když nejde ani jedno, háček nevloží nic a session
běží dál.

Použití:
  uzivatel.py                 JSON pro SessionStart (additionalContext)
  uzivatel.py --soubor CESTA  uloží výtah do souboru (cloud-bootstrap.sh); kód 1, když výtah není
Pro testy: AGENT_KIT_VYTAH_BEZ_GH=1 vynechá gh, AGENT_KIT_VYTAH_MISTNE přepíše místní cestu.
"""
import json
import os
import subprocess
import sys

REPO_SOUBOR = "repos/Brixyy/asistent/contents/pamet/pro-agenty.md"
LIMIT = 6_000  # vlastní rezerva; Claude Code vezme z jednoho hooku nejvýš 10 000 znaků


def z_gh():
    if os.environ.get("AGENT_KIT_VYTAH_BEZ_GH"):
        return None
    try:
        r = subprocess.run(
            ["gh", "api", REPO_SOUBOR, "-H", "Accept: application/vnd.github.raw"],
            capture_output=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 and r.stdout.strip() else None


def z_disku():
    cesta = os.environ.get("AGENT_KIT_VYTAH_MISTNE") or os.path.join(
        os.path.expanduser("~"), "Dev", "asistent", "pamet", "pro-agenty.md")
    try:
        with open(cesta, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def bez_hlavicky(text):
    """Odstraní úvodní frontmatter (--- … ---)."""
    if text.startswith("---"):
        konec = text.find("\n---", 3)
        if konec != -1:
            return text[konec + 4:].lstrip("\n")
    return text


def vytah():
    text = z_gh() or z_disku()
    if not text or not text.strip():
        return None
    text = bez_hlavicky(text.replace("\r\n", "\n")).strip()
    if len(text) > LIMIT:
        text = text[:LIMIT] + "\n…(zkráceno: výtah je delší než limit agent-kitu, zkrať pamet/pro-agenty.md)"
    return text + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    text = vytah()
    if len(sys.argv) == 3 and sys.argv[1] == "--soubor":
        if not text:
            sys.exit(1)
        os.makedirs(os.path.dirname(os.path.abspath(sys.argv[2])), exist_ok=True)
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(text)
    elif text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}, ensure_ascii=False))
