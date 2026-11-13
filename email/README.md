# Modul Odesílání e-mailů

Verze 1.0 · pro BusinessManager od verze se systémem modulů (Nastavení → Moduly)

Dokumenty, fotografie a přílohy zakázky se odešlou e-mailem přímo z aplikace, s podpisem firmy.

**Potřebuje:** e-mailovou schránku firmy (SMTP) a připojení k internetu ve chvíli odeslání. Bez nastavení se nic neodesílá a zbytek aplikace funguje dál offline.

## Instalace

1. Záloha aplikace (`zaloha.bat`).
2. Složku `email` zkopírujte do `C:\BusinessManager\moduly\`, aby vznikl `C:\BusinessManager\moduly\email\apps.py`.
3. Spusťte `aktualizace.bat` (nebo `docker compose up -d --build`). Tabulky modulu se vytvoří samy.
4. Administrátor: **Nastavení → Moduly → Nastavení e-mailu**.

## Nastavení

- **E-mail a jméno odesílatele** – adresa, ze které zákazník e-mail dostane.
- **Server, port, šifrování** – odkazy *Seznam.cz*, *Gmail*, *Microsoft 365* vyplní obvyklé hodnoty. U Gmailu a Microsoftu 365 je potřeba **heslo aplikace**.
- **Skrytá kopie odesílateli** – odeslaný e-mail bude i ve firemní schránce.
- **Podpis** se značkami `{pracovnik}`, `{pozice}`, `{firma}`, `{adresa}`, `{telefon}`, `{email}`, `{web}`, `{ico}`. Řádek bez údaje se vynechá.
- Tlačítko **Uložit a odeslat zkušební e-mail** ověří nastavení.

## Použití

Na zakázce (nebo v náhledu zakázkového listu, nabídky či faktury) tlačítko **✉ Odeslat e-mailem**. Příjemce se předvyplní podle zákazníka, další kontakty zakázky lze přidat kliknutím. Zaměstnanec napíše předmět a text a zaškrtne soubory: zakázkový list, nabídky a faktury (PDF podle výchozí šablony), faktury jako ISDOC, přílohy objednávek, fotografie a přílohy zakázky. Doklady se nabídnou jen tomu, kdo s nimi smí pracovat. Limit příloh je 18 MB.

Odeslané e-maily jsou v historii zakázky a v **Nastavení → Moduly → Odeslané e-maily**.

## Technicky

- Tabulky `modul_email_nastaveniemailu` (jediný záznam, heslo ke schránce) a `modul_email_odeslanyemail`.
- Odesílání vestavěným `django.core.mail` (SMTP), žádné další knihovny.
- Testy: `python manage.py test moduly.email`.
- Odebrání: smazat složku a znovu spustit aplikaci. Tabulky a data v databázi zůstanou.
