"""Test hooku rámečku „Pro tebe“: python -I tests/test_pro_tebe.py"""
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "pro_tebe.py")
DLOUHY = "Podrobnost. " * 60
ZAPNUTO = tempfile.mkdtemp()  # projekt se zapnutým stylem; má přednost před ~/.claude/settings.json
VYPNUTO = tempfile.mkdtemp()  # projekt s jiným stylem
for slozka, styl in [(ZAPNUTO, "agent-kit:Pro tebe"), (VYPNUTO, "default")]:
    os.makedirs(os.path.join(slozka, ".claude"))
    with open(os.path.join(slozka, ".claude", "settings.local.json"), "w", encoding="utf-8") as f:
        json.dump({"outputStyle": styl}, f)


def spust(vstup):
    if isinstance(vstup, dict):
        vstup = {"cwd": ZAPNUTO, **vstup}
    data = vstup if isinstance(vstup, str) else json.dumps(vstup, ensure_ascii=False)
    p = subprocess.run([sys.executable, "-I", HOOK], input=data, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout.strip()


def blokuje(vstup):
    kod, out = spust(vstup)
    return kod == 0 and out != "" and json.loads(out)["decision"] == "block"


def pusti(vstup):
    kod, out = spust(vstup)
    return kod == 0 and out == ""


pripady = [
    ("dlouhá zpráva bez rámečku se vrátí", blokuje({"last_assistant_message": DLOUHY})),
    ("dlouhá zpráva s rámečkem projde", pusti({"last_assistant_message": "> 📌 **Pro tebe:** schval PR.\n\n---\n\n" + DLOUHY})),
    ("rámeček „nic“ projde", pusti({"last_assistant_message": "\n> ✅ **Pro tebe:** nic, běží to samo.\n\n---\n" + DLOUHY})),
    ("nadpis s pruhem projde", pusti({"last_assistant_message": "### 👉 Pro tebe: schval PR\n\n👉 `Potřebuji tě` schval\n" + DLOUHY})),
    ("rámeček až dole nestačí", blokuje({"last_assistant_message": DLOUHY + "\n> 📌 **Pro tebe:** x"})),
    ("krátká odpověď projde", pusti({"last_assistant_message": "Ano, je to v main."})),
    ("druhý pokus projde (žádná smyčka)", pusti({"last_assistant_message": DLOUHY, "stop_hook_active": True})),
    ("jiný styl → hook nic nevynucuje", pusti({"cwd": VYPNUTO, "last_assistant_message": DLOUHY})),
    ("zpráva začínající JSON projde", pusti({"last_assistant_message": "{\"a\": 1}\n" + DLOUHY})),
    ("chybí zpráva → projde", pusti({})),
    ("rozbitý vstup → projde", pusti("není json")),
]

chyby = 0
for nazev, ok in pripady:
    print(("OK   " if ok else "CHYBA ") + nazev)
    chyby += not ok
sys.exit(1 if chyby else 0)
