import serial
import re
import time
import threading
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

clients = [
    {"name": "Client A", "port": "/dev/tty.usbmodemC208865F906F1", "command": "INITF -ADDR=1 -PADDR=2\n", "address": "0x0001", "position": (0, 0)},
    {"name": "Client B", "port": "/dev/tty.usbmodemFAD4A05A59E71", "command": "RESPF -ADDR=2 -PADDR=1\n", "address": "0x0002", "position": (100, 0)}
    #{"name": "Client C", "port": "/dev/tty.usbmodemXXXX3", "command": "RESPF -ADDR=3 -PADDR=1\n", "address": "0x0003", "position": (50, 100)},
]

BAUD_RATE = 115200
TIMEOUT = 1

distance_pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(\d+)\]')
measurement_lock = threading.Lock()
measurements = defaultdict(dict)  # {mac_address: {client_name: distance}}

client_positions = {client["name"]: client["position"] for client in clients}

def trilaterate(p1, r1, p2, r2, p3, r3):
    # https://en.wikipedia.org/wiki/Trilateration#Three_Circles
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    A = 2*(x2 - x1)
    B = 2*(y2 - y1)
    C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2

    D = 2*(x3 - x2)
    E = 2*(y3 - y2)
    F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

    denominator = A*E - B*D
    if abs(denominator) < 1e-6:
        return None  # Can't solve

    x = (C*E - F*B) / denominator
    y = (A*F - D*C) / denominator
    return (x, y)

def plot_position(mac_address, distances):
    # Holt Positionen & Distanzen
    positions = []
    radii = []
    for client_name, dist in distances.items():
        positions.append(client_positions[client_name])
        radii.append(dist)

    if len(positions) < 3:
        return

    pos = trilaterate(positions[0], radii[0], positions[1], radii[1], positions[2], radii[2])
    if not pos:
        print("⚠️ Keine eindeutige Lösung möglich.")
        return

    # Plotten
    plt.figure()
    for (x, y), r, client_name in zip(positions, radii, distances.keys()):
        circle = plt.Circle((x, y), r, color='b', fill=False, linestyle='--')
        plt.gca().add_patch(circle)
        plt.plot(x, y, 'bo')
        plt.text(x + 2, y + 2, client_name)

    plt.plot(pos[0], pos[1], 'ro')
    plt.text(pos[0] + 2, pos[1] + 2, f'{mac_address}\n({pos[0]:.1f}, {pos[1]:.1f})')
    plt.title(f"Triangulierte Position von {mac_address}")
    plt.axis("equal")
    plt.grid(True)
    plt.show()

def try_triangulate(mac_address):
    with measurement_lock:
        dists = measurements[mac_address]
        if len(dists) >= 3:
            print(f"\n📍 Trianguliere {mac_address}")
            for client, dist in dists.items():
                print(f"  - {client}: {dist} cm")
            plot_position(mac_address, dists)
            del measurements[mac_address]

def serial_client(client_info):
    try:
        ser = serial.Serial(client_info["port"], BAUD_RATE, timeout=TIMEOUT)
        print(f"[{client_info['name']}] Serielle Verbindung geöffnet.")
        ser.write(client_info["command"].encode('utf-8'))
        time.sleep(0.5)
        print(f"[{client_info['name']}] Starte Empfang...")

        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            print(f"[{client_info['name']}] {line}")
            match = distance_pattern.search(line)
            if match:
                mac_address, dist = match.groups()
                dist = int(dist)
                with measurement_lock:
                    measurements[mac_address][client_info["name"]] = dist
                try_triangulate(mac_address)

    except Exception as e:
        print(f"[{client_info['name']}] Fehler: {e}")
    finally:
        try:
            ser.close()
            print(f"[{client_info['name']}] Serielle Verbindung geschlossen.")
        except:
            pass

# Threads starten
threads = []
for client in clients:
    t = threading.Thread(target=serial_client, args=(client,))
    t.start()
    threads.append(t)

# Hauptthread wartet
try:
    for t in threads:
        t.join()
except KeyboardInterrupt:
    print("Beendet durch Benutzer.")