"""Tabulky modulu: nastavení schránky (jediný záznam) a záznam o odeslaných e-mailech."""
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from core.models import VYCET, Zakazka

from .sifrovani import SifrovaneHeslo, je_zasifrovane


def C(n=200, **k): return models.CharField(max_length=n, blank=True, **k)


class NastaveniEmailu(models.Model):
    """Údaje e-mailové schránky firmy pro odesílání dokumentů ze zakázky (jediný záznam, Nastavení → E-mail).

    Bez vyplněného serveru a odesílatele se nic neodesílá a zbytek aplikace funguje dál bez internetu."""
    SIFROVANI = (("tls", "STARTTLS (obvykle port 587)"), ("ssl", "SSL/TLS (obvykle port 465)"), ("zadne", "Bez šifrování (jen místní server)"))
    class Meta:
        verbose_name = "nastavení e-mailu"; verbose_name_plural = "Nastavení e-mailu"
        constraints = [VYCET("sifrovani", ("tls", "ssl", "zadne"), "email_sifrovani_platne", prazdne=False),
                       models.CheckConstraint(condition=Q(port__gte=1, port__lte=65535), name="email_port_rozsah")]
    smtp_server = C(200, verbose_name="server odchozí pošty (SMTP)", help_text="Např. smtp.seznam.cz, smtp.gmail.com nebo smtp.office365.com.")
    port = models.PositiveIntegerField(default=587)
    sifrovani = models.CharField("šifrování", max_length=10, default="tls", choices=SIFROVANI)
    uzivatel = C(200, verbose_name="přihlašovací jméno", help_text="Obvykle celá e-mailová adresa schránky.")
    heslo = SifrovaneHeslo("heslo", max_length=500, blank=True, help_text="U Gmailu a Microsoftu 365 heslo aplikace, ne běžné heslo k účtu. "
                           "Ukládá se zašifrované.")
    odesilatel_email = models.EmailField("e-mail odesílatele", blank=True, help_text="Adresa, ze které zákazník e-mail dostane.")
    odesilatel_jmeno = C(150, verbose_name="jméno odesílatele", help_text="Např. název firmy. Prázdné = název firmy z Nastavení → Firma.")
    kopie_odesilateli = models.BooleanField("posílat skrytou kopii odesílateli", default=True,
                                            help_text="Odeslaný e-mail přijde i do firemní schránky, takže je dohledatelný i mimo aplikaci.")
    podpis = models.TextField("podpis e-mailu", blank=True, help_text="Připojí se na konec každého e-mailu.")
    datum_upravy = models.DateTimeField(auto_now=True)
    VYCHOZI_PODPIS = "S pozdravem\n\n{pracovnik}\n{pozice}\n{firma}\n{adresa}\nTel.: {telefon}\nE-mail: {email}\n{web}"
    ZNACKY = (("pracovnik", "jméno a příjmení odesílajícího zaměstnance"), ("pozice", "pracovní pozice zaměstnance"),
              ("firma", "název firmy"), ("adresa", "adresa firmy"), ("telefon", "telefon zaměstnance, jinak firmy"),
              ("email", "e-mail zaměstnance, jinak firmy"), ("web", "web firmy"), ("ico", "IČO firmy"))
    @classmethod
    def aktualni(cls): return cls.objects.first()
    def je_nastaveno(self): return bool(self.smtp_server and self.odesilatel_email)
    def heslo_necitelne(self): return je_zasifrovane(self.heslo)  # uložené jiným SECRET_KEY (např. obnova bez původního .env)
    def __str__(self): return self.odesilatel_email or "Nastavení e-mailu"

class OdeslanyEmail(models.Model):
    """Záznam o odeslaném e-mailu (komu, co a s jakými přílohami), zobrazí se v historii zakázky."""
    class Meta: verbose_name = "odeslaný e-mail"; verbose_name_plural = "Odeslané e-maily"; ordering = ["-datum"]
    zakazka = models.ForeignKey(Zakazka, on_delete=models.CASCADE, null=True, blank=True)
    komu = models.CharField(max_length=500); kopie = C(500); predmet = models.CharField("předmět", max_length=200); text = models.TextField(blank=True)
    prilohy = models.TextField("přílohy", blank=True, help_text="Názvy přiložených souborů, jeden na řádek.")
    odeslal = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True); datum = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.predmet} → {self.komu}"
