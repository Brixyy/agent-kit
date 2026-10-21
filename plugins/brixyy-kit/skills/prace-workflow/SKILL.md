---
name: prace-workflow
description: Podrobný postup práce na úkolu v projektech Brixyy — Linear ticket, větev, PR, kontrola, předávka. Použij na začátku každé implementační úlohy, při zakládání PR a při přerušení práce.
---

# Postup práce na úkolu

## 1. Ticket
- Každá práce má ticket v Linearu. Když ho uživatel nezadal, založ ho (stručný název, popis cíle, kritéria hotovo) a pracuj až potom.
- Stavy: Backlog/Todo → **In Progress** (začínáš) → **AI kontrola** (hotovo, běží review a testy) → **Ke schválení** (čeká na uživatele) → Done (**jen uživatel**). Když potřebuješ rozhodnutí nebo podklad: **Blokováno** + komentář s jednou konkrétní otázkou.
- Komentáře v ticketu piš česky a krátce: co se udělalo, co je ověřené, co neověřené, odkaz na PR.

## 2. Větev a PR
- Větev z aktuální výchozí větve: `<zkratka-ticketu>-<cislo>-<kratky-popis>`, např. `web-12-stranky-sluzeb`.
- Jedno PR = jeden účel, ideálně do pár set řádků. Míří vždy do výchozí větve, nikdy na jinou feature větev.
- Popis PR (česky):
  - **Co a proč** (2–3 věty pro laika),
  - **Co se změnilo** (body),
  - **Jak ověřeno** (příkazy a výsledky; neověřené označ „neověřeno“),
  - **Rizika / co zkontrolovat**,
  - odkaz na ticket.

## 3. Kontrola
- Spusť testy, lint a typecheck projektu (příkazy jsou v `AGENTS.md`). U UI změn ověř stránku v prohlížeči na desktopu i mobilu.
- Před sloučením použij agenta `reviewer`. Nálezy oprav nebo je výslovně uveď v PR.
- Sloučení PR, produkční deploy a migrace produkční DB jen po výslovném souhlasu uživatele.

## 4. Když se to nedaří
- Po dvou neúspěšných cílených pokusech zastav. Napiš: co jsi zkusil, co se stalo, 2–3 hypotézy, co navrhuješ. Polož jednu otázku.
- Nestav nové nástroje na diagnostiku, kontrakty ani „důkazní“ infrastrukturu, pokud to uživatel výslovně nechce.

## 5. Předávka při přerušení
Do ticketu (nebo PR) napiš:
- **Hotovo:** …
- **Zbývá:** …
- **Kde:** větev, PR, soubory
- **Pozor na:** …
