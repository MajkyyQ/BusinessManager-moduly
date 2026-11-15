"""Heslo ke schránce se ukládá zašifrované (email/sifrovani.py). Už uložené čitelné heslo se při migraci zašifruje."""
import moduly.email.sifrovani
from django.db import migrations

from moduly.email.sifrovani import je_zasifrovane, rozsifruj


def zasifruj_ulozene(apps, schema_editor):
    M = apps.get_model("modul_email", "NastaveniEmailu")
    for pk, heslo in M.objects.values_list("pk", "heslo"):  # čitelné heslo projde from_db_value beze změny
        if heslo and not je_zasifrovane(heslo):
            M.objects.filter(pk=pk).update(heslo=heslo)  # při uložení ho pole zašifruje


def rozsifruj_ulozene(apps, schema_editor):  # návrat na verzi 1.1: heslo zase čitelně (přímým SQL, pole by ho zašifrovalo)
    M = apps.get_model("modul_email", "NastaveniEmailu"); t = schema_editor.quote_name(M._meta.db_table)
    with schema_editor.connection.cursor() as c:
        c.execute(f"SELECT id, heslo FROM {t}")
        for pk, heslo in c.fetchall():
            if je_zasifrovane(heslo) and not je_zasifrovane(rozsifruj(heslo)):
                c.execute(f"UPDATE {t} SET heslo = %s WHERE id = %s", [rozsifruj(heslo), pk])


class Migration(migrations.Migration):

    dependencies = [
        ("modul_email", "0002_opravneni_odesilat"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nastaveniemailu",
            name="heslo",
            field=moduly.email.sifrovani.SifrovaneHeslo(
                blank=True,
                help_text="U Gmailu a Microsoftu 365 heslo aplikace, ne běžné heslo k účtu. Ukládá se zašifrované.",
                max_length=500,
                verbose_name="heslo",
            ),
        ),
        migrations.RunPython(zasifruj_ulozene, rozsifruj_ulozene),
    ]
