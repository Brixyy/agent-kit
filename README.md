# agent-kit

Společná pravidla a nástroje pro AI agenty ve všech projektech Brixyy — nezávislé na konkrétním nástroji (Claude Code, Codex, …). Jeden zdroj pravdy: co se opraví tady, platí všude. Repozitář je **veřejný**: nepatří sem hesla, klíče, ID projektů ani údaje o zákaznících.

## Co obsahuje
| Složka | Co | Formát |
|---|---|---|
| `global/AGENTS.md` | Globální pravidla: kdo je uživatel, komunikace, pravdivost, autonomie, způsob práce, orchestrace | prostý Markdown (čte každý agent) |
| `global/PODROBNOSTI.md` | Podrobnosti k pravidlům (pojistka, `.env`, rutiny, orchestrace, úklid, cloud). Nevkládá se, hook předá cestu | prostý Markdown |
| `skills/` | Vlastní pracovní postupy: `prace-workflow`, `predavka`, `rozhodnuti`, `nez-zacnes-stavet`, `prevod-projektu`, `poznamka` (zápis do osobního asistenta Brixyy/asistent) | otevřený standard Agent Skills (`SKILL.md`) |
| `agents/reviewer.md` | Nezávislá kontrola PR před sloučením | subagent Claude Code |
| `agents/overovatel-ui.md` | Ověření obrazovek v prohlížeči na desktopu i mobilu | subagent Claude Code |
| `hooks/pojistka.py` | Zastaví nevratné a produkční akce i vypnutí vlastních kontrol, zakáže otevírání a vypisování `.env` (načíst do procesu se smí) | Claude Code (JSON) i Codex (`--exit-code`) |
| `hooks/uklid_hook.py` + `scripts/uklid.py` | Úklid po sessions (Windows): na konci session ukončí její dev servery a zastaví kontejnery se štítkem `agent-kit.slozka`, na startu session ukončí osiřelé dev servery v `~/Dev`. Ručně: `python -I scripts/uklid.py --sirotci [--provest]` | Claude Code (SessionEnd, SessionStart) |
| `scripts/` | `install.py` (počítač, Codex), `napojit-projekt.py` (projekt), `cloud-bootstrap.sh` + `cloud-pojistka.sh` (cloudové sessions) | |

Kam patří které pravidlo: **celé portfolio** → tento repozitář · **jeden projekt** → `AGENTS.md` projektu · **jen tento počítač** → lokální soubory agenta.

## Instalace
**Claude Code** (plugin, kořen repozitáře je plugin):
```
/plugin install agent-kit --marketplace Brixyy/agent-kit
```
nebo v terminálu `claude plugin marketplace add Brixyy/agent-kit` a `claude plugin install agent-kit@agent-kit`. Plugin vloží globální pravidla do každé session, přidá skills, agenty `reviewer` a `overovatel-ui` a pojistku.

**Codex a další agenti** na tomto počítači: `python -I scripts/install.py` — zkopíruje pravidla do `~/.agents/AGENTS.md` a `~/.codex/AGENTS.md`, skills do `~/.agents/skills/` a napojí pojistku do `~/.codex/hooks.json`.

**Projekt:** `python -I scripts/napojit-projekt.py <projekt>/.claude/settings.json` — marketplace, plugin a cloudové hooky. Celý postup: skill `prevod-projektu`.

## Cloud (claude.ai/code)
Cloudová session pluginy z `.claude/settings.json` projektu neinstaluje. Hooky projektu proto v cloudu spustí `scripts/cloud-bootstrap.sh` (stáhne tento repozitář do `~/.agents/agent-kit`, nainstaluje plugin, vloží pravidla) a `scripts/cloud-pojistka.sh` (pojistka). Lokálně nedělají nic. Ověřeno v Brixyy/trading 22. 10. 2026.

## Úpravy, testy, verze
- Změna → zvyš `version` v `.claude-plugin/plugin.json` a ověř `claude plugin validate .` a testy v `tests/` (CI `testy` je spouští při každém push a PR).
- **`global/AGENTS.md` je jádro do 9 000 znaků.** Claude Code vloží z hooku nejvýš 10 000 znaků, delší text nahradí náhledem 2 000 znaků a zbytek agent neuvidí. Nové podrobné pravidlo patří do `PODROBNOSTI.md`, do jádra jen jeho krátká verze; hlídá to `tests/test_kontext.py`.
- Nový skill jen z opakovaného postupu, který agent sám neumí (ne obecné znalosti typu React nebo TypeScript). Skills `predavka`, `rozhodnuti` a `nez-zacnes-stavet` jsou upravené podle [davidondrej/skills](https://github.com/davidondrej/skills) (MIT).
- Verze `HLAVNÍ.VEDLEJŠÍ.OPRAVA`: oprava → poslední číslo, nové pravidlo/skill → prostřední, změna vyžadující úpravu všech projektů → první. Nikdy se nesnižuje.
