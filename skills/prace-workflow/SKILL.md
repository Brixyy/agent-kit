---
name: prace-workflow
description: Podrobný postup práce na úkolu v projektech Brixyy — ticket (GitHub Issue, u robotiky Linear), větev, PR, kontrola, předávka. Použij na začátku každé implementační úlohy, při zakládání PR a při přerušení práce.
---

# Postup práce na úkolu

## 1. Ticket
- Každá práce má ticket. **Robotika:** Linear, tým ROB (řídí se vlastním `AGENTS.md` robotiky). **Ostatní projekty:** GitHub Issue v repozitáři projektu (`gh issue create`). Žádná společná nástěnka není (GitHub Project zrušen 2026-11-19), stav práce nesou issues a PR.
- Když ticket uživatel nezadal, založ ho (stručný název, popis cíle, kritéria hotovo) a pracuj až potom.
- Stav práce na GitHubu: otevřené issue = k práci, s otevřeným PR (`Closes`/`Refs #<č>`) = rozpracované, zavřené sloučením PR s `Closes` = Done (agent pak ověří změnu v produkci a výsledek zapíše do issue, při selhání issue znovu otevře). Když potřebuješ rozhodnutí nebo podklad od uživatele: štítek **`čeká na uživatele`** + komentář s jednou konkrétní otázkou; po odpovědi štítek sundej. V Linearu (robotika) stavy Backlog/Todo → **In Progress** → **AI kontrola** → Done, na uživatele **Ke schválení** (jen opravdu čeká na rozhodnutí) / **Blokováno**, vždy s komentářem s jednou otázkou.
- Komentáře v ticketu piš česky a krátce: co se udělalo, co je ověřené, co neověřené, odkaz na PR.

## 2. Větev a PR
- Větev z aktuální výchozí větve: `<cislo-issue>-<kratky-popis>` (robotika: `rob-<cislo>-<popis>`), např. `12-stranky-sluzeb`. PR, které úkol dokončuje, má v popisu `Closes #12` (issue se zavře při sloučení); průběžné PR k témuž úkolu `Refs #12`.
- Jedno PR = jeden účel, ideálně do pár set řádků. Míří vždy do výchozí větve, nikdy na jinou feature větev.
- PR zakládej jako koncept (`gh pr create --draft`); v repech se vzorem ze šablony na něj CI neběží (kontrola je `skipped`, to není zelená). Za hotové ho označ (`gh pr ready <č>`) až po dokončení práce a místním ověření; do hotového PR nepushuj mezikroky zbytečně často (podrobnosti, Levné CI).
- Popis PR předávej souborem (`gh pr create --body-file popis.md`), ne dlouhým textem v příkazu.
- Popis PR (česky):
  - **Co a proč** (2–3 věty pro laika),
  - **Co se změnilo** (body),
  - **Jak ověřeno** (příkazy a výsledky; neověřené označ „neověřeno“),
  - **Rizika / co zkontrolovat**,
  - odkaz na ticket.

## 3. Kontrola a sloučení
- Před pushem spusť testy, lint a typecheck dotčené změnou (příkazy jsou v `AGENTS.md`); CI nemá být první místo, kde se chyba objeví. U UI změn ověř stránku v prohlížeči na desktopu i mobilu.
- Před sloučením nezávislé review (Claude Code: agent `reviewer`; spouštěj ho bez parametru `effort`, nižší hodnota by přebila jeho `effort: high`). Nálezy oprav nebo je výslovně uveď v PR. U větší změny (nová funkce, výpočet, víc souborů) ho zadej jako samostatného hodnotitele: jen ticket, číslo PR a jak výsledek spustit, bez tvého souhrnu (podrobnosti, Kontroly a testy); použij i skill `rozhodnuti`.
- **Review po opravách:** když review vrátí NEPROCHÁZÍ, nebo jsi kvůli nálezům měnil logiku či kód, pusť agenta `reviewer` znovu jen nad opravami (seznam nálezů + diff od minulého kola). Opravy textu a drobnosti se znovu nereviewují. Nejvýš 2 opakovaná kola (3 review celkem). Zůstane-li závažný nález neopravený, PR nesluč (ani auto-merge nezapínej): nálezy napiš do PR, issue označ štítkem `čeká na uživatele` (v Linearu stav Blokováno) a polož jednu otázku.
- Sloučení PR je trvale povolené. Uživatele se kvůli sloučení neptej. Koncept nejdřív označ za hotové (`gh pr ready <č>`), jinak sloučení selže. **Soukromé repo** (tarif GitHub Free nevynutí povinné kontroly, takže `--auto` by sloučil hned, i když CI ještě běží nebo selhalo): po review počkej na CI v pozadí (`gh pr checks <č> --watch`) a když žádný job neselhal, sluč `gh pr merge <č> --squash`; práci kvůli tomu nepřerušuj. **Veřejné repo s povinnými kontrolami** (agent-kit): zapni automatické sloučení `gh pr merge <č> --auto --squash`, GitHub sloučí sám po kontrolách. Hotovo ale není zapnutím auto-merge: ověř, že PR opravdu doběhl do sloučení (selhání, timeout nebo BEHIND řeš, nebo předej hlídání dál). Repo bez CI slučuj ručně až po ověření.

## 4. Cloudová session
- Prostředí připraví `sh scripts/cloud-setup.sh` (je v každém projektu).
- `gh` přes GraphQL nefunguje (HTTP 403 — `gh issue list`, `gh pr list`, `gh pr view` …). Používej REST: `gh api repos/Brixyy/<repo>/issues`, `gh api repos/Brixyy/<repo>/pulls`, komentář `gh api -X POST repos/Brixyy/<repo>/issues/<č>/comments -f body=…`, nebo GitHub MCP. `gh` může při 403 skončit kódem 0 — kontroluj výstup.
- Výsledek odevzdej jako větev + PR; předávku napiš do ticketu.

## 5. Když se to nedaří
- Po dvou neúspěšných cílených pokusech zastav. Napiš: co jsi zkusil, co se stalo, 2–3 hypotézy, co navrhuješ. Polož jednu otázku.

## 6. Předávka
Při přerušení nebo konci session použij skill `predavka` (zápis do ticketu nebo PR).
