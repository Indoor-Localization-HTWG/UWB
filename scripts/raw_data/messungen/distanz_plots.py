from os import path
import statistics
import pandas as pd
import matplotlib.pyplot as plt

# key: distanz in cm
#messungen = {
#	200: "messung1.csv",
#	100: "messung7.csv",
#	50: "messung8.csv",
#	30: "messung9.csv",
#	20: "messung10.csv",
#	250: "messung11.csv",
#	300: "messung12.csv",
#	400: "messung13.csv",
#	2855: "messung14.csv"
#}
#

messungen = {
	200: "kalibriert/messung_2m_kalibriert.csv",
	400: "kalibriert/messung_4m_kalibriert.csv",
	2855: "kalibriert/messung_2855cm_kalibriert.csv",
}

daten = {}
for k, v in messungen.items():
	try:
		df = pd.read_csv(v)
		werte = df.iloc[:, 1]  # Nur zweite Spalte (gemessene Distanz)
		daten[k] = werte
	except Exception as e:
		print(f"Fehler beim Lesen von '{v}': {e}")

def strip():
	import seaborn as sns
	import matplotlib.pyplot as plt

	anzahl = len(sorted(daten.keys()))
	fig, axs = plt.subplots(1, anzahl, figsize=(2 * anzahl, 6), sharey=False)

	for ax, soll in zip(axs, sorted(daten.keys())):
		werte = daten[soll]
		sns.stripplot(y=werte, ax=ax, jitter=True, alpha=0.7)
		ax.set_title(f"{soll} cm")
		ax.set_xlabel("")  # unnötig bei vertikalem Plot
		ax.set_xticks([])
		ax.grid(True)
		
	axs[0].set_ylabel("Gemessene Distanz (cm)")
	plt.suptitle("Einzelmessungen pro Soll-Distanz", fontsize=16)
	plt.tight_layout(rect=[0, 0, 1, 0.95])
	plt.show()

def median_bar():
	x_labels = sorted(daten.keys())
	y_values = [statistics.median(daten[k]) for k in x_labels]
	x_positions = range(len(x_labels))

	# Zwei Subplots mit gemeinsamer X-Achse (gesplittete Y-Achse)
	fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6), gridspec_kw={'height_ratios': [1, 4]})

	# Grenzen für Achsen setzen (hier wird Y bei ~500 gebrochen)
	break_point = 500
	ax1.set_ylim(break_point, max(y_values) + 100)
	ax2.set_ylim(0, break_point)

	# Balken zeichnen
	ax1.bar(x_positions, y_values, width=0.6)
	ax1.set_yticks([x_labels[-1]])
	ax2.bar(x_positions, y_values, width=0.6)
	ax2.set_yticks(x_labels[:len(x_labels)-1])

	# X-Achse beschriften
	plt.xticks(ticks=x_positions, labels=x_labels, rotation=45)
	ax2.set_xlabel('Soll-Distanz (cm)')
	fig.supylabel('Gemessene Distanz (Mittelwert in cm)')  # über beide Subplots hinweg

	plt.suptitle('Mittelwert der Messdaten mit Y-Achsenbruch bei Ausreißern')
	plt.tight_layout()
	plt.grid(True, axis='y')
	plt.show()

#strip()
median_bar()
