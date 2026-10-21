# claude-kit

Sdílená sada pro Claude Code ve všech projektech Brixyy. Jeden zdroj pravdy: co se opraví tady, platí všude.

## Co obsahuje (plugin `brixyy-kit`)
- **Kontext při startu session** (`kontext.md`) — kdo je uživatel, jak komunikovat, společný workflow.
- **Pojistka** (`hooks/pojistka.py`) — před push do main, sloučením PR, produkčním deployem, migrací produkční DB a mazáním se Claude musí zeptat; čtení `.env` je zakázané.
- **Agent `reviewer`** — nezávislá kontrola PR před sloučením.
- **Skills:** `prace-workflow` (ticket → větev → PR → kontrola → předávka), kvalita kódu, React, TypeScript, Supabase, Tailwind + shadcn, testování, plánování, brainstorming, React Flow, React Doctor.

## Zapojení do projektu
Do `.claude/settings.json` projektu:
```json
{
  "extraKnownMarketplaces": {
    "claude-kit": { "source": { "source": "github", "repo": "Brixyy/claude-kit" } }
  },
  "enabledPlugins": { "brixyy-kit@claude-kit": true }
}
```
Lokálně jednorázově: `claude plugin marketplace add Brixyy/claude-kit` a `claude plugin install brixyy-kit@claude-kit`.

## Úpravy
Změnu udělej v tomto repu přes PR, zvyš `version` v `plugins/brixyy-kit/.claude-plugin/plugin.json` a ověř `claude plugin validate .`.
Projektově specifické věci sem nepatří — ty jsou v `AGENTS.md` a `.claude/skills/` daného projektu.
