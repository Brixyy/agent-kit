---
name: prace-workflow
description: Podrobný postup práce na úkolu v projektech Brixyy — ticket (GitHub Issue, u robotiky Linear), větev, PR, kontrola, předávka. Použij na začátku každé implementační úlohy, při zakládání PR a při přerušení práce.
---

# Postup práce na úkolu

## 1. Ticket
- Každá práce má ticket. **Robotika:** Linear, tým ROB (řídí se vlastním `AGENTS.md` robotiky). **Ostatní projekty:** GitHub Issue v repozitáři projektu (`gh issue create`), přidané do GitHub Projectu „Brixyy – projekty“ (`gh project item-add 13 --owner Brixyy --url <issue-url>`; https://github.com/users/Brixyy/projects/13).
- Když ticket uživatel nezadal, založ ho (stručný název, popis cíle, kritéria hotovo) a pracuj až potom.
- Stavy (pole **Stav** v GitHub Projectu, v Linearu stejnojmenné stavy): Backlog/Todo → **In Progress** (začínáš) → **AI kontrola** (hotovo, běží review a testy) → Done (issue zavře sloučení PR s `Closes`; agent pak ověří změnu v produkci a výsledek zapíše do issue, při selhání issue znovu otevře). **Ke schválení** jen tam, kde opravdu čeká na rozhodnutí uživatele. Když potřebuješ rozhodnutí nebo podklad: **Blokováno** + komentář s jednou konkrétní otázkou.
- Komentáře v ticketu piš česky a krátce: co se udělalo, co je ověřené, co neověřené, odkaz na PR.

## 2. Větev a PR
- Větev z aktuální výchozí větve: `<cislo-issue>-<kratky-popis>` (robotika: `rob-<cislo>-<popis>`), např. `12-stranky-sluzeb`. PR, které úkol dokončuje, má v popisu `Closes #12` (issue se zavře při sloučení); průběžné PR k témuž úkolu `Refs #12`.
- Jedno PR = jeden účel, ideálně do pár set řádků. Míří vždy do výchozí větve, nikdy na jinou feature větev.
- Popis PR předávej souborem (`gh pr create --body-file popis.md`), ne dlouhým textem v příkazu.
- Popis PR (česky):
  - **Co a proč** (2–3 věty pro laika),
  - **Co se změnilo** (body),
  - **Jak ověřeno** (příkazy a výsledky; neověřené označ „neověřeno“),
  - **Rizika / co zkontrolovat**,
  - odkaz na ticket.

## 3. Kontrola a sloučení
- Spusť testy, lint a typecheck projektu (příkazy jsou v `AGENTS.md`). U UI změn ověř stránku v prohlížeči na desktopu i mobilu.
- Před sloučením nezávislé review (Claude Code: agent `reviewer`). Nálezy oprav nebo je výslovně uveď v PR. U větší změny použij i skill `rozhodnuti`.
- **Review po opravách:** když review něco našlo a ty jsi to opravil, pusť review znovu, ale jen nad opravami (seznam nálezů + diff od minulého kola). Kolo opakuj, dokud review hlásí závažný nález, nejvýš 3 kola; pak se zastav a nevyřešené nálezy napiš do PR. Bez nálezů nebo s drobnostmi stylu se další kolo nepouští.
- Sloučení PR je trvale povolené. Po review zapni **automatické sloučení** `gh pr merge <č> --auto --squash` — GitHub PR sloučí sám po povinných kontrolách. Uživatele se kvůli sloučení neptej. Hotovo ale není zapnutím auto-merge: ověř, že PR opravdu doběhl do sloučení (selhání, timeout nebo BEHIND řeš, nebo předej hlídání dál). Repo bez CI slučuj ručně až po ověření.

## 4. Cloudová session
- Prostředí připraví `sh scripts/cloud-setup.sh` (je v každém projektu).
- `gh` přes GraphQL nefunguje (HTTP 403 — `gh issue list`, `gh pr list`, `gh pr view` …). Používej REST: `gh api repos/Brixyy/<repo>/issues`, `gh api repos/Brixyy/<repo>/pulls`, komentář `gh api -X POST repos/Brixyy/<repo>/issues/<č>/comments -f body=…`, nebo GitHub MCP. `gh` může při 403 skončit kódem 0 — kontroluj výstup.
- Výsledek odevzdej jako větev + PR; předávku napiš do ticketu.

## 5. Když se to nedaří
- Po dvou neúspěšných cílených pokusech zastav. Napiš: co jsi zkusil, co se stalo, 2–3 hypotézy, co navrhuješ. Polož jednu otázku.

## 6. Předávka
Při přerušení nebo konci session použij skill `predavka` (zápis do ticketu nebo PR).
