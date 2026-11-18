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

PLUGIN=0
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add Brixyy/agent-kit >/dev/null 2>&1
  claude plugin install agent-kit@agent-kit >/dev/null 2>&1
  # Jen zapnutý plugin v rozsahu uživatele; jinak (i bez node) záloha kopiemi.
  claude plugin list --json 2>/dev/null | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{try{process.exit(JSON.parse(s).some(p=>p.id==="agent-kit@agent-kit"&&p.scope==="user"&&p.enabled)?0:1)}catch(e){process.exit(1)}})' 2>/dev/null && PLUGIN=1
fi

# Skills a agenty dodává plugin (jako agent-kit:…). Kopie v ~/.claude jen jako
# záloha, když se plugin nenainstaloval; jinak by byly dvakrát (Brixyy/asistent#211).
for d in "$KIT"/skills/*/; do
  [ -e "$d" ] || continue
  n=$(basename "$d")
  if [ "$PLUGIN" = 1 ]; then rm -rf "$HOME/.claude/skills/$n"; else mkdir -p "$HOME/.claude/skills" && cp -R "$d" "$HOME/.claude/skills/"; fi
done
for f in "$KIT"/agents/*.md; do
  [ -e "$f" ] || continue
  n=$(basename "$f")
  if [ "$PLUGIN" = 1 ]; then rm -f "$HOME/.claude/agents/$n"; else mkdir -p "$HOME/.claude/agents" && cp "$f" "$HOME/.claude/agents/"; fi
done

echo "# agent-kit (cloud)"
echo "Globální pravidla načtena skriptem cloud-bootstrap.sh; pojistka běží přes PreToolUse hook projektu."
echo
cat "$KIT/global/AGENTS.md"
echo
echo "Podrobnosti globálních pravidel: \`$KIT/global/PODROBNOSTI.md\`"
