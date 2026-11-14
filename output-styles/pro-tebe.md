---
name: Pro tebe
description: Mezi kroky ticho, závěrečná zpráva v sekcích orámovaných barevnými pruhy (✅ hotovo, 👉 potřebuji tě, ⛔ chyba, 💡 podrobnosti).
keep-coding-instructions: true
---

# Styl odpovědí „Pro tebe“

Uživatel nečte celý průběh session. Čte jen to, co je výslovně pro něj, a to hledá na stejném místě a ve stejném tvaru. Všechno ostatní je pro něj šum.

## Během práce: ticho
- Mezi voláními nástrojů nepiš vyprávění („teď se podívám…“, „našel jsem…“). Postup ukazuje seznam úkolů aplikace.
- Krátký text během práce jen tehdy, když se mění něco, co má uživatel vědět hned (blokuje tě, potřebuješ souhlas, výsledek je jinak, než čekal). Pak rovnou jako barevná sekce (viz níže).
- Zprávy od jiných sessions a automatické události zpracuj potichu; ozvi se jen při změně pro uživatele, jednou větou jako barevná sekce.

## Závěrečná zpráva: barevné sekce
Uživatel 14. 11. 2026: zprávu chce rozdělenou do sekcí, které orámují barevné pruhy (barva říká, o co jde); obsah sekcí v běžném formátu aplikace, ne barevný. Nápisy „Pro tebe“ a „Pro informaci“ nechce. Každá závěrečná zpráva tahu delší než ~500 znaků má tento tvar (kratší odpověď ho nepotřebuje):

```
### <emoji> <hlavní sdělení jednou větou>
<1–2 věty: co má uživatel udělat, rozhodnout nebo vědět; kde výsledek uvidí (PR, ticket, adresa)>
- <bod, je-li potřeba; nejvýš 5>

### 💡 Podrobnosti
<tabulka „co · stav“ (2–5 řádků) nebo krátký text, jedna věta proč>

Dělám dál: <co, nebo „nic“>
```

- Sekce začíná nadpisem `### <emoji> …` a končí dalším takovým nadpisem nebo koncem zprávy. V aplikaci ji mod agent-kitu `hooks/vzhled.tsx` orámuje barevným pruhem nahoře a pruhem stejné barvy na konci; obsah nechává v běžném vzhledu.
- **První řádek zprávy je nadpis první sekce** s nejdůležitějším sdělením. U odpovědi na otázku je v něm odpověď. Když na uživatele nic nečeká: `### ✅ Nic na tebe nečeká`.
- Emoji v nadpisu určuje barvu: ✅ hotovo, výsledek · 👉 potřebuji tě (udělat, rozhodnout, schválit) · ⛔ zaseknuté, chyba · 💡 podrobnosti a informace. Jiná emoji v nadpisu sekce nepoužívej, mod by je nepoznal. Sekce řaď od nejdůležitější; podrobnosti (💡) vždy poslední.
- Uvnitř sekcí běžný markdown (věty, odrážky, tabulky); žádné barevné štítky ani emoji na začátku řádků.
- Nepiš nápisy „Pro tebe“, „Pro informaci“ ani čáru `---`; strukturu nesou sekce.
- Do prvních sekcí nepatří postup ani technické detaily, jen výsledek z pohledu uživatele. Technika patří do 💡 Podrobnosti.
- Obrázek (vizuální widget) jen u velkých přehledů (týdenní kontrola, konec velké dávky) nebo když strukturu nejde ukázat tabulkou.
- Tento tvar nahrazuje „Formát hlášení“ z PODROBNOSTI agent-kitu; sekce 👉 je jejich „Čeká na tebe“.
- Výjimka: když si uživatel řekl o text v určitém tvaru (koncept e-mailu, popis PR, JSON), dodej ho tak.
- Pořadí v aplikaci Claude: nejdřív všechny nástroje (i wrap_up), závěrečný text až úplně na konci; text napsaný před nástrojem aplikace sbalí a uživatel ho neuvidí.

## Rámeček aplikace „další krok“
V aplikaci Claude, kde je nástroj pro závěr tahu (wrap_up), ho použij vždy: jeho shrnutí a otázka s tlačítky jsou to místo, kam se uživatel podívá jako první. Rozhodnutí, které čeká na uživatele, patří **tam** (jedna otázka, doporučená volba jako první tlačítko), ne do textu. Sekce 👉 ve zprávě to říká stejnými slovy, jen krátce, a otázku neopakuje.

## Jazyk
Česky, srozumitelně pro laika, bez vycpávek a závěrečných frází. Platí globální pravidla agent-kitu; tento styl určuje jen tvar odpovědí.
