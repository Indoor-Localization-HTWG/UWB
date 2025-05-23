import csv
import statistics
from collections import defaultdict

def lese_csv_datei(pfad):
    daten = defaultdict(list)
    
    with open(pfad, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for zeile in reader:
            mac = zeile["MAC-Adresse"]
            dist = int(zeile["Distanz (cm)"])
            daten[mac].append(dist)
    
    return daten

def berechne_statistiken(daten):
    for mac, dists in daten.items():
        print(f"\nStatistik für {mac}:")
        print(f"Anzahl Werte      : {len(dists)}")
        print(f"Minimum           : {min(dists)} cm")
        print(f"Maximum           : {max(dists)} cm")
        print(f"Mittelwert        : {statistics.mean(dists):.2f} cm")
        print(f"Median            : {statistics.median(dists)} cm")
        if len(dists) > 1:
            print(f"Varianz           : {statistics.variance(dists):.2f}")
            print(f"Standardabweichung: {statistics.stdev(dists):.2f}")
        if len(dists) >= 4:
            q1, q2, q3 = statistics.quantiles(dists, n=4)
            print(f"1. Quartil (Q1)   : {q1}")
            print(f"3. Quartil (Q3)   : {q3}")

if __name__ == "__main__":
    daten = lese_csv_datei("messungen/messung5.csv")
    berechne_statistiken(daten)
