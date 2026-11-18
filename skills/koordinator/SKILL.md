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

## Delegace do sessions
- Zakládej je hned po pokynu uživatele. V tahu spuštěném událostí nebo zprávou jiné session je nezaložíš: navrhni je kartou.
- Zadání česky a úplné: ticket, soubory, hranice (co nesmí měnit, nenasazovat), testy, review agentem `reviewer`, `Closes #<č>`.
- U rizikových změn session PR **neslučuje**, jen nahlásí číslo PR a co ověřila; sloučíš ty po kontrole diffu a dopadu.
- Dva zapisující agenti nikdy nemění tytéž soubory; při souběhu session upozorni, co mění jiná.

## Sloučení, nasazení, ověření
- Před sloučením zelené kontroly (`gh pr checks <č> --watch`); když repozitář nevynucuje kontroly, slučuj jen bez neúspěšného jobu.
- Hlášení pod-session si ověř sám (stav PR, diff, CI na hlavní větvi), než ho řekneš uživateli jako hotové.
- Nasazení a jeho ověření podle `KOORDINACE.md`; výsledek zapiš do ticketu, při selhání ticket znovu otevři.
- Když CI vyprší nebo spadne, nejdřív v logu zjisti, který krok selhal (výpadek GitHubu ≠ chyba testů).

## Úklid
- Hotovou session (PR sloučené a ověřené, nebo výsledek zapsaný v ticketu) archivuj hned a bez ptaní. Automatické archivování po sloučení PR v aplikaci nezapínej: archivovalo by i koordinační a pracovní sessions uživatele.
- Pomocné větve po sloučení smaž, servery a kontejnery po sobě zastav.

## Hlášení
Podle globálního formátu: nahoře „Pro tebe“, pak tabulka úkolů (ticket, stav, kde to je), sessions jako odkaz, neověřené jako „neověřeno“.

## Konec nebo plný kontext
Předávku (skill `predavka`) přidej jako komentář do stálého issue předávek z `KOORDINACE.md`.

## Šablona `KOORDINACE.md`
```markdown
# Koordinace <projekt>
Projektová část skillu `koordinator` (agent-kit). Pravidla projektu jsou v `AGENTS.md`.

## Zásobník a předávky
- Zásobník: <kde, filtr, štítky priorit>
- Předávky: stálé issue #<č> (poslední komentář)

## Hranice
- <co koordinátor nebere bez dohody, např. UI, na kterém pracuje uživatel>
- <co spouští jen uživatel>

## Ověření stavu a nasazení
- <jak zjistit stav produkce, jak nasadit, co ověřit po nasazení>

## Pasti
- <opakované chyby a jejich řešení>
```
