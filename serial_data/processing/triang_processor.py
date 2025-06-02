from collections import defaultdict, deque
import re
import time
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

from .base_processor import UWBProcessor

class TriangulationProcessor(UWBProcessor):
    name: str = "triang"
    help: str = "Trianguliert die Position des Initiators anhand der festen Responder und plottet diese live"

    def __init__(self, args):
        self.args = args
        self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')

        # Speichert die letzten Distanzen von Initiator zu den Beacons
        self.initiator_dists = defaultdict(lambda: deque(maxlen=5))

        # Feste Positionen der Responder (Beacons)
        self.beacon_positions = {
            "0x0002": np.array([0, 0]),
            "0x0003": np.array([150, 0]),
            "0x0004": np.array([80, 120]),
        }

        # Plot-Vorbereitung
        self.fig, self.ax = plt.subplots()
        plt.ion()
        plt.show()

    @classmethod
    def cli(cls, parser):
        pass  # keine CLI-Argumente notwendig

    def on_data(self, i: int, line: str):
        match = self.pattern.search(line)
        if not match:
            return

        mac, dist = match.groups()
        if mac == "0x0001":
            return  # 0x0001 ist der Initiator, keine Beacon

        if mac in self.beacon_positions:
            self.initiator_dists[mac].append(int(dist))

    def estimate_position(self):
        available = [mac for mac in self.beacon_positions if len(self.initiator_dists[mac]) > 0]
        if len(available) < 3:
            return None

        macs = available[:3]
        p1 = self.beacon_positions[macs[0]]
        d1 = self.initiator_dists[macs[0]][-1]

        A = []
        b = []

        for mac in macs[1:]:
            p2 = self.beacon_positions[mac]
            d2 = self.initiator_dists[mac][-1]

            xi, yi = p1
            xj, yj = p2

            A.append([2 * (xj - xi), 2 * (yj - yi)])
            b.append(d2**2 - d1**2 + xi**2 - xj**2 + yi**2 - yj**2)

        try:
            A = np.array(A)
            b = np.array(b)
            pos, *_ = np.linalg.lstsq(A, b, rcond=None)
            return pos
        except np.linalg.LinAlgError:
            return None

    def main(self):
        while True:
            pos = self.estimate_position()
            self.ax.clear()

            # Beacons zeichnen
            for mac, (x, y) in self.beacon_positions.items():
                self.ax.plot(x, y, 'ro')
                self.ax.text(x + 5, y + 5, mac, fontsize=8, color='red')

                if self.initiator_dists[mac]:
                    r = self.initiator_dists[mac][-1]
                    circle = patches.Circle((x, y), r, edgecolor='r', fill=False, linestyle='--', alpha=0.3)
                    self.ax.add_patch(circle)

            # Position des Initiators zeichnen
            if pos is not None:
                self.ax.plot(pos[0], pos[1], 'bo')
                self.ax.text(pos[0] + 5, pos[1] + 5, "INIT", fontsize=9, color='blue')
                print(f"Position: x={pos[0]:.1f} cm, y={pos[1]:.1f} cm")

            self.ax.set_xlim(-50, 250)
            self.ax.set_ylim(-50, 200)
            self.ax.set_aspect('equal')
            self.ax.set_title("Live UWB Triangulation")
            self.fig.canvas.draw_idle()
            self.fig.canvas.flush_events()
            time.sleep(0.5)  # Aktualisierung alle 0.5 Sekunden

    def post_process(self):
        pass