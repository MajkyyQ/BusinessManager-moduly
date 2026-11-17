# Modul QR platba

Verze 1.0 · pro BusinessManager se systémem modulů (Nastavení → Moduly). QR kód přímo v okně **Vydat zákazníkovi** vyžaduje BusinessManager s místem pro rozšíření `platba_na_miste` (listopad 2026 a novější); ve starší verzi funguje jen tlačítko **▦ QR platba** na zakázce.

Když zákazník platí při vyzvednutí zakázky **QR kódem**, aplikace mu ukáže QR kód přímo na obrazovce. Zákazník ho naskenuje v aplikaci své banky a dostane vyplněný platební příkaz: účet firmy, částku, variabilní symbol a zprávu pro příjemce.

**Potřebuje:** číslo účtu firmy v **Nastavení → Firma**. Internet ani žádnou službu banky nepotřebuje, QR kód vytváří aplikace sama (knihovna `segno` z `requirements.txt` modulu).

## Instalace

1. Záloha aplikace (`zaloha.bat`).
2. Složku `qr_platba` zkopírujte do `C:\BusinessManager\moduly\`, aby vznikl `C:\BusinessManager\moduly\qr_platba\apps.py`.
3. Spusťte `aktualizace.bat` (nebo `docker compose up -d --build`). Při sestavení se nainstaluje knihovna `segno`. Modul nemá vlastní tabulky.
4. Administrátor: **Nastavení → Moduly → QR platba** zkontroluje číslo účtu a naskenuje zkušební QR kód na 100 Kč (platbu neodesílejte).

Při vývoji bez Dockeru: `pip install -r moduly/qr_platba/requirements.txt`.

## Použití

- **V okně Vydat zákazníkovi** (a v okně **Zapsat platbu na místě** u už vydané zakázky) vyberte způsob platby **QR kód**. Pod formulářem se ukáže QR kód na částku z okna. Když částku změníte, QR kód se sám obnoví. Kliknutím ho zvětšíte. Po zaplacení potvrďte tlačítkem **Vydat zákazníkovi** jako dosud.
- **Tlačítko ▦ QR platba** na zakázce otevře samostatnou stránku s velkým QR kódem, částkou a údaji platby, třeba pro monitor nebo tablet otočený k zákazníkovi. Tlačítko **Celá obrazovka** ukáže jen QR kód. Částku lze na stránce změnit. Po zapsání platby na místě se tlačítko na zakázce už neukazuje.

## Co QR kód obsahuje

Český standard **QR Platba** (formát SPAYD 1.0), který čtou aplikace všech českých bank:

| Údaj | Odkud |
|:--|:--|
| Účet (IBAN) | číslo účtu firmy z Nastavení → Firma. Číslo ve tvaru `19-2000145399/0800` se převede na IBAN, IBAN se použije rovnou. Číslo se kontroluje (kontrolní součet ČNB, kontrolní číslice IBAN), takže překlep v čísle účtu QR kód nevytvoří. |
| Částka | součet prací a materiálu zakázky s DPH (stejně jako v okně Vydat zákazníkovi), nebo částka zadaná v okně |
| Měna | měna firmy (CZK nebo EUR) |
| Variabilní symbol | číslice z čísla zakázky (např. `DMN260001` → `260001`, nejvýš 10 číslic) |
| Zpráva pro příjemce, příjemce | „Zakazka <číslo>“ a název firmy, bez diakritiky (ne všechny bankovní aplikace ji umí) |

Když číslo účtu chybí nebo je chybné, místo QR kódu se ukáže červený rámeček s vysvětlením.

## Oprávnění

QR kód a stránku QR platby vidí každý se základním přístupem (stejně jako tlačítko Vydat zákazníkovi). Stránku **Nastavení → Moduly → QR platba** jen role s oprávněním Nastavení.

## Co modul nedělá

Modul neověřuje, že peníze na účet opravdu přišly; to by vyžadovalo napojení na banku. Platbu na místě zapisuje zaměstnanec sám, až zákazník platbu v bance odešle.
