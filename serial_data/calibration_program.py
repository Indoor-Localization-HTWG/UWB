import time
import serial.tools.list_ports
import re
import signal
import sys
import threading
import argparse
from statistics import mean
import matplotlib.pyplot as plt

SERIAL_NUMBERS = ["C208865F906F", "FAD4A05A59E7", "FA6D881A5AFC", "F07DD0297227"]
ADDRS = [0x001, 0x002]

ser1 = None
ser2 = None
running = True
distance_values = []
distance_lock = threading.Lock()

def find_devices():
    ports = serial.tools.list_ports.comports()
    return {p.serial_number: p.device for p in ports if p.serial_number in SERIAL_NUMBERS}

def send_command(ser, cmd, delay=0.5):
    try:
        if cmd.strip() != "":
            print(f"[→] {ser.label}: {cmd}")
        ser.write((cmd + '\r\n').encode())
        time.sleep(delay)
        return ser.read_all().decode(errors='ignore')
    except Exception as e:
        return f"[ERROR] {e}"

def set_calkey(ser, ant, delay_value, channel):
    send_command(ser, f"CALKEY ant{ant}.ch{channel}.ant_delay {delay_value}", 1)

def graceful_exit(sig=None, frame=None):
    global running
    print("\n[!] Abbruch erkannt. Sende STOP an Geräte ...")
    running = False
    if ser1:
        send_command(ser1, "STOP")
    if ser2:
        send_command(ser2, "STOP")
    sys.exit(0)

def serial_logger(ser):
    pattern = re.compile(r'distance\[cm\]=(\d+)')
    while running:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"[{ser.label}] {line}")
                match = pattern.search(line)
                if match:
                    dist = int(match.group(1))
                    with distance_lock:
                        distance_values.append(dist)
        except Exception:
            pass

def plot_calibration_curve(delays, errors, final_delay, final_error):
    data = sorted(zip(delays, errors))
    delays_sorted, errors_sorted = zip(*data)

    plt.figure(figsize=(10, 5))
    plt.plot(delays_sorted, errors_sorted, marker='o', label='Messfehler')

    plt.scatter(final_delay, final_error, color='red', zorder=5, label='Finaler Wert')

    plt.title("Kalibrierfehler vs. Antennen-Delay")
    plt.xlabel("ant_delay")
    plt.ylabel("Fehler [cm]")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def calibrate_pair(initiator, responder, target_dist, duration, fixed_delay, tolerance, channel, plot):
    iteration = 1
    current_delay = fixed_delay
    delay_history = []
    error_history = []

    send_command(initiator, "\n")
    send_command(responder, "\n")
    send_command(initiator, "STOP")
    send_command(responder, "STOP")
    time.sleep(2)

    send_command(initiator, "RESTORE")
    send_command(responder, "RESTORE")

    for ant in range(4):
        set_calkey(responder, ant, fixed_delay, channel)
    send_command(responder, "SAVE")

    while True:
        print(f"\n=== Kalibrier-Durchlauf {iteration} ===")
        with distance_lock:
            distance_values.clear()

        send_command(responder, f"RESPF -ADDR={ADDRS[1]} -PADDR={ADDRS[0]} -CHAN={channel}")
        send_command(initiator, f"INITF -ADDR={ADDRS[0]} -PADDR={ADDRS[1]} -CHAN={channel}")

        print(f"[*] Messe für {duration} Sekunden ...")
        time.sleep(duration)

        send_command(initiator, "STOP")
        send_command(responder, "STOP")

        with distance_lock:
            distances = distance_values.copy()

        if not distances:
            print("Keine gültigen Messdaten empfangen.")
            return

        avg = mean(distances)
        error = avg - target_dist
        delay_history.append(current_delay)
        error_history.append(error)

        print(f"[=] Gemessener Abstand: {avg:.1f} cm")
        print(f"[=] Fehler: {error:.1f} cm (Erlaubt: ±{tolerance} cm)")

        if abs(error) <= tolerance:
            print("[✓] Kalibrierung abgeschlossen – Fehler innerhalb der Toleranz.")
            print(f"    ↪ Durchschnitt: {avg:.1f} cm")
            print(f"    ↪ Fehler: {error:.1f} cm")
            print(f"    ↪ Finaler ant_delay am Responder: {current_delay} (0x{current_delay:04X})")

            if plot:
                plot_calibration_curve(delay_history, error_history, current_delay, error)
            return

        delta = round(2 * error)
        delta = max(-100, min(100, delta))
        current_delay += delta

        print(f"[~] Wende Korrektur an: delta={delta}, neuer Responder-Delay={current_delay} (0x{current_delay:04X})")

        for ant in range(4):
            set_calkey(responder, ant, current_delay, channel)
        send_command(responder, "SAVE")

        iteration += 1

def main():
    global ser1, ser2
    signal.signal(signal.SIGINT, graceful_exit)

    parser = argparse.ArgumentParser(description="UWB Kalibrierung per Serial")
    parser.add_argument("--initiator", required=True, help="Seriennummer des Geräts, das Initiator ist")
    parser.add_argument("--dist", type=int, default=200, help="Zielabstand in cm (default: 200)")
    parser.add_argument("--duration", type=int, default=10, help="Messdauer in Sekunden (default: 10)")
    parser.add_argument("--fixed_delay", type=lambda x: int(x, 0), default=0x4015, help="Fester Delay-Wert für Initiator (default: 0x4015)")
    parser.add_argument("--tolerance", type=float, default=2.0, help="Toleranzbereich in cm (default: ±2.0)")
    parser.add_argument("--channel", type=int, default=9, choices=[5, 9], help="Kanal (5 oder 9) für Kalibrierung (default: 9)")
    parser.add_argument("--plot", action="store_true", help="Zeige Plot der Kalibrierwerte")

    args = parser.parse_args()

    devices = find_devices()
    if args.initiator not in devices:
        print(f"[!] Initiator mit Seriennummer {args.initiator} nicht gefunden.")
        return

    other_devices = [sn for sn in devices if sn != args.initiator]
    if not other_devices:
        print("Kein zweites Gerät für Responder gefunden.")
        return

    initiator_port = devices[args.initiator]
    responder_port = devices[other_devices[0]]

    ser1 = serial.Serial(initiator_port, baudrate=115200, timeout=0.2)
    ser2 = serial.Serial(responder_port, baudrate=115200, timeout=0.2)
    ser1.label = "INIT"
    ser2.label = "RESP"

    threading.Thread(target=serial_logger, args=(ser1,), daemon=True).start()
    threading.Thread(target=serial_logger, args=(ser2,), daemon=True).start()

    with ser1, ser2:
        calibrate_pair(
            ser1, ser2,
            args.dist,
            args.duration,
            args.fixed_delay,
            args.tolerance,
            args.channel,
            args.plot
        )

if __name__ == "__main__":
    main()