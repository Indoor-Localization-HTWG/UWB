import argparse
import time
import serial
import threading
import serial.tools.list_ports

serial_nrs = ["C208865F906F", "FAD4A05A59E7", "FA6D881A5AFC", "F07DD0297227"]
ports = serial.tools.list_ports.comports()
print([port.serial_number for port in ports if port.serial_number])
devices = [port.device for port in ports if port.serial_number in serial_nrs]
stop_event = threading.Event()

from processing import *

def get_processors() -> list[UWBProcessor]:
	return [PlotDistProcessor, LogProcessor, StatDistProcessor, TriangulationProcessor]

def start(command: str | None, baud: int = 115200, timeout: int = 1):
	threads = start_threads(command, baud, timeout)

	try:
		while any(t.is_alive() for t in threads) and not stop_event.is_set():
			processor.main()
	except KeyboardInterrupt:
		print("[GLOBAL] Stoppe Threads")
		stop_event.set()
		for t in threads:
			t.join()
	finally:
		processor.post_process()


def start_threads(cmd: str, baud: int, timeout: int) -> list[threading.Thread]:
	print(f"[GLOBAL] UWB Geräte: {devices}")
	if len(devices) == 0:
		print(f"[GLOBAL] Keine UWB Geräte erkannt. Abbruch.")
		return

	print("[GLOBAL] Starte Threads")
	threads: list[threading.Thread] = []
	for i in range(len(devices)):
		t = threading.Thread(target=start_serial, args=(cmd, i, baud, timeout))
		t.start()
		threads.append(t)

	return threads

def start_serial(cmd: str | None, i: int, baud: int, timeout: int):
	print(f"[{i}] Serielle Verbindung geöffnet.")
	s = serial.Serial(devices[i], baudrate=baud, timeout=timeout)
	time.sleep(args.delay)
	try:
		if (cmd == None):
			init_command = f"INITF -MULTI -ADDR=1 -PADDR=[{','.join([str(a) for a in range(2, len(devices)+1)])}] -CHAN={args.channel}"
			resp_command = f"RESPF -MULTI -ADDR={i+1} -PADDR=1 -CHAN={args.channel}"
			command = init_command if i == 0 else resp_command
		else:
			command = cmd
		print(f"[{i}] Schicke Befehl: {command}")
		s.write(f"{command}\n".encode('utf-8'))
		time.sleep(args.delay)
		while not stop_event.is_set():
			line = s.readline().decode('utf-8', errors='ignore').strip()
			if not line:
				continue

			processor.on_data(i, line)
		print(f"[{i}] Stoppe Schnittstelle")
	except Exception as err:
		print(f"[{i}] Fehler: {err}")
	finally:
		print(f"[{i}] Schicke Befehl: STOP")
		s.write(f"STOP\n".encode('utf-8'))
		time.sleep(args.delay)
		s.close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--baud', type=int, default=115200)
	parser.add_argument('--timeout', type=int, default=1)
	parser.add_argument("--cmd", type=str, default=None, help="Fester command der auf allen Modulen ausgeführt wird")
	parser.add_argument("--delay", type=float, default=0.5)
	parser.add_argument("--channel", type=int, default=9, choices=[5, 9], help="Kanal (5 oder 9, default: 9)")
	parser.add_argument("--remote-responders", type=str, default=None, help="Liste der Responder. Benutze diese Option wenn du nur ein Initator Modul angeschlossen hast. Beispiel: '[2,3,4]'")

	subparsers = parser.add_subparsers(title="processor", dest="command", required=True)

	for proc_cls in get_processors():
		proc_cls.add_cli(subparsers)

	args = parser.parse_args()
	processor: UWBProcessor = args.processor_class(args)

	try:
		if args.cmd:
			command = args.cmd
		else:
			command = f"INITF -MULTI -ADDR=1 -PADDR={args.remote_responders}"
		start(command=command, baud=args.baud, timeout=args.timeout)
	except KeyboardInterrupt:
		print("[GLOBAL] Tastaturabbruch erkannt")
		stop_event.set()