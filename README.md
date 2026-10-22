# agent-kit

Společná pravidla a nástroje pro AI agenty ve všech projektech Brixyy — nezávislé na konkrétním nástroji (Claude Code, Codex, …). Jeden zdroj pravdy: co se opraví tady, platí všude. Repozitář je **veřejný**: nepatří sem hesla, klíče, ID projektů ani údaje o zákaznících.

## Co obsahuje
| Složka | Co | Formát |
|---|---|---|
| `global/AGENTS.md` | Globální pravidla: kdo je uživatel, komunikace, pravdivost, autonomie, způsob práce, orchestrace | prostý Markdown (čte každý agent) |
| `skills/` | Vlastní pracovní postupy: `prace-workflow`, `predavka`, `rozhodnuti`, `nez-zacnes-stavet`, `prevod-projektu`, `poznamka` (zápis do osobního asistenta Brixyy/asistent) | otevřený standard Agent Skills (`SKILL.md`) |
| `agents/reviewer.md` | Nezávislá kontrola PR před sloučením | subagent Claude Code |
| `hooks/pojistka.py` | Zastaví nevratné a produkční akce, zakáže čtení `.env` | Claude Code (JSON) i Codex (`--exit-code`) |
| `scripts/` | `install.py` (počítač, Codex), `napojit-projekt.py` (projekt), `cloud-bootstrap.sh` + `cloud-pojistka.sh` (cloudové sessions) | |

Kam patří které pravidlo: **celé portfolio** → tento repozitář · **jeden projekt** → `AGENTS.md` projektu · **jen tento počítač** → lokální soubory agenta.

## Instalace
**Claude Code** (plugin, kořen repozitáře je plugin):
```
/plugin install agent-kit --marketplace Brixyy/agent-kit
```
nebo v terminálu `claude plugin marketplace add Brixyy/agent-kit` a `claude plugin install agent-kit@agent-kit`. Plugin vloží globální pravidla do každé session, přidá skills, agenta `reviewer` a pojistku.

**Codex a další agenti** na tomto počítači: `python -I scripts/install.py` — zkopíruje pravidla do `~/.agents/AGENTS.md` a `~/.codex/AGENTS.md`, skills do `~/.agents/skills/` a napojí pojistku do `~/.codex/hooks.json`.

**Projekt:** `python -I scripts/napojit-projekt.py <projekt>/.claude/settings.json` — marketplace, plugin a cloudové hooky. Celý postup: skill `prevod-projektu`.

## Cloud (claude.ai/code)
Cloudová session pluginy z `.claude/settings.json` projektu neinstaluje. Hooky projektu proto v cloudu spustí `scripts/cloud-bootstrap.sh` (stáhne tento repozitář do `~/.agents/agent-kit`, nainstaluje plugin, vloží pravidla) a `scripts/cloud-pojistka.sh` (pojistka). Lokálně nedělají nic. Ověřeno v Brixyy/trading 22. 10. 2026.

## Úpravy, testy, verze
- Změna → zvyš `version` v `.claude-plugin/plugin.json` a ověř `claude plugin validate .` a `python -I tests/test_pojistka.py`.
- Nový skill jen z opakovaného postupu, který agent sám neumí (ne obecné znalosti typu React nebo TypeScript). Skills `predavka`, `rozhodnuti` a `nez-zacnes-stavet` jsou upravené podle [davidondrej/skills](https://github.com/davidondrej/skills) (MIT).
- Verze `HLAVNÍ.VEDLEJŠÍ.OPRAVA`: oprava → poslední číslo, nové pravidlo/skill → prostřední, změna vyžadující úpravu všech projektů → první. Nikdy se nesnižuje.
