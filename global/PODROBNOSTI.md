# Globální pravidla – podrobnosti (agent-kit)

Doplněk k `global/AGENTS.md`. Jádro pravidel se vkládá do každé session; tento soubor ne (limit Claude Code je 10 000 znaků na vložený text). Agent ho čte, když řeší téma níže: potvrzení nevratných akcí, `.env`, rutiny, orchestraci sessions, úklid, noční běhy, cloudovou session, Vercel nebo vzhled frontendu. Platí stejně závazně jako jádro.

## Potvrzení nevratných akcí (pojistka)
Nevratné akce hlídá pojistka z agent-kitu; potvrzovací soubor `~/.agents/potvrzeno.txt` vytvoř jen po výslovném „ano“ uživatele v chatu. Jednorázový souhlas platí na jednu akci.

**Dávka:** když úkol obsahuje víc nebezpečných kroků, vypiš uživateli předem přesně všechny a po jeho „ano“ zapiš do souboru pro každý krok řádek `krok: <konkrétní text příkazu nebo název nástroje>` (např. `krok: supabase db push`, `krok: execute_sql`). Souhlas pak platí 15 minut na tyto kroky a jinou nebezpečnou akci pojistka zastaví. Kroky piš co nejkonkrétněji, ne obecně (`git`, `gh api`) (uživatel 24. 10. 2026, Brixyy/asistent#38).

Vypnutí nebo úprava vlastních kontrol: pojistka, hooky, vypnutí či smazání GitHub workflow. Úprava workflow v PR je v pořádku (Brixyy/asistent#105). Zápis do cizího repozitáře (PR, issue nebo komentář v open-source projektu): veřejný text piš obecně, bez interních údajů.

## Soubory `.env`
Hodnoty smíš načíst do procesu a použít (`set -a; . ./.env; set +a`, `node --env-file=.env`, `dotenv`), ale **nikdy je nevypisuj**: do chatu, logu, souboru, commitu ani argumentu příkazu. Soubor neotvírej nástrojem pro čtení, hodnoty by se objevily v kontextu. Zapisuj do něj jen skriptem `scripts/env_nastav.py` z agent-kitu (`C:\Users\Admin\Dev\agent-kit`), který nejdřív udělá zálohu do `~/.agents/env-zalohy/` (uživatel 24. 10. 2026). Token nikdy nevkládej do URL ani do argumentu příkazu (`git remote`). Tajemství nikdy nedávej do proměnných, které končí v prohlížeči (`VITE_*`, `NEXT_PUBLIC_*`).

## Prohlížeč místo chybějícího nástroje
Když nástroj nebo API něco neumí, použij prohlížeč (vestavěný v aplikaci, nebo Claude in Chrome, kde je uživatel přihlášený) a udělej to přes webové rozhraní, bez ptaní, jestli to tak smíš (uživatel 23. 10. 2026: „nástroje na to ještě nejsou… vyřešíme přes Chrome“). Neodpovídej „to nejde“, dokud jsi nezkusil prohlížeč. Platí dál ostatní pravidla: nevratné kroky (mazání) a produkční zásahy potvrdí uživatel, hesla (kromě testovacích účtů projektu) a platební údaje nezadáváš.

## Done bez čekání na uživatele
Uživatel 26. 10. 2026 (mění pravidlo „Done uzavírá jen uživatel“). PR, které úkol dokončuje, má v popisu `Closes #<č>`, takže GitHub issue zavře při sloučení (průběžná PR k témuž úkolu mají `Refs #<č>`). Po sloučení ověř nasazení a změnu tak, jak ji uvidí uživatel (u změn bez dopadu na web stačí zelené CI na výchozí větvi), a do issue zapiš krátký komentář s výsledkem. Když ověření selže, issue znovu otevři s popisem, co nefunguje. Hotovou a ověřenou práci uzavírá agent sám, nikdy ji nenechá viset ve stavu „Ke schválení“. Uživatel může kterékoli issue kdykoli znovu otevřít. Odbornou autorizaci (např. razítko statika) to nenahrazuje.

## Plánované úlohy (rutiny)
Opakované i jednorázové kontroly a úlohy zakládej jako cloudové rutiny Claude Code (skill `schedule`, správa na https://claude.ai/code/routines), nikdy jako lokální úlohy vázané na zapnutý počítač. Zakládání, úpravy i mazání rutin a úloh dělej sám bez ptaní (uživatel 22. 10. 2026: „aby se nestalo, že se mi vypne počítač a pak se něco nekontroluje“).

Úloha, která v cloudu opravdu nejde (potřebuje lokální soubory nebo stroj), je výjimka: řekni to uživateli a nech ho rozhodnout. Lokální výjimka se zakládá jako **lokální rutina v aplikaci Claude** (naplánované úlohy aplikace, „Only on this computer“), aby ji uživatel viděl v jednom seznamu s ostatními. Nikdy ne v Plánovači úloh Windows, cronu ani jiném systémovém plánovači (uživatel 23. 10. 2026: „od toho máme přece rutiny tady v lokální aplikaci“).

Každou založenou, změněnou nebo smazanou rutinu zapiš do rejstříku `portfolio/RUTINY.md` v `Brixyy/asistent` (účel, čas, kde, proč); podle něj se kontroluje, jestli rutiny běží a jsou pořád potřeba. Rutina pracuje nad čerstvým stavem z GitHubu a selhání hlásí, nikdy tiše neopakuje stejnou chybu. Novou rutinu nejdřív jednou zkušebně spusť.

## Orchestrace: podrobnosti
- **Zakládání sessions je trvale povolené** (uživatel 24. 10. 2026: „když hlavní session chce vytvořit subsessions, tak se mě na to nemusí ptát … automaticky udělat podle svého uvážení“). Tento trvalý souhlas se počítá jako výslovná žádost uživatele (v aplikaci Claude: `start_session` s `initiation: "user_asked"`, ne `offer` ani `own_initiative`). Uživateli v hlavním chatu jednou větou řekne, co spustila. Mimo rozsah zadání (úplně nová práce, kterou uživatel nechtěl) dál jen navrhuje.
- **Sessions zakládej hned v tahu po zprávě uživatele** (uživatel 26. 10. 2026). Aplikace Claude odmítne spustit session v tahu, který nezačal zprávou uživatele (doběhla jiná session, přišla událost z CI, probuzení), a místo toho ukáže kartu, kterou musí uživatel kliknout. Koordinátor proto při rozdělování práce založí všechny nezávislé sessions najednou, dokud odpovídá na zprávu uživatele. Navazující krok, který čeká na výsledek jiné session, předá rovnou té session jako pokračování (zprávou), nebo ho spustí, až uživatel znovu napíše; kartu s návrhem použije jen tehdy, když jinak nejde.
- **Práce v jiném projektu jde přes ticket a koordinační session toho projektu** (uživatel 26. 10. 2026). Session nezakládá pod-sessions v cizí složce (jiný repozitář): aplikace Claude si to sama ověřuje a ptá se uživatele, i když to pravidla povolují. Místo toho založí ticket v daném projektu (robotika → Linear, ostatní → GitHub Issues) s úplným zadáním a práci spustí koordinační session toho projektu ve své složce. Když žádná neběží, řekne uživateli jednou větou, kterou session v projektu otevřít.
- **Koordinátor** sám pravidelně hledá nečinné a zaseknuté pod-sessions a obnovuje je, nic nesmí potichu stát. Pod-sessions mají stejný režim oprávnění jako koordinátor (nikdy vyšší), aby uživatele nezahlcovaly žádostmi o potvrzení, a další sessions samy nezakládají. Nová úloha dostane novou session s čistým kontextem.
- **Přejímka:** agent ukazuje, uživatel se dívá. Koordinátor výsledek sám projde v prohlížeči, chybu vrátí autorovi a uživateli řekne, co a kde má vidět („podívej se na …, doporučuji uzavřít ticket“).
- **Uživatel mluví jen s hlavní session.** Krok, který vyžaduje souhlas uživatele (stažení, mazání, odeslání…), po souhlasu provede hlavní session sama; souhlas se nepřeposílá (uživatel 23. 10. 2026: „neovládám sessions, to je tvoje práce“).
- **PR hlídá jeho vlastník až do sloučení**, ne jen do zapnutí automatického sloučení. Hlídání hlásí i selhání, zrušení (timeout) a stav BEHIND, ne jen úspěch. Při více souběžných PR počítej s opakovaným BEHIND (slučují se postupně) a předem urči, kdo větve aktualizuje. Když vlastník končí dřív, předá hlídání koordinátorovi nebo zapne hlídání CI v aplikaci (Auto-fix).
- **Volba modelů:** model a úsilí hlavní session volí uživatel v aplikaci. Rizikovou práci (výpočty, data, bezpečnost, review, změny s vlivem na výsledky) dělá nejsilnější dostupný model. Pomocní agenti, kteří jen čtou a hledají (průzkum, sběr podkladů), smějí běžet na levnějším modelu.

## Úklid
- **Pracovní složky a větve** (uživatel 29. 10. 2026: „abychom po sobě uklízeli… je špatný, když to necháváme“). Kdo PR sloučí a ověří, hned smaže svou pracovní složku (`git worktree remove`) a lokální větev; větev na GitHubu maže sloučení PR. Platí trvalý souhlas bez ptaní, protože práce je celá ve výchozí větvi. Podmínky: složka nemá neuložené změny a obsah větve je ve výchozí větvi (sloučené PR nebo `git merge-tree` beze změny). Větev, jejíž práce ve výchozí větvi není, se před smazáním uloží jako značka `archiv/<větev>` (obnovitelná). Koordinátor na konci dávky zkontroluje `git worktree list` a `git branch` a uklidí, co po sessions zbylo; nikdy nemaže složku ani větev session, která ještě běží. Pracovní složky mimo projekt (dočasné kopie v Temp) patří do úklidu taky.
- **Sessions:** hotovou pod-session (její PR je sloučený a výsledek ověřený) koordinátor sám archivuje (v aplikaci, nástrojem pro správu sessions, jinak přes prohlížeč). Archivace je vratná a historie zůstane; mazat jen na pokyn uživatele (uživatel 23. 10. 2026).

## Noční a dlouhé běhy
- Dlouhou úlohu (uživatel 23. 10. 2026: „ideální pro noční běhy“) nepouštěj jako jednu session vázanou na zapnutý počítač. Rozděl ji na dávky a pusť jako cloudovou rutinu, která si drží stav („hotovo X z Y“) v issue nebo souboru v repozitáři a každý běh zpracuje jednu dávku.
- Ráno přijde jedno shrnutí (notifikace); selhání se hlásí hned. Když není co dělat, běh skončí bez hlášení.
- Úloha, která potřebuje lokální Chrome nebo počítač (např. sledování účtů na X), cloud nezvládne: pouští se lokálně jako výjimka a řekne se to uživateli.

## Cloudová session (claude.ai/code a podobné)
- Vidí jen svůj repozitář a veřejný agent-kit. Nemá `.env*`, složku `Dev`, prohlížeč ani lokální konektory; práce s Vercelem, Supabase nebo prohlížečem patří do lokální session.
- `gh` přes GraphQL nefunguje (`gh issue list`, `gh pr view` → 403); používej `gh api` (REST) nebo GitHub MCP.

## Vercel
- Nasazuje se **jen produkce z `main`**; náhledová nasazení pro PR a větve jsou vypnutá (`git.deploymentEnabled` ve `vercel.json`, nebo v nastavení projektu). Uživatel 28. 10. 2026: náhledy nejsou potřeba a agenti s několika PR denně zbytečně čerpají limity.
- Produkční build běží **jen při změně frontendu** (Ignored Build Step, např. `git diff --quiet HEAD^ HEAD -- <složka frontendu>/`).
- Změny frontendu ověřují CI testy a snímky obrazovky v PR, ne náhledy Vercelu.
- Výjimka jen na výslovnou žádost uživatele u konkrétního projektu (zapsat do `AGENTS.md` projektu).

## Vzhled frontendu (`DESIGN.md`)
- Každý projekt s obrazovkami má v kořeni **`DESIGN.md`**: závazná pravidla vzhledu (barvy a témata, písmo, mezery, sdílené komponenty, stavy, mobil). Je to rozšířená konvence pro AI agenty vedle `README.md` a `AGENTS.md`. `AGENTS.md` projektu na něj odkazuje. Projekt bez obrazovek ho nemá.
- **Jeden zdroj pravdy:** skutečné hodnoty žijí v kódu (CSS proměnné, Tailwind téma). `DESIGN.md` na ně odkazuje a popisuje pravidla, hodnoty neopisuje, aby nezastaral. Když už projekt pravidla vzhledu má jinde (skill, `docs/…`), je `DESIGN.md` jen krátký rozcestník na ně.
- **Změna vzhledu:** nejdřív přečti `DESIGN.md`. Novou barvu, písmo nebo komponentu nevymýšlej mimo něj. Změnu pravidla zapiš do `DESIGN.md` ve stejném PR. Ověř v prohlížeči na desktopu i mobilu a snímek přilož k PR.
- **Plugin `frontend-design`** (Anthropic, marketplace `claude-plugins-official`) používej na **nové** obrazovky a stránky a na návrh vzhledu nového projektu: nejdřív plán (barvy, písmo, rozvržení), porovnání se zadáním, pak kód a kontrola na snímcích. V existujícím projektu má přednost jeho `DESIGN.md` a pravidlo „nejmenší zásah“; plugin nesmí měnit zavedený vzhled bez zadání.
- Proč: bez vedení AI sklouzává k průměrnému vzhledu („distributional convergence“, Anthropic, 12. 11. 2025: https://claude.com/blog/improving-frontend-design-through-skills). Uživatel 29. 10. 2026, Brixyy/asistent#98.
