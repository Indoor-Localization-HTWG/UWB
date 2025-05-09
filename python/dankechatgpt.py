import serial
import re
import time
import threading

# Konfiguration für beide Ports
clients = [
    {
        "name": "Client A",
        "port": "/dev/tty.usbmodemFAD4A05A59E71",
        "command": "INITF -ADDR=1 -PADDR=2\n",
    },
    {
        "name": "Client B",
        "port": "/dev/tty.usbmodemC208865F906F1",
        "command": "RESPF -ADDR=2 -PADDR=1\n",
    }
]

BAUD_RATE = 9600
TIMEOUT = 1  # Sekunden
regex = re.compile(r'.*')  # Optional anpassen


def serial_client(client_info):
    try:
        ser = serial.Serial(client_info["port"], BAUD_RATE, timeout=TIMEOUT)
        print(f"[{client_info['name']}] Serielle Verbindung geöffnet.")

        # Befehl senden
        ser.write(client_info["command"].encode('utf-8'))
        print(f"[{client_info['name']}] Befehl gesendet: {client_info['command'].strip()}")

        # Kurze Pause
        time.sleep(0.5)

        print(f"[{client_info['name']}] Starte Empfang...")
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                match = regex.match(line)
                if match:
                    print(f"[{client_info['name']}] {line}")

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

# Hauptthread wartet auf Unterthreads
try:
    for t in threads:
        t.join()
except KeyboardInterrupt:
    print("Beendet durch Benutzer.")