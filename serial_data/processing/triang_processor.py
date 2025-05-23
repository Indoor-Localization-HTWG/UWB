from collections import defaultdict
import re
import time
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import matplotlib.patches as patches

from .base_processor import UWBProcessor

class TriangulationProcessor(UWBProcessor):
	name: str = "triang"
	help: str = "Trianguliert die Distanz des Initiatiors und plottet diese live"

	def __init__(self, args):
		self.args = args

		self.dists = defaultdict(lambda: deque(maxlen=5))  # Maximal 5 letzte Distanzen je Beacon

		self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')

		self.fig, self.ax = plt.subplots()
		plt.ion()
		plt.show()

		# Positionen in Zentimeter
		self.beacon_positions = {
			"0x0002": np.array([0, 0]),
			"0x0003": np.array([150, 0]),
			"0x0004": np.array([80, 120]),
		}

	def on_data(self, i: int, line: str):
		match = self.pattern.search(line)
		if match:
			mac, dist = match.groups()
			if mac == "0x0001":  # Initiator, keine Beacon
				return
			self.dists[mac].append(int(dist))

	def estimate_position(self):
		available = [mac for mac in self.beacon_positions if self.dists[mac]]
		if len(available) < 3:
			return None

		macs = available[:3]
		p1 = self.beacon_positions[macs[0]]
		d1 = self.dists[macs[0]][-1]

		A = []
		b = []

		for mac in macs[1:]:
			p2 = self.beacon_positions[mac]
			d2 = self.dists[mac][-1]

			xi, yi = p1
			xj, yj = p2

			A.append([2 * (xj - xi), 2 * (yj - yi)])
			b.append(d2**2 - d1**2 + xi**2 - xj**2 + yi**2 - yj**2)  # <- Korrektur hier

		A = np.array(A)
		b = np.array(b)

		try:
			pos, *_ = np.linalg.lstsq(A, b, rcond=None)
			return pos
		except np.linalg.LinAlgError:
			return None


	@classmethod
	def cli(cls, parser):
		...

	def post_process(self):
		return super().post_process()


	def main(self):
		pos = self.estimate_position()
		if pos is None:
			time.sleep(0.1)
			return

		print(f"Estimated Position: x={pos[0]:.1f} cm, y={pos[1]:.1f} cm")

		self.ax.cla()  # Clear axes, aber nicht ganze Figure

		# Plot Beacons
		for mac, (x, y) in self.beacon_positions.items():
			self.ax.plot(x, y, 'ro')
			self.ax.text(x + 5, y + 5, mac, fontsize=8, color='red')

			if self.dists[mac]:
				r = self.dists[mac][-1]
				circ = patches.Circle((x, y), r, color='r', fill=False, linestyle='--', alpha=0.3)
				self.ax.add_patch(circ)

		# Plot estimate
		self.ax.plot(pos[0], pos[1], 'bo')
		self.ax.text(pos[0] + 5, pos[1] + 5, "Est.", fontsize=9, color='blue')

		self.ax.set_xlim(-50, 250)
		self.ax.set_ylim(-50, 200)
		self.ax.set_aspect('equal')
		self.ax.set_title("Live UWB Triangulation")

		self.fig.canvas.draw_idle()
		self.fig.canvas.flush_events()
		time.sleep(0.05)  # ~20 FPS Limit
