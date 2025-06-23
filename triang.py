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

ANCHOR_POSITIONS = {
    0x0002: np.array([0.0, 0.0]),        # rot
    0x0003: np.array([0.0, 250]),     # grün
    0x0004: np.array([-180.0, 90]),      # ohne
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
    (x1, y1), (x2, y2), (x3, y3) = anchors
    r1, r2, r3 = d
    A, B = 2*(x2 - x1), 2*(y2 - y1)
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D, E = 2*(x3 - x1), 2*(y3 - y1)
    F = r1**2 - r3**2 - x1**2 + x3**2 - y1**2 + y3**2
    denom = A*E - B*D
    if abs(denom) < 1e-6:
        return None
    x = (C*E - F*B) / denom
    y = (A*F - D*C) / denom
    return np.array([x, y])

# --------------------------------------------------------------------------- #
#  Plot-Objekt
# --------------------------------------------------------------------------- #
class LivePlot:
    def __init__(self):
        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self._setup_axes()
        self.trace = deque(maxlen=TRACE_LENGTH)
        (self.line,)  = self.ax.plot([], [], "b--", lw=1, alpha=0.6)
        (self.point,) = self.ax.plot([], [], "ro",  ms=8)

    def _setup_axes(self):
        for mac, pos in ANCHOR_POSITIONS.items():
            self.ax.scatter(*pos, marker="^", c="k", s=80, zorder=4)
            self.ax.text(pos[0]+3, pos[1]+3, f"{mac:04X}", fontsize=9)
        self.ax.set_xlim(-300, 300)
        self.ax.set_ylim(-300, 300)
        self.ax.set_aspect("equal", adjustable="box")
        self.ax.grid(True)
        self.ax.set_xlabel("x [cm]")
        self.ax.set_ylabel("y [cm]")
        self.ax.set_title("UWB – Initiator-Position")

    def update(self, pos: np.ndarray):
        self.trace.append(pos)
        pts = np.asarray(self.trace)
        if len(pts) > 1:
            self.line.set_data(pts[:, 0], pts[:, 1])
        self.point.set_data([pos[0]], [pos[1]])
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
                buf += data
                while "SESSION_INFO_NTF" in buf and "}" in buf:
                    start = buf.find("SESSION_INFO_NTF")
                    end   = buf.find("}", start)
                    if end == -1:
                        break
                    msg = buf[start:end+1]
                    buf = buf[end+1:]
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
                    logging.info("x=%6.1f cm   y=%6.1f cm", *pos)
                    plot.update(pos)
        except KeyboardInterrupt:
            logging.info("Abbruch – fahre herunter …")
        finally:
            running.clear()
            t.join(timeout=2)
            plt.ioff(); plt.show()

if __name__ == "__main__":
    main()