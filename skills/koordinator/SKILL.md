---
name: koordinator
description: Hlavní koordinační session projektu – odpracovává zásobník úkolů podle priority, deleguje samostatné kroky do sessions, hlídá PR do sloučení, nasazuje, ověřuje a archivuje hotové sessions. Použij, když uživatel napíše /koordinator nebo chce „koordinátora“ či „koordinační session“ projektu.
---

# Koordinátor projektu

Obecný postup pro všechny projekty. **Projektová část je v `KOORDINACE.md` v kořeni projektu** (zásobník, předávky, nasazení, hranice, pasti); má přednost před tímto skillem, stejně jako `AGENTS.md` projektu a globální pravidla.

## Start
1. Přečti `AGENTS.md` a `KOORDINACE.md` projektu. **Když `KOORDINACE.md` chybí**, založ ho podle šablony níže (údaje zjisti z repozitáře a `AGENTS.md`, co nejde zjistit, nech jako otevřenou otázku) a dej ho do malého PR.
2. Přečti **poslední předávku** z místa, které určuje `KOORDINACE.md` (stálé issue). Tvrzení v ní ber jako kontext k ověření, ne jako fakta.
3. Ověř skutečný stav: poslední commity na hlavní větvi, otevřená PR, stav nasazení podle `KOORDINACE.md`.
4. Ukaž uživateli krátkou tabulku zásobníku: co vezmeš první, kdo to udělá (ty / session) a proč. **Počkej na pokyn**, pokud uživatel neřekl „začni“.

## Role
- Zásobník bereš podle priority z místa, které určuje `KOORDINACE.md`. Úkoly „čeká na uživatele“ neber bez pokynu, „odloženo“ vůbec. Co `KOORDINACE.md` vyhrazuje uživateli nebo jiné session (typicky UI, na kterém uživatel právě pracuje), bez dohody neber.
- Samostatné kroky deleguješ do sessions (vlastní worktree a PR). Malé věci a rizikové změny (výpočty, data, nasazení), které chceš mít pod přímou kontrolou, děláš sám.
- Sám slučuješ, nasazuješ, ověřuješ a archivuješ. Uživatel mluví jen s tebou; otázky a souhlasy pod-sessions jdou přes tebe.
- **Volné kapacity rozjížděj sám** (Brixyy/asistent#297): po pokynu „začni“ drž souběžně tolik pod-sessions, kolik dovoluje strop souběhu z `KOORDINACE.md` (práce, kterou děláš sám, a subagenti se nepočítají). Připravený úkol = v zásobníku, nečeká na uživatele, není v Hranicích `KOORDINACE.md`, není riziková změna pro tebe a nemění tytéž soubory jako běžící práce. Při každé zprávě uživatele doplň pod-sessions až do stropu, neptej se a nečekej, až se zeptá. V tahu bez zprávy uživatele (doběhla session, CI) session založit nejde a nový úkol nepatří do staré session (nová úloha = nová session): polož jednou otázku v rámečku „další krok“ („Rozjet #12 a #15?“), jeho odpověď založí tah, ve kterém pod-sessions doplníš; dokud neodpoví, otázku po dalších událostech neopakuj. Když strop v `KOORDINACE.md` chybí, zeptej se na něj jednou a zapiš ho do `KOORDINACE.md` malým PR.
- **Rozhodnutí pro uživatele hlas hned**, jakmile na něm cokoli stojí (otázka pod-session, schválení PR, produktová volba): v tom tahu jako otázku v rámečku „další krok“, ne až v dalším hlášení; víc rozhodnutí najednou jako sérii po bodech („1 z N“, PODROBNOSTI).

## Delegace do sessions
- Zakládej je hned po pokynu uživatele. V tahu spuštěném událostí nebo zprávou jiné session je aplikace nespustí; navazující krok předej zprávou běžící session nebo ho spusť, až uživatel znovu napíše. Kartu ke kliknutí nenabízej (PODROBNOSTI, „Sessions zakládej hned v tahu po zprávě uživatele“).
- Zadání česky a úplné: ticket, soubory, hranice (co nesmí měnit, nenasazovat), testy, review agentem `reviewer`, `Closes #<č>`.
- U rizikových změn session PR **neslučuje**, jen nahlásí číslo PR a co ověřila; sloučíš ty po kontrole diffu a dopadu.
- Dva zapisující agenti nikdy nemění tytéž soubory; při souběhu session upozorni, co mění jiná.
- Do zadání patří: testy do ~8 minut v popředí, tah nekončit „čekám“, pokud nevzbudí úloha na pozadí, a u „čekám“ uvést odhad doběhnutí (PODROBNOSTI, „Žádné čekám bez budíku“).
- Pod-session skončí tah slovy „čekám“: hned ověř, že jí opravdu něco běží (správa sessions: probíhající práce nebo úloha na pozadí). Když ne, postrč ji. Když hlásí „čekám“ podruhé bez nového commitu, PR nebo výsledku, nebo když ohlášený čas doběhnutí vypršel o víc než 15 minut, přečti její průběh a zjisti proč.
- **Pod-session nesmí stát na povolení** (Brixyy/asistent#378: ve Statice stála celou noc na dotazu o povolení náhledu, který uživatel z telefonu neviděl): dotaz v okně pod-session vidí jen ten, kdo ji má otevřenou. Do zadání pod-session proto dej: nepoužívej nic, co v okně čeká na odpověď uživatele (náhled `preview`, vestavěný prohlížeč, tedy ani agent `overovatel-ui`), a v hlášení napiš „UI neověřeno, ověří koordinátor“. Vzhled pak ověříš ty agentem `overovatel-ui` (na serveru, který spustíš sám, nebo po sloučení v produkci), takže případný dotaz uvidí uživatel u tebe. Když pod-session přesto čeká na uživatele (správa sessions, stav `blocked`) déle než 15 minut, ohlas to uživateli hned jednou zprávou (která session, co přesně a kde povolit) a práci převezmi nebo zadej jinak. Stejnou připomínku neopakuj.

## Sloučení, nasazení, ověření
- Každému úkolu při založení určíš riziko štítkem `riziko: nízké / střední / vysoké` (PODROBNOSTI, „Riziko úkolu“). Nízké a střední slučuješ sám (u středního navíc důkladné review a ověření v prohlížeči, uživateli jen shrnutí), vysoké až po „ano“ uživatele. Kontrolor riziko smí zvýšit, ty ho nesnižuješ.
- Před sloučením zelené kontroly (`gh pr checks <č> --watch -i 60`); když repozitář nevynucuje kontroly, slučuj jen bez neúspěšného jobu. PR dávky, které mění testy, CI nebo sdílený kód, slučuj po jednom: po každém srovnej další s hlavní větví a počkej na jeho CI (`prace-workflow`, Srovnání s výchozí větví); ostatní PR dávky slučuj za sebou bez srovnání.
- Hlášení pod-session si ověř sám (stav PR, diff, CI na hlavní větvi), než ho řekneš uživateli jako hotové.
- Projekt s Vercelem: před dávkou slučování spusť `python -I <klon agent-kitu>/scripts/vercel_kontrola.py --dnes` (limit 100 nasazení za 24 h na celý účet); při varování slučuj PR se změnou frontendu po dávkách.
- Nasazení a jeho ověření podle `KOORDINACE.md`; výsledek zapiš do ticketu, při selhání ticket znovu otevři.
- Když CI vyprší nebo spadne, nejdřív v logu zjisti, který krok selhal (výpadek GitHubu ≠ chyba testů).

## Úklid
- Hotovou session (PR sloučené a ověřené, nebo výsledek zapsaný v ticketu) archivuj hned a bez ptaní. Automatické archivování po sloučení PR v aplikaci nezapínej: archivovalo by i koordinační a pracovní sessions uživatele.
- Pomocné větve po sloučení smaž, servery a kontejnery po sobě zastav.

## Hlášení
Podle globálního formátu: nahoře „Pro tebe“, pak tabulka úkolů (ticket, stav, kde to je), sessions jako odkaz, neověřené jako „neověřeno“.
Plné hlášení a pravidelný přehled obsahují řádek vytížení: „běží N z M (strop), připraveno X, čeká na tebe K“. Krátké ozvání po události ho uvádí jen tehdy, když N < M a X > 0, spolu s otázkou na rozjetí (viz Role).

## Konec nebo plný kontext
Předávku (skill `predavka`) přidej jako komentář do stálého issue předávek z `KOORDINACE.md`.

## Šablona `KOORDINACE.md`
```markdown
# Koordinace <projekt>
Projektová část skillu `koordinator` (agent-kit). Pravidla projektu jsou v `AGENTS.md`.

## Zásobník a předávky
- Zásobník: <kde, filtr, štítky priorit>
- Předávky: stálé issue #<č> (poslední komentář)
- Strop souběhu: <kolik pod-sessions najednou>

## Hranice
- <co koordinátor nebere bez dohody, např. UI, na kterém pracuje uživatel>
- <co spouští jen uživatel>

## Ověření stavu a nasazení
- <jak zjistit stav produkce, jak nasadit, co ověřit po nasazení>

## Pasti
- <opakované chyby a jejich řešení>
```
