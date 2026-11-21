"""Test háčku s výtahem z paměti asistenta: python -I tests/test_uzivatel.py

Háček nesmí session nikdy rozbít: bez výtahu nevypíše nic, s výtahem platný JSON pod limitem
Claude Code (10 000 znaků z jednoho hooku). V CI se gh vypíná, výtah se bere z dočasného souboru.
"""
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
KOREN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HAK = os.path.join(KOREN, "hooks", "uzivatel.py")
LIMIT = 10_000


def spust(obsah=None, *argumenty, bez_gh_v_path=False, kodovani="utf-8"):
    with tempfile.TemporaryDirectory() as tmp:
        cesta = os.path.join(tmp, "pro-agenty.md")
        if obsah is not None:
            with open(cesta, "w", encoding=kodovani) as f:
                f.write(obsah)
        env = dict(os.environ, AGENT_KIT_VYTAH_BEZ_GH="1", AGENT_KIT_VYTAH_MISTNE=cesta)
        if bez_gh_v_path:  # skutečné volání gh, které selže (gh není k nalezení)
            env.pop("AGENT_KIT_VYTAH_BEZ_GH")
            env["PATH"] = tmp
        args = [a.replace("{tmp}", tmp) for a in argumenty]
        r = subprocess.run([sys.executable, "-I", HAK, *args], capture_output=True, text=True, encoding="utf-8", env=env)
        soubor = os.path.join(tmp, "vystup", "pro-agenty.md")
        ulozeno = open(soubor, encoding="utf-8").read() if os.path.isfile(soubor) else None
        return r, ulozeno


VZOR = "---\ntyp: vytah\n---\n# Uživatel\n\n- Vkus: střídmý obsah.\n"

chyby = 0
r, _ = spust(None)
r2, _ = spust(VZOR)
text = json.loads(r2.stdout)["hookSpecificOutput"]["additionalContext"] if r2.stdout.strip() else ""
r3, _ = spust("x" * 20_000)
dlouhy = json.loads(r3.stdout)["hookSpecificOutput"]["additionalContext"] if r3.stdout.strip() else ""
r4, ulozeno = spust(VZOR, "--soubor", "{tmp}/vystup/pro-agenty.md")
r5, _ = spust(None, "--soubor", "{tmp}/vystup/pro-agenty.md")
r6, _ = spust(None, bez_gh_v_path=True)
r7, _ = spust(VZOR, kodovani="utf-8-sig")
s_bom = json.loads(r7.stdout)["hookSpecificOutput"]["additionalContext"] if r7.stdout.strip() else ""
r8, _ = spust("---\nx\n---\nvkus: čšř\n", kodovani="cp1250")
bootstrap = open(os.path.join(KOREN, "scripts", "cloud-bootstrap.sh"), encoding="utf-8").read()
hooky = json.load(open(os.path.join(KOREN, "hooks", "hooks.json"), encoding="utf-8"))
start = [h["command"] for b in hooky["hooks"]["SessionStart"] for h in b["hooks"]]

for nazev, ok in [
    ("bez výtahu nic nevypíše a skončí bez chyby", r.returncode == 0 and not r.stdout.strip()),
    ("s výtahem vloží text bez frontmatteru", r2.returncode == 0 and "střídmý obsah" in text and "typ: vytah" not in text),
    (f"dlouhý výtah zkrátí pod limit ({len(dlouhy)} ≤ {LIMIT})", 0 < len(dlouhy) <= LIMIT and "zkráceno" in dlouhy),
    ("--soubor uloží výtah (cloud)", r4.returncode == 0 and ulozeno and "střídmý obsah" in ulozeno),
    ("--soubor bez výtahu skončí kódem 1", r5.returncode == 1),
    ("bez gh a bez výtahu nic nevypíše a skončí bez chyby", r6.returncode == 0 and not r6.stdout.strip()),
    ("soubor s BOM: frontmatter odstraněn", "střídmý obsah" in s_bom and "typ: vytah" not in s_bom),
    ("soubor v cp1250 háček neshodí", r8.returncode == 0 and "vkus" in r8.stdout),
    ("háček je zapsaný v SessionStart", any("uzivatel.py" in c for c in start)),
    ("cloud-bootstrap.sh výtah ukládá a dává jen odkaz", "uzivatel.py\" --soubor" in bootstrap and "pro-agenty.md" in bootstrap),
]:
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev)

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
