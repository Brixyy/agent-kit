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
    ("grep API_KEY " + ".env", "deny"),
    ("set -a; . ./" + ".env; set +a; npm run dev", "PROJDE"),
    ("node --env-file=" + ".env app.js", "PROJDE"),
    ("cat " + ".env.staging", "deny"),
    ("rg KEY " + ".env", "deny"),
    ("cat<" + ".env", "deny"),
    ("cat " + ".env.sample", "PROJDE"),
    ("python -I scripts/env_nastav.py " + ".env NAZEV < hodnota.txt", "PROJDE"),
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
    # Vlastní kontroly (Brixyy/asistent#105)
    ("gh workflow " + "disable ci.yml", "deny"),
    ("gh workflow run ci.yml", "PROJDE"),
    ("git rm .github/workflows/ci.yml", "deny"),
    ("rm -f .github\\workflows\\ci.yml", "deny"),
    ("cat .github/workflows/ci.yml", "PROJDE"),
    ("rm hooks/" + "pojistka.py", "deny"),
    ("echo x > hooks/" + "pojistka.py", "deny"),
    ("sed -i s/deny/allow/ hooks/hooks.json", "deny"),
    ("python -I tests/test_pojistka.py", "PROJDE"),
    ('git commit -m "pojistka.py: úprava"', "PROJDE"),
    ("claude plugin " + "disable agent-kit@agent-kit", "deny"),
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
for nastroj, cesta, text, ocekavano in [
    ("Edit", "C:\\Users\\Admin\\Dev\\agent-kit\\hooks\\pojistka.py", "x", "deny"),
    ("Write", "/home/u/.codex/hooks.json", "{}", "deny"),
    ("Edit", "C:\\Users\\Admin\\.claude\\settings.json", '"hooks": {}', "deny"),
    ("Edit", "/repo/.claude/settings.local.json", '"permissions": {"allow": []}', "PROJDE"),
    ("Edit", "/repo/.github/workflows/ci.yml", "timeout-minutes: 10", "PROJDE"),
    ("Read", "/repo/hooks/pojistka.py", "", "PROJDE"),
]:
    vstup = json.dumps({"tool_name": nastroj, "tool_use_id": "test", "tool_input": {"file_path": cesta, "new_string": text}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8").stdout
    skutecne = "deny" if '"deny"' in vystup else "PROJDE"
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + nastroj + " " + cesta)
for prikaz, ocekavano in [(PUSH, "deny"), ("git status", "PROJDE")]:
    skutecne = codex(prikaz)
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + "codex: " + prikaz)


def s_potvrzenim(obsah, prikazy, stari_s=0):
    """Spustí příkazy postupně s potvrzením v dočasném domově; vrátí rozhodnutí a zda soubor zůstal."""
    import tempfile
    import time
    domov = tempfile.mkdtemp()
    os.makedirs(os.path.join(domov, ".agents"))
    soubor = os.path.join(domov, ".agents", "potvrzeno.txt")
    with open(soubor, "w", encoding="utf-8") as f:
        f.write(obsah)
    if stari_s:
        os.utime(soubor, (time.time() - stari_s,) * 2)
    prostredi = dict(os.environ, HOME=domov, USERPROFILE=domov)
    vysledky = []
    for i, prikaz in enumerate(prikazy):
        vstup = json.dumps({"tool_name": "Bash", "tool_use_id": f"t{i}", "tool_input": {"command": prikaz}})
        vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True,
                                encoding="utf-8", env=prostredi).stdout
        vysledky.append("deny" if '"deny"' in vystup else "PROJDE")
    return vysledky, os.path.exists(soubor)


VERCEL = "npx vercel --prod"
SUPA = "supabase db push"
for nazev, obsah, prikazy, ocekavano, stari in [
    ("jednorázové: jen jednou", "ano", [PUSH, PUSH], ["PROJDE", "deny"], 0),
    ("dávka: všechny kroky, opakovaně", "krok: vercel --prod\nkrok: supabase db push\n", [VERCEL, SUPA, SUPA, VERCEL], ["PROJDE"] * 4, 0),
    ("dávka: jiný krok zastaví", "krok: supabase db push\n", [PUSH, SUPA], ["deny", "PROJDE"], 0),
    ("dávka: po 15 minutách neplatí", "krok: supabase db push\n", [SUPA], ["deny"], 16 * 60),
]:
    skutecne, _ = s_potvrzenim(obsah, prikazy, stari)
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + nazev + " " + str(skutecne))

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
