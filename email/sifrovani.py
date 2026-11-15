"""Šifrované uložení hesla ke schránce.

Aplikace heslo potřebuje při každém odeslání, takže ho nejde uložit jen jako otisk (hash) jako hesla k účtům.
Ukládá se proto zašifrované (Fernet: AES-128 v režimu CBC a HMAC-SHA256, knihovna cryptography). Klíč se odvozuje
z SECRET_KEY v souboru .env, takže kdo má jen databázi nebo její zálohu, heslo nepřečte.

Když se SECRET_KEY změní (nová instalace bez původního .env), uložené heslo nejde rozšifrovat. Zůstane uložené
zašifrované a nastavení e-mailu požádá o jeho nové zadání. Při plánované změně klíče stačí dát původní klíč do
SECRET_KEY_FALLBACKS a heslo se dál přečte."""
import base64
import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

PREDPONA = "sifr1:"


def _fernet():
    try:
        from cryptography.fernet import Fernet, MultiFernet
    except ImportError as e:  # starší BusinessManager bez knihovny v requirements.txt
        raise ImproperlyConfigured("Modul E-mail potřebuje knihovnu cryptography. Aktualizujte BusinessManager (aktualizace.bat).") from e
    klice = [settings.SECRET_KEY, *getattr(settings, "SECRET_KEY_FALLBACKS", [])]
    return MultiFernet([Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"BusinessManager modul e-mail heslo:" + k.encode()).digest()))
                        for k in klice])


def je_zasifrovane(hodnota): return bool(hodnota) and hodnota.startswith(PREDPONA)


def zasifruj(heslo):
    if not heslo or je_zasifrovane(heslo): return heslo
    return PREDPONA + _fernet().encrypt(heslo.encode()).decode()


def rozsifruj(hodnota):
    """Čitelné heslo. Když ho nejde rozšifrovat (jiný SECRET_KEY), vrátí hodnotu beze změny, tedy stále zašifrovanou."""
    if not je_zasifrovane(hodnota): return hodnota
    from cryptography.fernet import InvalidToken
    try: return _fernet().decrypt(hodnota[len(PREDPONA):].encode()).decode()
    except InvalidToken: return hodnota


class SifrovaneHeslo(models.CharField):
    """Textové pole, které se do databáze ukládá zašifrované a v aplikaci se čte jako obyčejný text."""
    def from_db_value(self, value, expression, connection): return rozsifruj(value)

    def get_prep_value(self, value): return zasifruj(super().get_prep_value(value))
