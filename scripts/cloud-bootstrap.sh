#!/bin/sh
# Cloudová session (claude.ai/code) neinstaluje pluginy z nastavení repozitáře.
# Tento skript spouští SessionStart hook projektu jen v cloudu: stáhne claude-kit,
# zkusí nainstalovat plugin a vypíše společná pravidla do kontextu session.
# Pojistku spouští PreToolUse hook projektu přímo ze staženého claude-kit.
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0

KIT="$HOME/.claude/brixyy-kit"
if [ -d "$KIT/.git" ]; then
  git -C "$KIT" pull -q --ff-only >/dev/null 2>&1
else
  git clone -q --depth 1 https://github.com/Brixyy/claude-kit.git "$KIT" >/dev/null 2>&1
fi
[ -f "$KIT/plugins/brixyy-kit/kontext.md" ] || { echo "brixyy-kit: stažení claude-kit selhalo, pravidla nejsou načtená."; exit 0; }

# Skills a agent reviewer jako uživatelské (načtou se, pokud je session vidí po startu).
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
cp -R "$KIT/plugins/brixyy-kit/skills/." "$HOME/.claude/skills/" 2>/dev/null
cp "$KIT/plugins/brixyy-kit/agents/"*.md "$HOME/.claude/agents/" 2>/dev/null

# Plugin (pro případ, že ho session po /reload-plugins načte celý).
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add Brixyy/claude-kit >/dev/null 2>&1
  claude plugin install brixyy-kit@claude-kit >/dev/null 2>&1
fi

echo "# brixyy-kit (cloud)"
echo "Společná pravidla načtena skriptem cloud-bootstrap.sh; pojistka běží přes PreToolUse hook projektu."
echo
cat "$KIT/plugins/brixyy-kit/kontext.md"
