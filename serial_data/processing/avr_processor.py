from collections import defaultdict
import re
import time
import statistics
import matplotlib.pyplot as plt

from .base_processor import UWBProcessor

class AverageDistProcessor(UWBProcessor):
	name: str = "avr"
	help: str = "Berechnet die durchschnittliche Distanz über eine gegebene Zeit"

	def __init__(self, args):
		self.args = args
		self.dists: dict[str, list] = defaultdict(lambda: [])
		self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')

	@classmethod
	def cli(cls, parser) -> None:
		...
	
	def on_data(self, i: int, line: str):
		match = self.pattern.match(line)
		if match:
			mac, dist = match.groups()
			self.dists[mac].append(int(dist))
		print(line)

	def main(self):
		time.sleep(1)

	def post_process(self):
		averages = {k: statistics.mean(v) for k,v in self.dists.items()}
		print(averages)
		
		macs = list(averages.keys())
		values = list(averages.values())

		plt.figure(figsize=(10, 5))
		plt.bar(macs, values, color='skyblue')
		plt.xlabel("MAC Address")
		plt.ylabel("Average Distance (cm)")
		plt.title("Durchschnittliche Distanzen pro MAC-Adresse")
		plt.xticks(rotation=45)
		plt.tight_layout()
		plt.show()