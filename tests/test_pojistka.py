"""Testy hooku pojistka: python -I tests/test_pojistka.py"""
import json
import os
import subprocess
import sys
import tempfile

# Testy běží v prázdném dočasném domově: nesmí číst ani spotřebovat skutečné ~/.agents/potvrzeno.txt
# a stará značka potvrzeno.txt.pouzito s id „test“ by jinak pustila všechny zakázané akce.
DOMOV = tempfile.mkdtemp()
PROSTREDI = dict(os.environ, HOME=DOMOV, USERPROFILE=DOMOV)

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
    ("rm " + "pojistka.py", "deny"),
    ("cd hooks && rm -f ./" + "pojistka.py", "deny"),
    ("rm hooks//" + "pojistka.py", "deny"),
    ("Remove-Item .\\" + "pojistka.py", "deny"),
    ("rm -f */" + "pojistka.py", "deny"),
    ("rm src/jiny_projekt/" + "pojistka.py", "deny"),
    ("sed -i s/a/b/ src/prove_statika/" + "pojistka.py", "PROJDE"),
    ("sed -i s/deny/allow/ hooks/hooks.json", "deny"),
    ("python -I tests/test_pojistka.py", "PROJDE"),
    ('git commit -m "pojistka.py: úprava"', "PROJDE"),
    ("claude plugin " + "disable agent-kit@agent-kit", "deny"),
    ("rm -rf " + ".github", "deny"),
    ("rm -rf " + "hooks", "deny"),
    ("rmdir /s .github\\workflows", "deny"),
    ("git checkout main -- hooks/" + "pojistka.py", "deny"),
    ("git checkout -b nova-vetev", "PROJDE"),
    ("rm tests/test_pojistka.py", "PROJDE"),
    ("cp hooks/pojistka.py /tmp/zaloha.py", "PROJDE"),
    ("docker run --rm img python hooks/pojistka.py", "PROJDE"),
    ("grep -n disableAllHooks README.md", "PROJDE"),
    # Obejití z Brixyy/agent-kit#30: spouštěč hooků, uvozovky, další zapisující příkazy, cache pluginu
    ("echo exit 0 > hooks/spust.sh", "deny"),
    ("rm hooks/spust.sh", "deny"),
    ("rm 'hooks/" + "pojistka.py'", "deny"),
    ('rm -f "hooks/' + 'pojistka.py"', "deny"),
    ("Remove-Item -LiteralPath 'C:\\Users\\Admin\\Dev\\agent-kit\\hooks\\" + "pojistka.py'", "deny"),
    ("rm 'hooks/pojistka.py '", "deny"),
    ("cp /dev/null hooks/" + "pojistka.py", "deny"),
    ("cp x.py 'hooks/" + "pojistka.py'", "deny"),
    ("Copy-Item x.py -Destination hooks\\" + "pojistka.py -Force", "deny"),
    ("Set-Content hooks\\" + "pojistka.py ''", "deny"),
    ("'' | Out-File -FilePath hooks\\" + "pojistka.py", "deny"),
    ("Clear-Content hooks/hooks.json", "deny"),
    ("find hooks -name " + "pojistka.py -delete", "deny"),
    ("find . -name 'pojistka.py' -exec rm {} \\;", "deny"),
    ("rm -rf ~/.claude/plugins/cache/" + "agent-kit", "deny"),
    ("Remove-Item -Recurse -Force C:\\Users\\Admin\\.claude\\plugins\\cache\\" + "agent-kit", "deny"),
    ("rm -rf ~/.agents/" + "agent-kit", "deny"),
    # Běžné příkazy dál projdou
    ("cat hooks/spust.sh", "PROJDE"),
    ("sh hooks/spust.sh kontext.py", "PROJDE"),
    ("cp hooks/spust.sh /tmp/x.sh", "PROJDE"),
    ("find hooks -name '*.py'", "PROJDE"),
    ("Get-Content hooks\\pojistka.py | Set-Content C:\\tmp\\kopie.py", "PROJDE"),
    ("ls ~/.claude/plugins/cache/agent-kit", "PROJDE"),
    ("rm -rf ~/.claude/plugins/cache/jiny-plugin", "PROJDE"),
    ('git commit -m "spust.sh: oprava"', "PROJDE"),
    ("rm 'notes.txt'", "PROJDE"),
    ("cp a.txt b.txt", "PROJDE"),
    # Falešné zákazy nalezené v review (zprávy commitů, grep, .git/hooks, src/hooks, workflow, find -exec čtení)
    ('git commit -m "Pojistka: hlídat cp pro spust.sh"', "PROJDE"),
    ('git commit -m "Move check into ' + 'pojistka.py"', "PROJDE"),
    ('git commit -m "Fix install of spust.sh" && git push', "PROJDE"),
    ('git commit -m "Pojistka: výjimka pro modul prove_statika/' + 'pojistka.py (2.10.2)"', "PROJDE"),
    ('gh pr create --title "Pojistka: zákaz rm pro spust.sh" --body "Closes #30"', "PROJDE"),
    ('grep -n "rm.*' + 'pojistka.py" README.md', "PROJDE"),
    ("cp scripts/pre-commit .git/hooks/", "PROJDE"),
    ("install -m 755 pre-commit .git/hooks/", "PROJDE"),
    ("cp useFoo.ts src/hooks/", "PROJDE"),
    ("Copy-Item x.ts -Destination src\\hooks\\", "PROJDE"),
    ("npm install @vueuse/hooks", "PROJDE"),
    ("New-Item -ItemType Directory -Force .github/workflows", "PROJDE"),
    ("Set-Content .github/workflows/ci.yml $obsah", "PROJDE"),
    ("New-Item -ItemType Directory src/hooks", "PROJDE"),
    ("find . -name " + "pojistka.py -exec cat {} \\;", "PROJDE"),
    ('find src/hooks -name "*.ts" -exec wc -l {} +', "PROJDE"),
    ("ln -s /c/Dev/agent-kit/hooks/spust.sh /tmp/s.sh", "PROJDE"),
    ("dd if=hooks/" + "pojistka.py of=/tmp/x.py", "PROJDE"),
    ("rm -rf .claude/worktrees/stara", "PROJDE"),
    # Obejití nalezená v review
    ("Copy-Item x.py hooks\\" + "pojistka.py -Force", "deny"),
    ("cp /dev/null hooks/" + "pojistka.py 2>/dev/null", "deny"),
    ("cp --target-directory=hooks x.py", "deny"),
    ("rsync /dev/null hooks/" + "pojistka.py", "deny"),
    ("Rename-Item hooks\\kontext.py " + "pojistka.py", "deny"),
    ("sc hooks\\" + "pojistka.py x", "deny"),
    ("ni -Force hooks\\" + "pojistka.py", "deny"),
    ("rm -rf hooks/*", "deny"),
    ("rm hooks/pojist*.py", "deny"),
    ('find . -name "pojist*" -delete', "deny"),
    ("find . -name " + "pojistka.py | xargs rm", "deny"),
    ("cd ~/.claude/plugins/cache && rm -rf " + "agent-kit", "deny"),
    ("rm -rf ~/.claude/plugins/cache/*", "deny"),
    ("rm -rf ~/.claude", "deny"),
    ("rm -rf ~/.agents", "deny"),
    ("dd if=/dev/null of=hooks/" + "pojistka.py", "deny"),
    # Druhé kolo review: cesty s proměnnou v uvozovkách, ./spust.sh, heredoc se zápisem
    ('rm -rf "$HOME/.claude/plugins/cache/' + 'agent-kit"', "deny"),
    ('rm -rf "${CLAUDE_PLUGIN_ROOT}/hooks"', "deny"),
    ('Remove-Item -Recurse -Force "$env:USERPROFILE\\.agents\\' + 'agent-kit"', "deny"),
    ('rm "$(pwd)/hooks/' + 'pojistka.py"', "deny"),
    ("rm 'hooks/[p]ojistka.py'", "deny"),
    ("cp x ./spust.sh", "deny"),
    ("cat <<EOF > hooks/" + "pojistka.py\nimport sys\nEOF", "deny"),
    ("rm -rf src/hooks", "PROJDE"),
    ("rm -rf .git/hooks", "PROJDE"),
    ("cp x.ts packages/app2/hooks/", "PROJDE"),
    # Stažení a rozbalení (Brixyy/agent-kit#41)
    ("curl -sL https://example.com/p.py -o hooks/" + "pojistka.py", "deny"),
    ("curl -o hooks/" + "pojistka.py https://example.com/p.py", "deny"),
    ("wget -O hooks/" + "pojistka.py https://example.com/p.py", "deny"),
    ("Invoke-WebRequest https://example.com/p.py -OutFile hooks\\" + "pojistka.py", "deny"),
    ("tar -xf x.tar -C hooks", "deny"),
    ("unzip -o x.zip -d hooks", "deny"),
    ("Expand-Archive x.zip -DestinationPath hooks -Force", "deny"),
    ("curl -s -o /tmp/odpoved.json https://api.example.com/hooks", "PROJDE"),
    ("curl -s https://example.com/hooks/" + "pojistka.py", "PROJDE"),
    ("tar -xf x.tar -C src/hooks", "PROJDE"),
    ("unzip x.zip -d build", "PROJDE"),
    ("tar -czf zaloha.tgz hooks", "PROJDE"),
    # Po review PR #46
    ("curl -sSLo hooks/" + "pojistka.py https://example.com/p.py", "deny"),
    ("curl --output-dir hooks -O https://example.com/p.py", "deny"),
    ("wget -P hooks https://example.com/p.py", "deny"),
    ("iwr https://example.com/p.py -Out hooks\\" + "pojistka.py", "deny"),
    ("Expand-Archive x.zip -Dest hooks", "deny"),
    ("wget -O - https://example.com/x.tgz | tar -xz -C hooks", "deny"),
    ("tar -c hooks", "PROJDE"),
    ("tar -czf /tmp/zaloha.tgz -C hooks .", "PROJDE"),
    ("tar xzf x.tgz -C hooks", "deny"),
    ("rg -n curl -o hooks/", "PROJDE"),
    ("rg tar -c hooks/", "PROJDE"),
    ("curl -O https://example.com/v1.2/hooks/readme", "PROJDE"),
    ("git commit -F - <<'EOF'\nrm hooks/" + "pojistka.py\nEOF", "PROJDE"),
    ('git commit -m "$(cat <<\'EOF\'\nOprava: rm hooks/' + 'pojistka.py\nEOF\n)"', "PROJDE"),
]


def rozhodnuti(prikaz):
    vstup = json.dumps({"tool_name": "Bash", "tool_use_id": "test", "tool_input": {"command": prikaz}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8", env=PROSTREDI).stdout
    return "deny" if '"deny"' in vystup else "PROJDE"


def codex(prikaz):
    """Režim --exit-code (Codex): zákaz = kód 2, bez tool_name."""
    vstup = json.dumps({"tool_input": {"command": prikaz}})
    vysledek = subprocess.run([sys.executable, "-I", HOOK, "--exit-code"], input=vstup, capture_output=True, text=True, encoding="utf-8", env=PROSTREDI)
    return "deny" if vysledek.returncode == 2 else "PROJDE"


sys.stdout.reconfigure(encoding="utf-8")
chyby = 0
for prikaz, ocekavano in PRIPADY:
    skutecne = rozhodnuti(prikaz)
    chyby += skutecne != ocekavano
    print(("OK    " if skutecne == ocekavano else "CHYBA ") + skutecne.ljust(7) + prikaz.replace("\n", " ⏎ ")[:70])
for nastroj, ocekavano in [("mcp__scheduled-tasks__delete_scheduled_task", "PROJDE"), ("mcp__x__delete_branch", "deny")]:
    vstup = json.dumps({"tool_name": nastroj, "tool_use_id": "test", "tool_input": {}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8", env=PROSTREDI).stdout
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
    ("Edit", "/repo/tests/test_pojistka.py", "x", "PROJDE"),
    ("Edit", "C:\\Users\\Admin\\Dev\\prove-statika\\src\\prove_statika\\pojistka.py", "x", "PROJDE"),
    ("Edit", "/home/u/.claude/plugins/cache/agent-kit/agent-kit/2.10.1/hooks/pojistka.py", "x", "deny"),
    ("Edit", "/repo/hooks/./pojistka.py", "x", "deny"),
    ("Edit", "C:\\Dev\\agent-kit\\Hooks\\Hooks.json", "x", "deny"),
    ("Edit", "/home/u/.claude/settings.json", '"agent-kit@agent-kit": false', "deny"),
    ("Edit", "/repo/hooks/spust.sh", "exit 0", "deny"),
    ("Write", "/repo/hooks/pojistka.py ", "x", "deny"),
    ("Write", "C:\\Dev\\agent-kit\\hooks\\pojistka.py. ", "x", "deny"),
    ("Edit", "/home/u/.claude/settings.json ", '"hooks": {}', "deny"),
    ("Write", "/repo/.env ", "KLIC=x", "deny"),
    ("Edit", "/repo/scripts/spustit.sh", "x", "PROJDE"),
    ("Write", "/c/Users/Admin/Dev/x/scripts/spust.sh", "x", "PROJDE"),
    ("Write", "/repo/hooks/pojistka.py::$DATA", "x", "deny"),
    ("Write", "C:\\Dev\\agent-kit\\hooks\\POJIST~1.PY", "x", "deny"),
]:
    vstup = json.dumps({"tool_name": nastroj, "tool_use_id": "test", "tool_input": {"file_path": cesta, "new_string": text}})
    vystup = subprocess.run([sys.executable, "-I", HOOK], input=vstup, capture_output=True, text=True, encoding="utf-8", env=PROSTREDI).stdout
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
