#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UWB-Initiator – Live-Trilateration & Plot
läuft stabil mit PySerial ≥ 3.5 und Matplotlib ≥ 3.8
"""
import serial.tools.list_ports as slp
import serial, re, time, signal, sys, threading, logging
from queue import Queue, Empty
from collections import deque
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------- #
#  Konfiguration
# --------------------------------------------------------------------------- #
SERIAL_NUMBERS = {
    "C208865F906F",
    "FAD4A05A59E7",
    "FA6D881A5AFC",
    "F07DD0297227",
}

# x, y, z Koordinaten der Anker
# Diese Werte sollten an die tatsächlichen Positionen der Anker angepasst werden.

ANCHOR_POSITIONS = {
    0x0002: np.array([0.0, 0.0, 0.0]),        # rot
    0x0003: np.array([-100, -180, 80]),     # grün
    0x0004: np.array([220, -85, -80]),      # ohne
}

BAUDRATE       = 115_200
READ_TIMEOUT   = 0.05          # s
TRACE_LENGTH   = 50            # vergangene Punkte im Plot

DIST_RE = re.compile(
    r"\[mac_address=0x([0-9a-fA-F]+),\s*status=\"SUCCESS\",\s*distance\[cm\]=(\d+)\]"
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")

# --------------------------------------------------------------------------- #
#  Hilfsfunktionen
# --------------------------------------------------------------------------- #
def find_initiator_port() -> str:
    for port in slp.comports():
        if (port.serial_number or "").upper() in SERIAL_NUMBERS:
            logging.info("Serielles Gerät gefunden: %s  (SN=%s)", port.device,
                         port.serial_number)
            return port.device
    raise RuntimeError("Kein bekanntes UWB-Modul eingesteckt!")

def parse_distances(msg: str) -> dict[int, float] | None:
    matches = DIST_RE.findall(msg)
    if len(matches) < 3:
        return None
    return {int(mac, 16): float(dist) for mac, dist in matches}

def trilateration(anchors: list[np.ndarray], d: list[float]) -> np.ndarray | None:
    # Überprüfen, ob genau drei Anker und Distanzen übergeben wurden
    if len(anchors) != 3 or len(d) != 3:
        logging.warning("Trilateration braucht genau 3 Anker und Distanzen.")
        return None

    # Ankerpositionen und Distanzen extrahieren
    P1, P2, P3 = anchors
    r1, r2, r3 = d

    # Berechnung des Einheitsvektors zwischen Anker 1 und Anker 2
    ex = P2 - P1
    distance = np.linalg.norm(ex)  # Abstand zwischen Anker 1 und Anker 2
    if distance == 0:
        logging.warning("Anker 1 und 2 sind identisch.")
        return None
    ex /= distance  # Normalisierung des Vektors

    # Berechnung des zweiten Einheitsvektors basierend auf Anker 3
    temp = P3 - P1
    i = np.dot(ex, temp)  # Projektion von temp auf ex
    temp2 = temp - i * ex  # Orthogonale Komponente von temp zu ex
    temp2_norm = np.linalg.norm(temp2)  # Norm der orthogonalen Komponente
    if temp2_norm == 0:
        logging.warning("Anker 3 liegt auf Linie zwischen Anker 1 und 2.")
        return None
    ey = temp2 / temp2_norm  # Normalisierung des zweiten Einheitsvektors
    ez = np.cross(ex, ey)  # Berechnung des dritten Einheitsvektors durch Kreuzprodukt

    # Berechnung der Koordinaten x und y
    j = np.dot(ey, temp)  # Projektion von temp auf ey
    x = (r1**2 - r2**2 + distance**2) / (2 * distance)  # x-Koordinate
    y = (r1**2 - r3**2 + i**2 + j**2 - 2 * i * x) / (2 * j)  # y-Koordinate

    # Berechnung der z-Koordinate
    z_squared = r1**2 - x**2 - y**2  # Quadrat der z-Koordinate
    if z_squared < 0:
        logging.warning("z_Wert negativ – Trilateration nicht möglich.")
        logging.info("x=%f, y=%f, z^2=%f", x, y, z_squared)
        return None
    else:
        z = np.sqrt(z_squared)  # z-Koordinate

    # Berechnung der zwei möglichen Lösungen
    result_1 = P1 + x * ex + y * ey + z * ez  # Lösung 1
    result_2 = P1 + x * ex + y * ey - z * ez  # Lösung 2

    # Rückgabe der Lösung mit dem niedrigeren z-Wert (näher am Boden)
    return result_1 if result_1[2] < result_2[2] else result_2

# --------------------------------------------------------------------------- #
#  Plot-Objekt
# --------------------------------------------------------------------------- #
class LivePlot:
    def __init__(self):
        plt.ion()
        self.fig = plt.figure(figsize=(8, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self._setup_axes()
        self.trace = deque(maxlen=TRACE_LENGTH)
        self.line, = self.ax.plot([], [], [], "b--", lw=1, alpha=0.6)
        self.point, = self.ax.plot([], [], [], "ro", ms=8)

    def _setup_axes(self):
        # Berechne die Grenzen basierend auf den Ankerpositionen
        x_coords = [pos[0] for pos in ANCHOR_POSITIONS.values()]
        y_coords = [pos[1] for pos in ANCHOR_POSITIONS.values()]
        z_coords = [pos[2] for pos in ANCHOR_POSITIONS.values()]

        x_min, x_max = min(x_coords) - 50, max(x_coords) + 50
        y_min, y_max = min(y_coords) - 50, max(y_coords) + 50
        z_min, z_max = min(z_coords) - 50, max(z_coords) + 50

        for mac, pos in ANCHOR_POSITIONS.items():
            self.ax.scatter(*pos, marker="^", c="k", s=80, zorder=4)
            self.ax.text(pos[0]+3, pos[1]+3, pos[2]+3, f"{mac:04X}", fontsize=9)

        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_zlim(z_min, z_max)
        self.ax.set_xlabel("x [cm]")
        self.ax.set_ylabel("y [cm]")
        self.ax.set_zlabel("z [cm]")
        self.ax.set_title("UWB – Initiator-Position")

    def update(self, pos: np.ndarray):
        self.trace.append(pos)
        pts = np.asarray(self.trace)
        if len(pts) > 1:
            self.line.set_data(pts[:, 0], pts[:, 1])
            self.line.set_3d_properties(pts[:, 2])
        self.point.set_data([pos[0]], [pos[1]])
        self.point.set_3d_properties([pos[2]])
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

# --------------------------------------------------------------------------- #
#  Reader-Thread
# --------------------------------------------------------------------------- #
def reader_thread(ser: serial.Serial, q: Queue, running: threading.Event):
    buf = ""
    while running.is_set():
        try:
            data = ser.read(ser.in_waiting or 1).decode(errors="ignore")
            if data:
                logging.debug("Empfangene Daten: %s", data)
                buf += data
                while "SESSION_INFO_NTF" in buf and "}" in buf:
                    start = buf.find("SESSION_INFO_NTF")
                    end   = buf.find("}", start)
                    if end == -1:
                        break
                    msg = buf[start:end+1]
                    buf = buf[end+1:]
                    logging.debug("Verarbeitete Nachricht: %s", msg)
                    q.put(msg.replace("\n", " "))
            else:
                time.sleep(READ_TIMEOUT)
        except serial.SerialException as e:
            logging.warning("Serielle Ausnahme: %s – versuche weiter …", e)
            time.sleep(1)

# --------------------------------------------------------------------------- #
#  Hauptprogramm
# --------------------------------------------------------------------------- #
def main():
    try:
        port = find_initiator_port()
    except RuntimeError as e:
        logging.error(e)
        sys.exit(1)

    with serial.Serial(port, BAUDRATE, timeout=READ_TIMEOUT) as ser:
        running = threading.Event(); running.set()
        q: Queue[str] = Queue()
        t = threading.Thread(target=reader_thread, args=(ser, q, running),
                             daemon=True)
        t.start()

        plot = LivePlot()
        try:
            while running.is_set():
                try:
                    msg = q.get(timeout=0.2)
                except Empty:
                    continue
                dists = parse_distances(msg)
                if not dists or len(dists) < 3:
                    continue
                macs = sorted(m for m in dists if m in ANCHOR_POSITIONS)[:3]
                if len(macs) < 3:
                    continue
                anchors   = [ANCHOR_POSITIONS[m] for m in macs]
                distances = [dists[m] for m in macs]
                pos = trilateration(anchors, distances)
                if pos is not None:
                    logging.info("x=%6.1f cm   y=%6.1f cm   z=%6.1f cm", pos[0], pos[1], pos[2])
                    plot.update(pos)
        except KeyboardInterrupt:
            logging.info("Abbruch – fahre herunter …")
        finally:
            running.clear()
            t.join(timeout=2)
            plt.ioff(); plt.show()

if __name__ == "__main__":
    main()