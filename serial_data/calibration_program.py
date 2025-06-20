import re
import sys
import time
import serial
import threading
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict
from serial.tools import list_ports

# Konfiguration
serial_nrs = ["C208865F906F", "FAD4A05A59E7", "FA6D881A5AFC", "F07DD0297227"]
ports = serial.tools.list_ports.comports()
print([port.serial_number for port in ports if port.serial_number])
BAUDRATE = 115200
TIMEOUT = 1
TARGET_DISTANCE_CM = 150
TOLERANCE_CM = 1
MEASURE_TIME_PER_ITERATION = 10
INITIAL_DELAY = 0x4015

# Globale Variablen
stop_event = threading.Event()
serial_ports = {}
dists = defaultdict(list)
current_delay = INITIAL_DELAY
calibration_history = []

pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')

def detect_devices():
    ports = list_ports.comports()
    matched = [(port.device, port.serial_number) for port in ports if port.serial_number in SERIAL_NRS]
    if not matched:
        print("❌ Keine bekannten UWB-Geräte gefunden.")
        sys.exit(1)
    print("🔌 Gefundene UWB-Geräte:")
    for dev, sn in matched:
        print(f" - {dev} (Serial: {sn})")
    return [dev for dev, _ in matched]

def send_cal_command(delay_value: int):
    for device_index, ser in serial_ports.items():
        ser.write(b"stop\n")
        time.sleep(0.1)
        for ant in [0, 1, 2, 3]:
            command = f"calkey ant{ant}.ch9.ant_delay {delay_value}\n"
            print(f"[{device_index}] {command.strip()}")
            ser.write(command.encode())
            time.sleep(0.1)
        if device_index == 0:
            cmd = f"INITF -ADDR=1 -PADDR=2"
        else:
            cmd = f"RESPF -ADDR={device_index + 1} -PADDR=1"
        ser.write(f"{cmd}\n".encode())
        time.sleep(0.5)

def read_serial(i: int, port: str):
    ser = serial.Serial(port, baudrate=BAUDRATE, timeout=TIMEOUT)
    serial_ports[i] = ser

    time.sleep(0.5)
    while not stop_event.is_set():
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        print(line)
        match = pattern.match(line)
        if match:
            mac, dist = match.groups()
            if mac != "0x0001":
                dists[mac].append(int(dist))

    ser.write(b"stop\n")
    time.sleep(0.1)
    ser.close()

def calibrate():
    global current_delay
    start_time = time.time()

    step = 100

    while not stop_event.is_set():
        time.sleep(1)
        if time.time() - start_time < MEASURE_TIME_PER_ITERATION:
            continue

        if not dists:
            continue

        avg_distances = {mac: statistics.mean(values) for mac, values in dists.items()}
        all_within_tolerance = True

        for mac, avg_dist in avg_distances.items():
            error = avg_dist - TARGET_DISTANCE_CM
            calibration_history.append((current_delay, error))
            print(f"[{mac}] AVG={avg_dist:.2f} cm, ERROR={error:.2f} cm")

            if abs(error) > TOLERANCE_CM:
                all_within_tolerance = False

                # Richtung des Fehlers bestimmen
                direction = -1 if error < 0 else 1

                # Anpassung der Delay-Werte mit Schrittgröße
                current_delay += direction * step
                current_delay = max(0, min(current_delay, 0xFFFF))

                send_cal_command(current_delay)

        if all_within_tolerance:
            print("✅ Kalibrierung abgeschlossen.")
            for ser in serial_ports.values():
                ser.write(b"stop\n")
                time.sleep(0.1)
                ser.write(b"save\n")
                time.sleep(0.1)
            stop_event.set()
            break

        # Schrittweite halbieren für feinere Korrektur
        step = max(1, step // 2)

        dists.clear()
        start_time = time.time()

def plot_results():
    if not calibration_history:
        return

    # Sortiere nach Delay-Wert (x-Achse)
    sorted_history = sorted(calibration_history, key=lambda x: x[0])
    delays, errors = zip(*sorted_history)

    plt.figure(figsize=(8, 5))
    plt.plot(delays, errors, marker='o', linestyle='-')  # Linie verbindet sortierte Punkte
    plt.axhline(0, color='gray', linestyle='--')
    plt.title("Kalibrierungsverlauf")
    plt.xlabel("Antenna Delay (dezimal)")
    plt.ylabel("Fehler zur Zieldistanz (cm)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    devices = [port.device for port in ports if port.serial_number in serial_nrs]

    # Ports öffnen und in serial_ports speichern
    for i, port in enumerate(devices):
        ser = serial.Serial(port, baudrate=BAUDRATE, timeout=TIMEOUT)
        serial_ports[i] = ser

    # Jetzt initialen Delay setzen – Ports sind offen
    print("⚙️ Setze initialen Delay...")
    send_cal_command(INITIAL_DELAY)

    # Jetzt Threads starten
    threads = []
    for i, port in enumerate(devices):
        t = threading.Thread(target=read_serial, args=(i, port))
        t.start()
        threads.append(t)

    try:
        calibrate()
    except KeyboardInterrupt:
        print("Abbruch durch Benutzer.")
        stop_event.set()
    finally:
        for t in threads:
            t.join()
        plot_results()
        sys.exit(0)