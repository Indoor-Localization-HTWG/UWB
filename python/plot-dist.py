import time
import serial
import threading
import re
from clize import run
import serial.tools.list_ports

stop_event = threading.Event()

devices = []
ports = serial.tools.list_ports.comports()

for port in ports:
	if port.manufacturer == "Nordic Semiconductor":
		devices.append(port.device)

def start_serial(i: int, baud: int, timeout: int):
	print(f"[{i}] Serielle Verbindung geöffnet.")
	s = serial.Serial(devices[i], baudrate=baud, timeout=timeout)
	try:
		command = "INITF" if i == 0 else "RESPF"
		print(f"[{i}] Schicke Befehl: {command}")
		s.write(f"{command}\n".encode('utf-8'))
		time.sleep(0.5)
		while not stop_event.is_set():
			line = s.readline().decode('utf-8', errors='ignore').strip()
			if not line:
				continue
			print(f"[{i}]: {line}")
		print(f"[{i}] Stoppe Schnittstelle")
	except Exception as err:
		print(f"Fehler: {err}")
	finally:
		print(f"[{i}] Schicke Befehl: STOP")
		s.write(f"STOP\n".encode('utf-8'))
		time.sleep(0.5)
		s.close()

def plot(baud: int = 115200, timeout: int = 1):
	distance_pattern = re.compile(r'\[mac_address=(0x[0-9a-fA-F]+), status="SUCCESS", distance\[cm\]=(\d+)\]')

	print(f"[GLOBAL] UWB Geräte: {devices}")

	print("[GLOBAL] Starte Threads")
	threads: list[threading.Thread] = []
	for i in range(len(devices)):
		t = threading.Thread(target=start_serial, args=(i, baud, timeout))
		t.start()
		threads.append(t)
	
	try:
		for t in threads:
			t.join()
	except KeyboardInterrupt:
		print("[GLOBAL] Stoppe Threads")
		stop_event.set()
		for t in threads:
			t.join()

if __name__ == '__main__':
	run(plot)