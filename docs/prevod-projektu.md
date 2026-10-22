# Převod existujícího projektu na brixyy-kit (kontrolní seznam)

Ověřeno pilotem na prove-webu (Brixyy/prove-web#6).

1. **AGENTS.md** přepiš podle `Brixyy/project-template` (do ~200 řádků, pravdivě, bez Codexu). `CLAUDE.md` nech jako jediný řádek `@AGENTS.md` (import zaručí, že Claude pravidla načte; obsah patří jen do AGENTS.md).
2. **`.claude/settings.json`**: `extraKnownMarketplaces` + `enabledPlugins` (brixyy-kit) + deny čtení `.env`, `.env.local`, `.env.production`, `.env.development`, `.env.*.local`.
3. **`.gitignore`** musí obsahovat `.env*` soubory (kromě `.env.example`) a `.claude/worktrees/`. Zkontroluj, že v historii gitu nejsou tajné klíče (`git log -p | grep` na typické prefixy) — nález hlas uživateli, nic nepřepisuj.
4. **`.gitattributes`**: u existujícího repa **nepřidávej** `* text=auto eol=lf` (přepsalo by konce řádků ve všech souborech). Stačí `*.sh text eol=lf`.
5. **Cloud:** `scripts/cloud-setup.sh` (spustitelný, `git update-index --chmod=+x`), v cloud prostředí volat `sh scripts/cloud-setup.sh`. Do `.env.example` názvy proměnných bez hodnot. Cloudová session plugin z nastavení repozitáře **neinstaluje** — spusť `python -I scripts/zapojit-cloud.py <projekt>/.claude/settings.json` (z claude-kit): přidá hooky, které v cloudu stáhnou claude-kit, nainstalují plugin, vloží pravidla a zapnou pojistku.
6. **CI:** lint + typecheck + build při PR (vzor v šabloně). Pokud chybí skript `typecheck`, doplň ho — build typy často nekontroluje.
7. **Lint** ať vynechává `.claude/worktrees/`.
8. **Úkoly:** GitHub Issues + Project „Brixyy – projekty“ (č. 13); robotika zůstává v Linearu.
9. Zruš `_flow/` a ruční zrcadlení `.agents/skills` ↔ `.claude/skills` (skills jen v `.claude/skills`).
10. Jedno PR do výchozí větve, popis přes `--body-file`, po review `gh pr merge --auto --squash`. Repo s CI potřebuje povinné kontroly (ruleset) a zapnuté automatické sloučení.
