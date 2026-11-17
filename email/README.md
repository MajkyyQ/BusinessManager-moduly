# Modul Odesílání e-mailů

Verze 1.3 · pro BusinessManager od verze se systémem modulů (Nastavení → Moduly); oprávnění Odesílání e-mailů vyžaduje BusinessManager s vlastními oprávněními modulů a šifrované heslo knihovnu `cryptography` z jeho `requirements.txt` (BusinessManager z listopadu 2026 a novější)

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

## Kdo smí odesílat

E-mail z firemní schránky odešle jen role s oprávněním **Odesílání e-mailů** (`email.odesilat`). Při instalaci modulu ho dostanou výchozí role **Technik** a **Administrativa** a samozřejmě administrátor. Základní role **Zaměstnanec** ho nemá. Administrátor ho přidá nebo odebere v **Nastavení → Role**. Bez oprávnění se tlačítko Odeslat e-mailem nezobrazí a stránka odesílání se neotevře.

Oprávnění vzniklo po bezpečnostním auditu: dřív mohl každý zaměstnanec poslat z firemní schránky libovolný text na libovolnou adresu s podpisem firmy. Se starší verzí BusinessManager, která vlastní oprávnění modulů nezná, modul funguje dál a odesílat smí každý se základním přístupem.

## Heslo ke schránce

Heslo se do databáze ukládá **zašifrované** (od verze 1.2). Aplikace ho potřebuje při každém odeslání, proto ho nejde uložit jen jako otisk jako hesla k účtům. Šifruje se klíčem odvozeným ze `SECRET_KEY` v souboru `.env` aplikace (Fernet z knihovny `cryptography`), takže kdo má jen databázi nebo její zálohu, heslo nepřečte. Heslo uložené ve starší verzi se při aktualizaci zašifruje samo.

Když se `SECRET_KEY` změní, například po obnově zálohy na novém PC bez původního `.env`, uložené heslo nejde rozšifrovat. Nastavení e-mailu pak požádá o jeho nové zadání a odeslání do té doby skončí srozumitelnou hláškou. Proto `zaloha.bat` ukládá do zálohy i `.env`. Pro schránku je i tak vhodné použít heslo aplikace, které jde kdykoli zrušit.

## Technicky

- Tabulky `modul_email_nastaveniemailu` (jediný záznam, heslo ke schránce zašifrované, viz `sifrovani.py`) a `modul_email_odeslanyemail`.
- Odesílání vestavěným `django.core.mail` (SMTP), šifrování hesla knihovnou `cryptography` (je v `requirements.txt` aplikace).
- Testy: `python manage.py test moduly.email` (přehled níže).
- Odebrání: smazat složku a znovu spustit aplikaci. Tabulky a data v databázi zůstanou.

## Automatické testy

Modul je pokryt 18 automatickými testy v souboru `tests.py`. Běží v testovacím prostředí s vymyšlenými daty a žádný skutečný e-mail přitom neodejde (Django zprávy jen zachytí). Ověřují, že kód modulu funguje správně. Že funguje spojení s poštovním serverem konkrétní firmy, ověří po instalaci tlačítko **Uložit a odeslat zkušební e-mail** v nastavení.

Spuštění ze složky aplikace:

```
python manage.py test moduly.email
```

| Test | Co ověřuje |
|---|---|
| `test_odeslani_s_prilohami_a_podpisem` | E-mail odejde správnému příjemci, se skrytou kopií odesílateli a odpovědí na pracovníka. Připojí se PDF faktury, fotografie i příloha zakázky, doplní se podpis. Odeslání se uloží do přehledu odeslaných e-mailů a do historie zakázky. |
| `test_formular_nabidne_soubory_zakazky_a_kontakt` | Formulář nabídne zakázkový list, fakturu (PDF i ISDOC), fotografie a přílohy zakázky, předvyplní adresu zákazníka a předem zaškrtne vybraný doklad. |
| `test_technik_neposle_fakturu` | Technik nemá oprávnění k fakturám: faktura se mu nenabídne a nejde ji poslat ani podvrženým požadavkem. |
| `test_cizi_soubor_nejde_pripojit` | K e-mailu nejde připojit soubor, který k zakázce nepatří. |
| `test_kontrola_adres_a_predmetu` | Neplatná adresa příjemce a chybějící předmět se zachytí před odesláním. |
| `test_bez_nastaveni_se_neodesila` | Bez vyplněného nastavení je tlačítko Odeslat neaktivní, aplikace to vysvětlí a nic neodejde. |
| `test_bez_internetu_srozumitelna_chyba` | Bez připojení k internetu aplikace nespadne a ukáže srozumitelnou hlášku. |
| `test_odmitnute_prihlaseni_neskryje_zavrene_spojeni` | Když server odmítne jméno nebo heslo a hned zavře spojení (tak to dělá Gmail), uživatel uvidí „Server odmítl přihlášení“, ne nic neříkající „Connection unexpectedly closed“. |
| `test_port_a_sifrovani_musi_sedet` | Nastavení nejde uložit s portem 465 a STARTTLS ani s portem 587 a SSL/TLS, protože takové spojení server hned ukončí. |
| `test_podpis_vynecha_prazdne_radky` | Řádky podpisu bez vyplněného údaje se vynechají a v textu nezůstanou značky ani prázdné mezery. |
| `test_nastaveni_jen_pro_administratora_a_heslo_se_neukazuje` | Nastavení modulu otevře jen administrátor, heslo ke schránce se nikde nezobrazí a prázdné pole hesla při uložení ponechá původní heslo. |
| `test_zkusebni_email` | Tlačítko pro zkušební e-mail pošle zprávu na adresu odesílatele. |
| `test_tlacitko_na_zakazce` | Na zakázce je tlačítko ✉ Odeslat e-mailem. |
| `test_modul_v_nastaveni_a_odeslane` | Modul je vidět v Nastavení → Moduly a odeslaný e-mail se objeví v přehledu odeslaných. |
| `test_odeslane_jen_pro_administratora` | Přehled odeslaných e-mailů vidí jen administrátor. |
| `test_tlacitko_v_nahledu_dokumentu` | V náhledu dokladu (např. faktury) je tlačítko pro odeslání, které daný doklad rovnou předvybere. |
| `test_odesilat_smi_jen_role_s_opravnenim` | Bezpečnost: zaměstnanec bez oprávnění Odesílání e-mailů tlačítko nevidí a e-mail neodešle ani přímým požadavkem; po přidání oprávnění roli odeslat může. Technik oprávnění má. |
| `test_heslo_je_v_databazi_zasifrovane` | Bezpečnost: heslo ke schránce je v databázi zašifrované a aplikace ho přečte. S jiným `SECRET_KEY` (obnova bez původního `.env`) odeslání skončí srozumitelnou hláškou a nastavení požádá o nové heslo; s původním klíčem v `SECRET_KEY_FALLBACKS` se heslo přečte. |
