---
name: predavka
description: Předávka práce do nové session nebo jinému agentovi. Použij při konci nebo přerušení session, při plném kontextu, při přepnutí na jiný úkol nebo když uživatel chce „zadání / prompt pro novou session“.
---

# Předávka

Zachyť jen to, co nový agent potřebuje, aby pokračoval bez opakovaného ptaní, hledání a stejných chyb. (Upraveno podle skillu `handoff` z [davidondrej/skills](https://github.com/davidondrej/skills), licence MIT.)

## Zásady
1. **Popisuj stav, ne příkazy.** „Přihlášení hotové, odhlášení nezačaté“, ne „udělej odhlášení“. Nový agent si kroky zvolí sám.
2. **Odkazuj, nekopíruj.** Ticket, PR, commit, soubor (`cesta:řádek`), ADR, specifikace — odkazem.
3. **Zachovej proč.** Rozhodnutí, zavržené cesty a nezdary, které z kódu vyčíst nejdou.
4. **Pravdivě.** U každého tvrzení „ověřeno“ (čím) nebo „neověřeno“. Nový agent má tvrzení ověřit, ne jim slepě věřit.
5. **Bez tajemství.** Žádné klíče, hesla, tokeny ani osobní údaje — jen *kde* jsou (např. „Vercel env `RESEND_API_KEY`“).
6. **Jen užitečné.** Nepiš, co je v `AGENTS.md` projektu nebo v globálních pravidlech.

## Postup
1. Přečti `AGENTS.md` projektu, ať předávka neopakuje jeho obsah.
2. Pokud už předávka existuje (ticket, `STAV.md`, PR), aktualizuj ji místo nové.
3. Předávku zapiš **do ticketu** (komentář) nebo do PR; u práce napříč projekty do `portfolio/STAV.md` v repozitáři Brixyy/asistent. Uživateli ji ukaž v jednom bloku a připoj prompt pro novou session.

## Šablona
```
# PŘEDÁVKA: <krátký název>
<datum> · Ticket: <odkaz> · Projekt: <složka>

## Cíl
<1–3 věty>

## Stav
- HOTOVO: … (ověřeno: …)
- ROZPRACOVÁNO: … (kde: větev, PR)
- NEZAČATO: …

## Rozhodnutí a proč
- …

## Slepé uličky a pasti
- …

## Kde co je
- <soubor:řádky / PR / ticket> — co tam je

## Otevřená práce a závislosti
- …

---
## Prompt pro novou session
<Krátký kontext oznamovacími větami („X je hotové“, „Y nezačalo“).> Než odpovíš, přečti všechno z části „Kde co je“. Tvrzení v předávce ber jako kontext k ověření v kódu, ne jako fakta. Pak počkej na můj pokyn.
```
