# agent-kit

Společná pravidla a nástroje pro AI agenty ve všech projektech Brixyy — nezávislé na konkrétním nástroji (Claude Code, Codex, …). Jeden zdroj pravdy: co se opraví tady, platí všude. Repozitář je **veřejný**: nepatří sem hesla, klíče, ID projektů ani údaje o zákaznících.

## Co obsahuje
| Složka | Co | Formát |
|---|---|---|
| `global/AGENTS.md` | Globální pravidla: kdo je uživatel, komunikace, pravdivost, autonomie, způsob práce, orchestrace | prostý Markdown (čte každý agent) |
| `global/PODROBNOSTI.md` | Podrobnosti k pravidlům (pojistka, `.env`, rutiny, orchestrace, úklid, cloud). Nevkládá se, hook předá cestu | prostý Markdown |
| `skills/` | Vlastní pracovní postupy: `prace-workflow`, `predavka`, `rozhodnuti`, `nez-zacnes-stavet`, `prevod-projektu`, `poznamka` (zápis do osobního asistenta Brixyy/asistent), `koordinator` (koordinační session projektu; projektová část v `KOORDINACE.md` projektu), `audit` (kompletní audit projektu 1. a 15. v měsíci; projektová část v `AUDIT.md` projektu) | otevřený standard Agent Skills (`SKILL.md`) |
| `agents/reviewer.md` | Nezávislá kontrola PR před sloučením | subagent Claude Code |
| `agents/overovatel-ui.md` | Ověření obrazovek v prohlížeči na desktopu i mobilu | subagent Claude Code |
| `output-styles/pro-tebe.md` + `hooks/pro_tebe.py` + `hooks/vzhled.tsx` | Styl odpovědí „Pro tebe“: mezi kroky ticho, závěrečná zpráva začíná rámečkem 📌 pro uživatele, podrobnosti pod čarou. Mod `vzhled.tsx` (Desktop) kreslí odpověď jako barevné sekce (✅ 👉 ⛔ 💡): pruh nahoře, celá sekce podbarvená, řádky se štítky. Stop hook při zapnutém stylu vrátí delší zprávu bez rámečku jednou k doplnění rámečku. Zapnutí: `"outputStyle": "agent-kit:Pro tebe"` v `~/.claude/settings.json`; bez něj hook nic nevynucuje | Claude Code (output style, Stop) |
| `hooks/uzivatel.py` | Vloží do session výtah z paměti osobního asistenta o uživateli (`pamet/pro-agenty.md` v soukromém Brixyy/asistent: vkus v UI, jak rozhoduje). Bere ho přes `gh api`, záložně z místní kopie `~/Dev/asistent` (může být zastaralá, když se checkout nestahuje); bez nich nevloží nic. Data v agent-kitu nejsou. V cloudu ho `cloud-bootstrap.sh` uloží do `~/.agents/pro-agenty.md` a předá jen odkaz | Claude Code (SessionStart) |
| `hooks/pojistka.py` | Zastaví nevratné a produkční akce i vypnutí vlastních kontrol, zakáže otevírání a vypisování `.env` (načíst do procesu se smí) | Claude Code (JSON) i Codex (`--exit-code`) |
| `hooks/verze.py` | Upozorní dlouho běžící session na novou verzi agent-kitu: při startu si zapamatuje verzi, při každé zprávě uživatele porovná s nejnovější verzí v cache pluginu a jednou na každou novou verzi vloží výzvu přečíst nové jádro a podrobnosti a ohlásit to uživateli (Brixyy/asistent#344) | Claude Code (SessionStart, UserPromptSubmit) |
| `hooks/uklid_hook.py` + `scripts/uklid.py` | Úklid po sessions (Windows): na konci session ukončí její dev servery a zastaví kontejnery se štítkem `agent-kit.slozka`, na startu session ukončí osiřelé dev servery v `~/Dev`. Ručně: `python -I scripts/uklid.py --sirotci [--provest]` | Claude Code (SessionEnd, SessionStart) |
| `scripts/` | `install.py` (počítač, Codex), `napojit-projekt.py` (projekt), `cloud-bootstrap.sh` + `cloud-pojistka.sh` (cloudové sessions), `vercel_kontrola.py` (projekty s Vercelem a celý účet Vercelu: vypnuté náhledy; `--dnes` spočítá nasazení na účtu za 24 h, varování od 60, chyba od 85), `env_nastav.py` (bezpečně nastaví jednu proměnnou v `.env`: hodnota ze stdin, záloha mimo repo, nic se nevypisuje), `stitky.py` (jednotné štítky issues ve všech repozitářích: zakládá a upravuje základ, anglické `bug`/`enhancement`/`documentation` přejmenuje na české, ostatní výchozí anglické smaže; `--nanecisto` jen plán, `--kontrola` issues bez právě jednoho stavu) | |

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
Cloudová session pluginy z `.claude/settings.json` projektu neinstaluje. Hooky projektu proto v cloudu spustí `scripts/cloud-bootstrap.sh` (stáhne tento repozitář do `~/.agents/agent-kit`, nainstaluje plugin, vloží pravidla) a `scripts/cloud-pojistka.sh` (pojistka). Lokálně nedělají nic. Ověřeno v Brixyy/elyon 22. 10. 2026.

## Úpravy, testy, verze
- **Vydání po dávkách** (uživatel 23. 11. 2026, audit Brixyy/agent-kit#96). Běžné PR `version` v `.claude-plugin/plugin.json` nemění. Claude Code bez změny verze nový obsah nestáhne ([dokumentace](https://code.claude.com/docs/en/plugins/host-marketplace.md), „Release a new version“), takže sloučené změny čekají na vydání.
  - Vydání je zvýšení `version` (a verze v názvu PR), nejvýš jednou za 24 h. Vydává se vždy celá dávka nevydaných změn.
  - **Kdo vydává:** každá session, která v agent-kitu pracuje, na začátku i před sloučením PR zkontroluje nevydané změny. Když je poslední vydání starší než 24 h, přidá zvýšení do slučovaného PR. Když žádné PR neslučuje, založí malé PR „Vydání X.Y.Z“. Při konfliktu v `plugin.json` platí PR sloučené dřív, druhé zvýšení odebere.
  - **Hned se vydává:** oprava pojistky, bezpečnosti nebo rozbitého hooku (sessions bez pravidel) a pravidlo, které má podle uživatele platit hned.
  - **Příkazy (Git Bash):**
    - Nevydané změny: `git fetch -q origin && git log --oneline $(git log -1 --format=%H -G'"version"' origin/main -- .claude-plugin/plugin.json)..origin/main`.
    - Čas posledního vydání: `git log -1 --format=%cI -G'"version"' origin/main -- .claude-plugin/plugin.json`.
  - **Cloud a Codex vydání nečekají.** `cloud-bootstrap.sh` a `install.py` berou `main` přímo, takže každé sloučené PR musí být bezpečné hned.
- Před sloučením ověř `claude plugin validate .` a testy v `tests/` (CI `testy` je spouští u hotového PR, ne u konceptu, a po sloučení přeskočí strom, který už prošel v PR; vzor Levné CI v `PODROBNOSTI.md`).
- **`global/AGENTS.md` je jádro do 8 500 znaků.** Claude Code vloží z hooku nejvýš 10 000 znaků, delší text nahradí náhledem 2 000 znaků a zbytek agent neuvidí. Nové podrobné pravidlo patří do `PODROBNOSTI.md`, do jádra jen jeho krátká verze; hlídá to `tests/test_kontext.py`.
- Nový skill jen z opakovaného postupu, který agent sám neumí (ne obecné znalosti typu React nebo TypeScript). Skills `predavka`, `rozhodnuti` a `nez-zacnes-stavet` jsou upravené podle [davidondrej/skills](https://github.com/davidondrej/skills) (MIT).
- Verze `HLAVNÍ.VEDLEJŠÍ.OPRAVA` podle největší změny v dávce: oprava → poslední číslo, nové pravidlo/skill → prostřední, změna vyžadující úpravu všech projektů → první. Nikdy se nesnižuje.
