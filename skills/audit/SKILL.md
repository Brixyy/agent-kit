---
name: audit
description: Kompletní nezávislý audit celé aplikace „z gruntu“, jako by ji přinesl cizí zákazník – směr a zadání, výsledky, architektura a kvalita kódu, testy, bezpečnost, provoz, data, UI a proces. Použij, když uživatel napíše /audit, chce „kompletní audit“, „velký přehled“, „globální nadhled“, nebo ho spustí rutina auditu projektů (1. a 15. v měsíci).
---

# Kompletní audit aplikace

Obecný postup pro všechny projekty. **Projektová část je v `AUDIT.md` v kořeni projektu** (kam ukládat zprávu, přístup k produkci, otázky a měřítka projektu); má přednost před tímto skillem, stejně jako `AGENTS.md` projektu a globální pravidla. Když `AUDIT.md` chybí: s uživatelem ho založ podle šablony níže v malém PR; při běhu rutinou bez uživatele ho nezakládej, audituj podle tohoto skillu a návrh `AUDIT.md` dej do zprávy.

Audit odpovídá na tři otázky: **Míří aplikace tam, kam má? Funguje opravdu, nebo jen vypadá, že funguje? Kde je nejvíc rizika a co s tím?** Obsahová kontrola sama nestačí: audit vždy zahrne i kód, testy, bezpečnost a provoz.

## Kdy a v jakém rozsahu
- **Kadence pro všechny projekty stejná:** 1. a 15. den v měsíci, mimořádně na požádání. Spouští ho jedna společná rutina „Portfolio – audit projektů“, která projde všechna repa po sobě; zakládá a spravuje ji hlavní session asistenta (`Brixyy/asistent`). Projekt si vlastní rutinu auditu nezakládá. Rutina je dlouhý běh: drží si stav (které repo je hotové, „hotovo X z Y“) a po pádu pokračuje dalším repem (podrobnosti, Noční a dlouhé běhy); oblasti, na které její prostředí nestačí (prohlížeč, přihlášení do produkce), dá do zprávy jako „neověřeno“.
- **Rozsah úměrný projektu:** malé repo bez produkce dostane lehký audit (oblasti 1, 3, 4, 5, 9, 10), ostatní plný. Rozsah může určit `AUDIT.md`.

## Pravidla
- **Audit jen čte** (globální pravidlo 5). Nic neopravuje, nenasazuje, nemigruje, nemění data ani nastavení. Produkční databáze jen `SELECT`, nejlépe v transakci `read only`. Výstupem jsou zpráva, souhrnné issue a issues nálezů, nic jiného.
- **Nezávislost:** auditoři dostanou otázky, kód a data, ne tvůj názor ani závěry předchozích sessions. Tvrzení z dokumentace, předávek a hlášení jsou hypotézy k ověření.
- **Důkaz u každého nálezu:** `soubor:řádek`, dotaz a jeho výsledek, příkaz a výstup nebo snímek. Bez důkazu je nález „neověřeno“ a nesmí mezi kritické.
- **Pevný bod:** na začátku zapiš commit (`git rev-parse origin/<hlavní větev>`), datum a čas měření. Všechno se vztahuje k němu.
- Snímek a čísla z produkce ber aktuálně, ne z paměti ani starších zpráv.
- **Kontroly kódu** (instalace, lint, testy) pouštěj ve vlastním dočasném worktree na pevném commitu, ne v pracovním checkoutu; po auditu ho smaž.
- **Produkční UI jen procházej:** nemačkej nic, co odesílá, spouští nebo mění (formuláře, spuštění AI, exporty, nastavení). Stejný zákaz dej do zadání každého agenta, který UI ověřuje.
- **Tajemství:** `.env` ani podobné soubory neotvírej a negrepuj; stav přepínačů zjišťuj jen způsobem z `AUDIT.md`.

## Postup
1. **Příprava.** Přečti `AGENTS.md`, `AUDIT.md` a **předchozí audit** (místo určuje `AUDIT.md`). Vypiš si jeho nálezy a doporučení: u každého v tomto auditu zjistíš, jestli se vyřešil, zhoršil nebo trvá.
2. **Oblasti auditu.** Rozděl práci mezi nezávislé subagenty, kteří jen čtou (nejvýš ~6 najednou, každý jednu až dvě oblasti z tabulky). Každý dostane: oblast, otázky z tabulky i z `AUDIT.md`, pevný commit, přístupy z `AUDIT.md`, požadovaný tvar nálezu a zákaz cokoli měnit. Jejich výsledek si přečti celý, ne jen shrnutí.
3. **Ověření.** Každý nález se závažností kritická nebo vysoká předej dalšímu subagentovi, který se ho pokusí **vyvrátit** (dostane jen tvrzení a důkaz). Co neobstojí, sniž nebo vyřaď. U výpočtů aspoň jeden kontrolní přepočet z dat.
4. **Velké otázky.** Sám odpověz na otázky v části níže a na projektové otázky z `AUDIT.md`. Odpověď opři o nálezy, ne o dojem.
5. **Výstup** (viz níže). Pak **probrání s uživatelem**: velké otázky po jedné, s tvým názorem a doporučením; uživatel je oponent. Jeho rozhodnutí zapiš tam, kam projekt zapisuje rozhodnutí, a z dohodnutých kroků udělej tickety.

## Oblasti
| Oblast | Ptá se |
|---|---|
| 1. Směr a zadání | Odpovídá postavené cíli a potvrzeným rozhodnutím? Co se postavilo navíc nebo mimo pořadí (rozlézání rozsahu)? Kde si odporují rozhodnutí, dokumentace a kód? Jak často se měnily zásadní věci a proč? |
| 2. Výsledky | Plní aplikace svůj účel měřitelně? Které metriky z produkce to ukazují a jaký mají trend proti minulému auditu? Co je jen postavené, ale nic nedává? |
| 3. Architektura a kód | Odpovídá struktura diagramům? Duplicity, **mrtvý kód** (nepoužívané soubory, exporty a závislosti; nástroj podle jazyka, např. `knip`, `vulture`, `deptry`), **pojmenování** (stejný pojem všude stejně, přejmenování na čisto bez aliasů), příliš velké soubory a funkce, místa s nejvíc změnami (`git log` za období), skryté závislosti, natvrdo zadané hodnoty, tiché náhradní hodnoty, polykání chyb. Co by zkušený vývojář přepsal jako první? |
| 4. Testy a CI | Pokrývají testy kritické cesty (peníze, výpočty, data, přihlášení)? Co testy neověří, i když jsou zelené? Nestabilní testy, doba běhu CI, přeskočené kontroly, lint a typy. **Hygiena testů** podle pravidla „Jak psát testy“ (agent-kit, PODROBNOSTI): testy, které se 90 dní nezměnily ani nepadly a zdvojují jiné; testy pojmenované podle úkolu (`test_r209.py`); nejpomalejší testy a jejich podíl na čase CI; poměr testů ke kódu a jeho trend. |
| 5. Bezpečnost a závislosti | Tajemství v repozitáři a historii, přihlášení a oprávnění, vstupy z internetu, otevřené porty, závislosti se známými zranitelnostmi (`npm audit`, `pip-audit` apod.) i zastaralé závislosti, zálohy a obnova, kdo může co spustit. |
| 6. Provoz | Chyby a výpadky v logu za období, hlídání a upozornění (hlídá se skutečná práce, nebo jen že proces běží?), disk, paměť, výkon, plánované úlohy a rutiny. |
| 7. Data | Správnost klíčových výpočtů (kontrolní vzorek přepočtem), úplnost a čerstvost zdrojů dat, konzistence mezi tabulkami, migrace. |
| 8. UI | Vidí uživatel všechno důležité, co systém ví a dělá, a srozumitelně? Desktop i telefon, přihlášená část, soulad s `DESIGN.md`. Kde UI ukazuje něco, co neplatí? |
| 9. Dokumentace a znalosti | Je dokumentace pravdivá k pevnému commitu? Jeden zdroj pravdy, zastaralé stavy, otevřené otázky bez majitele. |
| 10. Proces | Rychlost a velikost PR, reverty a opakované opravy téhož, stáří a štítky issues, zaseknuté úkoly, opakované chyby agentů, co čeká na uživatele a jak dlouho. |
| 11. Náklady | Kolik projekt stojí a jaký je trend proti minulému auditu: CI runnery (minuty, zrušené a opakované běhy), hosting, databáze, AI a další placené služby. Co platíme a nic to nedává? |
| 12. Expirace | Kdy vyprší domény, certifikáty, předplatná, tokeny a klíče? Co vyprší do příštích dvou auditů a hlídá to něco? |
| 13. Soulad s agent-kitem a šablonou | Řídí se repo globálními pravidly (levné CI, štítky, `AGENTS.md`, `DESIGN.md`) a odpovídá šabloně `Brixyy/project-template` (CI, struktura `AGENTS.md`, `.env.example`, `scripts/cloud-setup.sh`)? Co chybí nebo se rozešlo? |

## Velké otázky (vždy)
1. Kdybychom začínali dnes s tím, co víme, postavili bychom to stejně? Co ne?
2. Co je teď největší riziko pro cíl projektu a pro data či peníze uživatele?
3. Co bychom měli **přestat** dělat nebo vypnout, protože nic nedává?
4. Co uživatel neví, ale měl by (co tvrdí dokumentace nebo UI a neplatí)?
5. Ujíždí projekt od zadání? Kterým směrem a je to vědomé rozhodnutí?
6. Co se od minulého auditu zlepšilo, co zhoršilo a co z jeho doporučení se neudělalo?
7. Jaké tři kroky do příštího auditu mají největší užitek?

## Tvar nálezu
`[závažnost] oblast · krátký název` → co platí, **důkaz**, dopad laicky (proč na tom záleží), doporučení, ověřeno / neověřeno, trend proti minulému auditu (nový / trvá / zhoršeno / vyřešeno).
Závažnost: **kritická** (ohrožuje data, peníze, bezpečnost nebo cíl teď) · **vysoká** (do měsíce) · **střední** · **nízká**.

## Výstup
- **Zpráva** do místa z `AUDIT.md`: nahoře „kde jsme jednou větou“, semafor oblastí 🟢🟡🔴 s trendem ↑↓→, velké otázky s odpověďmi, nálezy podle závažnosti, srovnání s minulým auditem, co nešlo ověřit.
- **Obrázek:** přehled semaforu a trendů jako artefakt nebo obrázek (uživatel je vizuální typ); na telefonu jako soubor PNG.
- **Souhrnné issue** „Audit projektu RRRR-MM-DD“ se štítkem `audit-projektu` (stejný ve všech repech): semafor, tři doporučené kroky, odkazy na zprávu a issues nálezů. Je to místo, kde příští audit najde předchozí.
- **Issues nálezů** jen pro kritické a vysoké, které nejsou už v otevřeném issue (zkontroluj duplicity; trvající nález doplň komentářem ke stávajícímu issue).
- **Spuštěno rutinou bez uživatele:** udělej body 1–4 a výstup bez probrání s uživatelem, pošli mu krátké upozornění a velké otázky nech na probrání v příští konverzaci. Nic nerozhoduj za něj.
- **Rutina přes víc projektů:** souhrnné issue založ v projektu hned po dokončení jeho auditu, ne až na konci, aby se výsledek neztratil, když běh později spadne. Společný přehled všech projektů dělá rutina na konci.

## Šablona `AUDIT.md`
```markdown
# Audit <projekt>
Projektová část skillu `audit` (agent-kit). Pravidla projektu jsou v `AGENTS.md`.

## Kdy a kam
- Kdy: 1. a 15. v měsíci, společná rutina „Portfolio – audit projektů“; mimořádně na požádání
- Rozsah: <plný / lehký (oblasti 1, 3, 4, 5, 9, 10)>
- Zpráva: <složka nebo místo, mimo git>; souhrnné issue „Audit projektu RRRR-MM-DD“ se štítkem `audit-projektu` v <repo>
- Předchozí audit: <jak ho najít>
- Upozornění uživateli při běhu rutinou: <kanál a příkaz>

## Přístupy (jen čtení)
- Kód: <hlavní větev>, kontroly v dočasném worktree; produkce: <jak se dostat, s jakým omezením>; přepínače: <bezpečný způsob bez čtení .env>; databáze: <projekt, jen SELECT, jak>

## Měřítka projektu
- <metriky, které říkají, jestli projekt plní účel, a odkud je vzít>

## Otázky projektu
- <otázky navíc k velkým otázkám, např. hranice, které se nesmí překročit>

## Kontroly kódu
- <příkazy lintu, typů, testů, auditu závislostí>
```
