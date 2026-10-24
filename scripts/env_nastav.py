"""Nastaví jednu proměnnou v souboru .env, s hodnotou ze stdin, a nejdřív udělá zálohu.

Použití: python -I env_nastav.py <cesta k .env> <NAZEV> < soubor_s_hodnotou
         (nebo: <příkaz, který vypíše hodnotu> | python -I env_nastav.py .env NAZEV)

- Hodnota se nikam nevypisuje (jen název a délka) a zapíše se v jednoduchých uvozovkách,
  aby ji `set -a; . ./.env` nespustil jako příkaz a dotenv neusekl za `#`.
- Záloha jde mimo repozitář: ~/.agents/env-zalohy/<složka>__<soubor>.<čas>.
- Existující řádek NAZEV=… (i s `export`) se nahradí, jinak se proměnná přidá na konec.
  Zachová se BOM, konce řádků (CRLF/LF) i prefix `export`. Zápis je atomický.
"""
import os
import re
import shutil
import sys
import tempfile
import time

ZALOHY = os.path.join(os.path.expanduser("~"), ".agents", "env-zalohy")


def zalohuj(cesta):
    os.makedirs(ZALOHY, exist_ok=True)
    plna = os.path.abspath(cesta)
    zaklad = re.sub(r"[^\w.-]+", "_", os.path.basename(os.path.dirname(plna)) + "__" + os.path.basename(plna))
    cil = os.path.join(ZALOHY, f"{zaklad}.{time.strftime('%Y%m%d-%H%M%S')}")
    poradi = 1
    while os.path.exists(cil):
        poradi += 1
        cil = os.path.join(ZALOHY, f"{zaklad}.{time.strftime('%Y%m%d-%H%M%S')}-{poradi}")
    shutil.copy2(plna, cil)
    return cil


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sys.argv[2]):
        sys.exit("Použití: python -I env_nastav.py <cesta k .env> <NAZEV>  (hodnota na stdin)")
    cesta, nazev = sys.argv[1], sys.argv[2]
    hodnota = sys.stdin.buffer.read().decode("utf-8-sig").strip()
    if not hodnota or "\n" in hodnota or "\r" in hodnota:
        sys.exit("Hodnota na stdin chybí nebo má víc řádků.")
    if "'" in hodnota:
        sys.exit("Hodnota obsahuje apostrof ('), ten skript neumí bezpečně zapsat. Zapiš ji ručně se zálohou.")

    bom, konec, radky = "", "\n", []
    if os.path.exists(cesta):
        with open(cesta, "rb") as f:
            surove = f.read()
        if surove.startswith(b"\xef\xbb\xbf"):
            bom, surove = "﻿", surove[3:]
        text = surove.decode("utf-8")
        if "\r\n" in text:
            konec = "\r\n"
        radky = text.splitlines()
        print(f"Záloha: {zalohuj(cesta)}")
    else:
        print(f"Soubor {cesta} neexistoval, vytvářím nový.")

    vzor = re.compile(rf"^(\s*export\s+)?{re.escape(nazev)}\s*=")
    nahrazeno = False
    for i, radek in enumerate(radky):
        shoda = vzor.match(radek)
        if shoda:
            radky[i] = f"{(shoda.group(1) or '').lstrip()}{nazev}='{hodnota}'"
            nahrazeno = True
    if not nahrazeno:
        radky.append(f"{nazev}='{hodnota}'")

    slozka = os.path.dirname(os.path.abspath(cesta))
    fd, docasny = tempfile.mkstemp(dir=slozka, prefix=".env_nastav.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(bom + konec.join(radky) + konec)
    os.replace(docasny, cesta)
    print(f"{'Nahrazeno' if nahrazeno else 'Přidáno'}: {nazev} ({len(hodnota)} znaků).")


if __name__ == "__main__":
    main()
