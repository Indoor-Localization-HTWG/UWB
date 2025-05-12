from collections import defaultdict
import re
import statistics
import time
import matplotlib.pyplot as plt
import numpy as np
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .base_processor import UWBProcessor

class TriangulationProcessor(UWBProcessor):
	name: str = "triang"
	help: str = "Trianguliert die Distanz des Initiatiors und plottet diese live"

	def __init__(self, args):
		self.args = args
		self.dists: dict[str, list] = defaultdict(lambda: [])
		self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')

		self.fig, self.ax = plt.subplots()
		plt.ion()
		plt.show()


	@classmethod
	def cli(cls, parser) -> None:
		...

	def on_data(self, i: int, line: str):
		match = self.pattern.match(line)
		if match:
			mac, dist = match.groups()
			if mac == "0x0001": return
			self.dists[mac].append(int(dist))
		#print(line)

	def post_process(self):
		return super().post_process()

	beacon_positions = {
		"0x0002": np.array([0, 0]),
		"0x0003": np.array([150, 0]),
		"0x0004": np.array([80, 120]),
	}

	def estimate_position(self):
		available = [mac for mac in self.beacon_positions if len(self.dists[mac]) > 0]
		if len(available) < 3:
			return None

		A = []
		b = []
		macs = list(available)[:3]
		pos1, d1 = self.beacon_positions[macs[0]], self.dists[macs[0]][-1]

		for mac in macs[1:]:
			pos2 = self.beacon_positions[mac]
			d2 = self.dists[mac][-1]
			xi, yi = pos1
			xj, yj = pos2
			A.append([2 * (xj - xi), 2 * (yj - yi)])
			b.append(d1**2 - d2**2 - xi**2 + xj**2 - yi**2 + yj**2)

		A = np.array(A)
		b = np.array(b)
		try:
			pos, *_ = np.linalg.lstsq(A, b, rcond=None)
			return pos
		except np.linalg.LinAlgError:
			return None

	def main(self):
		pos = self.estimate_position()
		if pos is None:
			time.sleep(0.5)
			return
		print(pos)
		# Clear previous frame
		self.ax.clear()

		# Plot beacons
		for mac, (x, y) in self.beacon_positions.items():
			self.ax.plot(x, y, 'ro')  # Red dots for beacons
			self.ax.text(x + 20, y + 20, mac, fontsize=9, color='red')

			if len(self.dists[mac]) > 0:
				radius = self.dists[mac][-1]
				circle = plt.Circle((x, y), radius, color='r', fill=False, linestyle='--', alpha=0.3)
				self.ax.add_patch(circle)

		# Plot estimated position
		self.ax.plot(pos[0], pos[1], 'bo')  # Blue dot for estimated position
		self.ax.text(pos[0] + 20, pos[1] + 20, "Est.", fontsize=9, color='blue')

		# Set plot limits
		self.ax.set_xlim(-20, 220)
		self.ax.set_ylim(-20, 220)
		self.ax.set_aspect('equal')
		self.ax.set_title("Live UWB Triangulation")

		# Refresh plot
		self.fig.canvas.draw()
		self.fig.canvas.flush_events()