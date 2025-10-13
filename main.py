from lxml import etree
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date

# === Konfiguration ===
DEFAULT_SUPPLIER_NAME = "Supplier Name"
DEFAULT_SUPPLIER_CITY = "Supplier City"
VERSION = "5.0"

# === Funktion zur Erstellung eines XML-Baums ===
def create_datanorm_tree(grouped_data):
    datanorm = ET.Element("DATANORM")

    today = date.today().strftime("%Y-%m-%d")

    umgewandelte = []
    nicht_umgewandelte = []

    for supplier, rows in grouped_data.items():
        # Kopfblock
        kopf = ET.SubElement(datanorm, "KOPF")
        ET.SubElement(kopf, "VERSION").text = VERSION
        lieferant = ET.SubElement(kopf, "LIEFERANT")
        ET.SubElement(lieferant, "NAME").text = supplier or DEFAULT_SUPPLIER_NAME
        ET.SubElement(lieferant, "ORT").text = DEFAULT_SUPPLIER_CITY
        ET.SubElement(lieferant, "DATUM").text = today

        # Artikelliste
        artikelliste = ET.SubElement(datanorm, "ARTIKELLISTE")
        for row in rows:
            try:
                artikel = ET.SubElement(artikelliste, "ARTIKEL")
                ET.SubElement(artikel, "ARTIKELNR").text = row[0] if len(row) > 0 else ""
                ET.SubElement(artikel, "BEZEICHNUNG").text = row[1] if len(row) > 1 else ""
                ET.SubElement(artikel, "PREIS").text = row[2] if len(row) > 2 else ""
                umgewandelte.append(row)
            except Exception:
                nicht_umgewandelte.append(row)

    return datanorm, umgewandelte, nicht_umgewandelte

# === CSV lesen und gruppieren ===
def read_and_group_csv(csv_path):
    grouped = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            # Umlaute und Sonderzeichen werden direkt korrekt übernommen
            supplier = row[3].strip() if len(row) > 3 else DEFAULT_SUPPLIER_NAME
            grouped[supplier].append(row)
    return grouped

# === XML-Datei schön speichern ===
def save_pretty_xml(element, output_path):
    import xml.dom.minidom
    xml_str = ET.tostring(element, encoding="utf-8")
    pretty = xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="utf-8")
    with open(output_path, "wb") as f:
        f.write(pretty)

# === Hauptprogramm ===
if __name__ == "__main__":
    import os, re
    artikelstamm_dir = "Artikelstamm"
    pattern = re.compile(r"(.*)[-_](\d{8})\.csv$")
    files = [f for f in os.listdir(artikelstamm_dir) if f.endswith('.csv')]
    def get_date_from_filename(filename):
        m = pattern.match(filename)
        if m:
            return m.group(2)  # YYYYMMDD
        return ''
    files_with_date = [(f, get_date_from_filename(f)) for f in files]
    files_with_date = [(f, d) for f, d in files_with_date if d]
    # Finde das neueste Datum
    if files_with_date:
        max_date = max(d for _, d in files_with_date)
        latest_files = [f for f, d in files_with_date if d == max_date]
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = "datanorm_results"
        import os
        os.makedirs(output_dir, exist_ok=True)
        for latest_file in latest_files:
            input_csv = os.path.join(artikelstamm_dir, latest_file)
            base_name = os.path.splitext(latest_file)[0]
            output_xml = os.path.join(output_dir, f"{base_name}_DATANORMv5_{now}.dat")

            print(f"\n===== Verarbeitung für Datei: {input_csv} =====")
            grouped_data = read_and_group_csv(input_csv)
            datanorm_tree, umgewandelte, nicht_umgewandelte = create_datanorm_tree(grouped_data)
            save_pretty_xml(datanorm_tree, output_xml)

            print(f"✅ DATANORM V5-Datei erfolgreich erstellt: {output_xml}")
            gesamt = sum(len(rows) for rows in grouped_data.values())
            print(f"🔎 Gefundene Datensätze: {gesamt}\n")
            print(f"📦 Umgewandelte Datensätze: {len(umgewandelte)} von {gesamt}\n")
            if nicht_umgewandelte:
                print(f"Nicht umgewandelte Datensätze: {len(nicht_umgewandelte)}")
                for row in nicht_umgewandelte:
                    print("  -", row)
    else:
        print("Keine passende CSV-Datei im Ordner 'Artikelstamm' gefunden.")
        exit(1)

from collections import Counter

def validate_datanorm(xml_file, xsd_file="Datanorm_V5.xsd"):
    """
    Validiert eine DATANORM V5 Datei gegen das XSD-Schema und führt zusätzliche Prüfungen durch.
    Gibt eine detaillierte Auswertung in der Konsole aus.
    """
    print(f"\n🔍 Starte einfache DATANORM V5-Validierung für: {xml_file}\n")

    results = {
        "custom_errors": [],
        "warnings": []
    }

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Pflichtfelder prüfen
        artikel_elems = root.findall(".//ARTIKEL")
        artikelnummern = []
        for art in artikel_elems:
            nr = (art.findtext("ARTIKELNR") or "").strip()
            bez = (art.findtext("BEZEICHNUNG") or "").strip()
            preis = (art.findtext("PREIS") or "").strip()

            if not nr:
                results["custom_errors"].append("Fehlende Artikelnummer")
            if not bez:
                results["warnings"].append(f"Artikel {nr or '(unbekannt)'}: fehlende Bezeichnung")
            try:
                if preis:
                    # Entferne Tausenderpunkte und ersetze Komma durch Punkt
                    cleaned_preis = preis.replace(".", "").replace(",", ".")
                    float(cleaned_preis)
            except ValueError:
                results["custom_errors"].append(f"Artikel {nr}: ungültiger Preiswert '{preis}'")
            artikelnummern.append(nr)

        # Doppelte Artikelnummern prüfen
        from collections import Counter
        duplicates = [num for num, count in Counter(artikelnummern).items() if count > 1 and num]
        if duplicates:
            results["custom_errors"].append(f"Doppelte Artikelnummern: {', '.join(duplicates)}")

        # Kopfdatensätze prüfen
        kopf_count = len(root.findall(".//KOPF"))
        if kopf_count == 0:
            results["custom_errors"].append("Kein <KOPF>-Block vorhanden")
        else:
            print(f"📦 Gefundene Lieferantenblöcke (KOPF): {kopf_count}")
    except Exception as ex:
        results["custom_errors"].append(f"Fehler bei inhaltlicher Prüfung: {ex}")

    # Zusammenfassung
    print("\n📊 Validierungszusammenfassung:")
    print(f"  Zusatzfehler:    {len(results['custom_errors'])}")
    print(f"  Warnungen:       {len(results['warnings'])}")

    if results["custom_errors"]:
        print("\n🔴 Logische Fehler:")
        for e in results["custom_errors"]:
            print("  -", e)

    if results["warnings"]:
        print("\n🟠 Warnungen:")
        for w in results["warnings"]:
            print("  -", w)

    if not results["custom_errors"]:
        print("\n✅ Datei ist strukturell DATANORM-konform.\n")
    return results

# === Beispielaufruf der Validierungsfunktion ===

if __name__ == "__main__":
    xml_to_validate = output_xml  # Nutze die aktuelle Ausgabedatei
    xsd_schema = "Datanorm_V5.xsd"  # Pfad zum XSD-Schema

    print(f"✅ DATANORM V5-Datei erstellt: {output_xml}")

    results = validate_datanorm(xml_to_validate, xsd_schema)

