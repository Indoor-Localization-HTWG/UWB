# Versuchsprotokoll – UWB-Kalibrierung und Genauigkeitstest

**Datum:** 23.05.2025

---

## Ziel des Versuchs

Kalibrierung von zwei UWB-Modulen und Überprüfung der Messgenauigkeit bei festem Abstand.

---


## Beobachtungen

- 1. Messreihe bei 2,00 m Abstand mit zueinander parallel stehende Antennen (-> | <-)
  - [Mittelwert: 1,97m]

- 2. Messreihe bei 2,00m Abstand mit zueinander orthogonal stehenden Antennen (pfeil-runter | ->)
  - [Mittelwert: 2,08m ]

- 3. Messreihe bei 2,00m Abstand mit zueinander weg stehenden Antennen (<- | ->)
  - [Mittelwert: 1,89m]

- 4. Messreihe bei 2,00m Abstand mit zueinander parallel stehende Antennen (-> | <-)
  - [Mittelwert: 2,13m]

- 5. Messreihe bei 2,00m Abstand mit Holz und zueinander parallel stehende Antennen (-> | <-)
  - [Mittelwert: 2,01m]

- 6. Messreihe bei 2,00m Abstand mit Aluminium und zueinander parallel stehende Antennen
  - [Mittelwert: 2,05m]

- 7. Messreihe bei 1,00m Abstand ohne Hindernis und zueinander parallel stehende Antennen
  - [Mittelwert: 0,89m]

- 8. Messreihe bei 0,5m Abstand ohne Hindernis und zueinander parallel stehende Antennen
  - [Mittelwert: 0,37m]

- 9. Messreihe bei 0,3m Abstand ohne Hindernis und zueinander parallel stehende Antennen
  - [Mittelwert: 0,14m]

- 10. Messreihe bei 0,2m Abstand ohne Hindernis und zueinander parallel stehende Antennen
  - [Mittelwert: 0,03m]

- 11. Messreihe bei 2,5m Abstand ohne Hindernis und zueinander parallel stehende Antennen,
  - [Mittelwert: 2,56m ]

- 12. Messreihe bei 3,0m Abstand ohne Hindernis und zueinander parallel stehende Antennen,
  - [Mittelwert: 2,98m]

- 13. Messreihe bei 4,0m Abstand ohne Hindernis und zueinander parallel stehende Antennen,
  - [Mittelwert: 4,01m ]

- 14. Messreihe bei 28,175m Abstand ohne Hindernis und zueinander parallel stehende Antennen,
  - [Mittelwert: 28,55m ]
---

## Auswertung

- Abweichung vom Soll-Abstand: [Wert]
- Systematische Fehler? [Ja/Nein + Beschreibung]
- Streuung der Werte: [z. B. ±x cm]

## Die naechsten Schritte

- Recherchierung wie man die Module kalibrieren koennte?

- Fragen von Herr Staehle:  -  Ist TDoA tendenziell moeglich?
                             Phase Difference of Arrival?
                            - Staehle interessiert was man mehr rausfinden beim TDoA? Wenn nicht, dann fundiert begrüenden warum es nicht geht?

                            Wir haben vier UWB Module, wie platziere ich die Module sinnvoll im Raum.
                            Wie viele Anker brauchen wir, wie genau bekommen wir die Messung/Lokalisierung hin ?

                            Idee mit der Stromversorgung:: Batterie oder Powerbank?

  Wäre tendenziell schon mieglich mit TDoA zu messen:

  Sehr großer Aufwand:
  --> Kein SDK Support vorhanden
  --> Die größte technische Hürde liegt der sehr präzisen Synchronisation zwischen den Anker und Client( Nanosekundenbereich). Unser UWB-Modul verwendet jedoch lediglich einen einfachen Quarzoszillator (kein TCXO), wodurch es zu temperatur- und driftbedingten Ungenauigkeiten kommt.



ok
ant0.ch9.ant_delay: 0x000040a2 (len: 4)

ok
ant1.ch9.ant_delay: 0x000040a2 (len: 4)

ok
reps
error unknown command
save

Das hat nicht so guut geklappt, denn wir bekamen schlechte Werte wie bspw.
SESSION_INFO_NTF: {session_handle=1, sequence_number=12, block_index=0, n_measurements=1
 [mac_address=0x0000, status="SUCCESS", distance[cm]=-75]}
SESSION_INFO_NTF: {session_handle=1, sequence_number=13, block_index=1, n_measurements=1
 [mac_address=0x0000, status="SUCCESS", distance[cm]=-72]}


Auch nicht so gut:

calkey ant0.ch9.ant_delay 0x00003BC9
calkey ant1.ch9.ant_delay 0x00003BC9

SESSION_INFO_NTF: {session_handle=1, sequence_number=0, block_index=386, n_measurements=1
 [mac_address=0x0000, status="SUCCESS", distance[cm]=1093]}
SESSION_INFO_NTF: {session_handle=1, sequence_number=1, block_index=387, n_measurements=1
 [mac_address=0x0000, status="SUCCESS", distance[cm]=1089]}
SESSION_INFO_NTF: {session_handle=1, sequence_number=2, block_index=388, n_measurements=1
 [mac_address=0x0000, status="SUCCESS", distance[cm]=1091]}


twr im code:
3 messagetypes,
- `PollDtm` (0x00): Initial message sent by the initiator
- `ResponseDtm` (0x01): Response message from the responder
- `FinalDtm` (0x02): Final message in the exchange

Each message contains:
- Frame control (2 bytes): 0x8841 for data frames using 16-bit addressing
- Sequence number (1 byte): Incremented for each new frame
- PAN ID (2 bytes): 0xDECA
- Destination address (2 bytes)
- Source address (2 bytes)
- Function code (1 byte): Indicates the message type in the ranging process

Message content:
- Poll message: Basic frame structure only
- Response message: Contains additional timestamps
  - Poll message reception timestamp (4 bytes)
  - Response message transmission timestamp (4 bytes)
- All messages end with a 2-byte checksum




beim calibraten setzen wir folgenden wert:
Antenna Delay Calibration:
The system uses antenna delay values that need to be calibrated
These delays account for the time the signal takes to travel through the antenna and RF circuitry


timing berechnung, heißt auch ursprung des größeren messfehlers:


1. **Sequenznummern-Verwendung**:
```c
/* Frame sequence number, incremented after each transmission. */
static uint8_t frame_seq_nb = 0;
```
Die Sequenznummer wird nur für die Nachrichtenidentifikation verwendet, nicht für die Signalerkennung.

2. **Signalerkennung**:
```c
if ((status_reg & DWT_INT_RXFCG_BIT_MASK) && (goodSts >= 0) && (dwt_readstsstatus(&stsStatus, 0) == DWT_SUCCESS))
```
Die Signalerkennung erfolgt in mehreren Schritten:
- `DWT_INT_RXFCG_BIT_MASK`: Grundlegende Frame-Erkennung
- `goodSts >= 0`: STS (Secure Time Stamping) Qualitätsprüfung
- `dwt_readstsstatus(&stsStatus, 0) == DWT_SUCCESS`: STS Status-Überprüfung

3. **Warum Fehldetektionen möglich sind**:
- Die Sequenznummer wird erst NACH der Signalerkennung geprüft
- Der Chip muss zuerst das Signal erkennen und einen Zeitstempel generieren
- Bei schlechter Signalqualität kann der Chip:
  - Ein Rauschen als Signal interpretieren
  - Eine Reflexion als Hauptsignal erkennen
  - Den falschen Zeitpunkt für den Signalbeginn bestimmen

4. **Prozessablauf**:
```c
/* A frame has been received, read it into the local buffer. */
frame_len = dwt_getframelength(0);
if (frame_len <= RX_BUF_LEN)
{
    dwt_readrxdata(rx_buffer, frame_len, 0);
}
/* Check that the frame is the expected response... */
rx_buffer[ALL_MSG_SN_IDX] = 0;
```
1. Signal wird erkannt
2. Zeitstempel wird generiert
3. Frame wird gelesen
4. Sequenznummer wird geprüft

5. **Warum die Sequenznummer nicht hilft**:
- Die Sequenznummer ist Teil des Frames
- Der Frame wird erst NACH der Signalerkennung gelesen
- Die Zeitstempel-Erfassung erfolgt VOR der Frame-Verarbeitung
- Wenn der Chip ein falsches Signal erkennt, wird der falsche Zeitstempel bereits generiert, bevor die Sequenznummer überprüft werden kann

6. **Technische Details**:
- Die Signalerkennung erfolgt auf Hardware-Ebene
- Die Sequenznummern-Prüfung erfolgt auf Software-Ebene
- Die Zeitstempel-Erfassung ist ein Hardware-Prozess
- Bei schlechter Signalqualität kann die Hardware falsche Signale erkennen, bevor die Software die Sequenznummer prüfen kann

Die Sequenznummer schützt also vor falschen Nachrichten, aber nicht vor falschen Zeitstempeln. Die Zeitstempel-Erfassung ist ein Hardware-Prozess, der vor der Sequenznummern-Prüfung stattfindet und bei schlechter Signalqualität fehleranfällig ist.




Protokoll zum 16.06.2025
–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

Neue Erkenntnisse:

Neue Fragen/Weitere Vorgehensweise:

- Im Raum montieren und im Raum vesuchen zu messen. 
batterie anschliessen. Tobi moechte 
