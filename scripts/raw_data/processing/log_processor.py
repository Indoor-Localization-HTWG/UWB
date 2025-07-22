import time

from .base_processor import UWBProcessor

class LogProcessor(UWBProcessor):
	name = "log"
	help = "Schreibt den Seriellen Output der UWB Module in die Konsole"

	def __init__(self, args):
		super().__init__(args)

	@classmethod
	def cli(cls, parser):
		...
		
    # Wird aufgerufen jedes mal wenn neue Daten kommen
	def on_data(self, i: int, line: str):
		print(f"[{i}]: {line}")

	# Wird solange das Programm läuft, wiederholt auf dem Main-Thread aufgerufen
	def main(self):
		time.sleep(1)
	
	def post_process(self):
		...