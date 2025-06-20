import serial
import time
from serial.tools import list_ports
import logging

BAUDRATE = 115200
TIMEOUT = 1

device_roles = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_uwb_devices():
    ports = list_ports.comports()
    return [port.device for port in ports if port.serial_number]

def open_serial(device):
    return serial.Serial(device, baudrate=BAUDRATE, timeout=TIMEOUT)

def read_all(ser):
    time.sleep(0.3)
    lines = []
    while ser.in_waiting:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            lines.append(line)
    return lines

def send_command(ser, cmd):
    logging.info(f"Sende Befehl: {cmd}")
    ser.write(f"{cmd}\n".encode())
    time.sleep(0.2)
    response = read_all(ser)
    for line in response:
        logging.info(f"Antwort: {line}")
    return response

def reset_to_none(ser):
    send_command(ser, "STOP")
    send_command(ser, "RESTORE")
    send_command(ser, "SAVE")

def setup_device(ser, role, addr, paddr, port, use_multi=False):
    reset_to_none(ser)
    send_command(ser, f"SETAPP {role}")
    send_command(ser, "SAVE")

    if role == "INITF":
        cmd = f"INITF -ADDR={addr} -PADDR={paddr}"
        if use_multi:
            cmd += " -MULTI"
    else:
        cmd = f"RESPF -ADDR={addr} -PADDR={paddr}"

    send_command(ser, cmd)

    device_roles.append({
        "port": port,
        "role": role,
        "addr": addr,
        "paddr": paddr,
        "multi": use_multi
    })

def print_summary():
    print("\n📋 Geräte-Konfiguration:")
    for d in device_roles:
        print(f"🔹 {d['port']}:")
        print(f"    Rolle:   {d['role']}")
        print(f"    ADDR:    {d['addr']}")
        print(f"    PADDR:   {d['paddr']}")
        print(f"    MULTI:   {'ja' if d['multi'] else 'nein'}")

def main():
    devices = sorted(find_uwb_devices())
    n = len(devices)

    if n < 2:
        print("❌ Mindestens 2 Geräte benötigt.")
        return

    serial_ports = [open_serial(dev) for dev in devices]

    try:
        if n >= 3:
            base_addr = 1
            initiator_addr = base_addr
            responder_addrs = list(range(base_addr + 1, base_addr + n))
            paddr_list = "[" + ",".join(map(str, responder_addrs)) + "]"
            setup_device(serial_ports[0], "INITF", initiator_addr, paddr_list, devices[0], use_multi=True)

            for i, addr in enumerate(responder_addrs, start=1):
                setup_device(serial_ports[i], "RESPF", addr, initiator_addr, devices[i])
        else:
            initiator_addr = 0
            responder_addr = 1
            setup_device(serial_ports[0], "INITF", initiator_addr, responder_addr, devices[0])
            setup_device(serial_ports[1], "RESPF", responder_addr, initiator_addr, devices[1])
    finally:
        for ser in serial_ports:
            ser.close()

    print_summary()

if __name__ == "__main__":
    main()