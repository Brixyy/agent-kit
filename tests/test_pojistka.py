"""Testy hooku pojistka: python -I tests/test_pojistka.py"""
import json
import os
import subprocess
import sys

HOOK = os.path.join(os.path.dirname(__file__), "..", "hooks", "pojistka.py")
PUSH = "git push origin " + "main"
MERGE = "gh pr " + "merge 5"
ENV = "cat " + ".env"

PRIPADY = [
    (PUSH, "deny"),
    ("git push origin feat/x", "PROJDE"),
    (f'gh pr create --title "x" --body "Ověřeno: {PUSH} je blokované"', "PROJDE"),
    (f"echo '{PUSH}' > /dev/null", "PROJDE"),
    (f"gh pr create --body-file - <<EOF\ntext {PUSH}\nEOF", "PROJDE"),
    (f'sh -c "{PUSH}"', "deny"),
    (f"bash -c '{MERGE}'", "PROJDE"),
    (f"{MERGE} --squash", "PROJDE"),
    (f"cd repo && {PUSH}", "deny"),
    (ENV, "deny"),
    ("cat .env.example", "PROJDE"),
    ("npx vercel --prod", "deny"),
    ("npx prisma migrate dev", "PROJDE"),
    (f"cd /c/Users/Admin/Dev/agent-kit && {PUSH}", "PROJDE"),
    (f"cd /c/Users/Admin/Dev/project-template && {PUSH}", "PROJDE"),
    (f"cd /c/Users/Admin/Dev/robotika && {PUSH}", "deny"),
    ("gh api -X " + "PATCH repos/Brixyy/asistent/issues/5 -f state=closed", "PROJDE"),
    ("gh api -X " + "PATCH repos/Brixyy/asistent -F allow_auto_merge=true", "deny"),
    ("gh api -X " + "DELETE repos/Brixyy/asistent/git/refs/heads/x", "deny"),
    ("gh api -X " + "PUT repos/Brixyy/asistent/pulls/12/merge -f merge_method=squash", "PROJDE"),
    ("gh api -X " + "PUT repos/Brixyy/asistent/branches/main/protection", "deny"),
]


def rozhodnuti(prikaz):
    vstup = json.dumps({"tool_name": "Bash", "tool_use_id": "test", "tool_input": {"command": prikaz}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8").stdout
    return "deny" if '"deny"' in vystup else "PROJDE"


def codex(prikaz):
    """Režim --exit-code (Codex): zákaz = kód 2, bez tool_name."""
    vstup = json.dumps({"tool_input": {"command": prikaz}})
    vysledek = subprocess.run([sys.executable, "-I", HOOK, "--exit-code"], input=vstup, capture_output=True, text=True, encoding="utf-8")
    return "deny" if vysledek.returncode == 2 else "PROJDE"


sys.stdout.reconfigure(encoding="utf-8")
chyby = 0
for prikaz, ocekavano in PRIPADY:
    skutecne = rozhodnuti(prikaz)
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + prikaz.replace("\n", " ⏎ ")[:70])
for nastroj, ocekavano in [("mcp__scheduled-tasks__delete_scheduled_task", "PROJDE"), ("mcp__x__delete_branch", "deny")]:
    vstup = json.dumps({"tool_name": nastroj, "tool_use_id": "test", "tool_input": {}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8").stdout
    skutecne = "deny" if '"deny"' in vystup else "PROJDE"
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + nastroj)
for prikaz, ocekavano in [(PUSH, "deny"), ("git status", "PROJDE")]:
    skutecne = codex(prikaz)
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + "codex: " + prikaz)
print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
