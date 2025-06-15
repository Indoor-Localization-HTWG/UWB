from collections import defaultdict
import re
import sys
import time
import statistics
import serial
import matplotlib.pyplot as plt
from .base_processor import UWBProcessor

class CalProcessor(UWBProcessor):
    name: str = "cal"
    help: str = "Kalibriert die Antennenverzögerung basierend auf gemessenen Distanzen"

    def __init__(self, args, stop_event=None):
        self.args = args
        self.stop_event = stop_event
        self.dists: dict[str, list] = defaultdict(list)
        self.pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(-?\d+)\]')
        self.start_time = None
        self.timeout = args.time
        self.target_distance = args.target
        self.current_delay = 0x4015  # Default delay value
        self.measurement_time = args.measure_time
        self.tolerance = args.tolerance
        self.serial_ports = {}
        self.calibration_history: list[tuple[int, float]] = []
        self.calibration_done = False

    @classmethod
    def cli(cls, parser) -> None:
        parser.add_argument("--time", type=int, default=0, help="Gesamtzeit für die Kalibrierung in Sekunden")
        parser.add_argument("--target", type=int, required=True, help="Zieldistanz in cm")
        parser.add_argument("--measure-time", type=int, default=10, help="Messzeit pro Iteration in Sekunden")
        parser.add_argument("--tolerance", type=int, default=5, help="Toleranz in cm")

    def on_data(self, i: int, line: str):
        if self.start_time is None:
            self.start_time = time.time()

        if self.timeout > 0 and time.time() - self.start_time > self.timeout:
            print("Kalibrierungszeit abgelaufen.")
            if self.stop_event:
                self.stop_event.set()
            sys.exit(0)

        match = self.pattern.match(line)
        if match:
            mac, dist = match.groups()
            if mac == "0x0001":
                return
            self.dists[mac].append(int(dist))
        print(line)

    def send_cal_command(self, device_index: int, delay_value: int):
        if device_index not in self.serial_ports:
            return

        print(f"[{device_index}] Stoppe aktuelle Anwendung...")
        self.serial_ports[device_index].write(b"stop\n")
        time.sleep(0.1)

        for ant in [0, 1]:
            command = f"calkey ant{ant}.ch9.ant_delay {delay_value}\n"
            print(f"[{device_index}] Sende Befehl: {command.strip()}")
            self.serial_ports[device_index].write(command.encode('utf-8'))
            time.sleep(0.1)

        if device_index == 0:
            restart_cmd = f"INITF -MULTI -ADDR=1 -PADDR=[{','.join(str(a) for a in range(2, len(self.serial_ports)+1))}]"
        else:
            restart_cmd = f"RESPF -MULTI -ADDR={device_index+1} -PADDR=1"

        print(f"[{device_index}] Starte Anwendung neu mit: {restart_cmd}")
        self.serial_ports[device_index].write(f"{restart_cmd}\n".encode('utf-8'))
        time.sleep(0.5)

    def set_serial_ports(self, ports: dict[int, serial.Serial]):
        self.serial_ports = ports

    def main(self):
        if not self.dists:
            return

        current_time = time.time()
        if current_time - self.start_time < self.measurement_time:
            return

        avg_distances = {mac: statistics.mean(dists) for mac, dists in self.dists.items()}
        all_within_tolerance = True

        for mac, avg_dist in avg_distances.items():
            error = avg_dist - self.target_distance
            self.calibration_history.append((self.current_delay, error))

            if abs(error) <= self.tolerance:
                print(f"Kalibrierung für {mac} erfolgreich! Durchschnittliche Distanz: {avg_dist}cm")
                continue
            else:
                all_within_tolerance = False

            if error > 0:
                self.current_delay += 1
            else:
                self.current_delay -= 1

            self.current_delay = max(0, min(self.current_delay, 0xFFFF))

            for device_index in range(len(self.serial_ports)):
                self.send_cal_command(device_index, self.current_delay)

        if all_within_tolerance:
            print("Kalibrierung erfolgreich abgeschlossen!")

            for device_index in range(len(self.serial_ports)):
                print(f"[{device_index}] Stoppe Anwendung...")
                self.serial_ports[device_index].write(b"stop\n")
                time.sleep(0.1)

            for device_index in range(len(self.serial_ports)):
                print(f"[{device_index}] Speichere Kalibrierung...")
                self.serial_ports[device_index].write(b"save\n")
                time.sleep(0.1)

            self.calibration_done = True
            if self.stop_event:
                self.stop_event.set()

        self.dists.clear()
        self.start_time = current_time

    def plot_results(self):
        if not self.calibration_history:
            return

        delays, errors = zip(*self.calibration_history)

        plt.figure(figsize=(8, 5))
        plt.plot(delays, errors, marker='o')
        plt.axhline(0, color='gray', linestyle='--')
        plt.title("Kalibrierungsverlauf")
        plt.xlabel("Antenna Delay (dezimal)")
        plt.ylabel("Fehler zur Zieldistanz (cm)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def post_process(self):
        if not self.dists:
            print("Keine Daten vorhanden.")
        else:
            print("\nFinale Kalibrierungsergebnisse:")
            for mac, dists in self.dists.items():
                avg = statistics.mean(dists)
                std = statistics.stdev(dists) if len(dists) > 1 else 0
                print(f"{mac}: Durchschnitt = {avg:.2f}cm, Standardabweichung = {std:.2f}cm")

        if self.calibration_done:
            self.plot_results()
            sys.exit(0)