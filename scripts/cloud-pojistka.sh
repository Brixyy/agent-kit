#!/bin/sh
# PreToolUse hook projektu: v cloudu spustí pojistku ze staženého agent-kitu.
# Lokálně nedělá nic (pojistku tam spouští plugin agent-kit).
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0
P="$HOME/.agents/agent-kit/hooks/pojistka.py"
[ -f "$P" ] || exit 0
if command -v python3 >/dev/null 2>&1; then exec python3 -I "$P"; fi
exec python -I "$P"
