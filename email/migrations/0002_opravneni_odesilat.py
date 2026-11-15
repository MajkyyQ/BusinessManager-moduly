"""Oprávnění „Odesílání e-mailů“ (email.odesilat). Dostanou ho výchozí role Technik a Administrativa;
role Zaměstnanec (základní přístup) ho nemá. Administrátor ho může přidat nebo odebrat v Nastavení → Role."""
from django.db import migrations

from moduly.email.apps import OPRAVNENI, VYCHOZI_ROLE


def pridej(apps, schema_editor):
    Opravneni = apps.get_model("core", "Opravneni"); Role = apps.get_model("core", "Role")
    kod, nazev, popis = OPRAVNENI
    o, _ = Opravneni.objects.get_or_create(kod=kod, defaults={"nazev": nazev, "popis": popis})
    for r in Role.objects.filter(nazev__in=VYCHOZI_ROLE):
        r.opravneni.add(o)


def odeber(apps, schema_editor):
    apps.get_model("core", "Opravneni").objects.filter(kod=OPRAVNENI[0]).delete()


class Migration(migrations.Migration):
    dependencies = [("modul_email", "0001_initial"), ("core", "0018_opravneni_a_vychozi_role")]
    operations = [migrations.RunPython(pridej, odeber)]
