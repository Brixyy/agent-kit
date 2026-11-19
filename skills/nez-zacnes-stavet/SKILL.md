---
name: nez-zacnes-stavet
description: Ve chvíli, kdy uživatel navrhne novou funkci, produkt nebo větší změnu, okamžitě pojmenuj 1–3 zásadní volby skryté v nápadu a postup k úplné specifikaci. Použij dřív, než začneš cokoli číst nebo programovat.
---

# Než začneš stavět

(Upraveno podle skillu `before-building` z [davidondrej/skills](https://github.com/davidondrej/skills), licence MIT.)

Uživatel chce mít zadání „do posledního puntíku popsané a vyspecifikované, než začneme programovat“.

## 1. Hned, bez čtení souborů
Odpověz rovnou z toho, co uživatel řekl:
- **1–3 zásadní volby** skryté v nápadu (méně je lépe). U každé možnosti pár slovy + tvoje doporučení.
- Typické: jednorázové vs. bude se opakovat · pár řádků vs. pořádný modul · co nejhoršího to může rozbít (data zákazníků, výpočet, produkce) · kdo to bude používat.
- Drobnosti vynech. Pak se zastav a počkej na odpovědi.

## 2. Vizuální pilot (produkt nebo funkce s obrazovkami)
Hned po odpovědích na 1–3 zásadní volby ukaž **pilot**: jen vzhled s vymyšlenými daty, žádná backend logika. Další otázky klaď až nad ním („tady chybí X?“), ne v dlouhém kole otázek naslepo. Kontext už máš, doplň rozumné výchozí volby (uživatel 18. 11. 2026 po pátém kole otázek: chce pilotní návrh, ne zadávat odpovědi).
- Varianty jen **opravdu odlišné formy** (např. plocha s dlaždicemi vs. volné plátno vs. seznam), ne skoro stejné návrhy s jinou barvou. Radši jedna varianta než tři podobné.
- Navrhuj do skutečné aplikace, ne do odděleného dema. Vybraný návrh je závazný cíl.

## 3. Specifikace
Pak se doptávej **po jedné otázce** (s doporučením), dokud není jasné:
- co přesně má funkce dělat a pro koho, krok po kroku z pohledu uživatele,
- co dělat nemá (hranice),
- okrajové případy a chyby,
- jak poznáme, že je hotovo (měřítka přijetí, která jde ověřit),
- dopad na data, výpočet a produkci.

Navíc:
- Před stavbou vlastního nástroje najdi hotové (open-source) řešení a porovnej (uživatel: „neříkej mi, že na GitHubu není žádná hotová aplikace“).
- Když produkt sbírá osobní údaje, cizí data (scraping) nebo zprostředkovává práci, patří do specifikace i právní rámec (GDPR, licence).

Specifikaci zapiš do ticketu nebo do `docs/` projektu (podle jeho `AGENTS.md`) a nech ji uživatele schválit. **Kód až po schválení.**
