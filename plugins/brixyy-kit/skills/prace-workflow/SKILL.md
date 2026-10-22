---
name: prace-workflow
description: Podrobný postup práce na úkolu v projektech Brixyy — ticket (GitHub Issue, u robotiky Linear), větev, PR, kontrola, předávka. Použij na začátku každé implementační úlohy, při zakládání PR a při přerušení práce.
---

# Postup práce na úkolu

## 1. Ticket
- Každá práce má ticket. **Robotika:** Linear, tým ROB (řídí se vlastním `AGENTS.md` robotiky). **Ostatní projekty:** GitHub Issue v repozitáři projektu (`gh issue create`), přidané do GitHub Projectu „Brixyy – projekty“ (`gh project item-add 13 --owner Brixyy --url <issue-url>`; https://github.com/users/Brixyy/projects/13).
- Když ticket uživatel nezadal, založ ho (stručný název, popis cíle, kritéria hotovo) a pracuj až potom.
- Stavy (pole **Stav** v GitHub Projectu, v Linearu stejnojmenné stavy): Backlog/Todo → **In Progress** (začínáš) → **AI kontrola** (hotovo, běží review a testy) → **Ke schválení** (čeká na uživatele) → Done (**jen uživatel**; issue zavírá uživatel). Když potřebuješ rozhodnutí nebo podklad: **Blokováno** + komentář s jednou konkrétní otázkou.
- Komentáře v ticketu piš česky a krátce: co se udělalo, co je ověřené, co neověřené, odkaz na PR.

## 2. Větev a PR
- Větev z aktuální výchozí větve: `<cislo-issue>-<kratky-popis>` (robotika: `rob-<cislo>-<popis>`), např. `12-stranky-sluzeb`. V popisu PR uveď `Refs #12` — ne `Closes`, issue zavírá uživatel.
- Jedno PR = jeden účel, ideálně do pár set řádků. Míří vždy do výchozí větve, nikdy na jinou feature větev.
- Popis PR předávej souborem (`gh pr create --body-file popis.md`), ne dlouhým textem v příkazu.
- Popis PR (česky):
  - **Co a proč** (2–3 věty pro laika),
  - **Co se změnilo** (body),
  - **Jak ověřeno** (příkazy a výsledky; neověřené označ „neověřeno“),
  - **Rizika / co zkontrolovat**,
  - odkaz na ticket.

## 3. Kontrola
- Spusť testy, lint a typecheck projektu (příkazy jsou v `AGENTS.md`). U UI změn ověř stránku v prohlížeči na desktopu i mobilu.
- Před sloučením použij agenta `reviewer`. Nálezy oprav nebo je výslovně uveď v PR.
- Sloučení PR má uživatel trvale povolené. Po review zapni **automatické sloučení**: `gh pr merge <č> --auto --squash` — GitHub PR sloučí sám, jakmile projdou povinné kontroly (nastavené ve všech repozitářích s CI). Na zelené CI nečekej a uživatele se kvůli sloučení neptej. Bez povinných kontrol (repo bez CI) slučuj ručně až po ověření. Ruční produkční deploy a migrace produkční DB mimo PR jen po výslovném souhlasu uživatele.

## Cloudová session (claude.ai/code)
- Vidí jen repozitář, nad kterým běží, a tento veřejný `claude-kit`. Nemá `.env*`, složku `Dev`, Chrome ani lokální konektory — práce, která potřebuje Vercel, Supabase nebo prohlížeč, patří do lokální session.
- Prostředí připraví `sh scripts/cloud-setup.sh` (je v každém projektu).
- `gh` přes GraphQL v cloudu nefunguje (HTTP 403 — týká se `gh issue list`, `gh pr list`, `gh pr view` …). Používej REST: `gh api repos/Brixyy/<repo>/issues`, `gh api repos/Brixyy/<repo>/pulls`, komentář `gh api -X POST repos/Brixyy/<repo>/issues/<č>/comments -f body=…`, nebo nástroje GitHub MCP. Pozor: `gh` při chybě 403 může skončit kódem 0 — kontroluj výstup.
- Výsledek odevzdej jako větev + PR; předávku napiš do ticketu.

## 4. Když se to nedaří
- Po dvou neúspěšných cílených pokusech zastav. Napiš: co jsi zkusil, co se stalo, 2–3 hypotézy, co navrhuješ. Polož jednu otázku.
- Nestav nové nástroje na diagnostiku, kontrakty ani „důkazní“ infrastrukturu, pokud to uživatel výslovně nechce.

## 5. Předávka při přerušení
Do ticketu (nebo PR) napiš:
- **Hotovo:** …
- **Zbývá:** …
- **Kde:** větev, PR, soubory
- **Pozor na:** …
