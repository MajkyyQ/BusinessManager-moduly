"""Testy modulu Odesílání e-mailů. Spuštění: python manage.py test moduly.email"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.models import Faktura, NastaveniFirmy, Zakaznik
from core.tests import uzivatel


class ModulEmailTest(TestCase):
    """Modul Odesílání e-mailů: nastavení, podpis, výběr souborů zakázky, oprávnění a srozumitelné chyby."""
    def setUp(self):
        import tempfile
        from unittest import mock
        from django.core.files.base import ContentFile
        from django.test import override_settings
        from core.models import Fotografie, Priloha, Zakazka, Zamestnanec
        from moduly.email.models import NastaveniEmailu
        self.media = override_settings(MEDIA_ROOT=tempfile.mkdtemp()); self.media.enable(); self.addCleanup(self.media.disable)
        pdf = mock.patch("moduly.email.views._pdf", side_effect=lambda typ, o: (f"{typ}_{o.pk}.pdf", b"%PDF-1.4 ukazka", "application/pdf"))
        pdf.start(); self.addCleanup(pdf.stop)  # PDF vytváří LibreOffice, v testu stačí obsah
        NastaveniFirmy.objects.all().delete()
        NastaveniFirmy.objects.create(nazev_firmy="Servis s.r.o.", adresa="Dílenská 5, Ústí nad Labem", telefon="604851237", email="info@servis.cz", web="www.servis.cz")
        self.n = NastaveniEmailu.objects.create(smtp_server="smtp.servis.cz", port=587, odesilatel_email="info@servis.cz", uzivatel="info@servis.cz", heslo="tajne",
                                                podpis=NastaveniEmailu.VYCHOZI_PODPIS)
        self.u = uzivatel("sekretarka", "Administrativa")
        Zamestnanec.objects.filter(uzivatel=self.u).update(jmeno="Jana", prijmeni="Malá", pracovni_pozice="Administrativa", email="jana@servis.cz")
        self.client.force_login(self.u)
        self.zak = Zakaznik.objects.create(firma="Odběratel a.s.", email="nakup@odberatel.cz")
        self.z = Zakazka.objects.create(zakaznik=self.zak)
        self.f = Faktura.objects.create(zakaznik=self.zak); self.f.zakazky.add(self.z)
        self.foto = Fotografie.objects.create(zakazka=self.z, popis="Vadný díl", soubor=ContentFile(b"\x89PNGdata", name="dil.png"))
        self.p = Priloha.objects.create(nazev="Protokol", soubor=ContentFile(b"protokol", name="protokol.txt")); self.p.zakazky.add(self.z)

    def _odeslat(self, **k):
        data = {"zakazka": self.z.pk, "odeslat": "1", "komu": "nakup@odberatel.cz", "predmet": "Faktura k zakázce", "text": "Dobrý den,",
                "soubor": [f"dok:faktura:{self.f.pk}", f"foto:{self.foto.pk}", f"pril:{self.p.pk}"]}
        data.update(k)
        return self.client.post(reverse("modul_email:odeslat"), data)

    def test_odeslani_s_prilohami_a_podpisem(self):
        from django.core import mail
        from core.models import HistorieZmen
        from moduly.email.models import OdeslanyEmail
        r = self._odeslat()
        self.assertEqual(r.status_code, 302)
        self.assertEqual(len(mail.outbox), 1); m = mail.outbox[0]
        self.assertEqual(m.to, ["nakup@odberatel.cz"]); self.assertEqual(m.bcc, ["info@servis.cz"]); self.assertEqual(m.reply_to, ["jana@servis.cz"])
        self.assertEqual([a[0] for a in m.attachments], [f"faktura_{self.f.pk}.pdf", "dil.png", "Protokol.txt"])
        self.assertIn("S pozdravem\n\nJana Malá\nAdministrativa\nServis s.r.o.", m.body)
        self.assertIn("Tel.: 604 851 237", m.body); self.assertIn("E-mail: jana@servis.cz", m.body)
        self.assertTrue(OdeslanyEmail.objects.filter(zakazka=self.z, komu="nakup@odberatel.cz").exists())
        self.assertTrue(HistorieZmen.objects.filter(typ_objektu="zakazka", id_objektu=self.z.pk, akce="odeslán e-mail").exists())

    def test_formular_nabidne_soubory_zakazky_a_kontakt(self):
        r = self.client.get(reverse("modul_email:odeslat"), {"zakazka": self.z.pk, "vybrat": f"dok:faktura:{self.f.pk}"})
        self.assertContains(r, f"Zakázkový list {self.z.cislo_zakazky} (PDF)"); self.assertContains(r, f"Faktura {self.f.cislo_faktury} (ISDOC")
        self.assertContains(r, "Vadný díl"); self.assertContains(r, "Protokol"); self.assertContains(r, 'value="nakup@odberatel.cz"')
        self.assertContains(r, f'value="dok:faktura:{self.f.pk}" id="s1_2" data-sk="1" data-vel="0" checked')

    def test_technik_neposle_fakturu(self):
        from django.core import mail
        self.client.force_login(uzivatel("technik", "Technik"))
        r = self.client.get(reverse("modul_email:odeslat"), {"zakazka": self.z.pk})
        self.assertNotContains(r, "Faktura "); self.assertContains(r, "Zakázkový list")
        r = self._odeslat(soubor=[f"dok:faktura:{self.f.pk}"])
        self.assertContains(r, "nepatří"); self.assertEqual(len(mail.outbox), 0)

    def test_cizi_soubor_nejde_pripojit(self):
        from django.core import mail
        from core.models import Zakazka
        jina = Zakazka.objects.create(zakaznik=self.zak)
        r = self._odeslat(zakazka=jina.pk, soubor=[f"foto:{self.foto.pk}"])
        self.assertContains(r, "nepatří"); self.assertEqual(len(mail.outbox), 0)

    def test_kontrola_adres_a_predmetu(self):
        from django.core import mail
        r = self._odeslat(komu="spatna-adresa", predmet="")
        self.assertContains(r, "není platný e-mail"); self.assertContains(r, "Napište předmět"); self.assertEqual(len(mail.outbox), 0)

    def test_bez_nastaveni_se_neodesila(self):
        from django.core import mail
        self.n.delete()
        r = self.client.get(reverse("modul_email:odeslat"), {"zakazka": self.z.pk})
        self.assertContains(r, "Odesílání zatím není nastavené"); self.assertContains(r, "disabled>Odeslat")
        self.assertContains(self._odeslat(), "není nastavené"); self.assertEqual(len(mail.outbox), 0)

    def test_bez_internetu_srozumitelna_chyba(self):
        import socket
        from unittest import mock
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=socket.gaierror("Name or service not known")):
            r = self._odeslat()
        self.assertContains(r, "připojený k internetu")

    def test_podpis_vynecha_prazdne_radky(self):
        from moduly.email import views as email_modul
        NastaveniFirmy.objects.update(web="")
        u = User.objects.create_user("bezkarty", first_name="Petr", last_name="Novák")
        t = email_modul.podpis(self.n, u)
        self.assertIn("Petr Novák\nServis s.r.o.", t); self.assertNotIn("{", t); self.assertNotIn("\n\n\n", t)

    def test_nastaveni_jen_pro_administratora_a_heslo_se_neukazuje(self):
        r = self.client.get(reverse("modul_email:nastaveni")); self.assertEqual(r.status_code, 302)  # Administrativa nemá oprávnění Nastavení
        self.client.force_login(uzivatel("admin", "Administrátor"))
        self.assertEqual(self.client.get("/nastaveniemailu/").status_code, 404)  # tabulky modulu nemají obecný seznam (heslo)
        r = self.client.get(reverse("modul_email:nastaveni"))
        self.assertContains(r, "připojení k internetu"); self.assertNotContains(r, "tajne")
        r = self.client.post(reverse("modul_email:nastaveni"), {"odesilatel_email": "info@servis.cz", "smtp_server": "smtp.seznam.cz", "port": 465, "sifrovani": "ssl",
                                                          "uzivatel": "info@servis.cz", "heslo": "", "podpis": "S pozdravem\n{pracovnik}"})
        self.assertEqual(r.status_code, 302); self.n.refresh_from_db()
        self.assertEqual((self.n.smtp_server, self.n.heslo, self.n.sifrovani), ("smtp.seznam.cz", "tajne", "ssl"))  # prázdné heslo = ponechat

    def test_zkusebni_email(self):
        from django.core import mail
        self.client.force_login(uzivatel("admin", "Administrátor"))
        self.client.post(reverse("modul_email:nastaveni"), {"odesilatel_email": "info@servis.cz", "smtp_server": "smtp.servis.cz", "port": 587, "sifrovani": "tls",
                                                      "podpis": "", "zkouska": "1"})
        self.assertEqual(len(mail.outbox), 1); self.assertEqual(mail.outbox[0].to, ["info@servis.cz"])

    def test_tlacitko_na_zakazce(self):
        r = self.client.get(reverse("plocha", args=[self.z.pk]))
        self.assertContains(r, f"{reverse('modul_email:odeslat')}?zakazka={self.z.pk}&next=")

    def test_modul_v_nastaveni_a_odeslane(self):
        self._odeslat()
        self.client.force_login(uzivatel("admin", "Administrátor"))
        r = self.client.get(reverse("nastaveni"))
        self.assertContains(r, "Odesílání e-mailů"); self.assertContains(r, reverse("modul_email:nastaveni"))
        self.assertContains(self.client.get(reverse("modul_email:odeslane")), "Faktura k zakázce")

    def test_odeslane_jen_pro_administratora(self):
        r = self.client.get(reverse("modul_email:odeslane"))
        self.assertEqual(r.status_code, 302)  # Administrativa nemá oprávnění Nastavení

    def test_tlacitko_v_nahledu_dokumentu(self):
        r = self.client.get(reverse("dokument", args=["faktura", self.f.pk]))
        self.assertContains(r, f"vybrat=dok%3Afaktura%3A{self.f.pk}")
