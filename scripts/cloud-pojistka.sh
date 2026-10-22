#!/bin/sh
# PreToolUse hook projektu: v cloudu spustí pojistku ze staženého claude-kit.
# Lokálně nedělá nic (pojistku tam spouští plugin brixyy-kit).
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0
P="$HOME/.claude/brixyy-kit/plugins/brixyy-kit/hooks/pojistka.py"
[ -f "$P" ] || exit 0
if command -v python3 >/dev/null 2>&1; then exec python3 -I "$P"; fi
exec python -I "$P"
