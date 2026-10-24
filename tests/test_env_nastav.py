"""Testy skriptu env_nastav.py: python -I tests/test_env_nastav.py"""
import os
import subprocess
import sys
import tempfile

SKRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "env_nastav.py")
NAZEV = "." + "env"


def spust(domov, cesta, nazev, hodnota):
    prostredi = dict(os.environ, USERPROFILE=domov, HOME=domov)
    return subprocess.run([sys.executable, "-I", SKRIPT, cesta, nazev], input=hodnota.encode("utf-8"),
                          capture_output=True, env=prostredi)


def main():
    chyby = 0

    def over(podminka, popis):
        nonlocal chyby
        print(("OK    " if podminka else "CHYBA ") + popis)
        chyby += not podminka

    with tempfile.TemporaryDirectory() as d:
        domov = os.path.join(d, "domov")
        os.makedirs(domov)
        cesta = os.path.join(d, NAZEV)
        with open(cesta, "wb") as f:
            f.write(b"\xef\xbb\xbfKEY=stare\r\nexport DALSI=1\r\n")

        r = spust(domov, cesta, "KEY", "má mezeru #a $(id)")
        obsah = open(cesta, "rb").read()
        over(r.returncode == 0, "nahrazení proběhlo")
        over(obsah.startswith(b"\xef\xbb\xbfKEY='"), "BOM zachován, první řádek nahrazen (žádná duplicita)")
        over("KEY='má mezeru #a $(id)'".encode("utf-8") in obsah, "hodnota v jednoduchých uvozovkách, diakritika v pořádku")
        over(obsah.count(b"KEY=") == 1, "proměnná jen jednou")
        over(b"\r\n" in obsah and b"\n" not in obsah.replace(b"\r\n", b""), "konce řádků CRLF zachovány")
        over("má mezeru".encode("utf-8") not in r.stdout, "hodnota se nevypisuje")

        spust(domov, cesta, "DALSI", "2")
        over(b"export DALSI='2'" in open(cesta, "rb").read(), "prefix export zachován")

        zalohy = os.listdir(os.path.join(domov, ".agents", "env-zalohy"))
        over(len(zalohy) == 2, "dvě zálohy mimo repozitář")
        over(not [f for f in os.listdir(d) if "zaloha" in f or f.endswith(".tmp")], "ve složce s .env nezůstala záloha ani dočasný soubor")

        r = spust(domov, cesta, "KEY", "s'apostrofem")
        over(r.returncode != 0, "hodnota s apostrofem odmítnuta")

        novy = os.path.join(d, "jiny", NAZEV)
        os.makedirs(os.path.dirname(novy))
        r = spust(domov, novy, "A", "1")
        over(r.returncode == 0 and open(novy, encoding="utf-8").read() == "A='1'\n", "nový soubor vytvořen")

    print("VŠE OK" if not chyby else f"CHYB: {chyby}")
    sys.exit(1 if chyby else 0)


if __name__ == "__main__":
    main()
