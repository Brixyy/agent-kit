---
name: poznamka
description: Zapiš myšlenku, nápad, podnět, stížnost nebo fakt o uživateli do schránky osobního asistenta (Brixyy/asistent) a vrať se k práci. Použij vždy, když uživatel řekne „poznamenej si“, „zapamatuj si“, „podnět“, „nápad“, „stížnost“, „do asistenta“, nebo když chce změnit globální pravidla a není v session asistenta.
---

# Poznámka do asistenta

Zápis je rychlý a neodvádí od práce: jedno issue v soukromém repozitáři `Brixyy/asistent`. Zpracuje ho asistent (session ve složce `Dev/asistent`), ne ty.

1. Vyber štítek: `myšlenka` (nápad, postřeh) · `podnět` (změna pravidel, nástrojů, workflow) · `stížnost` (co vadí) · `o mně` (fakt nebo preference uživatele).
2. Název: krátké shrnutí česky. Tělo: **slova uživatele** (citace nebo věrná parafráze), datum, odkud (projekt/session) a jednou větou kontext. Nic nedomýšlej; domněnku označ „odvozeno“.
3. Nikdy nezapisuj hesla, klíče ani citlivé údaje (zdraví, finance…), pokud o to uživatel výslovně nepožádá.
4. Založ přes REST (funguje lokálně i v cloudu):
   ```
   gh api -X POST repos/Brixyy/asistent/issues -f title="<název>" -f body="<tělo>" -f "labels[]=<štítek>"
   ```
5. Uživateli jednou větou potvrď s odkazem na issue a pokračuj v původní práci.
