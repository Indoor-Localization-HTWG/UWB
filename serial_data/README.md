# UWB Datenverarbeitung

## Processing
Mit diesem CLI Tool kann man Daten aus den UWB Modulen über ihren seriellen Port auslesen, verarbeiten und darstellen.

Wie man es benutzt kann man mit `start_uwb.py -h` sehen:
```
usage: start_uwb.py [-h] [--baud BAUD] [--timeout TIMEOUT] [--cmd CMD] {plot,log,stat,triang} ...

options:
  -h, --help            show this help message and exit
  --baud BAUD
  --timeout TIMEOUT
  --cmd CMD

processor:
  {plot,log,stat,triang}
    plot                Plottet die Distanzmessungen live auf einen Graph
    log                 Schreibt den Seriellen Output der UWB Module in die Konsole
    stat                Berechnet die Statistik über eine gegebene Zeit
    triang              Trianguliert die Position des Initiators anhand der festen Responder und plottet diese live
```

### Processors hinzufügen
Die einzelnen sub-commands nennt nennen wir Processors. Im Ordner `processing` könnt ihr einen Processor hinzufügen. Jeder Processor bekommt seine eigene Datei und ist eine Unterklasse von `UWBProcessor`.

Ein leerer Processor sieht so aus (ihr könnt diesen als Template benutzen):
```py
from .base_processor import UWBProcessor

class MyProcessor(UWBProcessor):
	name: str = ...
	help: str = ...

	def __init__(self, args):
		super().__init__(args)

	@classmethod
	def cli(cls, parser: argparse.ArgumentParser) -> None:
		"""Füge hier cli Argumente hinzu"""
		pass

	def on_data(self, i: int, line: str):
		"""Wird aufgerufen jedes mal wenn neue Daten kommen"""
		pass

	def main(self):
		"""Wird solange das Programm läuft, wiederholt auf dem Main-Thread aufgerufen"""
		pass # falls ihr nichts in main machen müsst kann es sinnvoll sein ein sleep hinzuzufügen

	def post_process(self):
		"""Wird aufgerufen, nachdem alle Threads erfolgreich durch sind"""
		pass
```

Wenn ihr euren Processor hinzugefügt habt, müsst ihr noch `processing/__init__.py` ergänzen: `from .my_processor import MyProcessor`.\
Und schließlich die liste in `start_uwb.py::get_processors()` erweitern.

## Headless setup
`setup_headless.py` configuriert alle angeschlossenen UWB Module zum Autostart im Multi-TWR Modus.

Die genaue anordnung ist im Code über die Variablen `responders` und `initiator` definiert.

## Kalibrierung laden
1. Den output einer Kalibrierung als `.cal` Datei speichern
2. Die Kalibrierungs bei `<file>` in das Modul `<port>` laden: `set_calibration.py -p <port> -f <file>`

## Kalibrierung durchführen

Das Kalibrierungsprogramm `calibration.py` dient dazu, die UWB-Module zu kalibrieren, um präzise Abstandsmessungen zu gewährleisten. Es unterstützt die automatische Anpassung des Antennen-Delays basierend auf den gemessenen Fehlern.

### Nutzung
Das Programm wird über die Kommandozeile gestartet und erfordert einige Parameter:

```bash
python calibration_program.py --initiator <Seriennummer> [--dist <Zielabstand>] [--duration <Messdauer>] [--fixed_delay <fester Delay-Wert>] [--tolerance <Toleranz>] [--channel <Kanal>] [--plot]
```

#### Parameter
- `--initiator`: Seriennummer des Geräts, das als Initiator fungiert (Pflichtfeld).
- `--dist`: Zielabstand in cm (Standard: 200).
- `--duration`: Messdauer in Sekunden (Standard: 10).
- `--fixed_delay`: Fester Delay-Wert für den Initiator (Standard: 0x4015).
- `--tolerance`: Toleranzbereich in cm (Standard: ±2.0).
- `--channel`: Kanal für die Kalibrierung (5 oder 9, Standard: 9).
- `--plot`: Zeigt einen Plot der Kalibrierwerte an.

### Ablauf
1. **Geräte finden**: Das Programm sucht nach angeschlossenen Geräten mit den definierten Seriennummern.
2. **Kalibrierung starten**: Der Initiator und der Responder werden konfiguriert und die Messung beginnt.
3. **Fehlerberechnung**: Der Abstand wird gemessen und der Fehler berechnet.
4. **Delay-Anpassung**: Basierend auf dem Fehler wird der Antennen-Delay-Wert angepasst.
5. **Wiederholung**: Der Prozess wird wiederholt, bis der Fehler innerhalb der Toleranz liegt.
6. **Plot (optional)**: Ein Diagramm der Kalibrierwerte wird angezeigt, wenn `--plot` angegeben ist.

### Beispiel
```bash
python calibration_program.py --initiator F07DD0297227 --dist 250 --duration 15 --tolerance 1.5 --channel 9 --plot
```

Dieses Beispiel kalibriert das Gerät mit der Seriennummer `F07DD0297227` auf einen Zielabstand von 250 cm, mit einer Messdauer von 15 Sekunden und einer Toleranz von ±1.5 cm. Der Kanal 9 wird verwendet und die Kalibrierwerte werden geplottet.
