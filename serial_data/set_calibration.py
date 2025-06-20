import serial
import time
import re
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Kalibrierungswerte an das Gerät senden."
    )
    parser.add_argument(
        "--port", "-p", required=True,
        help="Name des seriellen Ports (z. B. COM3 oder /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--file", "-f", default="calibration.cal",
        help="Pfad zur Kalibrierungsdatei (Standard: calibration.cal)"
    )
    parser.add_argument(
        "--baudrate", "-b", type=int, default=115200,
        help="Baudrate für die serielle Verbindung (Standard: 115200)"
    )
    return parser.parse_args()

def parse_calibration_file(filepath):
    commands = []
    with open(filepath, "r") as file:
        for line in file:
            if match := re.match(r"^([a-zA-Z0-9_.]+):\s+0x([0-9a-fA-F]+)", line.strip()):
                key, hex_value = match.groups()
                commands.append((key, hex_value))
    return commands

def send_calkey_command(ser, key, value):
    command = f"calkey {key} {value}\r\n"
    ser.write(command.encode("utf-8"))
    time.sleep(0.1)
    response = ser.read_all().decode("utf-8", errors="ignore")
    print(f"> {command.strip()}")
    print(response.strip())

def main():
    args = parse_args()

    commands = parse_calibration_file(args.file)

    with serial.Serial(args.port, args.baudrate, timeout=0.5) as ser:
        print(f"[INFO] Verbunden mit {args.port} @ {args.baudrate} Baud")

        # Gerät anhalten, um calkey zu nutzen
        ser.write(b"stop\r\n")
        time.sleep(0.2)
        ser.read_all()

        for key, value in commands:
            send_calkey_command(ser, key, value)

        ser.write(b"save\r\n")
        time.sleep(0.2)
        print(ser.read_all().decode("utf-8", errors="ignore"))

if __name__ == "__main__":
    main()
