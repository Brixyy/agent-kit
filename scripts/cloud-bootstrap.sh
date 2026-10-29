#!/bin/sh
# Cloudová session (claude.ai/code) neinstaluje pluginy z nastavení repozitáře.
# Tento skript spouští SessionStart hook projektu jen v cloudu: stáhne agent-kit,
# nainstaluje plugin a vypíše globální pravidla do kontextu session.
# Pojistku spouští PreToolUse hook projektu přes cloud-pojistka.sh ze staženého kitu.
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0

KIT="$HOME/.agents/agent-kit"
if [ -d "$KIT/.git" ]; then
  git -C "$KIT" pull -q --ff-only >/dev/null 2>&1
else
  mkdir -p "$HOME/.agents"
  git clone -q --depth 1 https://github.com/Brixyy/agent-kit.git "$KIT" >/dev/null 2>&1
fi
[ -f "$KIT/global/AGENTS.md" ] || { echo "agent-kit: stažení selhalo, globální pravidla ani pojistka nejsou načtené."; exit 0; }

# Skills a agent reviewer i mimo plugin (kdyby se plugin nenačetl).
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
cp -R "$KIT/skills/." "$HOME/.claude/skills/" 2>/dev/null
cp "$KIT/agents/"*.md "$HOME/.claude/agents/" 2>/dev/null

if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add Brixyy/agent-kit >/dev/null 2>&1
  claude plugin install agent-kit@agent-kit >/dev/null 2>&1
fi

echo "# agent-kit (cloud)"
echo "Globální pravidla načtena skriptem cloud-bootstrap.sh; pojistka běží přes PreToolUse hook projektu."
echo
cat "$KIT/global/AGENTS.md"
echo
echo "Podrobnosti globálních pravidel: \`$KIT/global/PODROBNOSTI.md\`"
