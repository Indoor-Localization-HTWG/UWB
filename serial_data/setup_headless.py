import threading
import time
import serial.tools.list_ports

BAUDRATE = 115200

serial_nrs = ["C208865F906F", "FAD4A05A59E7", "FA6D881A5AFC", "F07DD0297227"]
ports = serial.tools.list_ports.comports()
print(f"connected devices: {[port.serial_number for port in ports if port.serial_number]}")
devices = { port.serial_number: port.device for port in ports if port.serial_number in serial_nrs }
stop_event = threading.Event()

def send_command(ser: serial.Serial, cmd: str):
	ser.write(f"{cmd}\n".encode())
	time.sleep(0.1)
	print(f"OUTPUT: {ser.read_all().decode().strip()}")

def program_responder(serial_nr: str, id: int):
	if serial_nr not in devices:
		print(f"WARNING: Tried to program {serial_nr} as responder, but it's not connected")
		return
	
	print(f"INFO: Programming {serial_nr} as responder")
	with serial.Serial(devices[serial_nr], BAUDRATE, timeout=0.5) as ser:
		send_command(ser, "STOP")
		send_command(ser, "SETAPP RESPF")
		send_command(ser, f"RESPF -MULTI -ADDR={id} -PADDR=1")
		time.sleep(0.5)
		send_command(ser, "STOP")
		send_command(ser, "SAVE")

def program_initiator(serial_nr: str, n_responder: int):
	if serial_nr not in devices:
		print(f"WARNING: Tried to program {serial_nr} as initiator, but it's not connected")
		return

	print(f"INFO: Programming {serial_nr} as responder with {n_responder} responders")
	with serial.Serial(devices[serial_nr], BAUDRATE, timeout=0.5) as ser:
		send_command(ser, "STOP")
		send_command(ser, "SETAPP INITF")
		send_command(ser, f"INITF -MULTI -ADDR=1 -PADDR=[{','.join([str(a) for a in range(2, n_responder+2)])}]")
		time.sleep(0.5)
		send_command(ser, "STOP")
		send_command(ser, "SAVE")

responders = { 
	"FA6D881A5AFC": 2, # rot
	"C208865F906F": 3, # grün
	"FAD4A05A59E7": 4, # ohne
}

for serial_nr, id in responders.items():
	program_responder(serial_nr, id)

initiator = "F07DD0297227" # gelb
program_initiator(initiator, len(responders))
