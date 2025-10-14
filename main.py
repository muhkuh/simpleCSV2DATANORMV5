import sys
def csv_to_datanorm_v4(csv_path, output_path):
    from datetime import datetime
    import re
    today = datetime.now().strftime('%d%m%y')
    # Name für Kopfzeile als Parameter
    DATANORM_NAME = globals().get('DATANORM_NAME', 'Article master data')
    # Header dynamisch auf 129 Zeichen auffüllen
    header_prefix = f"V {today}{DATANORM_NAME}"
    # 129 - (len(header_prefix) + len("04EUR")) = Anzahl Leerzeichen
    spaces_needed = 129 - (len(header_prefix) + len("04EUR"))
    header = f"{header_prefix}{' ' * spaces_needed}04EUR"
    artikel_lines = []
    if not os.path.isfile(csv_path):
        print(f"❌ Input file not found: {csv_path}")
        return
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            artikelnummer = row[0] if len(row) > 0 else ''
            bezeichnung = row[1] if len(row) > 1 else ' '
            zusatztext = ' '
            preis_raw = row[2] if len(row) > 2 else '0'
            preis_clean = re.sub(r'[^0-9,\.]', '', preis_raw)
            try:
                preis_float = float(preis_clean.replace(',', '.'))
                preis_int = int(round(preis_float * 100))
            except Exception:
                preis_int = 0
            a_fields = [
                'A', 'N', artikelnummer, '00', bezeichnung, zusatztext, '1', '0', 'Stck', str(preis_int), '001', ' ', ' ', ' '
            ]
            artikel_lines.append(';'.join(a_fields))
            b_fields = [
                'B', 'N', artikelnummer, ' ', ' ', ' ', '0', '0', '0', ' ', ' ', ' ', '0', '0', ' ', ' ', ' '
            ]
            artikel_lines.append(';'.join(b_fields))
    # Feldanzahl für A- und B-Datensatz wie Vorlage (14 Felder)
    def pad_fields(fields, total):
        return fields + [' '] * (total - len(fields))

    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as out:
        out.write(header.rstrip() + '\n')
        for i, line in enumerate(artikel_lines):
            # Prüfe, ob A- oder B-Datensatz
            if line.startswith('A;'):
                fields = line.split(';')
                line = ';'.join(pad_fields(fields, 14)).rstrip()
            elif line.startswith('B;'):
                fields = line.split(';')
                line = ';'.join(pad_fields(fields, 14)).rstrip()
            out.write(line + '\n')
        # SUB-Zeichen als einzelnes Byte am Ende
        out.write(chr(26))

import csv
import os
from datetime import datetime

def csv_to_datanorm(csv_path, output_path):
    # Variablen für Kopf und Endzeile
    DATANORM_NAME = globals().get('DATANORM_NAME', 'Article master data')
    END_LINE_TEXT = "Created by simpleCSV2DATANORMV5"
    today = datetime.now().strftime('%Y%m%d')
    header = f"V;050;A;{today};EUR;{DATANORM_NAME};;;;;;;;;;"
    artikel_lines = []
    if not os.path.isfile(csv_path):
        print(f"❌ Input file not found: {csv_path}")
        return
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            # Mapping analog zur Vorlage
            artikelnummer = row[0] if len(row) > 0 else ''
            bezeichnung = row[1] if len(row) > 1 else ''
            zusatztext = ''
            import re
            preis_raw = row[2] if len(row) > 2 else '0'
            preis_clean = re.sub(r'[^0-9,\.]', '', preis_raw)
            try:
                preis_float = float(preis_clean.replace(',', '.'))
                preis_int = int(round(preis_float * 100))
            except Exception:
                preis_int = 0
            print(f"Preis-Umwandlung: Original='{preis_raw}', Clean='{preis_clean}', Float={preis_float if 'preis_float' in locals() else 'ERROR'}, Cent={preis_int}")
            mengeneinheit = 'PCE'
            menge = '1'
            rabatt = '1'
            warengruppe = '001'
            # Reihenfolge: artikelnummer;bezeichnung;zusatztext;PCE;1;1;preis;001
            artikel_line = f"A;N;{artikelnummer};{bezeichnung};{zusatztext};{mengeneinheit};{menge};{rabatt};{preis_int};{warengruppe};;;;;;;;;;;0;;0;;;;;;;"
            artikel_lines.append(artikel_line)
    end_line = f"E;{len(artikel_lines)};{END_LINE_TEXT};"
    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as out:
        out.write(header + '\n')
        for line in artikel_lines:
            out.write(line + '\n')
        out.write(end_line + '\n')

if __name__ == "__main__":
    article_master_dir = "example"
    # Name for header line as parameter
    DATANORM_NAME = 'Article master data'
    for arg in sys.argv[1:]:
        if arg.startswith('--name='):
            DATANORM_NAME = arg.split('=',1)[1]
    globals()['DATANORM_NAME'] = DATANORM_NAME
    pattern = r"(.*)[-_](\d{8})\.csv$"
    files = [f for f in os.listdir(article_master_dir) if f.endswith('.csv')]
    import re
    def get_date_from_filename(filename):
        m = re.match(pattern, filename)
        if m:
            return m.group(2)
        return ''
    files_with_date = [(f, get_date_from_filename(f)) for f in files]
    files_with_date = [(f, d) for f, d in files_with_date if d]
    if files_with_date:
        max_date = max(d for _, d in files_with_date)
        latest_files = [f for f, d in files_with_date if d == max_date]
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = "datanorm_results"
        os.makedirs(output_dir, exist_ok=True)
        # Read version parameter
        version = 'v4'
        for arg in sys.argv[1:]:
            if arg.startswith('--version='):
                version = arg.split('=',1)[1].lower()
        import zipfile
        for latest_file in latest_files:
            input_csv = os.path.join(article_master_dir, latest_file)
            base_name = os.path.splitext(latest_file)[0]
            output_datanorm = os.path.join(output_dir, f"{base_name}_DATANORM{version}_{now}.001")
            print(f"\n===== Processing file: {input_csv} =====")
            if version == 'v5':
                csv_to_datanorm(input_csv, output_datanorm)
                print(f"✅ DATANORM V5 file successfully created: {output_datanorm}")
            else:
                csv_to_datanorm_v4(input_csv, output_datanorm)
                print(f"✅ DATANORM V4 file successfully created: {output_datanorm}")
            # Create ZIP archive
            zip_path = output_datanorm + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(output_datanorm, arcname=os.path.basename(output_datanorm))
            print(f"📦 ZIP archive created: {zip_path}")
    else:
        print("No suitable CSV file found in the 'example' folder.")
        exit(1)

