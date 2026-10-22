"""PreToolUse pojistka: zastaví nevratné a produkční akce v jakémkoli režimu oprávnění.

Akci pustí jen tehdy, když existuje čerstvé jednorázové potvrzení
~/.agents/potvrzeno.txt (max. 15 minut staré). Agent ho smí vytvořit
jedině poté, co uživatel akci výslovně schválil v chatu. Po použití se smaže.
Čtení souborů .env se blokuje vždy, bez možnosti potvrzení.

Výstup: Claude Code dostane JSON s permissionDecision. S argumentem --exit-code
(Codex a další agenti) se zákaz hlásí kódem 2 a důvodem na stderr.
"""
import json
import os
import re
import sys
import time

POTVRZENI = os.path.join(os.path.expanduser("~"), ".agents", "potvrzeno.txt")
EXIT_KOD = "--exit-code" in sys.argv
PLATNOST_S = 15 * 60

RIZIKOVE_PRIKAZY = [
    (r"\bgit\s+push\b[^\n;&|]*\b(main|master)\b", "push do main/master"),
    (r"\bgit\s+push\b[^\n;&|]*(\s--force\b|\s-f\b|\s--delete\b|\s:\S)", "force push nebo mazání větve na GitHubu"),
    (r"\bgh\s+repo\s+(delete|archive|rename)\b", "mazání/archivace repozitáře"),
    # Úpravy issues (zavřít, štítek, komentář) jsou vratné; hlídají se zápisy do nastavení, větví a obsahu.
    (r"\bgh\s+api\b(?![^\n]*\brepos/[^/\s]+/[^/\s]+/issues\b)[^\n]*(-X|--method)\s*(DELETE|PUT|PATCH)\b", "zápis přes GitHub API"),
    (r"\bvercel\b[^\n]*\s--prod\b", "produkční deploy na Vercel"),
    (r"\bvercel\s+(deploy|promote|rollback|remove|rm|env\s+(add|rm|update)|domains\s+rm)\b", "změna na Vercelu"),
    (r"\bvercel\s+api\b[^\n]*--method\s+(POST|PATCH|PUT|DELETE)\b", "zápis přes Vercel API"),
    (r"\bsupabase\s+(db\s+(push|reset)|functions\s+deploy|migration\s+repair|secrets\s+(set|unset))\b", "změna v Supabase"),
    (r"\bprisma\s+(migrate\s+(deploy|reset)|db\s+push)\b", "migrace databáze"),
    (r"\b(poe|npm\s+run|pnpm|yarn)\s+[^\n]*\b(deploy|release)[:\w-]*\b", "deploy/release skript"),
]

RIZIKOVE_MCP = re.compile(
    r"__(apply_migration|execute_sql|deploy_edge_function|merge_branch|reset_branch|delete_branch|"
    r"pause_project|unpause_project|create_deployment|request_promote|request_rollback|"
    r"delete_[a-z_]+|create_project|update_project|edit_project_env|create_project_env|"
    r"add_project_domain|buy_domain|replace_domain_dns_records|update_record|create_record)$"
)
# Plánované úlohy agent spravuje sám (uživatel 22. 10. 2026: „chci, aby sis nastavoval tyhle rutiny“).
VOLNE_MCP = re.compile(r"^mcp__scheduled-tasks__")

ENV_CTENI = re.compile(
    r"\b(cat|type|less|more|head|tail|Get-Content|gc|bat|xxd|strings)\b[^\n|;&]*"
    r"(^|[\\/\s\"'])\.env(\.local|\.production|\.development|\.[\w-]+\.local)?([\s\"']|$)"
)


def bez_textu(prikaz):
    """Odstraní obsah heredoců a řetězců v uvozovkách, aby pojistka nereagovala na text (popis PR, echo)."""
    prikaz = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n.*?\n\s*\1\b", "<<HEREDOC", prikaz, flags=re.S)
    prikaz = re.sub(r"'[^']*'", "''", prikaz)
    return re.sub(r'"(\\.|[^"\\])*"', '""', prikaz)


def vystup(rozhodnuti, duvod):
    if EXIT_KOD:
        print(duvod, file=sys.stderr)
        sys.exit(2)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": rozhodnuti,
        "permissionDecisionReason": duvod,
    }}, ensure_ascii=False))
    sys.exit(0)


def pouzito_pro(tool_use_id):
    try:
        return bool(tool_use_id) and open(POTVRZENI + ".pouzito", encoding="utf-8").read().strip() == tool_use_id
    except OSError:
        return False


def potvrzeno(tool_use_id):
    # Potvrzení se spotřebuje pro jedno konkrétní volání nástroje; další hook nad stejným voláním ho uzná také.
    if pouzito_pro(tool_use_id):
        return True
    try:
        cerstve = time.time() - os.path.getmtime(POTVRZENI) <= PLATNOST_S
        os.remove(POTVRZENI)
    except OSError:
        # Souběžný hook nad stejným voláním mohl potvrzení právě spotřebovat; chvíli počkej na jeho zápis.
        for _ in range(10):
            time.sleep(0.05)
            if pouzito_pro(tool_use_id):
                return True
        return False
    if cerstve and tool_use_id:
        with open(POTVRZENI + ".pouzito", "w", encoding="utf-8") as f:
            f.write(tool_use_id)
    return cerstve


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    vstup = data.get("tool_input") or {}
    # Codex a jiní agenti nemusí posílat tool_name; příkaz v tool_input.command znamená shell.
    nastroj = data.get("tool_name") or ("Bash" if vstup.get("command") else "")

    if nastroj in ("Read", "Edit", "Write"):
        cesta = os.path.basename(str(vstup.get("file_path", "")))
        if re.fullmatch(r"\.env(\.local|\.production|\.development|\.[\w-]+\.local)?", cesta):
            vystup("deny", "Pojistka: soubory .env s hesly a klíči se nečtou ani neupravují. Ptej se uživatele na konkrétní název proměnné.")
        sys.exit(0)

    popis = None
    if nastroj in ("Bash", "PowerShell") or (vstup.get("command") and "__" not in nastroj):
        prikaz = str(vstup.get("command", ""))
        if ENV_CTENI.search(prikaz):
            vystup("deny", "Pojistka: vypisování souborů .env je zakázané. Pracuj jen s názvy proměnných, ne s hodnotami.")
        # Text v uvozovkách se ignoruje, kromě případů, kdy se spouští jako příkaz (sh -c, eval, PowerShell -Command).
        spousti_text = re.search(r"\b(sh|bash|zsh|pwsh|powershell|cmd)(\.exe)?\b[^\n]*\s(-c|-Command|/c)\b|\beval\b", prikaz, re.I)
        kontrolovany = prikaz if spousti_text else bez_textu(prikaz)
        for vzor, nazev in RIZIKOVE_PRIKAZY:
            if re.search(vzor, kontrolovany, re.IGNORECASE):
                popis = nazev
                break
        # Nástrojová repa bez produkce (agent-kit, šablona) smí pushovat do main bez potvrzení.
        misto = (str(data.get("cwd", "")) + " " + prikaz).replace("\\", "/").lower()
        if popis == "push do main/master" and re.search(r"/dev/(agent-kit|project-template)\b", misto):
            popis = None
    elif RIZIKOVE_MCP.search(nastroj) and not VOLNE_MCP.search(nastroj):
        popis = "produkční akce přes " + nastroj.split("__")[-1]

    if popis is None:
        sys.exit(0)
    if potvrzeno(data.get("tool_use_id", "")):
        sys.exit(0)
    vystup("deny", (
        f"Pojistka: {popis}. Tohle je nevratná nebo produkční akce. Nejdřív se zeptej uživatele v chatu "
        f"a řekni mu přesně, co se stane. Teprve po jeho výslovném souhlasu vytvoř soubor {POTVRZENI} "
        f"a akci zopakuj (potvrzení platí 15 minut a jednou)."
    ))


main()
