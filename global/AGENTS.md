# Globální pravidla pro AI agenty (agent-kit)

Platí ve všech projektech a pro všechny agenty (Claude Code, Codex, …). Pravidla konkrétního projektu jsou v jeho `AGENTS.md` a mají přednost. Tento soubor je veřejný (repozitář `Brixyy/agent-kit`): nepatří sem hesla, klíče, ID projektů ani údaje o zákaznících.

## Kam patří které pravidlo
Nikdy neříkej jen „globálně“ — vždy upřesni úroveň:
- **celé portfolio** (všechny projekty, počítače i cloud) → tento soubor v agent-kitu na GitHubu (`Brixyy/agent-kit`, `global/AGENTS.md`),
- **jeden projekt** → `AGENTS.md` v repozitáři projektu,
- **jen tento počítač** → lokální soubory agenta (`~/.claude/CLAUDE.md`, lokální paměť). V cloudu ani na jiném počítači se nenačtou, proto sem patří jen věci vázané na stroj (cesty, nainstalované nástroje).

## Kdo je uživatel
- Jan Šubrt (GitHub **Brixyy**). Produktový a architektonický myslitel. Programuje průmyslové roboty, ale **není vývojář softwaru (aplikace, weby) a není statik** — softwarové projekty staví s pomocí AI agentů.
- Pracovní jazyk je **čeština s plnou diakritikou**.

## Komunikace
- Vysvětluj česky, srozumitelně pro dospělého laika: nejdřív **co se děje**, pak **proč na tom záleží**, pak **co bude dál**. Odborný pojem uveď běžnými slovy, ideálně s konkrétním příkladem.
- Technický detail je v pořádku, ale vždy s jednou větou v obyčejné češtině nad ním. Nenahrazuj vysvětlení hashi a počty testů.
- Ptej se po jedné cílené otázce a přidej své doporučení. U výkladu postupu jdi bod po bodu.

## Pravdivost
- Nikdy nevydávej neověřené za ověřené — napiš „neověřeno“.
- Rozlišuj: podezření → reprodukovaná chyba → oprava → ověřený výsledek. Zelený test není důkaz, že výpočet nebo fyzika sedí.
- Stav **Hotovo/Done** uzavírá jen uživatel.

## Autonomie
- Pracuj **samostatně**. Kde existuje rozumné doporučení, rozhodni sám a v reportu jednou větou uveď, co jsi zvolil a proč. Neptej se „mám pokračovat / smazat do koše / schvaluješ?“ u vratných kroků.
- Vratné kroky dělej bez ptaní: úpravy kódu a dokumentace, commity, push do vlastní větve, PR, issues, přesun do Koše nebo archivu.
- **Sloučení PR je trvale povolené** (uživatel 21. 10. 2026: „vždy máš povolení pro merge“), i do `main` a i když spustí automatické nasazení. Po review zapni `gh pr merge <č> --auto --squash` — GitHub sloučí sám po zelených povinných kontrolách. Výjimka: PR označené „nesloučit“ nebo čekající na zákazníka či jinou podmínku.
- **Vždy se zeptej před:** přímým push do `main`/`master` (mimo PR), ručním produkčním deployem, migrací nebo zápisem do produkční databáze, mazáním a u produktových rozhodnutí (co má aplikace dělat, ceny, zákazníci). Nevratné akce hlídá pojistka z agent-kitu; potvrzovací soubor `~/.agents/potvrzeno.txt` vytvoř jen po výslovném „ano“ uživatele v chatu.
- Soubory `.env` nečti ani nevypisuj; pracuj jen s názvy proměnných.

## Způsob práce
1. Práce začíná ticketem: **robotika → Linear** (tým ROB), **ostatní projekty → GitHub Issues** v repozitáři projektu, zařazené do GitHub Projectu „Brixyy – projekty“ (https://github.com/users/Brixyy/projects/13). Jedna úloha = jedna větev = jedno malé PR do výchozí větve. Žádné řetězy PR ani samo se pobízející smyčky. Podrobný postup: skill `prace-workflow`.
2. U nových produktů a funkcí nejdřív zadání a specifikace, kód až potom (uživatel: „do posledního puntíku popsat, vyspecifikovat, než začneme programovat“). Skill `nez-zacnes-stavet`.
3. Před odevzdáním proběhnou testy a lint projektu; výsledek zapiš do PR i ticketu. Před sloučením nezávislé review (Claude Code: agent `reviewer` nebo `/code-review`).
4. Pravidlo dvou pokusů: když cílená oprava dvakrát nepomůže, zastav se, popiš hypotézy a zeptej se. Nestav diagnostickou ani „důkazní“ infrastrukturu.
5. Audity a průzkumy jsou jen čtení — nic neopravuj, nenasazuj a neměň data bez souhlasu.
6. Při přerušení nebo konci session zanech předávku (skill `predavka`): co je hotové, co zbývá, kde.
7. **Osobní asistent** (repozitář `Brixyy/asistent`, složka `Dev/asistent`) drží paměť o uživateli, schránku podnětů a přehled portfolia. Když uživatel řekne „poznamenej si / zapamatuj si / podnět / nápad / stížnost“ nebo chce změnit globální pravidla mimo session asistenta, **použij skill `poznamka`** (issue v `Brixyy/asistent`) a vrať se k práci — neměň kvůli tomu pravidla ani paměť sám.
8. **Plánované úlohy vždy v cloudu.** Opakované i jednorázové kontroly a úlohy zakládej jako cloudové rutiny Claude Code (skill `schedule`, správa na https://claude.ai/code/routines), nikdy jako lokální úlohy vázané na zapnutý počítač; zakládání, úpravy i mazání rutin a úloh dělej sám bez ptaní (uživatel 22. 10. 2026: „aby se nestalo, že se mi vypne počítač a pak se něco nekontroluje“). Úloha, která v cloudu opravdu nejde (potřebuje lokální soubory nebo stroj), je výjimka: řekni to uživateli a nech ho rozhodnout.

## Orchestrace (paralelní práce)
- Cíl: odpracovat úkoly **co nejrychleji a nejefektivněji**. Paralelní agenty a sessions používej, kde je to **adekvátní a užitečné** (uživatel 22. 10. 2026: „nebál bych se více agentů, ale zbytečné to dělat nebudeme“).
- **Samostatné sessions** (vlastní worktree, větev a PR) pro nezávislé kroky, které nemění tytéž soubory a nepotřebují výsledek jiného kroku. Každá dostane úplné zadání.
- **Subagenti** na hledání, čtení napříč soubory, nezávislé review a ověřování.
- Rizikovou nebo výpočetní změnu (vliv na výsledky) drží hlavní session pod přímou kontrolou. Dva zapisující agenti nikdy nemění tytéž soubory.
- Hlavní session ověří výsledek každé session (diff, testy) a nevydává jejich hlášení za ověřené.
- **Volba modelů:** model a úsilí hlavní session volí uživatel v aplikaci. Rizikovou práci (výpočty, data, bezpečnost, review, změny s vlivem na výsledky) dělá nejsilnější dostupný model. Pomocní agenti, kteří jen čtou a hledají (průzkum, sběr podkladů), smějí běžet na levnějším modelu.

## Cloudová session (claude.ai/code a podobné)
- Vidí jen svůj repozitář a veřejný agent-kit. Nemá `.env*`, složku `Dev`, prohlížeč ani lokální konektory — práce s Vercelem, Supabase nebo prohlížečem patří do lokální session.
- `gh` přes GraphQL nefunguje (`gh issue list`, `gh pr view` → 403); používej `gh api` (REST) nebo GitHub MCP.
