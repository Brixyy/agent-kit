"""Napojí projekt na agent-kit: marketplace + plugin a hooky, které v cloudové session načtou agent-kit.

Použití: python -I scripts/napojit-projekt.py <cesta k .claude/settings.json>
Lokálně cloudové hooky nic nedělají (agent-kit tam spouští plugin). Starší napojení na claude-kit
nahradí; opakované spuštění nic nezdvojí.
"""
import json
import os
import sys

STARE = ("claude-kit", "brixyy-kit")
SESSION_START = {
    "hooks": [{
        "type": "command",
        "command": "[ \"$CLAUDE_CODE_REMOTE\" = \"true\" ] && curl -fsSL "
                   "https://raw.githubusercontent.com/Brixyy/agent-kit/main/scripts/cloud-bootstrap.sh | sh || true",
        "timeout": 120,
    }]
}
PRE_TOOL_USE = {
    "matcher": "Bash|PowerShell|Read|Edit|Write|mcp__.*",
    "hooks": [{
        "type": "command",
        "command": "[ -f \"$HOME/.agents/agent-kit/scripts/cloud-pojistka.sh\" ] && "
                   "sh \"$HOME/.agents/agent-kit/scripts/cloud-pojistka.sh\" || true",
    }],
}


def bez_starych(skupiny):
    return [s for s in skupiny if not any(x in json.dumps(s) for x in STARE + ("agent-kit",))]


cesta = sys.argv[1]
try:
    with open(cesta, encoding="utf-8") as f:
        nastaveni = json.load(f)
except FileNotFoundError:
    os.makedirs(os.path.dirname(os.path.abspath(cesta)), exist_ok=True)
    nastaveni = {"permissions": {"deny": [f"Read(./{n})" for n in
                 (".env", ".env.local", ".env.production", ".env.development", ".env.*.local")]}}

trhy = nastaveni.setdefault("extraKnownMarketplaces", {})
trhy.pop("claude-kit", None)
trhy["agent-kit"] = {"source": {"source": "github", "repo": "Brixyy/agent-kit"}}
pluginy = nastaveni.setdefault("enabledPlugins", {})
for k in [k for k in pluginy if k.endswith("@claude-kit")]:
    del pluginy[k]
pluginy["agent-kit@agent-kit"] = True

hooky = nastaveni.setdefault("hooks", {})
hooky["SessionStart"] = bez_starych(hooky.get("SessionStart", [])) + [SESSION_START]
hooky["PreToolUse"] = bez_starych(hooky.get("PreToolUse", [])) + [PRE_TOOL_USE]

with open(cesta, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nastaveni, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("napojeno na agent-kit")
