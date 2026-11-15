from django.apps import AppConfig

VERZE = "1.1"
ODESILAT = "email.odesilat"
OPRAVNENI = (ODESILAT, "Odesílání e-mailů", "Odeslání dokumentů, fotografií a příloh zakázky e-mailem z firemní schránky (modul Odesílání e-mailů).")
VYCHOZI_ROLE = ("Technik", "Administrativa")  # role, které oprávnění dostanou při instalaci modulu (migrace 0002)


class EmailConfig(AppConfig):
    """Modul se zapojí do aplikace přes core.moduly.registruj(): odkazy v Nastavení a tlačítka na zakázce a v náhledu dokumentu."""
    name = "moduly.email"; label = "modul_email"; verbose_name = "Modul Odesílání e-mailů"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.urls import reverse
        from urllib.parse import urlencode
        from core import moduly, prava as P

        def akce_zakazky(request, z):
            return [dict(text="✉ Odeslat e-mailem", url=reverse("modul_email:odeslat") + "?" + urlencode({"zakazka": z.pk}),
                         title="Odeslat dokumenty, fotografie nebo přílohy zakázky e-mailem")]

        def akce_dokumentu(request, typ, o):
            z = o if typ == "zakazkovy_list" else o.zakazky.order_by("pk").first()
            if not z: return []
            return [dict(text="✉ Odeslat e-mailem", url=reverse("modul_email:odeslat") + "?" + urlencode({"zakazka": z.pk, "vybrat": f"dok:{typ}:{o.pk}"}),
                         title="Odeslat dokument e-mailem")]

        # Odeslat e-mail z firemní schránky smí jen role s oprávněním „Odesílání e-mailů“ (Nastavení → Role).
        # Starší základní aplikace vlastní oprávnění modulů nezná: tam odesílání zůstane jako dřív (stačí základní přístup).
        vlastni = "opravneni" in getattr(moduly.Modul, "__dataclass_fields__", {})
        prava = {"modul_email:nastaveni": {P.NASTAVENI}, "modul_email:odeslane": {P.NASTAVENI}}
        if vlastni: prava["modul_email:odeslat"] = {ODESILAT}
        moduly.registruj(moduly.Modul(
            kod="email", nazev="Odesílání e-mailů", verze=VERZE,
            popis="Dokumenty, fotografie a přílohy zakázky odeslané e-mailem přímo z aplikace, s podpisem firmy.",
            pozadavky="e-mailovou schránku firmy (vyplní se v Nastavení e-mailu) a připojení k internetu při odesílání",
            nastaveni=[("Nastavení e-mailu", "modul_email:nastaveni"), ("Odeslané e-maily", "modul_email:odeslane")],
            akce_zakazky=akce_zakazky, akce_dokumentu=akce_dokumentu,
            prava=prava, **({"opravneni": [OPRAVNENI]} if vlastni else {})))
