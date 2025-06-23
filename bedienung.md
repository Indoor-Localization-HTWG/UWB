# Firmware Flashen:
- Board über USB Port "J9" anschließen
- Flasher "JFlashLiteExe" öffnen
- Konfiguration:
	- Target Device: NRF52833
	- Target interface: SWD
	- Speed: 4000kHz
	- -> Ok
	- Data File: `/SDK/Binaries/DWM3001CDK/DWM3001CDK-DW3_QM33_SDK_UCI-FreeRTOS.hex`
	- -> Program Device

# GUI
In `/SDK/Tools/GUI/*` gibt es eine Applikation "QorvoOneTWR-2.1.1" womit man das Board konfigurieren und testen kann. Wir konnten bisher nur Two-Way-Ranging ausprobieren und kein TDoA

# Firmware bauen
Siehe SDK Doku und hoffe es funktioniert bei dir. Python envs und pip könnte Probleme machen. Musst schauen, dass der Interpreter ausgewählt ist, wo pip alle packages installiert hat. 

# CLI
## 1. Vorraussetzungen
- Ein Programm welches eine Serielle verbindung öffnen kann.
  Zum Beispiel: GNU `screen`, auf Linux unter mit `sudo apt install screen`

## 2. CLI firmware flashen
- Board an USB Port "J9" anschließen
- JFlashLiteExe öffnen
- Konfiguration:
	- Target Device: NRF52833
	- Target interface: SWD
	- Speed: 4000kHz
	- -> Ok
	- Data File: `/SDK/Binaries/DWM3001CDK/DWM3001CDK-DW3_QM33_SDK_CLI-FreeRTOS.hex`
	  Oder selbst gebaute
	- -> Program Device

## 3. Device öffnen
1. Zu USB Port "J20" wechseln.
2. device file notieren: `ls /dev/ | grep tty.usbmodem`, oder `ls /dev/serial/by-id/`
3. Pro Device öffnen: `screen <device file>`
4. Eine Liste an Befehlen mit `help` ausgelesen werden:
```
   DWM3001CDK - DW3_QM33_SDK - FreeRTOS
---       Anytime commands       ---
HELP      ?         STOP      THREAD
STAT

---    Application selection     ---
LISTENER  RESPF     INITF

---      IDLE time commands      ---
UART      CALKEY    LISTCAL

---       Service commands       ---
RESTORE   DIAG      LCFG      DECAID
SAVE      SETAPP    GETOTP

---       LISTENER Options       ---
LSTAT
```
5. Mit STRG-A -> k -> y kann man das Fenster verlassen
## 4. TWR Daten auslesen
### TWR mit zwei Devices
1. Beide devices in ihren eigenen Terminal Fenstern öffnen.
2. Auf einem Device `INITF` und auf dem anderen `RESPF`
3. Dann sollte man Distanzmessungen im folgenden Format sehen 
```
SESSION_INFO_NTF: {session_handle=1, sequence_number=39, block_index=39, n_measurements=1 [mac_address=0x0001, status="SUCCESS", distance[cm]=71]}
```
   
### TWR mit mehreren Devices
- Alle Geräte öffnen
- Befehle ausführen
	- Auf Responder1: `RESPF -MULTI -ADDR=1 -PADDR=3`
	- Auf Responder2: `RESPF -MULTI -ADDR=2 -PADDR=3`
	- Auf Initiator: `INITF -MULTI -ADDR=3 -PADDR=[1,2]`
- Dann bekommt man die Distanz für jeden Responder

Um Ranging zu stoppen benutzt man den Befehl `STOP`.
## Kalibrierungsdaten
Die Kalibrierungsdaten sind als Key-Value pair in einem Non-Volatile-Speicher gelagert. 
Man kann sie alle mit `LISTCAL` auslesen und mit `CALKEY <key> <value>` setzen. Mit `CALKEY <key>` kann man einen einzelnen Key abfragen.

Der `RESTORE` Befehl setzt alle Einstellungen und Kalibrierungswerte auf den default Wert.

# Batteriebetrieb
Das UWB Modul hat einen Batterieanschluss und zwei USB anschlüsse, die Strom liefern können.

Mit dieser Folge von Befehlen lässt sich ein Modul in einen bestimmten Modus zum Autostart setzen:
```
SETAPP RESPF
RESPF -ADDR=<address> -PADDR=<responder address>
STOP
SAVE
``` 

Hier startet das Modul jetzt als Responder. Man würde denken, dass man nun das Modul an eine Powerbank anschließen kann und es funktioniert, jedoch wird die Übertragung nach kurzer Zeit Unterbrochen. 

Der Workaround wird in diesem Forum post beschrieben: https://forum.qorvo.com/t/tutorial-how-to-use-dw3-qm33-sdk-to-operate-a-battery-operated-dk-to-take-ranging-measurements-for-evaluation/21845

Beachte, nun wird der USB Port J9 benutzt.