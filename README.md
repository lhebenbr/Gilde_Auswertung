# 🏹 Gilde Auswertung

## 🔧 Setup

1. Stelle sicher, dass **Python** und **pip** installiert sind.
2. Installiere die benötigten Pakete:

   ```bash
   pip install -r requirements.txt
3. Lege die Export-XML-Datei im Verzeichnis export ab.
4. Starte das Skript aus dem Projektverzeichnis:
   ```bash
   python3 main.py
5. Die Auswertungsdatei auswertung_gesamt.csv sowie das Fehlerprotokoll fehler_auswertung.txt werden automatisch erstellt.

(Das Programm ist fehleranfällig da Bedingungen über Strings abgeglichen werden, bei Fehlerfällen wo z.B. nicht die Bedingung verglichen werden kann, muss händisch nachgebarbeitet werden)

Beschreibung:
Die Auswertung enthält:

    Name

    Vorname

    Bester Teiler (aus der Saison)

    Bester Score
    (beste Serie an einem Tag – jeder Score muss von einem anderen Tag stammen)

    Zweiter Score

    Dritter Score

    Anwesenheiten
    (Anzahl unterschiedlicher Schießtage – basierend auf Timestamps der Serien)

    Bedingung Erfüllt

        < 50 Jahre: BNEins, BNZwei, BNDrei

        ≥ 50 Jahre: SNEins, SNZwei, SNDrei

    Senioren Bedingung Erfüllt
    (ab 60 Jahren kann alternativ die Bedingung aus bedingungen_senioren.csv erfüllt werden – durch Erreichen einer bestimmten Ringzahl über mehrere Sitzungen)