import threading
import re
from datetime import datetime
from collections import defaultdict, deque
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base_processor import UWBProcessor

class PlotDistProcessor(UWBProcessor):
	name = "plot"
	help = "Plottet die Distanzmessungen live auf einen Graph"

	def __init__(self, args):
		super().__init__(args)
		self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')
		self.distance_history = defaultdict(lambda: deque(maxlen=args.max_points))
		self.data_lock = threading.Lock()

		self.fig, self.ax = plt.subplots()
		plt.ion()
		plt.show()

	@classmethod
	def cli(cls, parser):
		parser.add_argument("--max_points", type=int, default=100)
		parser.add_argument("--max_y", type=int, default=150)

	def on_data(self, i: int, line: str):
		match = self.pattern.match(line)
		if match:
			mac, dist = match.groups()
			with self.data_lock:
				self.distance_history[mac].append((datetime.now(), int(dist)))
			print(f"[{i}] MAC={mac}, Distance={dist} cm")
	
	def main(self):
		self.ax.clear()
		self.ax.set_title("Live Distance Readings Over Time")
		self.ax.set_xlabel("Time")
		self.ax.set_ylabel("Distance (cm)")
		self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
		self.ax.set_ylim(-20, self.args.max_y)

		with self.data_lock:
			for mac, data in self.distance_history.items():
				times, dists = zip(*data)
				self.ax.plot(times, dists, label=mac)

		self.ax.legend()
		self.fig.autofmt_xdate()
		self.fig.canvas.draw()
		self.fig.canvas.flush_events()
