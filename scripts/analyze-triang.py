import re
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="Berechne Mittelwerte und Abweichungen aus 3D-Koordinaten.")
parser.add_argument("dateipfad", type=str, help="Pfad zur Datei mit den Logdaten")
parser.add_argument("--soll", type=float, nargs=3, metavar=('X', 'Y', 'Z'), default=[180.0, 85.0, -80.0],
                    help="Sollwerte für x, y und z (Standard: 180, 85, -80)")

args = parser.parse_args()

with open(args.dateipfad, "r") as file:
    log_data = file.read()

# Alle Koordinaten extrahieren
pattern = r"x=\s*(-?\d+\.?\d*)\s*cm\s*y=\s*(-?\d+\.?\d*)\s*cm\s*z=\s*(-?\d+\.?\d*)\s*cm"
matches = re.findall(pattern, log_data)

# In NumPy-Arrays umwandeln
data = np.array(matches, dtype=np.float32)
x_vals, y_vals, z_vals = data[:, 0], data[:, 1], data[:, 2]

# Mittelwerte berechnen
mean_x = np.mean(x_vals)
mean_y = np.mean(y_vals)
mean_z = np.mean(z_vals)

# Ausgabe
print(f"Mittelwerte:")
print(f"x̄ = {mean_x:.2f} cm")
print(f"ȳ = {mean_y:.2f} cm")
print(f"z̄ = {mean_z:.2f} cm\n")

soll_x, soll_y, soll_z = args.soll
abw_x, abw_y, abw_z = abs(mean_x - soll_x), abs(mean_y - soll_y), abs(mean_z - soll_z)
print(f"Abweichungen:")
print(f"x = {abw_x:.2f} cm")
print(f"y = {abw_y:.2f} cm")
print(f"z = {abw_z:.2f} cm\n")