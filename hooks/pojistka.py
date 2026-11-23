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
HODNOTA = r"""('[^']*'|"[^"]*"|\S+)"""
GIT_PREPINACE = re.compile(
    r"\bgit(\.exe)?((\s+(-C|-c|--git-dir|--work-tree|--namespace|--super-prefix|--config-env|--attr-source)"
    r"(\s+|=)" + HODNOTA + r"|\s+--?[\w-]+(=" + HODNOTA + r")?))*(?=\s)",
    re.I,
)


def bez_prepinacu_gitu(prikaz):
    """git <globální přepínače> <podpříkaz> → git <podpříkaz>, aby vzory push viděly podpříkaz hned za gitem.
    Pokračování řádku (\\ + nový řádek) se spojí. Upravený text se kontroluje navíc k původnímu, protože
    slovo „git“ jako argument jiného příkazu (find … -name git -delete) by jinak smazalo přepínače za ním."""
    return GIT_PREPINACE.sub("git", re.sub(r"\\\r?\n", " ", prikaz))


# Vzdálené servery (audit Brixyy/agent-kit#96). Pojistka chytá běžné chyby agenta, ne záměrné
# obcházení: rozbor shellu regulárními výrazy nikdy není úplný. Skutečnou ochranu dávají práva
# na serveru (agent má klíč, který smí jen číst). Pojistka nezná jména serverů (soubor je veřejný),
# proto hlídá každý server kromě GitHubu: ssh, scp, rsync a podobné na pozici příkazu chtějí
# potvrzení, pokud volání přesně neodpovídá bezpečnému tvaru (čtení logů a stavu, tunel, stažení
# ze serveru, místní kopie). Slovo ssh jako argument (grep ssh, ssh://) se nehlídá.
SSH_NAZVY = r"(?P<nazev>ssh|scp|rsync|sftp|ssh-copy-id|autossh|plink|mosh)(\.exe)?"
PSQL_NAZEV = r"psql(\.exe)?"


def _volani(nazev):
    """Volání programu na místě příkazu (i za sudo, env, PROMENNA=…, s cestou nebo v uvozovkách)."""
    return re.compile(
        r"(^|(?<=[;&|(\n`{\"']))[ \t]*"
        r"((nohup|time|command|exec|if|then|do|else|xargs|nice|!)[ \t]+|timeout[ \t]+\S+[ \t]+|env[ \t]+"
        r"|sudo([ \t]+-[a-zA-Z]*[ugCDhpr][ \t]+\S+|[ \t]+-[a-zA-Z-]+)*[ \t]+"
        # Obálky, které spustí příkaz s produkčním prostředím nebo v kontejneru.
        r"|(railway|doppler|infisical|op)[ \t]+run([ \t]+-\S+([ \t]+[^\s-]\S*)?)*([ \t]+--)?[ \t]+"
        r"|((npx|pnpm|yarn)[ \t]+)?(dotenv|dotenv-cli)\b[^\n;&|]*?[ \t]--[ \t]+"
        r"|(kubectl|oc)[ \t]+exec\b[^\n;&|]*?[ \t]--[ \t]+"
        r"|\w+=\S*[ \t]+|&[ \t]*|\$\w+[ \t]*=[ \t]*)*"
        r"(?P<q>[\"']?)(\S*[\\/])?" + nazev + r"(?P=q)(?=[ \t]|$)",
        re.I | re.M,
    )


SSH_VOLANI = _volani(SSH_NAZVY)
PSQL_VOLANI = _volani(PSQL_NAZEV)
SSH_ZA = r"(?=[ \t]*($|\n|&|\|\|?|;|[12]?>))"
SLOVO = r"[\w./\\~:@=,+%*-]+"
SSH_BEZPECNE = re.compile(
    r"ssh(\.exe)?(?P<prep>([ \t]+-[NTqvCtnf46]+|[ \t]+-[NTqvCtnf46]*[pilFJLRDE][ \t]*" + SLOVO +
    r"|[ \t]+-o[ \t]*(BatchMode|ConnectTimeout|StrictHostKeyChecking|ServerAliveInterval|ServerAliveCountMax"
    r"|LogLevel|ConnectionAttempts)=[\w-]+))*"
    r"[ \t]+(?P<host>[\w.@-]+)"
    r"([ \t]+(?P<cmd>'[^'\n]*'|\"[^\"\n]*\"|[^'\"\n;&|<>]+?))?" + SSH_ZA,
    re.I,
)
SSH_VERZE = re.compile(r"ssh(\.exe)?[ \t]+-V" + SSH_ZA, re.I)
STAZENI = re.compile(
    r"(scp|rsync)(\.exe)?([ \t]+-(?![a-zA-Z]*[eoFSJ])[a-zA-Z]+|[ \t]+-P[ \t]+\d+"
    r"|[ \t]+--(archive|verbose|compress|progress|partial|human-readable|dry-run|stats|checksum|times|recursive"
    r"|list-only|delete|ignore-existing|update|itemize-changes|size-only|(info|exclude|include)=" + SLOVO + r"))*"
    r"[ \t]+[\w.@-]+:" + SLOVO + r"[ \t]+(?![\w.@-]{2,}:)(" + SLOVO + r"|[A-Za-z]:[\\/]" + SLOVO + r")" + SSH_ZA,
    re.I,
)
ARG = r"([ \t]+(?!-)" + SLOVO + r"|[ \t]+-" + SLOVO + r"|[ \t]+(" + SLOVO + r")?('[^']*'|\"[^\"$`\\]*\"))*"
CTENI_VZDALENE = re.compile(
    r"[ \t]*(sudo([ \t]+-n)?[ \t]+)?("
    r"(tail|head|cat|ls|ll|df|du|free|uptime|wc|stat|whoami|uname|pwd|nproc|id|lsblk|findmnt|ps|pgrep|grep|egrep"
    r"|realpath|which|echo|cd|true|test)" + ARG +
    r"|hostname|rg(?![^|;&]*--pre)" + ARG +
    r"|journalctl(?![^|;&]*--(vacuum|rotate|flush|sync|relinquish|setup-keys))" + ARG +
    r"|systemctl([ \t]+--no-pager)?[ \t]+(status|is-active|is-enabled|is-failed|list-units|list-timers|show|cat)\b" + ARG +
    r"|docker[ \t]+(ps|logs|inspect|stats|images|version|info|top)\b" + ARG +
    r"|docker[ \t]+compose[ \t]+(ps|logs|ls|top|images|version)\b" + ARG +
    r"|git([ \t]+-C[ \t]+" + SLOVO + r")?([ \t]+--no-pager)?[ \t]+(status|log|show|rev-parse|describe)\b"
    r"(?![^|;&]*--output)" + ARG +
    r"|(ss|netstat)(?![^|;&]*(-\w*K|--kill))" + ARG +
    r")[ \t]*",
    re.I,
)


# Obsah, který shell spustí jako příkaz (sh -c '…', eval, iex).
SPOUSTI_OBSAH = (r"(?:\b(?:sh|bash|zsh|pwsh|powershell|cmd)(?:\.exe)?\s+(?:-c|-Command|/c)|\beval|\biex|\bInvoke-Expression)"
                 r"\s+('([^']*)'|\"([^\"]*)\")")


def _maskuj(text):
    """Text v uvozovkách s mezerou nahradí mezerami stejné délky (pozice zůstanou). Apostrofy jen
    v rámci řádku, aby „don't“ v komentáři neschovalo další řádky. Cesta k ssh (C:\\Program Files\\…\\ssh.exe)
    zůstane vidět."""
    def nahrad(m):
        obsah = m.group(0)
        if re.search(r"[\\/](" + SSH_NAZVY + r"|" + PSQL_NAZEV + r")[\"']$", obsah, re.I):
            return re.sub(r"\s", "_", obsah)
        return obsah[0] + re.sub(r"[^\n]", " ", obsah[1:-1]) + obsah[-1] if re.search(r"\s", obsah) else obsah
    text = re.sub(r"@'[\s\S]*?\n'@|@\"[\s\S]*?\n\"@", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    return re.sub(r"(?<![^\s=(])'[^']*'|'[^'\n]*'|\"(\\.|[^\"\\])*\"", nahrad, text)


def _vzdaleny_jen_cte(cmd):
    if cmd[:1] in "'\"":
        cmd = cmd[1:-1]
    cmd = re.sub(r"[ \t]*(2>&1|[12]?>[ \t]*/dev/null(?=[ \t]|$))", " ", cmd)
    # Nahrazení a komentáře ($(), ``, ${}, #, \, přesměrování) se nepouští, ať je rozbor jistý.
    if re.search(r"[`$#\\<>(){}!\n]", cmd):
        return False
    # Rozdělit podle ; && || | mimo uvozovky.
    casti, cast = [], ""
    for t in re.findall(r"'[^']*'|\"[^\"]*\"|&&|\|\||[;|]|[^'\"&|;]+|.", cmd):
        if t in ("&&", "||", ";", "|"):
            casti.append(cast)
            cast = ""
        else:
            cast += t
    casti.append(cast)
    return all(CTENI_VZDALENE.fullmatch(c) for c in casti)


def ssh_riziko(prikaz, maskovat=True):
    """Vrátí popis rizika pro ssh/scp/rsync/… na server, nebo None."""
    prikaz = prikaz.replace("\r", "")
    hledany = _maskuj(prikaz) if maskovat else prikaz
    for m in SSH_VOLANI.finditer(hledany):
        nastroj, zacatek = m.group("nazev").lower(), m.start("nazev")
        if nastroj in ("scp", "rsync"):
            # Kopie mezi místními složkami (bez host:) a stažení ze serveru projdou.
            volani = re.match(r"[^\n;&|]*", prikaz[zacatek:]).group(0)
            if not re.search(r"(?<![\w.@-])[\w.@-]{2,}:", volani) or STAZENI.match(prikaz, zacatek):
                continue
            return "nahrání souborů na server nebo změna na serveru (" + nastroj + ")"
        if nastroj != "ssh":
            return "příkaz na vzdáleném serveru (" + nastroj + ")"
        if SSH_VERZE.match(prikaz, zacatek):
            continue
        b = SSH_BEZPECNE.match(prikaz, zacatek)
        if not b:
            return "příkaz na vzdáleném serveru (ssh)"
        if re.search(r"(^|@)github\.com$", b.group("host"), re.I):
            continue
        cmd = (b.group("cmd") or "").strip()
        if not cmd:
            if re.search(r"\s-\w*N", prikaz[zacatek:b.start("host")]):
                continue  # tunel bez příkazu
            return "interaktivní přihlášení na server (ssh)"
        if not _vzdaleny_jen_cte(cmd):
            return "příkaz, který mění vzdálený server (ssh)"
    return None


# psql: bez potvrzení projde čtení (-c se SELECT, SHOW, EXPLAIN, \d…), výpis databází a místní databáze.
# Soubor (-f), standardní vstup a neznámý obsah ($PROMENNA) se berou jako zápis (audit Brixyy/agent-kit#96).
PSQL_SLOVO = re.compile(r"\\\n|`\n|'[^']*'|\"(?:\\.|[^\"\\])*\"|(?:[^\s'\";&|<>\\`]|[\\`](?!\n))+|[<>]|[ \t]+|.", re.S)
PSQL_HODNOTA = set("cdfhLoUpPTvFR")
PSQL_DLOUHE = {"--command", "--file", "--host", "--dbname", "--port", "--username", "--variable", "--set",
               "--output", "--log-file", "--field-separator", "--record-separator", "--pset", "--table-attr"}
MISTNI_HOST = r"(localhost|127\.0\.0\.1|::1|\[::1\])"
SQL_CTENI = re.compile(r"\s*((select|show|explain|table|values|with)\b|\\(d[a-z]*\+?|l\+?|conninfo|x|timing)(\s+[\w.*\"']+)*\s*$)", re.I)
# Příkaz musí začínat čtením; hledají se jen zápisy, které se do čtení dají schovat (CTE, INTO, EXPLAIN, funkce).
SQL_ZAPIS = re.compile(
    r"\b(insert|update|delete|merge|create|execute|into|nextval|setval"
    r"|pg_terminate_backend|pg_cancel_backend|pg_reload_conf|set_config|lo_\w+|dblink\w*)\b",
    re.I,
)
# Místní databáze jen na výchozím portu (5432, místní Supabase 54322): jiný port bývá ssh tunel na server.
MISTNI_PORTY = {"", "5432", "54322"}


def _sql_jen_cte(sql):
    sql = re.sub(r"'(?:[^']|'')*'|\"[^\"]*\"", "''", sql)
    prikazy = [p for p in sql.split(";") if p.strip()]
    return bool(prikazy) and all(
        SQL_CTENI.match(p) and not SQL_ZAPIS.search(p) and "\\" not in p.strip()[1:] for p in prikazy)


def _psql_slova(text):
    """Slova volání psql až po konec příkazu (; & | nový řádek). Vrátí (slova, čte ze vstupu)."""
    slova, slovo, vstup = [], None, False
    for t in PSQL_SLOVO.findall(text):
        if t in (";", "&", "|", "\n"):
            break
        if t == "<":
            vstup = True
        if t in ("\\\n", "`\n") or t.isspace() or t in "<>":
            if slovo is not None:
                slova.append(slovo)
            slovo = None
            continue
        slovo = (slovo or ("", False))
        promenna = t[:1] == '"' and re.search(r"[$`]", t) or t[:1] not in "'\"" and "$" in t
        slovo = (slovo[0] + (t[1:-1] if t[:1] in "'\"" else t), slovo[1] or bool(promenna))
    if slovo is not None:
        slova.append(slovo)
    return slova, vstup


def _hosty(text, promenna):
    """Servery z adresy postgres://…@server nebo z „host=…“; neznámá hodnota ($PROMENNA) je cizí server."""
    if promenna:
        return ["$"]
    if "://" not in text and "=" not in text:
        return []  # jméno databáze, ne adresa
    hosty = [a or b for a, b in re.findall(r"@\[?([^:/?\]@]+)|host(?:addr)?=([^\s&]+)", text)]
    porty = re.findall(r"@[^/?\s]*:(\d+)|port=(\d+)", text)
    return hosty + ["port:" + (a or b) for a, b in porty]


def psql_riziko(prikaz, maskovat=True):
    """Vrátí popis rizika pro zápis do databáze přes psql, nebo None."""
    prikaz = prikaz.replace("\r", "")
    hledany = _maskuj(prikaz) if maskovat else prikaz
    for m in PSQL_VOLANI.finditer(hledany):
        slova, vstup = _psql_slova(prikaz[m.end():])
        sql, soubor, info, hosty, i = [], vstup, False, [], 0
        while i < len(slova):
            s, promenna = slova[i]
            dalsi = slova[i + 1] if i + 1 < len(slova) else ("", False)
            if s.startswith("--"):
                nazev, je_rovno, hodnota = s.partition("=")
                if not je_rovno and nazev in PSQL_DLOUHE:
                    hodnota, promenna, i = dalsi[0], dalsi[1], i + 1
                if nazev == "--command":
                    sql.append((hodnota, promenna))
                elif nazev == "--file":
                    soubor = True
                elif nazev == "--host":
                    hosty.append("$" if promenna else hodnota)
                elif nazev == "--port":
                    hosty.append("port:" + ("$" if promenna else hodnota))
                elif nazev == "--dbname":
                    hosty += _hosty(hodnota, promenna)
                elif nazev in ("--list", "--version", "--help"):
                    info = True
            elif s.startswith("-") and len(s) > 1:
                for k, znak in enumerate(s[1:], 1):
                    if znak in "lV?":
                        info = True
                    if znak in PSQL_HODNOTA:
                        hodnota, prom = (s[k + 1:], promenna) if s[k + 1:] else (dalsi[0], dalsi[1])
                        if not s[k + 1:]:
                            i += 1
                        if znak == "c":
                            sql.append((hodnota, prom))
                        elif znak == "f":
                            soubor = True
                        elif znak == "h":
                            hosty.append("$" if prom else hodnota)
                        elif znak == "p":
                            hosty.append("port:" + ("$" if prom else hodnota))
                        elif znak == "d":
                            hosty += _hosty(hodnota, prom)
                        break
            else:
                # Pozice: databáze, adresa postgres://… nebo „host=… dbname=…“.
                hosty += _hosty(s, promenna)
            i += 1
        servery = [h for h in hosty if not h.startswith("port:")]
        if servery and all(re.fullmatch(MISTNI_HOST, h, re.I) or h.startswith("/") and "cloudsql" not in h.lower()
                           for h in servery) and all(h[5:] in MISTNI_PORTY for h in hosty if h.startswith("port:")):
            continue  # místní databáze (vývoj) na výchozím portu
        if info and not sql and not soubor:
            continue
        if not soubor and sql and all(not prom and _sql_jen_cte(text) for text, prom in sql):
            continue
        return "zápis do databáze přes psql (neznámý obsah, soubor nebo vstup se bere jako zápis)"
    return None


# Začátek příkazu: začátek řádku nebo za ; & | ( (volitelně sudo).
ZACATEK_PRIKAZU = r"(^|(?<=[;&|(\n]))\s*(sudo\s+)?"
# Příkazy, které find spustí nad nalezenými soubory a které soubor mění.
FIND_MENI = r"(rm|mv|cp|tee|truncate|sed\s+-i|ln|shred|dd|Remove-Item)\b"

RIZIKOVE_PRIKAZY = [
    (r"\bgit\s+push\b[^\n;&|]*\b(main|master)\b", "push do main/master"),
    (r"\bgit\s+push\b[^\n;&|]*(\s--force\b|\s-f\b|\s--delete\b|\s:\S|\s\+\S)", "force push nebo mazání větve na GitHubu"),
    (r"\bgh\s+repo\s+(delete|archive|rename)\b", "mazání/archivace repozitáře"),
    # Sloučení přes administrátora obchází povinné kontroly (audit Brixyy/agent-kit#96).
    (r"\bgh\s+pr\s+merge\b[^\n;&|]*\s--admin\b", "sloučení PR mimo povinné kontroly (gh pr merge --admin)"),
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
        spousti_text = re.search(r"\b(sh|bash|zsh|pwsh|powershell|cmd)(\.exe)?\b[^\n]*\s(-c|-Command|/c)\b|\b(eval|iex|Invoke-Expression)\b", prikaz, re.I)
        kontrolovany = prikaz if spousti_text else bez_textu(prikaz)
        upraveny = bez_prepinacu_gitu(kontrolovany)
        for vzor, nazev in RIZIKOVE_PRIKAZY:
            if re.search(vzor, kontrolovany, re.IGNORECASE) or re.search(vzor, upraveny, re.IGNORECASE):
                popis = nazev
                break
        if popis is None:
            # Vzdálený příkaz bývá v uvozovkách: hledá se v textu s maskovanými uvozovkami, posuzuje v původním.
            popis = ssh_riziko(bez_heredocu(prikaz)) or psql_riziko(bez_heredocu(prikaz))
            for obsah in re.findall(SPOUSTI_OBSAH, prikaz, re.I):
                popis = popis or ssh_riziko(obsah[1] or obsah[2]) or psql_riziko(obsah[1] or obsah[2])
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
