from collections import defaultdict
import csv
import re
import sys
import time
import statistics
import matplotlib.pyplot as plt

from .base_processor import UWBProcessor

class StatDistProcessor(UWBProcessor):
	name: str = "stat"
	help: str = "Berechnet die Statistik über eine gegebene Zeit"

	def __init__(self, args):
		self.args = args
		self.dists: dict[str, list] = defaultdict(lambda: [])
		self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')
		self.start_time = None
		self.timeout = args.time

	@classmethod
	def cli(cls, parser) -> None:
		parser.add_argument("--time", type=int, default=0)
		parser.add_argument("--save", type=str, default=None)

	
	def on_data(self, i: int, line: str):
		if self.start_time is None:
			self.start_time = time.time()

		# Stop if time limit exceeded
		if self.timeout > 0 and time.time() - self.start_time > self.timeout:
			print("Messzeit abgelaufen.")
			sys.exit(0)  # stop execution

		match = self.pattern.match(line)
		if match:
			mac, dist = match.groups()
			if mac == "0x0001": return
			self.dists[mac].append(int(dist))
		print(line)

	def main(self):
		time.sleep(1)

	def post_process(self):
		if not self.dists:
			print("Keine Daten vorhanden.")
			return
		
		if self.args.save:
			print(f"Speichere in {self.args.save}")
			with open(self.args.save, "w", newline="") as csvfile:
				writer = csv.writer(csvfile)
				writer.writerow(["MAC-Adresse", "Distanz (cm)"])
				for mac, dist_list in self.dists.items():
					for dist in dist_list:
						writer.writerow([mac, dist])

		stats = {k: {
			"median": statistics.median(v),
			"variance": statistics.variance(v) if len(v) > 1 else 0,
			"quartile": statistics.quantiles(v) if len(v) >= 4 else []
		} for k, v in self.dists.items()}
		

		print("Statistiken pro MAC-Adresse:")
		for mac, s in stats.items():
			print(f"{mac}: Median = {s['median']}, Varianz = {s['variance']}, Quartile = {s['quartile']}")

		# Vorbereitung der Daten für Boxplot
		macs = list(self.dists.keys())
		data = [self.dists[mac] for mac in macs]

		# Boxplot erzeugen
		plt.figure(figsize=(10, 5))
		plt.boxplot(data, labels=macs, showmeans=True)
		plt.xlabel("MAC-Adresse")
		plt.ylabel("Distanz (cm)")
		plt.title("Boxplot der Distanzen pro MAC-Adresse")
		plt.xticks(rotation=45)
		plt.tight_layout()
		plt.show()

		
