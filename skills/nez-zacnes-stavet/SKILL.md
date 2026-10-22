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

## 2. Specifikace
Po odpovědích se doptávej **po jedné otázce** (s doporučením), dokud není jasné:
- co přesně má funkce dělat a pro koho, krok po kroku z pohledu uživatele,
- co dělat nemá (hranice),
- okrajové případy a chyby,
- jak poznáme, že je hotovo (měřítka přijetí, která jde ověřit),
- dopad na data, výpočet a produkci.

Specifikaci zapiš do ticketu nebo do `docs/` projektu (podle jeho `AGENTS.md`) a nech ji uživatele schválit. **Kód až po schválení.**
