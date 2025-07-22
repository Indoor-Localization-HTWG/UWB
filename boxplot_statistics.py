#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV-Reader für Boxplot-Statistiken
Berechnet Mittelwert, Median, Quartile und weitere Statistiken aus einer CSV-Datei.
"""
import csv
import numpy as np
import logging

# --------------------------------------------------------------------------- #
#  Konfiguration
# --------------------------------------------------------------------------- #
INPUT_FILE = "uwb_positions.csv"
OUTPUT_FILE = "boxplot_statistics.csv"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")

# --------------------------------------------------------------------------- #
#  Hilfsfunktionen
# --------------------------------------------------------------------------- #
def calculate_statistics(data: np.ndarray) -> dict:
    """Berechnet Statistiken für die gegebenen Daten."""
    return {
        "mean": np.mean(data),
        "median": np.median(data),
        "std_dev": np.std(data),
        "min": np.min(data),
        "max": np.max(data),
        "q1": np.percentile(data, 25),
        "q3": np.percentile(data, 75),
    }

# --------------------------------------------------------------------------- #
#  Hauptprogramm
# --------------------------------------------------------------------------- #
def main():
    try:
        # Daten aus CSV lesen
        logging.info("Lese Daten aus %s", INPUT_FILE)
        with open(INPUT_FILE, "r") as csvfile:
            csvreader = csv.reader(csvfile)
            header = next(csvreader)  # Überspringe Header
            data = np.array([list(map(float, row)) for row in csvreader])

        if data.size == 0:
            logging.error("Keine Daten in der Datei gefunden!")
            return

        # Statistiken berechnen
        logging.info("Berechne Statistiken ...")
        x_stats = calculate_statistics(data[:, 0])
        y_stats = calculate_statistics(data[:, 1])

        # Ergebnisse in eine neue CSV-Datei schreiben
        logging.info("Schreibe Statistiken in %s", OUTPUT_FILE)
        with open(OUTPUT_FILE, "w", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(["Statistik", "x [cm]", "y [cm]"])
            for stat in x_stats.keys():
                csvwriter.writerow([stat, x_stats[stat], y_stats[stat]])

        logging.info("Statistiken erfolgreich berechnet und gespeichert.")

    except Exception as e:
        logging.error("Fehler: %s", e)

if __name__ == "__main__":
    main()
