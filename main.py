import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# ========== KONSTANTEN ==========
EXPORT_DIR = "export"
FEHLER_DATEI = "fehler_auswertung.txt"
AUSWERTUNG_DATEI = "auswertung_gesamt.csv"
HEUTIGES_JAHR = datetime.now().year

# ========== HILFSFUNKTIONEN ==========
def format_datum(iso_str):
    return datetime.strptime(iso_str, "%Y%m%d").strftime("%d/%m/%Y")

def finde_xml_datei(verzeichnis):
    """
    Finds the newest XML file in the specified directory.
    """
    xml_files = [os.path.join(verzeichnis, f) for f in os.listdir(verzeichnis) if f.endswith(".xml")]
    if not xml_files:
        raise FileNotFoundError(f"Keine XML-Datei im '{verzeichnis}'-Ordner gefunden!")

    # Get the newest file based on modification time
    newest_xml = max(xml_files, key=os.path.getmtime)
    return newest_xml

def lade_bedingungen():
    return {
        "bedingungen": pd.read_csv("resources/bedingungen_herren_damen.csv"),
        "senioren": pd.read_csv("resources/bedingungen_senioren.csv")
    }

def extrahiere_serien(shooter):
    serien = shooter.findall(".//series")
    daten = []
    for serie in serien:
        shots = serie.findall(".//shot")
        if not shots:
            continue
        datum_set = {shot.attrib["datetime"].split()[0] for shot in shots}
        daten.append({
            "totalscore": int(serie.attrib.get("totalscore", "0")),
            "teiler": float(serie.attrib.get("bester_teiler", "99999")),
            "datum": shots[0].attrib["datetime"].split()[0],
            "anwesenheiten": len(datum_set)
        })
    return daten

def berechne_beste_serien(serien):
    serien.sort(key=lambda x: -x["totalscore"])
    beste, benutzt = [], set()
    for s in serien:
        if s["datum"] not in benutzt:
            beste.append(s)
            benutzt.add(s["datum"])
        if len(beste) == 3:
            break
    while len(beste) < 3:
        beste.append({"totalscore": 0, "teiler": "-", "anwesenheiten": 0})
    return beste

def berechne_gesamt_ringzahl(serien):
    ringe_gesamt = 0
    for s in serien:
        ringe_gesamt += s["totalscore"]
    return ringe_gesamt

def pruefe_bedingungen(daten, bedingungen_row):
    geburtsdatum = datetime.strptime(daten["Geburtsdatum"], "%d/%m/%Y")
    alter = datetime.now().year - geburtsdatum.year

    if alter < 50:
        scores = [
            ("Bester_Score", bedingungen_row["BNEins"]),
            ("Zweiter_Score", bedingungen_row["BNZwei"]),
            ("Dritter_Score", bedingungen_row["BNDrei"])
        ]
    else:
        scores = [
            ("Bester_Score", bedingungen_row["SNEins"]),
            ("Zweiter_Score", bedingungen_row["SNZwei"]),
            ("Dritter_Score", bedingungen_row["SNDrei"])
        ]

    if daten["Anwesenheiten"] < 5:
        return False

    for feld, wert in scores:
        try:
            if wert != "-" and float(daten[feld]) < float(wert):
                return False
        except:
            return False

    return True

def pruefe_senioren_bedingung(shooter, serien, senioren_df):
    geburtsjahr = int(shooter.attrib["birthdateiso"][:4])
    alter = HEUTIGES_JAHR - geburtsjahr
    if alter < 60:
        return "-"
    eintrag = senioren_df[senioren_df["Alter"] == alter]
    if eintrag.empty:
        return "-"
    ringzahl = float(eintrag.iloc[0]["Ringzahl"])
    summierte_scores, anwesenheiten, benutzt = 0, 0, set()
    for s in serien:
        if s["datum"] not in benutzt:
            summierte_scores += s["totalscore"]
            anwesenheiten += s["anwesenheiten"]
            benutzt.add(s["datum"])
    return summierte_scores >= ringzahl and anwesenheiten >= 5

# ========== VERARBEITUNG ==========
def verarbeite_schuetzen(root, bedingungen_df, senioren_df, fehler_liste):
    auswertung = []

    for shooter in root.findall(".//shooter"):
        clubsname = shooter.attrib.get("clubsname", "")
        if clubsname not in bedingungen_df["Auszeichnung"].values:
            fehler_liste.append(f"Nicht gefunden: {shooter.attrib['idShooters']} - {shooter.attrib['lastname']}, {shooter.attrib['firstname']} (clubsname: {clubsname})")
            continue

        daten = {
            "Schuetzennummer": shooter.attrib["idShooters"],
            "Bedingung": shooter.attrib["clubsname"],
            "Zugehoerigkeit": shooter.attrib["identification"],
            "Geburtsdatum": format_datum(shooter.attrib["birthdateiso"]),
            "Name": shooter.attrib["lastname"],
            "Vorname": shooter.attrib["firstname"],
            "besterteiler": float(shooter.attrib.get("bester_teiler", "99999"))
        }

        serien_daten = extrahiere_serien(shooter)
        beste = berechne_beste_serien(serien_daten)
        ringe_gesamt = berechne_gesamt_ringzahl(serien_daten)

        all_unique_dates = set()
        for s in serien_daten:
            all_unique_dates.add(s["datum"])
        total_anwesenheiten = len(all_unique_dates)

        daten.update({
            "Bester_Score": beste[0]["totalscore"],
            "Zweiter_Score": beste[1]["totalscore"],
            "Dritter_Score": beste[2]["totalscore"],
            "Ringe_Gesamt": ringe_gesamt,
            "Anwesenheiten": total_anwesenheiten
        })

        bedingung = bedingungen_df[bedingungen_df["Auszeichnung"] == clubsname]
        daten["Bedingung_Erfuellt"] = False
        if not bedingung.empty:
            daten["Bedingung_Erfuellt"] = pruefe_bedingungen(daten, bedingung.iloc[0])

        daten["Senioren_Bedingung_Erfuellt"] = pruefe_senioren_bedingung(shooter, serien_daten, senioren_df)

        auswertung.append(daten)
    return auswertung

# ========== HAUPTPROGRAMM ==========
def main():
    bedingungen = lade_bedingungen()
    xml_pfad = finde_xml_datei(EXPORT_DIR)
    tree = ET.parse(xml_pfad)
    root = tree.getroot()

    fehler_liste = []
    bedingungen = verarbeite_schuetzen(root, bedingungen["bedingungen"], bedingungen["senioren"], fehler_liste)

    df = pd.DataFrame(bedingungen)
    df.to_csv(AUSWERTUNG_DATEI, index=False, sep=";")

    with open(FEHLER_DATEI, "w", encoding="utf-8") as f:
        if fehler_liste:
            f.write("Folgende Schützen hatten keinen passenden Eintrag in den Bedingungen:\n\n")
            f.writelines(f"{e}\n" for e in fehler_liste)
        else:
            f.write("Keine Fehler – alle Schützen wurden korrekt zugeordnet.\n")

    print(f"{AUSWERTUNG_DATEI} und {FEHLER_DATEI} wurden erstellt.")

if __name__ == "__main__":
    main()
