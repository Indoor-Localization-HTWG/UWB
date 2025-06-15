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


