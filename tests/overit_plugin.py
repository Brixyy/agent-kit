"""Ověří nainstalovanou kopii pluginu: python -I tests/overit_plugin.py <složka pluginu>"""
import json
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
koren = sys.argv[1]
kontext = subprocess.run(["sh", f"{koren}/hooks/spust.sh", "kontext.py"], capture_output=True, text=True, encoding="utf-8").stdout
text = json.loads(kontext)["hookSpecificOutput"]["additionalContext"]
print("kontext:", text.splitlines()[0], f"({len(text)} znaků)")
vstup = json.dumps({"tool_name": "Bash", "tool_use_id": "x", "tool_input": {"command": "git push origin " + "main"}})
pojistka = subprocess.run(["sh", f"{koren}/hooks/spust.sh", "pojistka.py"], input=vstup, capture_output=True, text=True, encoding="utf-8").stdout
print("pojistka:", "blokuje push do main" if '"deny"' in pojistka else "NEBLOKUJE")
