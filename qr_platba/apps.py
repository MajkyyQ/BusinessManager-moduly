from django.apps import AppConfig

VERZE = "1.0"
ZPUSOB = "QR kód"  # způsob platby na místě v základní aplikaci, u kterého se QR platba ukáže


class QrPlatbaConfig(AppConfig):
    """Modul se zapojí do aplikace přes core.moduly.registruj(): QR kód v okně platby na místě, tlačítko na zakázce a odkaz v Nastavení."""
    name = "moduly.qr_platba"; label = "modul_qr_platba"; verbose_name = "Modul QR platba"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from django.urls import reverse
        from core import moduly, prava as P

        def zaplaceno(z):
            from core import views
            f = getattr(views, "platba_na_miste", None)  # starší aplikace platbu na místě nezná
            return bool(f and f(z))

        def akce_zakazky(request, z):
            if zaplaceno(z): return []
            return [dict(text="▦ QR platba", url=reverse("modul_qr_platba:zobrazit", args=[z.pk]),
                         title="Zobrazit zákazníkovi QR kód pro zaplacení zakázky z bankovní aplikace")]

        def platba_na_miste(request, z, zpusob):
            return reverse("modul_qr_platba:obrazek", args=[z.pk]) if zpusob == ZPUSOB else None

        # QR kód přímo v okně Vydat zákazníkovi umí jen aplikace s místem pro rozšíření platba_na_miste (listopad 2026 a novější).
        # Ve starší aplikaci zůstane jen tlačítko QR platba na zakázce.
        pole = getattr(moduly.Modul, "__dataclass_fields__", {})
        moduly.registruj(moduly.Modul(
            kod="qr_platba", nazev="QR platba", verze=VERZE,
            popis="QR kód pro zaplacení zakázky z bankovní aplikace (český standard QR Platba), zobrazený přímo na obrazovce aplikace.",
            pozadavky="číslo účtu firmy (Nastavení → Firma); internet nepotřebuje",
            nastaveni=[("QR platba", "modul_qr_platba:nastaveni")],
            akce_zakazky=akce_zakazky, prava={"modul_qr_platba:nastaveni": {P.NASTAVENI}},
            **({"platba_na_miste": platba_na_miste} if "platba_na_miste" in pole else {})))
