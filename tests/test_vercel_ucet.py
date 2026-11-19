"""Testy kontroly účtu Vercelu a přepínače --dnes bez sítě: python -I tests/test_vercel_ucet.py"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8")
SKRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "vercel_kontrola.py")
spec = importlib.util.spec_from_file_location("vercel_kontrola", SKRIPT)
vk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vk)

TED = 1_800_000_000  # pevný čas testu (s)
SPRAVNE = {"git": {"deploymentEnabled": {"main": True, "*": False, "**": False}}, "ignoreCommand": "git diff --quiet HEAD^ HEAD -- ."}
BEZ_IGNORE = {"git": {"deploymentEnabled": {"main": True, "*": False, "**": False}}}


def projekt(nazev, repo=None, root=None, ignore=None, vetev="main"):
    p = {"name": nazev, "rootDirectory": root}
    if repo:
        p["link"] = {"type": "github", "org": "Brixyy", "repo": repo, "productionBranch": vetev}
    if ignore:
        p["commandForIgnoringBuildStep"] = ignore
    return p


class Falesny:
    """Nahradí spust(): odpovědi vercel api a gh api podle cesty, bez sítě."""

    def __init__(self, vercel=None, soubory=None, vercel_chyba=None, gh_chyba=None):
        self.vercel = vercel or {}
        self.soubory = soubory or {}
        self.vercel_chyba = vercel_chyba
        self.gh_chyba = gh_chyba
        self.volani = []

    def __call__(self, prikaz):
        self.volani.append(prikaz)
        if prikaz[0] == "gh":
            if self.gh_chyba:
                return 1, "", self.gh_chyba
            cesta = prikaz[-1].split("/contents/")[1].split("?")[0]
            repo = prikaz[-1].split("/")[2]
            obsah = self.soubory.get(f"{repo}:{cesta}")
            if obsah is None:
                return 1, "", "gh: Not Found (HTTP 404)"
            return 0, obsah if isinstance(obsah, str) else json.dumps(obsah), ""
        if self.vercel_chyba:
            return 1, "", self.vercel_chyba
        cesta = prikaz[prikaz.index("api") + 1]
        for zacatek, odpoved in self.vercel.items():
            if cesta.startswith(zacatek):
                return 0, json.dumps(odpoved(cesta) if callable(odpoved) else odpoved), ""
        return 1, "", "Error: neznámá cesta"


def spust_s(falesny, funkce, *argumenty):
    vystup = io.StringIO()
    with mock.patch.object(vk, "spust", falesny), mock.patch.object(vk, "vercel_prikaz", return_value=["vercel"]), \
            contextlib.redirect_stdout(vystup):
        vysledek = funkce(*argumenty)
    return vysledek, vystup.getvalue()


def urovne(vysledek):
    return [uroven for _, radky in vysledek for uroven, _ in radky]


class Ucet(unittest.TestCase):
    def ucet(self, projekty, soubory=None, **kw):
        f = Falesny(vercel={"/v9/projects": {"projects": projekty, "pagination": {"next": None}}}, soubory=soubory, **kw)
        return spust_s(f, vk.zkontroluj_ucet)[0]

    def test_spravny_projekt_v_root_directory(self):
        v = self.ucet([projekt("elyon", "elyon", root="web")], {"elyon:web/vercel.json": SPRAVNE})
        self.assertEqual(urovne(v), ["OK"])
        self.assertIn("Brixyy/elyon:web/vercel.json", v[0][1][0][1])

    def test_chybejici_vercel_json_je_chyba(self):
        v = self.ucet([projekt("hub", "hub")], {})
        self.assertEqual(urovne(v), ["CHYBA"])

    def test_vercel_json_jen_v_koreni_kdyz_root_je_podslozka(self):
        v = self.ucet([projekt("elyon", "elyon", root="web")], {"elyon:vercel.json": SPRAVNE})
        self.assertEqual(urovne(v), ["CHYBA"])

    def test_nahledy_zapnute(self):
        v = self.ucet([projekt("hub", "hub")], {"hub:vercel.json": {"cleanUrls": True}})
        self.assertEqual(urovne(v), ["CHYBA"])

    def test_ignore_v_nastaveni_projektu_staci(self):
        v = self.ucet([projekt("elyon", "elyon", ignore="git diff --quiet HEAD^ HEAD -- .")], {"elyon:vercel.json": BEZ_IGNORE})
        self.assertEqual(urovne(v), ["OK"])

    def test_bez_ignore_varovani(self):
        v = self.ucet([projekt("hub", "hub")], {"hub:vercel.json": BEZ_IGNORE})
        self.assertEqual(urovne(v), ["VAROVÁNÍ"])

    def test_jina_produkcni_vetev(self):
        v = self.ucet([projekt("x", "x", vetev="develop")], {"x:vercel.json": SPRAVNE})
        self.assertEqual(urovne(v), ["VAROVÁNÍ", "OK"])

    def test_bez_repozitare_ok(self):
        self.assertEqual(urovne(self.ucet([projekt("rucni")])), ["OK"])

    def test_bom_ve_vercel_json(self):
        v = self.ucet([projekt("x", "x")], {"x:vercel.json": "\ufeff" + json.dumps(SPRAVNE)})
        self.assertEqual(urovne(v), ["OK"])

    def test_gh_bez_pristupu_je_neovereno(self):
        v = self.ucet([projekt("x", "x")], gh_chyba="gh: Bad credentials (HTTP 401)")
        self.assertEqual(urovne(v), ["NEOVĚŘENO"])

    def test_vercel_neprihlaseny_je_neovereno(self):
        v = self.ucet([], vercel_chyba="Error: No existing credentials found.")
        self.assertEqual(urovne(v), ["NEOVĚŘENO"])
        self.assertIn("vercel login", v[0][1][0][1])

    def test_main_bez_argumentu_projde_ucet_a_neovereno_neni_ok(self):
        f = Falesny(vercel_chyba="Error: No existing credentials found.")
        with mock.patch.object(vk, "dev_slozka", return_value=tempfile.mkdtemp()):
            kod, vystup = spust_s(f, vk.main, [])
        self.assertEqual(kod, 1)
        self.assertIn("NEOVĚŘENO", vystup)
        self.assertNotIn("VŠE OK", vystup)


def nasazeni(pocet, nazev="elyon", stav="READY", target="production", stari=3600):
    return [{"name": nazev, "state": stav, "target": target, "created": int((TED - stari) * 1000) - i} for i in range(pocet)]


class Dnes(unittest.TestCase):
    def dnes(self, seznam, chyba=None):
        def odpoved(cesta):
            do = int(cesta.split("until=")[1]) if "until=" in cesta else None
            zbyle = sorted((n for n in seznam if do is None or n["created"] < do), key=lambda n: -n["created"])
            stranka = zbyle[:100]
            dalsi = stranka[-1]["created"] if len(zbyle) > 100 else None
            return {"deployments": stranka, "pagination": {"next": dalsi}}
        return spust_s(Falesny(vercel={"/v6/deployments": odpoved}, vercel_chyba=chyba), vk.dnes, TED)

    def test_pod_60_ok(self):
        kod, vystup = self.dnes(nasazeni(30) + nasazeni(5, stav="CANCELED"))
        self.assertEqual(kod, 0)
        self.assertIn("produkce CANCELED 5", vystup)
        self.assertIn("celkem                35", vystup)
        self.assertTrue(vystup.strip().endswith("OK"))

    def test_60_varovani(self):
        kod, vystup = self.dnes(nasazeni(40) + nasazeni(20, "hub", target=None))
        self.assertEqual(kod, 0)
        self.assertIn("VAROVÁNÍ: 60 z 100", vystup)
        self.assertIn("náhled READY 20", vystup)

    def test_85_chyba(self):
        kod, vystup = self.dnes(nasazeni(70) + nasazeni(15, stav="ERROR"))
        self.assertEqual(kod, 1)
        self.assertIn("CHYBA: 85 z 100", vystup)

    def test_strankovani_nad_100(self):
        kod, vystup = self.dnes(nasazeni(130))
        self.assertIn("celkem               130", vystup)

    def test_starsi_nez_24_h_se_nepocita(self):
        kod, vystup = self.dnes(nasazeni(10) + nasazeni(70, stari=vk.DEN + 60))
        self.assertEqual(kod, 0)
        self.assertIn("celkem                10", vystup)

    def test_bez_prihlaseni_neovereno(self):
        kod, vystup = self.dnes([], chyba="Error: No existing credentials found.")
        self.assertEqual(kod, 1)
        self.assertIn("NEOVĚŘENO", vystup)


class Escapovani(unittest.TestCase):
    def test_npx_cmd_escapuje_ampersand(self):
        f = Falesny(vercel={"/v6": {"deployments": []}})
        with mock.patch.object(vk, "spust", f), mock.patch.object(vk, "vercel_prikaz", return_value=["C:/x/npx.CMD", "--yes", "vercel"]):
            vk.vercel_api("/v6/deployments?since=1&limit=100")
        self.assertIn("/v6/deployments?since=1^^^&limit=100", f.volani[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
