---
name: prevod-projektu
description: Převod existujícího projektu nebo založení nového na společná pravidla agent-kitu (AGENTS.md, nastavení agenta, pojistka, cloud, CI, automatické sloučení). Použij, když uživatel chce „převést projekt“, „založit nový projekt“ nebo „napojit projekt na agent-kit“.
---

# Převod projektu na agent-kit

Nový projekt zakládej ze šablony `Brixyy/project-template` (už obsahuje body 1–6). U existujícího projektu projdi seznam; vše jedním PR do výchozí větve. Ověřeno na prove-webu, prove-aplikaci, statice, robotice, tradingu a cloudroomu (10/2026).

1. **`AGENTS.md`** přepiš podle šablony: do ~200 řádků, pravdivě, bez historických nástrojů. `CLAUDE.md` je jediný řádek `@AGENTS.md` (Claude Code tak načte stejná pravidla jako Codex; obsah patří jen do `AGENTS.md`). Globální pravidla sem nekopíruj.
2. **`.claude/settings.json`** (vytvoří a doplní i `scripts/napojit-projekt.py` z bodu 3): `extraKnownMarketplaces` `agent-kit` (`github`, `Brixyy/agent-kit`) + `enabledPlugins` `agent-kit@agent-kit` + deny čtení `.env`, `.env.local`, `.env.production`, `.env.development`, `.env.*.local`.
3. **Cloud:** cloudová session plugin z nastavení repozitáře neinstaluje. Z agent-kitu spusť `python -I scripts/napojit-projekt.py <projekt>/.claude/settings.json` — přidá hooky, které v cloudu stáhnou agent-kit, nainstalují plugin, vloží pravidla a zapnou pojistku. Do projektu patří i `scripts/cloud-setup.sh` (instalace závislostí; spustitelný přes `git update-index --chmod=+x`).
4. **`.gitignore`**: `.env*` (kromě `.env.example`) a `.claude/worktrees/`. Zkontroluj historii gitu na tajné klíče (`git log -p | grep` na typické prefixy) — nález hlas uživateli, historii nepřepisuj.
5. **`.gitattributes`**: u existujícího repa **nepřidávej** `* text=auto eol=lf` (přepsalo by konce řádků všech souborů); stačí `*.sh text eol=lf`.
6. **CI** při PR: lint + typecheck + testy (+ build, pokud nesahá do produkční DB). Pravidelné (cron) běhy jen pro věci, které se mění bez změny kódu. Lint vynechává `.claude/worktrees/`.
7. **GitHub:** ruleset s **povinnými kontrolami** na výchozí větvi + zapnuté **automatické sloučení** a mazání větví po sloučení (`gh api -X PATCH repos/Brixyy/<repo> -F allow_auto_merge=true -F delete_branch_on_merge=true`). Bez povinných kontrol by automatické sloučení proběhlo hned, před testy.
8. **Úkoly:** GitHub Issues + Project „Brixyy – projekty“ (č. 13); robotika v Linearu.
9. Zruš pozůstatky starých nástrojů (`_flow/`, zrcadla `.agents/skills` ↔ `.claude/skills`, lokální zákazy v `.claude/settings.local.json`, které blokují běžnou práci).
10. PR s popisem přes `--body-file`, review, pak `gh pr merge --auto --squash`.
