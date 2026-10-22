---
name: rozhodnuti
description: Vypiš rozhodnutí z aktuální práce, kterými si nejsi jistý, a lepší alternativy. Jen když o to uživatel požádá („rozhodnutí“, „čím si nejsi jistý“, „/rozhodnuti“) nebo před sloučením větší změny.
disable-model-invocation: true
---

# Nejistá rozhodnutí

(Upraveno podle skillu `decisions` z [davidondrej/skills](https://github.com/davidondrej/skills), licence MIT.)

Projdi důležitá rozhodnutí a volby, které jsi při této práci udělal. U každého se zamysli, jestli existuje jiná dobrá varianta, kterou jsme nezvážili.

- **Nevypisuj** rozhodnutí, u kterých už máme nejlepší možné řešení.
- Vypiš **jen ta, kterými si opravdu nejsi jistý** — nejvýš 5, seřazená podle dopadu.
- U každého: co jsi zvolil · jaká je alternativa · co by se stalo, kdyby volba byla špatná · tvoje doporučení.
- Česky, krátce, srozumitelně pro laika. Na konci jedna otázka: které rozhodnutí chce uživatel změnit.
