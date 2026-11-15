# BusinessManager – volitelné moduly

Rozšíření pro aplikaci [BusinessManager](https://github.com/MajkyyQ/BusinessManager), která nejsou součástí základní aplikace. Firma si přidá jen ty moduly, které potřebuje.

| Modul | Složka | Co dělá | Potřebuje |
|:--|:--|:--|:--|
| Odesílání e-mailů | [`email`](email/README.md) | dokumenty, fotky a přílohy zakázky e-mailem s podpisem firmy | schránku firmy (SMTP), internet při odesílání |

## Jak přidat modul do aplikace

1. Udělejte zálohu aplikace (`zaloha.bat`).
2. Stáhněte tento repozitář: zelené tlačítko **Code → Download ZIP** a ZIP rozbalte.
3. Složku modulu (např. `email`) zkopírujte do složky `moduly` aplikace: `C:\BusinessManager\moduly\email\apps.py`.
4. Spusťte `aktualizace.bat` v aplikaci (nebo `docker compose up -d --build`). Tabulky modulu se vytvoří samy.
5. V aplikaci otevřete **Nastavení → Moduly**. Nastavení konkrétního modulu popisuje jeho `README.md`.

Aktualizace aplikace složku `moduly` nepřepisuje. Modul se odebere smazáním jeho složky a novým spuštěním, jeho data v databázi zůstanou.

Podrobný popis systému modulů a návod, jak napsat nový modul, je v dokumentaci aplikace: [docs/11-moduly.md](https://github.com/MajkyyQ/BusinessManager/blob/main/docs/11-moduly.md).

## Struktura modulu

```
email/
  __init__.py
  apps.py          registrace modulu v aplikaci (core.moduly.registruj)
  models.py        tabulky modulu
  sifrovani.py     šifrované uložení hesla ke schránce
  migrations/      migrace tabulek
  urls.py          stránky na /moduly/email/...
  views.py
  templates/modul_email/
  tests.py         python manage.py test moduly.email
  README.md
```

Licence MIT, stejně jako aplikace.
