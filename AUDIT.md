# Audit agent-kit
Projektová část skillu `audit` (`skills/audit/SKILL.md`). Repo je veřejné: do zprávy ani issues nepatří hesla, klíče, ID projektů ani údaje o zákaznících. Audit jen čte: nic neopravuje ani nevydává.

## Kdy a kam
- **Kdy:** 1. a 15. den v měsíci v 9:00, společná lokální rutina aplikace Claude „Portfolio – audit projektů“ (projde všechna repa portfolia po sobě, zakládá ji asistent). Mimořádně na požádání uživatele.
- **Rozsah:** lehký (nástroj bez produkce): oblasti 1, 3, 4, 5, 9 a 10 skillu.
- **Zpráva:** `_local/audit-<RRRR-MM-DD>/` v hlavní pracovní kopii (`/_local/` je v `.gitignore`), souhrn `ZPRAVA.md`.
- **Souhrnné issue** „Audit projektu <RRRR-MM-DD>“ se štítkem **`audit-projektu`** v `Brixyy/agent-kit`; text issue je veřejný. Issues nálezů jen pro kritické a vysoké.
- **Předchozí audit:** `gh issue list --repo Brixyy/agent-kit --label audit-projektu --state all --limit 1`. První audit podle tohoto souboru předchozí nemá.
- **Upozornění uživateli:** krátkou zprávu za celé portfolio posílá společná rutina do Telegramu (bot asistenta).

## Přístupy (jen čtení)
- **Kód a kontroly:** dočasný worktree na pevném commitu (`git worktree add --detach .claude/worktrees/audit-<datum> origin/main`), po auditu `git worktree remove`.
- **Nainstalovaná kopie pluginu:** verze v cache Claude Code proti `version` v `.claude-plugin/plugin.json` (`python -I tests/overit_plugin.py <složka pluginu>`).
- **Tajemství:** `.env*` neotvírat ani negrepovat. Úniky hledat přes upozornění GitHubu: `gh api repos/Brixyy/agent-kit/secret-scanning/alerts`.

## Měřítka projektu
- Kontext vkládaný hookem pod 9 000 znaků (hlídá `tests/test_kontext.py`, jádro je `global/AGENTS.md`); kolik místa zbývá.
- Opakované chyby agentů: kolik podnětů za období vedlo ke změně pravidla, kontroly nebo skriptu a zda se chyba přestala opakovat (odkud brát: doplnit s uživatelem).
- Používají všechny počítače a cloud aktuální verzi pluginu?

## Otázky projektu
- Neobsahuje repo ani historie nic citlivého (repo je veřejné)?
- Neodporují si `global/AGENTS.md`, `global/PODROBNOSTI.md`, skills a styl odpovědí? Nejsou pravidla duplicitní na více místech?
- Vznikl každý skill z opakovaného postupu, nebo jsou mezi nimi nepoužívané?
- Pokrývají testy pojistku (`hooks/`) tak, aby nevratná akce nemohla projít bez potvrzení?

## Kontroly kódu (v dočasném worktree)
- Testy jako CI (`.github/workflows/testy.yml`): `python -I tests/<soubor>.py` pro každý test, který workflow pouští; navíc `claude plugin validate .`.
- Lint ani typy projekt nemá; pro přehled `uvx ruff check .`. Závislosti projekt nemá. Mrtvý kód: `uvx vulture hooks scripts tests --min-confidence 80` (jen přehled, nálezy ověř ručně; neověřeno, že projde bez nastavení).
