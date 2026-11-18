"""Testy kontroly Vercelu: python -I tests/test_vercel_kontrola.py"""
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
SKRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "vercel_kontrola.py")


def projekt(vercel_json=None, podslozka="", vercel_slozka=False):
    slozka = tempfile.mkdtemp()
    if vercel_json is not None:
        cil = os.path.join(slozka, podslozka)
        os.makedirs(cil, exist_ok=True)
        with open(os.path.join(cil, "vercel.json"), "w", encoding="utf-8") as f:
            f.write(vercel_json if isinstance(vercel_json, str) else json.dumps(vercel_json))
    if vercel_slozka:
        os.makedirs(os.path.join(slozka, ".vercel"))
    return slozka


def spust(slozka):
    v = subprocess.run([sys.executable, "-I", SKRIPT, slozka], capture_output=True, text=True, encoding="utf-8")
    return v.returncode, v.stdout


SPRAVNE = {"git": {"deploymentEnabled": {"main": True, "*": False, "**": False}}, "ignoreCommand": "git diff --quiet HEAD^ HEAD -- web/"}
PRIPADY = [
    ("správně nastavené", projekt(SPRAVNE), 0, "OK"),
    ("Git nasazení vypnutá", projekt({"git": {"deploymentEnabled": False}}), 0, "vypnutá"),
    ("bez ignoreCommand jen varování", projekt({"git": {"deploymentEnabled": {"main": True, "*": False, "**": False}}}), 0, "VAROVÁNÍ"),
    ("chybí deploymentEnabled", projekt({"cleanUrls": True}), 1, "CHYBA"),
    ("jen „*“ nestačí na claude/…", projekt({"git": {"deploymentEnabled": {"main": True, "*": False}}, "ignoreCommand": "x"}), 1, '"**"'),
    ("vercel.json v podsložce", projekt({"cleanUrls": True}, podslozka="prototype"), 1, "prototype/vercel.json"),
    (".vercel bez vercel.json", projekt(vercel_slozka=True), 1, "nemá vercel.json"),
    ("rozbitý vercel.json", projekt("{nejde"), 1, "nejde přečíst"),
    ("projekt bez Vercelu", projekt(), 0, "VŠE OK"),
    ("jiné pravidlo povolí náhledy", projekt({"git": {"deploymentEnabled": {"main": True, "**": False, "claude/**": True}}, "ignoreCommand": "x"}), 1, '"claude/**": true'),
    ("vypnutá i produkce", projekt({"git": {"deploymentEnabled": {"**": False}}}), 0, '"main": true'),
    ("BOM z PowerShellu", projekt("﻿" + json.dumps(SPRAVNE)), 0, "OK"),
    ("deploymentEnabled true", projekt({"git": {"deploymentEnabled": True}}), 1, "je true"),
]

chyby = 0
for nazev, slozka, kod, text in PRIPADY:
    skutecny, vystup = spust(slozka)
    ok = skutecny == kod and text in vystup
    chyby += not ok
    print(("OK    " if ok else "CHYBA ") + nazev + ("" if ok else f" (kód {skutecny}): {vystup!r}"))

print("VŠE OK" if not chyby else f"{chyby} CHYB")
sys.exit(1 if chyby else 0)
