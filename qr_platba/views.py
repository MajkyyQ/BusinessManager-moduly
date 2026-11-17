"""Modul QR platba (stránky a obrázek QR kódu).

QR kód se vytváří na serveru knihovnou segno jako obrázek SVG, nepotřebuje internet ani žádnou službu banky.
Účet je číslo účtu firmy z Nastavení → Firma, částka podle zakázky (lze změnit), variabilní symbol z čísla zakázky."""
from decimal import Decimal
from html import escape
from urllib.parse import urlencode

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from core.models import NastaveniFirmy, Zakazka
from . import spayd as S


def k_zaplaceni(z):
    """Částka zakázky s DPH (stejně jako ji předvyplní okno Vydat zákazníkovi)."""
    from core.views import nabidka_polozky
    return sum((x["s"] for x in nabidka_polozky(z)), Decimal(0))


def udaje(z, castka_text=None):
    """Údaje QR platby pro zakázku: dict(iban, castka, mena, vs, zprava, prijemce, text). Chyba -> ChybaUdaju."""
    f = NastaveniFirmy.objects.first()
    iban = S.iban(f.cislo_uctu if f else "")
    castka = S.castka(k_zaplaceni(z) if castka_text in (None, "") else castka_text)
    d = dict(iban=iban, castka=castka, mena=(f.mena or "CZK"), vs=S.variabilni_symbol(z.cislo_zakazky, z.pk),
             zprava=f"Zakazka {z.cislo_zakazky or z.pk}", prijemce=f.nazev_firmy if f else "")
    d["text"] = S.spayd(d["iban"], d["castka"], d["mena"], d["vs"], d["zprava"], d["prijemce"])
    return d


def svg_qr(text):
    import io
    import segno
    b = io.BytesIO()
    segno.make(text, error="m", micro=False).save(b, kind="svg", border=4, omitsize=True, dark="#000", light="#fff", xmldecl=False)
    return b.getvalue()


def svg_chyba(zprava):
    """Obrázek s textem místo QR kódu, aby okno platby ukázalo, co chybí (obrázek s chybou by se jen nezobrazil)."""
    slova, radky, r = zprava.split(), [], ""
    for s in slova:
        if len(r) + len(s) > 26: radky.append(r); r = ""
        r = f"{r} {s}".strip()
    radky.append(r)
    t = "".join(f'<tspan x="120" dy="{0 if i == 0 else 20}">{escape(x)}</tspan>' for i, x in enumerate(radky))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240"><rect width="240" height="240" fill="#fff" stroke="#dc3545" stroke-width="4"/>'
            f'<text x="120" y="{120 - 10 * (len(radky) - 1)}" text-anchor="middle" font-family="sans-serif" font-size="15" fill="#dc3545">{t}</text></svg>').encode()


def obrazek(request, pk):
    """SVG s QR platbou zakázky; ?castka= změní částku. Používá ho okno platby na místě i stránka QR platby."""
    z = get_object_or_404(Zakazka, pk=pk)
    try: obsah = svg_qr(udaje(z, request.GET.get("castka"))["text"])
    except S.ChybaUdaju as e: obsah = svg_chyba(str(e))
    r = HttpResponse(obsah, content_type="image/svg+xml")
    r["Cache-Control"] = "no-store"; r["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'"
    return r


def zobrazit(request, pk):
    """Stránka pro zákazníka: velký QR kód s částkou a údaji platby (např. na monitoru nebo tabletu u pultu)."""
    from core.views import R
    z = get_object_or_404(Zakazka.objects.select_related("zakaznik"), pk=pk)
    castka_text = request.GET.get("castka", "").strip(); d, chyba = None, ""
    try: d = udaje(z, castka_text)
    except S.ChybaUdaju as e: chyba = str(e)
    return R(request, "modul_qr_platba/zobrazit.html", sec="zakazky", crumbs=[("📋 Zakázky", reverse("list", args=["zakazka"])), (str(z), reverse("plocha", args=[z.pk])), ("QR platba", None)],
             z=z, d=d, chyba=chyba, iban=S.formatuj_iban(d["iban"]) if d else "", ucet=(NastaveniFirmy.objects.first() or NastaveniFirmy()).cislo_uctu,
             castka_pole=castka_text or (f"{d['castka']:.2f}".replace(".", ",") if d else ""),
             obrazek_url=reverse("modul_qr_platba:obrazek", args=[z.pk]) + ("?" + urlencode({"castka": castka_text}) if castka_text else ""))


def nastaveni(request):
    """Nastavení → Moduly → QR platba: kontrola čísla účtu firmy a ukázkový QR kód."""
    from core.views import R, jen_admin_ok
    if not jen_admin_ok(request): return redirect("dashboard")
    f = NastaveniFirmy.objects.first(); iban, chyba = "", ""
    try: iban = S.iban(f.cislo_uctu if f else "")
    except S.ChybaUdaju as e: chyba = str(e)
    ukazka = S.spayd(iban, Decimal("100"), (f.mena if f else "") or "CZK", "123456", "Zkouska QR platby", f.nazev_firmy if f else "") if iban else ""
    return R(request, "modul_qr_platba/nastaveni.html", sec="nastaveni", f=f, iban=S.formatuj_iban(iban) if iban else "", chyba=chyba,
             ukazka_svg=svg_qr(ukazka).decode() if ukazka else "")
