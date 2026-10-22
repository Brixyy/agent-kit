# claude-kit

Sdílená sada pro Claude Code ve všech projektech Brixyy. Jeden zdroj pravdy: co se opraví tady, platí všude.

## Co obsahuje (plugin `brixyy-kit`)
- **Kontext při startu session** (`kontext.md`) — kdo je uživatel, jak komunikovat, společný workflow.
- **Pojistka** (`hooks/pojistka.py`) — před přímým push do main, ručním produkčním deployem, migrací produkční DB a mazáním se Claude musí zeptat; čtení `.env` je zakázané. Sloučení PR pojistka neblokuje (uživatel ho trvale povolil).
- **Agent `reviewer`** — nezávislá kontrola PR před sloučením.
- **Skills:** `prace-workflow` (ticket v GitHub Issues, u robotiky v Linearu → větev → PR → kontrola → předávka), kvalita kódu, React, TypeScript, Supabase, Tailwind + shadcn, testování, plánování, brainstorming, React Flow, React Doctor.

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

## Testy
`python -I tests/test_pojistka.py` ověří, že pojistka zastaví rizikové příkazy a nereaguje na text v popisu PR.

## Cloud (claude.ai/code)
Cloudová session pluginy z `.claude/settings.json` projektu neinstaluje. Projekty proto mají hooky (generuje `scripts/zapojit-cloud.py`), které v cloudu spustí `scripts/cloud-bootstrap.sh` (stáhne tento repozitář, nainstaluje plugin, vloží pravidla) a `scripts/cloud-pojistka.sh` (pojistka). Lokálně nedělají nic. Repozitář je proto **veřejný** — nepatří sem hesla, ID projektů ani údaje o zákaznících.

Postup převodu existujícího projektu: [`docs/prevod-projektu.md`](docs/prevod-projektu.md).

## Verze
`HLAVNÍ.VEDLEJŠÍ.OPRAVA` v `plugins/brixyy-kit/.claude-plugin/plugin.json` — oprava chyby → poslední číslo, nové pravidlo/skill → prostřední, změna vyžadující úpravu všech projektů → první. Verze se nikdy nesnižuje (plugin se aktualizuje jen na vyšší číslo).
