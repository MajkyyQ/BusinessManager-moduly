"""Testy modulu QR platba. Spuštění: python manage.py test moduly.qr_platba"""
from decimal import Decimal

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.models import NastaveniFirmy, Zakaznik
from core.tests import uzivatel
from moduly.qr_platba import spayd as S


class SpaydTest(SimpleTestCase):
    """Převod čísla účtu na IBAN, částka a řetězec QR Platby podle specifikace SPAYD 1.0."""
    def test_iban_z_ceskeho_cisla_uctu(self):
        self.assertEqual(S.iban("19-2000145399/0800"), "CZ6508000000192000145399")  # vzorový účet z dokumentace České spořitelny
        self.assertEqual(S.iban(" cz65 0800 0000 1920 0014 5399 "), "CZ6508000000192000145399")
        self.assertTrue(S.iban_platny(S.iban("2000145399/0800")))

    def test_chybne_cislo_uctu(self):
        for u in ("", "123", "19-2000145398/0800", "CZ6608000000192000145399", "2000145399/80"):
            with self.subTest(ucet=u), self.assertRaises(S.ChybaUdaju): S.iban(u)

    def test_castka(self):
        self.assertEqual(S.castka("1 234,5"), Decimal("1234.50")); self.assertEqual(S.castka(Decimal("605")), Decimal("605.00"))
        for c in ("", "abc", "0", "-5", "10000000", "NaN"):
            with self.subTest(castka=c), self.assertRaises(S.ChybaUdaju): S.castka(c)

    def test_retezec_qr_platby(self):
        t = S.spayd("CZ6508000000192000145399", Decimal("605"), "CZK", "260001", "Zakázka *DMN260001*", "Servis Novák s.r.o.")
        self.assertEqual(t, "SPD*1.0*ACC:CZ6508000000192000145399*AM:605.00*CC:CZK*X-VS:260001*RN:Servis Novak s.r.o.*MSG:Zakazka DMN260001")
        self.assertEqual(S.variabilni_symbol("DMN260001", 7), "260001"); self.assertEqual(S.variabilni_symbol("ABC", 7), "7")
        self.assertEqual(S.variabilni_symbol("2026-00012345678", 7), "12345678")


class ModulQrPlatbaTest(TestCase):
    """QR kód v okně platby na místě, stránka QR platby pro zákazníka a nastavení modulu."""
    def setUp(self):
        from core.models import ProvedenyUkon, StavZakazky, TypUkonu, Zakazka
        NastaveniFirmy.objects.all().delete()
        self.f = NastaveniFirmy.objects.create(nazev_firmy="Servis s.r.o.", cislo_uctu="19-2000145399/0800", vychozi_dph=Decimal("21"))
        self.client.force_login(uzivatel("tech", "Technik"))
        self.z = Zakazka.objects.create(zakaznik=Zakaznik.objects.create(jmeno="Jan"), stav=StavZakazky.objects.create(nazev="Připraveno k vyzvednutí"))
        ProvedenyUkon.objects.create(zakazka=self.z, typ_ukonu=TypUkonu.objects.create(nazev="Diagnostika"), cena=Decimal("500"), sazba_dph=Decimal("21"))
        self.qr = reverse("modul_qr_platba:obrazek", args=[self.z.pk])

    def test_udaje_platby_zakazky(self):
        from moduly.qr_platba.views import udaje
        d = udaje(self.z)
        self.assertEqual((d["iban"], d["castka"], d["mena"]), ("CZ6508000000192000145399", Decimal("605.00"), "CZK"))  # 500 Kč + 21 % DPH
        self.assertIn("*AM:605.00*", d["text"]); self.assertIn(f"*X-VS:{S.variabilni_symbol(self.z.cislo_zakazky, self.z.pk)}*", d["text"])
        self.assertIn("*AM:300.50*", udaje(self.z, "300,50")["text"])

    def test_obrazek_qr_a_chyba(self):
        r = self.client.get(self.qr, {"castka": "300,50"})
        self.assertEqual(r["Content-Type"], "image/svg+xml"); self.assertIn(b"<svg", r.content); self.assertIn(b"<path", r.content)
        self.assertIn("Částka není číslo".encode(), self.client.get(self.qr, {"castka": "abc"}).content)
        self.f.cislo_uctu = ""; self.f.save()
        self.assertIn("Číslo účtu firmy není".encode(), self.client.get(self.qr).content)  # text se v obrázku zalomí do řádků

    def test_qr_v_okne_vydat_zakaznikovi(self):
        from core import moduly
        if "platba_na_miste" not in moduly.Modul.__dataclass_fields__: self.skipTest("starší aplikace bez místa pro rozšíření platba_na_miste")
        r = self.client.get(reverse("plocha", args=[self.z.pk]))
        self.assertContains(r, 'id="bm-pl-obr"'); self.assertContains(r, self.qr)
        self.assertContains(r, "▦ QR platba"); self.assertContains(r, reverse("modul_qr_platba:zobrazit", args=[self.z.pk]))

    def test_po_zaplaceni_se_tlacitko_neukaze(self):
        from core.models import Platba
        Platba.objects.create(zakazka=self.z, stav="Zaplaceno", zpusob="QR kód", castka=Decimal("605"))
        r = self.client.get(reverse("plocha", args=[self.z.pk]))
        self.assertNotContains(r, "▦ QR platba"); self.assertNotContains(r, 'id="bm-pl-obr"')

    def test_stranka_pro_zakaznika(self):
        url = reverse("modul_qr_platba:zobrazit", args=[self.z.pk])
        r = self.client.get(url)
        self.assertContains(r, "QR Platba"); self.assertContains(r, "605,00 CZK"); self.assertContains(r, "CZ65 0800 0000 1920 0014 5399"); self.assertContains(r, f'src="{self.qr}"')
        r = self.client.get(url, {"castka": "1 000"})
        self.assertContains(r, "1\xa0000,00 CZK")  # oddělovač tisíců je nezlomitelná mezera; self.assertContains(r, f"{self.qr}?castka=1+000")
        self.f.cislo_uctu = "124/0800"; self.f.save()
        self.assertContains(self.client.get(url), "neprošlo kontrolou platnosti")

    def test_nastaveni_jen_pro_spravce(self):
        url = reverse("modul_qr_platba:nastaveni")
        self.assertNotEqual(self.client.get(url).status_code, 200)  # technik nemá oprávnění Nastavení
        self.client.force_login(uzivatel("admin", "Administrátor"))
        r = self.client.get(url); self.assertContains(r, "CZ65 0800 0000 1920 0014 5399"); self.assertContains(r, "<svg")
