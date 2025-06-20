# UWB Datenverarbeitung

Mit diesem CLI Tool kann man Daten aus den UWB Modulen über ihren seriellen Port auslesen, verarbeiten und darstellen.

Wie man es benutzt kann man mit `start_uwb.py -h` sehen:
```
usage: start_uwb.py [-h] [--baud BAUD] [--timeout TIMEOUT] {plot,log,avr} ...

options:
  -h, --help         show this help message and exit
  --baud BAUD
  --timeout TIMEOUT

processor:
  {plot,log,avr,cal}
    plot             Plottet die Distanzmessungen live auf einen Graph
    log              Schreibt den Seriellen Output der UWB Module in die Konsole
    avr              Berechnet die durchschnittliche Distanz über eine gegebene Zeit
```

## Processors hinzufügen
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