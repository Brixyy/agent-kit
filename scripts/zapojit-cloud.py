"""Doplní do .claude/settings.json projektu hooky, které v cloudové session načtou brixyy-kit.

Použití: python -I scripts/zapojit-cloud.py <cesta k .claude/settings.json>
Lokálně hooky nic nedělají (brixyy-kit tam spouští plugin). Opakované spuštění nic nezdvojí.
"""
import json
import sys

ZNACKA = "claude-kit/main/scripts/cloud-bootstrap.sh"
SESSION_START = {
    "hooks": [{
        "type": "command",
        "command": "[ \"$CLAUDE_CODE_REMOTE\" = \"true\" ] && curl -fsSL "
                   "https://raw.githubusercontent.com/Brixyy/claude-kit/main/scripts/cloud-bootstrap.sh | sh || true",
        "timeout": 120,
    }]
}
PRE_TOOL_USE = {
    "matcher": "Bash|PowerShell|Read|Edit|Write|mcp__.*",
    "hooks": [{
        "type": "command",
        "command": "[ -f \"$HOME/.claude/brixyy-kit/scripts/cloud-pojistka.sh\" ] && "
                   "sh \"$HOME/.claude/brixyy-kit/scripts/cloud-pojistka.sh\" || true",
    }],
}

cesta = sys.argv[1]
with open(cesta, encoding="utf-8") as f:
    nastaveni = json.load(f)

if ZNACKA in json.dumps(nastaveni):
    print("už zapojeno")
    sys.exit(0)

hooky = nastaveni.setdefault("hooks", {})
hooky.setdefault("SessionStart", []).append(SESSION_START)
hooky.setdefault("PreToolUse", []).append(PRE_TOOL_USE)

with open(cesta, "w", encoding="utf-8", newline="\n") as f:
    json.dump(nastaveni, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("zapojeno")
