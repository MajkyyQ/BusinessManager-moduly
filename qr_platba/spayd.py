"""QR Platba (český standard SPAYD, „Short Payment Descriptor“, verze 1.0) a převod čísla účtu na IBAN.

Řetězec QR Platby vypadá takto:  SPD*1.0*ACC:CZ6508000000192000145399*AM:450.00*CC:CZK*X-VS:260001*MSG:Zakazka 260001
Bankovní aplikace všech českých bank ho po naskenování otevřou jako vyplněný platební příkaz.
Specifikace: https://qr-platba.cz/pro-vyvojare/specifikace-formatu/"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation

VAHY = (6, 3, 7, 9, 10, 5, 8, 4, 2, 1)  # váhy kontrolního součtu (modulo 11) českého čísla účtu, vyhláška ČNB č. 169/2011 Sb.
MAX_CASTKA = Decimal("9999999.99")  # pole AM má nejvýš 10 znaků


class ChybaUdaju(ValueError):
    """Srozumitelná chyba pro uživatele (chybí číslo účtu, špatná částka…)."""


def _mod11(cislo): return sum(int(c) * v for c, v in zip(cislo.zfill(10), VAHY)) % 11 == 0


def iban_platny(iban):
    s = iban[4:] + iban[:4]
    return int("".join(str(int(c, 36)) for c in s)) % 97 == 1


def iban(ucet):
    """Číslo účtu firmy („19-2000145399/0800“ nebo IBAN) -> IBAN bez mezer. Chybné číslo vyvolá ChybaUdaju."""
    u = re.sub(r"\s", "", ucet or "").upper()
    if not u: raise ChybaUdaju("Číslo účtu firmy není vyplněné.")
    if re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", u):
        if not iban_platny(u): raise ChybaUdaju(f"IBAN {u} má chybnou kontrolní číslici, zkontrolujte ho.")
        return u
    m = re.fullmatch(r"(?:(\d{1,6})-)?(\d{2,10})/(\d{4})", u)
    if not m: raise ChybaUdaju(f"Číslo účtu „{ucet}“ není ve tvaru 123456789/0800, 19-123456789/0800 ani IBAN.")
    predcisli, cislo, banka = m.group(1) or "", m.group(2), m.group(3)
    if not (_mod11(predcisli) and _mod11(cislo)): raise ChybaUdaju(f"Číslo účtu „{ucet}“ neprošlo kontrolou platnosti, zkontrolujte ho.")
    bban = banka + predcisli.zfill(6) + cislo.zfill(10)
    return f"CZ{98 - int(bban + '123500') % 97:02d}{bban}"  # C = 12, Z = 35, kontrolní číslice 00


def formatuj_iban(i): return " ".join(i[k:k + 4] for k in range(0, len(i), 4))


def castka(text):
    """„1 234,50“ -> Decimal('1234.50'). Prázdná, záporná nebo příliš velká částka vyvolá ChybaUdaju."""
    s = str(text if text is not None else "").replace("\xa0", "").replace(" ", "").replace(",", ".")
    if not s: raise ChybaUdaju("Zadejte částku.")
    try: c = Decimal(s)
    except InvalidOperation: raise ChybaUdaju("Částka není číslo.")
    if not c.is_finite() or c <= 0: raise ChybaUdaju("Částka musí být kladné číslo.")
    if c > MAX_CASTKA: raise ChybaUdaju("Částka je příliš vysoká pro QR platbu.")
    return c.quantize(Decimal("0.01"))


def variabilni_symbol(cislo_zakazky, pk):
    """Číslice z čísla zakázky (DMN260001 -> 260001), nejvýš posledních 10; bez číslic primární klíč zakázky."""
    c = re.sub(r"\D", "", cislo_zakazky or "")[-10:].lstrip("0")
    return c or str(pk)[-10:]


def _text(s, n):
    """Text do pole QR platby: bez diakritiky (některé bankovní aplikace ji neumí), bez hvězdičky (oddělovač polí)."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.replace("*", " ")).strip()[:n].strip()


def spayd(iban_, castka_, mena="CZK", vs="", zprava="", prijemce=""):
    casti = ["SPD", "1.0", f"ACC:{iban_}", f"AM:{castka_:.2f}", f"CC:{mena or 'CZK'}"]
    if vs: casti.append(f"X-VS:{vs}")
    if prijemce and _text(prijemce, 35): casti.append(f"RN:{_text(prijemce, 35)}")
    if zprava and _text(zprava, 60): casti.append(f"MSG:{_text(zprava, 60)}")
    return "*".join(casti)
