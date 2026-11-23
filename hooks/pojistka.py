"""PreToolUse pojistka: zastaví nevratné a produkční akce v jakémkoli režimu oprávnění.

Akci pustí jen tehdy, když existuje čerstvé potvrzení ~/.agents/potvrzeno.txt
(max. 15 minut staré). Agent ho smí vytvořit jedině poté, co uživatel akci
výslovně schválil v chatu. Dva druhy:
- jednorázové (bez řádků „krok:“): pustí jednu akci a smaže se;
- dávka (řádky „krok: <text>“): 15 minut pustí každou akci, jejíž příkaz nebo volání
  nástroje obsahuje text některého kroku; jiná riziková akce se zastaví.
Potvrzení chce i vypnutí vlastních kontrol: úprava pojistky a hooků, hooky v nastavení
agenta, vypnutí nebo smazání GitHub workflow (Brixyy/asistent#105).
Otevírání a vypisování souborů .env se blokuje vždy, bez možnosti potvrzení.
Načíst je do procesu (source, --env-file) se smí; zápis jen skriptem scripts/env_nastav.py se zálohou.

Výstup: Claude Code dostane JSON s permissionDecision. S argumentem --exit-code
(Codex a další agenti) se zákaz hlásí kódem 2 a důvodem na stderr.
"""
import bisect
import json
import os
import re
import sys
import time

POTVRZENI = os.path.join(os.path.expanduser("~"), ".agents", "potvrzeno.txt")
EXIT_KOD = "--exit-code" in sys.argv
PLATNOST_S = 15 * 60

# Soubory, kterými agent vypíná vlastní kontroly: pojistka, hooky pluginu, nastavení s hooky.
# Výjimka jen pro stejnojmenný modul výpočtu prove-statika (src/prove_statika/pojistka.py),
# který vlastní kontrolou agenta není; při pochybnosti pojistka blokuje dál.
# Spouštěč spust.sh se hlídá v hooks/ nebo bez cesty (jiné projekty můžou mít vlastní scripts/spust.sh).
VLASTNI_KONTROLY = (
    r"(?<![\w-])((?<!prove_statika[\\/])pojistka\.py|pojist~\d+\.py|cloud-pojistka\.sh"
    r"|hooks[\\/]spust\.sh|(?<![\w-][\\/])spust\.sh|hooks[\\/]hooks\.json|\.codex[\\/]hooks\.json)"
)
NASTAVENI = re.compile(r"/\.claude/settings(\.local)?\.json$", re.I)
# Příkazy, které soubor mažou, přesouvají, přepisují nebo vrací do jiné verze.
MENI_SOUBOR = (
    r"(?<![\w-])(rm|rmdir|rd|del|erase|Remove-Item|mv|move|Move-Item|ren|rni|Rename-Item|tee|truncate|sed\s+-i"
    r"|git\s+(rm|mv|checkout|restore))\b"
)
# Zápis obsahu v PowerShellu (i zkratky); hlídá se jen u vlastních kontrol, nové workflow v PR projdou.
ZAPISUJE = r"(?<![\w-])(Set-Content|Add-Content|Clear-Content|Out-File|New-Item|sc|ac|clc|ni)\b"
# Kopírování a odkazy: soubor přepíše jen cíl (každý argument kromě zdroje), čtení zdroje je v pořádku.
# „install“ jen jako samostatný příkaz, ne „npm install“.
KOPIRUJE = r"((?<![\w-])(cp|copy|cpi|Copy-Item|rsync|ln)\b|(^|(?<=[;&|(\n]))\s*install\b)"
# Složka hooks agent-kitu: bez cesty, ./hooks, agent-kit/hooks nebo nainstalovaná verze …/2.15.4/hooks.
# Ne .git/hooks ani src/hooks jiných projektů.
HOOKS_AK = (
    r"(^|(?<=[\s='\"])|(?<=\./)|(?<=\.\\)|(?<=agent-kit[\\/])|(?<=\.\d[\\/])|(?<=\.\d\d[\\/])"
    r"|(?<=CLAUDE_PLUGIN_ROOT[\\/])|(?<=CLAUDE_PLUGIN_ROOT}[\\/]))hooks"
)
CIL_KONTROLY = r"(" + VLASTNI_KONTROLY + r"|" + HOOKS_AK + r"([\\/]|\s|$))"
# Zástupné znaky, které zasáhnou pojistku nebo hooky (rm hooks/*, rm pojist*.py).
GLOB_KONTROLY = r"(" + HOOKS_AK + r"[\\/]\S*[*?\[]|(?<![\w-])(pojist|spust)\S*[*?\[])"
# Instalace pluginu: smazáním cache zmizí pojistka i hooky (lokálně i v cloudu).
INSTALACE = (
    r"(\.claude([\\/](plugins([\\/](cache|marketplaces))?))?[\\/]?(\*|\s|$)|\.claude[\\/]plugins[\\/]\S*agent-kit"
    r"|\.agents([\\/]agent-kit)?[\\/]?(\*|\s|$)|(?<![\w./\\-])agent-kit[\\/]?(\*|\s|$))"
)
# Globální přepínače gitu před podpříkazem (git -C . push, git -c a=b push, git --no-pager push,
# Brixyy/agent-kit#95). Přepínače s hodnotou v dalším slově jsou vyjmenované, ostatní jsou bez hodnoty
# nebo s ní za „=“.
GIT_PREPINACE = re.compile(
    r"\bgit((\s+(-C|-c|--git-dir|--work-tree|--namespace|--super-prefix|--config-env)(\s+|=)\S+"
    r"|\s+--?[\w-]+(=\S+)?))+(?=\s)",
    re.I,
)


def bez_prepinacu_gitu(prikaz):
    """git <globální přepínače> <podpříkaz> → git <podpříkaz>, aby vzory viděly podpříkaz hned za gitem."""
    return GIT_PREPINACE.sub("git", prikaz)


# Začátek příkazu: začátek řádku nebo za ; & | ( (volitelně sudo).
ZACATEK_PRIKAZU = r"(^|(?<=[;&|(\n]))\s*(sudo\s+)?"
# Příkazy, které find spustí nad nalezenými soubory a které soubor mění.
FIND_MENI = r"(rm|mv|cp|tee|truncate|sed\s+-i|ln|shred|dd|Remove-Item)\b"

RIZIKOVE_PRIKAZY = [
    (r"\bgit\s+push\b[^\n;&|]*\b(main|master)\b", "push do main/master"),
    (r"\bgit\s+push\b[^\n;&|]*(\s--force\b|\s-f\b|\s--delete\b|\s:\S)", "force push nebo mazání větve na GitHubu"),
    (r"\bgh\s+repo\s+(delete|archive|rename)\b", "mazání/archivace repozitáře"),
    # Úpravy issues (zavřít, štítek, komentář) jsou vratné a sloučení PR je trvale povolené (i přes REST v cloudu);
    # hlídají se zápisy do nastavení, větví a obsahu.
    (r"\bgh\s+api\b(?![^\n]*\brepos/[^/\s]+/[^/\s]+/(issues\b|pulls/\d+/merge\b))[^\n]*(-X|--method)\s*(DELETE|PUT|PATCH)\b", "zápis přes GitHub API"),
    (r"\bvercel\b[^\n]*\s--prod\b", "produkční deploy na Vercel"),
    (r"\bvercel\s+(deploy|promote|rollback|remove|rm|env\s+(add|rm|update)|domains\s+rm)\b", "změna na Vercelu"),
    (r"\bvercel\s+api\b[^\n]*--method\s+(POST|PATCH|PUT|DELETE)\b", "zápis přes Vercel API"),
    (r"\bsupabase\s+(db\s+(push|reset)|functions\s+deploy|migration\s+repair|secrets\s+(set|unset))\b", "změna v Supabase"),
    (r"\bprisma\s+(migrate\s+(deploy|reset)|db\s+push)\b", "migrace databáze"),
    (r"\b(poe|npm\s+run|pnpm|yarn)\s+[^\n]*\b(deploy|release)[:\w-]*\b", "deploy/release skript"),
    # Agent nesmí potichu vypnout vlastní kontroly (Brixyy/asistent#105). Úpravy workflow v PR projdou, hlídá je audit testování.
    (r"\bgh\s+workflow\s+disable\b", "vypnutí kontroly (GitHub workflow)"),
    (MENI_SOUBOR + r"[^\n;&|]*(?<![\w-])\.github([\\/]workflows)?([\\/]?\s|[\\/]?$)", "smazání kontroly (GitHub workflow)"),
    (MENI_SOUBOR + r"[^\n;&|]*\.github[\\/]workflows[\\/]", "smazání kontroly (GitHub workflow)"),
    (MENI_SOUBOR + r"[^\n;&|]*(" + VLASTNI_KONTROLY + r"|" + HOOKS_AK + r"[\\/]?(\s|$)|" + GLOB_KONTROLY + r")"
     r"|" + ZAPISUJE + r"[^\n;&|]*" + VLASTNI_KONTROLY + r"|>\s*\S*" + VLASTNI_KONTROLY,
     "úprava pojistky nebo hooků"),
    (KOPIRUJE + r"(\s+-\S+)*\s+[^\s-]\S*[^\n;&|]*?[\s=]\S*?" + CIL_KONTROLY
     + r"|" + KOPIRUJE + r"[^\n;&|]*-(Destination|-?target-directory)[\s=]+\S*" + CIL_KONTROLY,
     "úprava pojistky nebo hooků"),
    (r"(?<![\w-])dd\b[^\n;&|]*\bof=\S*" + CIL_KONTROLY, "úprava pojistky nebo hooků"),
    (r"(?<![\w-])find\b[^\n;&|]*(" + VLASTNI_KONTROLY + r"|" + GLOB_KONTROLY + r"|" + HOOKS_AK + r"\b)[^\n;&|]*"
     r"\s(-delete\b|-(exec|execdir|ok)\s+" + FIND_MENI + r")", "úprava pojistky nebo hooků"),
    (r"(?<![\w-])find\b[^\n;&]*(" + VLASTNI_KONTROLY + r"|" + GLOB_KONTROLY + r"|" + HOOKS_AK + r"\b)[^\n;&]*"
     r"\|\s*xargs\b[^\n;&|]*\b" + FIND_MENI, "úprava pojistky nebo hooků"),
    (MENI_SOUBOR + r"[^\n;&|]*" + INSTALACE, "smazání pluginu agent-kit (pojistka)"),
    # Stažení nebo rozbalení přes pojistku či do složky hooks (Brixyy/agent-kit#41).
    # Jen jako příkaz (ne „rg curl -o …“); velikost písmen přepínačů rozhoduje (curl -O, tar -c jen čtou).
    (ZACATEK_PRIKAZU + r"(curl\b[^\n;&|]*\s((?-i:-[a-zA-Z]*o)|--output|--output-dir)"
     r"|wget\b[^\n;&|]*\s((?-i:-O|-P)|--output-document|--directory-prefix)"
     r"|(Invoke-WebRequest|iwr|Invoke-RestMethod|irm)\b[^\n;&|]*\s-Out(File)?)[\s=]*\S*" + CIL_KONTROLY,
     "úprava pojistky nebo hooků"),
    (ZACATEK_PRIKAZU + r"(tar\b(?=\s+-?(?-i:[a-zA-Z]*x[a-zA-Z]*)\b|[^\n;&|]*\s(--extract|--get)\b)[^\n;&|]*\s((?-i:-C)|--directory)|unzip\b[^\n;&|]*\s(?-i:-d)"
     r"|Expand-Archive\b[^\n;&|]*\s-Dest\w*)[\s=]*\S*" + CIL_KONTROLY, "úprava pojistky nebo hooků"),
    (r"\bclaude\s+plugins?\s+(disable|uninstall|remove)\b[^\n;&|]*agent-kit", "vypnutí pluginu agent-kit (pojistka)"),
    (r"\bdisableAllHooks\W*[:=]\s*true", "vypnutí hooků"),
]

RIZIKOVE_MCP = re.compile(
    r"__(apply_migration|execute_sql|deploy_edge_function|merge_branch|reset_branch|delete_branch|"
    r"pause_project|unpause_project|create_deployment|request_promote|request_rollback|"
    r"delete_[a-z_]+|create_project|update_project|edit_project_env|create_project_env|"
    r"add_project_domain|buy_domain|replace_domain_dns_records|update_record|create_record)$"
)
# Plánované úlohy agent spravuje sám (uživatel 22. 10. 2026: „chci, aby sis nastavoval tyhle rutiny“).
VOLNE_MCP = re.compile(r"^mcp__scheduled-tasks__")

# Každý soubor .env* kromě šablon (.env.example, .env.sample, .env.template) — i zálohy a .env.staging.
ENV_SOUBOR = r"\.env(?!\.(example|sample|template)\b)[\w.-]*"
ENV_CTENI = re.compile(
    r"\b(cat|type|less|more|head|tail|Get-Content|gc|bat|xxd|strings|grep|rg|findstr|Select-String|sed|awk|"
    r"base64|sort|nl|diff)\b[^\n|;&]*(^|[\\/\s\"'<])" + ENV_SOUBOR + r"([\s\"']|$)"
)


def _uvozovky(m):
    """Text v uvozovkách zahodí; cestu (jedno slovo nebo cesta k vlastní kontrole) ponechá bez uvozovek."""
    obsah = m.group(0)[1:-1].strip()
    if re.search(r"\||\.\*", obsah):  # regulární výraz (grep), ne cesta, glob ani $PROMENNA
        return "''"
    if not re.search(r"\s", obsah):
        return obsah
    if re.search(VLASTNI_KONTROLY + r"$", obsah, re.I):
        # Cesta s mezerou (C:\Program Files\…): spojit bez mezer, aby se z věty nestaly příkazy.
        return re.sub(r"\s+", "", obsah)
    return "''"


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


def bez_heredocu(prikaz):
    """Vynechá těla heredoců (po řádek začínající ukončovacím slovem). Zbytek prvního řádku
    (cat <<EOF > soubor) zůstává ke kontrole. Po řádcích a přes rejstřík, aby dlouhý text
    s „<<“ (C++, bitový posun) nebyl pomalý a nepřekročil časový limit hooku."""
    radky = prikaz.split("\n")
    zacatky = {}
    for i, radek in enumerate(radky):
        m = re.match(r"\s*(\w+)", radek)
        if m:
            zacatky.setdefault(m.group(1), []).append(i)
    vysledek, i = [], 0
    while i < len(radky):
        m = HEREDOC.search(radky[i])
        indexy = zacatky.get(m.group(2), []) if m else []
        k = bisect.bisect_right(indexy, i)
        if k < len(indexy):
            vysledek.append(radky[i][:m.start()] + "<<HEREDOC" + radky[i][m.end():])
            i = indexy[k] + 1
            continue
        vysledek.append(radky[i])
        i += 1
    return "\n".join(vysledek)


def bez_textu(prikaz):
    """Odstraní obsah heredoců a řetězců v uvozovkách, aby pojistka nereagovala na text (popis PR, echo)."""
    prikaz = bez_heredocu(prikaz)
    prikaz = re.sub(r"'[^']*'", _uvozovky, prikaz)
    return re.sub(r'"(\\.|[^"\\])*"', _uvozovky, prikaz)


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


def kroky_davky():
    try:
        with open(POTVRZENI, encoding="utf-8") as f:
            radky = f.read().splitlines()
    except OSError:
        return []
    return [r.split(":", 1)[1].strip() for r in radky if r.lower().startswith("krok:") and r.split(":", 1)[1].strip()]


def jednotne(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def potvrzeno_davkou(akce):
    """Dávka: platí 15 minut na všechny vyjmenované kroky, nespotřebuje se."""
    kroky = kroky_davky()
    if not kroky:
        return None
    try:
        if time.time() - os.path.getmtime(POTVRZENI) > PLATNOST_S:
            os.remove(POTVRZENI)
            return False
    except OSError:
        return False
    akce = jednotne(akce)
    return any(jednotne(k) in akce for k in kroky)


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

    popis = None
    if nastroj == "Grep":
        cil = os.path.basename(str(vstup.get("path", ""))) + " " + str(vstup.get("glob", ""))
        if re.search(r"(^|[\s*/\\])" + ENV_SOUBOR + r"(\s|$)", cil):
            vystup("deny", "Pojistka: soubory .env se neprohledávají (hodnoty by byly v kontextu). Načti je do procesu a použij.")
        sys.exit(0)

    elif nastroj in ("Read", "Edit", "Write"):
        # Windows zahodí mezery a tečky na konci názvu i proud ::$DATA, „pojistka.py “ je tentýž soubor.
        cela = re.sub(r"::\$DATA$", "", str(vstup.get("file_path", "")).rstrip(" .\t"), flags=re.I).rstrip(" .\t")
        cesta = os.path.basename(cela)
        if re.fullmatch(ENV_SOUBOR, cesta):
            vystup("deny", "Pojistka: soubory .env se neotevírají (hodnoty by byly v kontextu). Načti je do procesu (`set -a; . ./.env; set +a`, `--env-file`) a zapisuj skriptem scripts/env_nastav.py z agent-kitu (dělá zálohu).")
        if nastroj == "Read":
            sys.exit(0)
        cela = cela.replace("\\", "/")
        text = " ".join(str(vstup.get(k, "")) for k in ("old_string", "new_string", "content"))
        if re.search(VLASTNI_KONTROLY + "$", cela, re.I) or (
                NASTAVENI.search(cela) and re.search(r"\bhooks\b|disableAllHooks|PreToolUse|pojistka|agent-kit@", text)):
            popis = "úprava pojistky nebo hooků"
        else:
            sys.exit(0)

    elif nastroj in ("Bash", "PowerShell") or (vstup.get("command") and "__" not in nastroj):
        prikaz = str(vstup.get("command", ""))
        if ENV_CTENI.search(prikaz):
            vystup("deny", "Pojistka: vypisování souborů .env je zakázané. Hodnoty smíš jen načíst do procesu (`set -a; . ./.env; set +a`, `--env-file`) a použít, nikdy je nevypisuj.")
        # Text v uvozovkách se ignoruje, kromě případů, kdy se spouští jako příkaz (sh -c, eval, PowerShell -Command).
        spousti_text = re.search(r"\b(sh|bash|zsh|pwsh|powershell|cmd)(\.exe)?\b[^\n]*\s(-c|-Command|/c)\b|\beval\b", prikaz, re.I)
        kontrolovany = bez_prepinacu_gitu(prikaz if spousti_text else bez_textu(prikaz))
        for vzor, nazev in RIZIKOVE_PRIKAZY:
            if re.search(vzor, kontrolovany, re.IGNORECASE):
                popis = nazev
                break
        # Push do main/master chce potvrzení v každém repu, i v agent-kitu a šabloně (Brixyy/agent-kit#95):
        # výjimka podle textu cwd + příkazu pouštěla i push do jiného repa.
    elif RIZIKOVE_MCP.search(nastroj) and not VOLNE_MCP.search(nastroj):
        popis = "produkční akce přes " + nastroj.split("__")[-1]

    if popis is None:
        sys.exit(0)
    davka = potvrzeno_davkou(nastroj + " " + json.dumps(vstup, ensure_ascii=False))
    if davka:
        sys.exit(0)
    if davka is None and potvrzeno(data.get("tool_use_id", "")):
        sys.exit(0)
    vystup("deny", (
        f"Pojistka: {popis}. Tohle je nevratná nebo produkční akce. Nejdřív se zeptej uživatele v chatu "
        f"a řekni mu přesně, co se stane. Teprve po jeho výslovném souhlasu vytvoř soubor {POTVRZENI} "
        f"a akci zopakuj (potvrzení platí 15 minut a jednou). U schválené dávky více kroků zapiš do souboru "
        f"pro každý krok řádek „krok: <text, který je v příkazu>“ — pak platí 15 minut na všechny tyto kroky."
    ))


main()
