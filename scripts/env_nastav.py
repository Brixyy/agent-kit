"""Nastaví jednu proměnnou v souboru .env, s hodnotou ze stdin, a nejdřív udělá zálohu.

Použití: python -I env_nastav.py <cesta k .env> <NAZEV> < soubor_s_hodnotou
         (nebo: <příkaz, který vypíše hodnotu> | python -I env_nastav.py .env NAZEV)

Hodnota se nikam nevypisuje. Záloha: <cesta>.zaloha-RRRRMMDD-HHMMSS vedle souboru.
Existující řádek NAZEV=… se nahradí, jinak se proměnná přidá na konec.
"""
import os
import re
import shutil
import sys
import time


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3 or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sys.argv[2]):
        sys.exit("Použití: python -I env_nastav.py <cesta k .env> <NAZEV>  (hodnota na stdin)")
    cesta, nazev = sys.argv[1], sys.argv[2]
    hodnota = sys.stdin.read().strip()
    if not hodnota or "\n" in hodnota:
        sys.exit("Hodnota na stdin chybí nebo má víc řádků.")

    radky = []
    if os.path.exists(cesta):
        zaloha = f"{cesta}.zaloha-{time.strftime('%Y%m%d-%H%M%S')}"
        poradi = 1
        while os.path.exists(zaloha):
            poradi += 1
            zaloha = f"{cesta}.zaloha-{time.strftime('%Y%m%d-%H%M%S')}-{poradi}"
        shutil.copy2(cesta, zaloha)
        print(f"Záloha: {zaloha}")
        with open(cesta, encoding="utf-8", newline="") as f:
            radky = f.read().splitlines()

    novy = f"{nazev}={hodnota}"
    vzor = re.compile(rf"^\s*(export\s+)?{re.escape(nazev)}\s*=")
    nahrazeno = False
    for i, radek in enumerate(radky):
        if vzor.match(radek):
            radky[i] = novy
            nahrazeno = True
    if not nahrazeno:
        radky.append(novy)

    with open(cesta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(radky) + "\n")
    print(f"{'Nahrazeno' if nahrazeno else 'Přidáno'}: {nazev} ({len(hodnota)} znaků).")


if __name__ == "__main__":
    main()
