import csv
import matplotlib.pyplot as plt

# Pfade zu den CSV-Dateien mit den Soll-Distanzen
messungen = {
    200: "kalibriert/messung_2m_kalibriert.csv",
    400: "kalibriert/messung_4m_kalibriert.csv",
    2855: "kalibriert/messung_2855cm_kalibriert.csv",
}

abweichungen = {}

# CSVs einlesen und Abweichungen berechnen
for soll_distanz, pfad in messungen.items():
    distanz_werte = []

    with open(pfad, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                distanz = float(row["Distanz (cm)"])
                distanz_werte.append(distanz)
            except ValueError:
                continue  # Überspringe ungültige Werte

    if not distanz_werte:
        continue

    mittelwert = sum(distanz_werte) / len(distanz_werte)
    abweichung = mittelwert - soll_distanz
    abweichungen[soll_distanz] = (abweichung, distanz_werte)

# Subplots zeichnen
anzahl = len(abweichungen)
fig, axs = plt.subplots(anzahl, 1, figsize=(10, 5 * anzahl), constrained_layout=True)

if anzahl == 1:
    axs = [axs]  # Wenn nur ein Subplot, in Liste umwandeln

for idx, (soll, (abweichung, werte)) in enumerate(sorted(abweichungen.items())):
    ax = axs[idx]
    ax.hist(werte, bins=15, color='lightgreen', edgecolor='black')
    ax.axvline(soll, color='red', linestyle='--', label=f"Soll: {soll} cm")
    ax.axvline(sum(werte)/len(werte), color='blue', linestyle='-', label=f"Mittelwert: {sum(werte)/len(werte):.2f} cm")
    ax.set_title(f"Messung für Soll-Distanz: {soll} cm\nAbweichung: {abweichung:+.2f} cm", fontsize=14)
    ax.set_xlabel("Gemessene Distanz (cm)", fontsize=12)
    ax.set_ylabel("Anzahl", fontsize=12)
    ax.tick_params(axis='both', labelsize=10)
    ax.legend(fontsize=10)
    ax.grid(True)

plt.show()
