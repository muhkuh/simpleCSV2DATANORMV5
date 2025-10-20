import sys
from datetime import datetime
import csv
import os
import re

def write_hero_encoding(lines, output_path):
    # Write each line as CP850 bytes (DOS), no UTF-8 conversion
    with open(output_path, 'wb') as out:
        for line in lines:
            out.write(line.encode('cp850') + b'\r\n')
        # Write SUB character (end of file) as in original
        out.write(chr(26).encode('cp850'))

def write_utf8_bom_encoding(lines, output_path):
    # Write lines with UTF-8 BOM at the beginning
    with open(output_path, 'wb') as out:
        out.write(b'\xef\xbb\xbf')  # UTF-8 BOM
        for line in lines:
            out.write(line.encode('utf-8') + b'\r\n')
        out.write(chr(26).encode('utf-8'))

def csv_to_datanorm_v4(csv_path, output_path, input_encoding='utf-8', output_encoding='utf-8'):
    today = datetime.now().strftime('%d%m%y')
    DATANORM_NAME = globals().get('DATANORM_NAME', 'Article master data')
    header_prefix = f"V {today}{DATANORM_NAME}"
    spaces_needed = 129 - (len(header_prefix) + len("04EUR"))
    header = f"{header_prefix}{' ' * spaces_needed}04EUR"
    artikel_lines = []
    if not os.path.isfile(csv_path):
        print(f"❌ Input file not found: {csv_path}")
        return
    vk2ek_printed = set()
    with open(csv_path, newline='', encoding=input_encoding) as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            artikelnummer = row[0] if len(row) > 0 else ''
            # Replace umlauts and special characters in article number
            def replace_umlauts(text):
                orig = text
                text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
                text = text.replace('ß', 'ss')
                if text != orig:
                    print(f"\033[93mArtikelnummer-Umlautersetzung: Original='{orig}' -> Cleaned='{text}'\033[0m")
                return text
            artikelnummer = replace_umlauts(artikelnummer)
            bezeichnung = row[1] if len(row) > 1 else ' '
            # Remove quotes and replace semicolon in description
            if bezeichnung.startswith('"') and bezeichnung.endswith('"'):
                bezeichnung = bezeichnung[1:-1].replace(';', ',')
            zusatztext = ' '
            rabattgruppe = '001'
            if '*Nettopreis*' in bezeichnung:
                bezeichnung = bezeichnung.replace('*Nettopreis*', '').strip()
                rabattgruppe = ' '
            match = re.search(r'\(([A-Z])\)', bezeichnung)
            if match:
                rabattgruppe = match.group(1)
                bezeichnung = re.sub(r'\([A-Z]\)', '', bezeichnung).strip()
            # Remove duplicate VK2EK calculation (now only in price logic block)
            # VK-Mapping active?
            if globals().get('VK_MAPPING', False):
                if rabattgruppe in ['A','B','C','D']:
                    rabattgruppe = f"VK{ord(rabattgruppe)-ord('A')+1}"
            preis_raw = row[2] if len(row) > 2 else '0'
            preis2_raw = row[3] if len(row) > 3 else '0'
            preis_clean = re.sub(r'[^0-9,\.]', '', preis_raw)
            preis2_clean = re.sub(r'[^0-9,\.]', '', preis2_raw)
            try:
                preis_float_basis = float(preis_clean.replace(',', '.'))
            except Exception:
                preis_float_basis = 0.0
            try:
                preis2_float = float(preis2_clean.replace(',', '.'))
            except Exception:
                preis2_float = 0.0
            # Price logic: If column 4 > 0, do NOT apply discount
            if preis2_float > 0.0:
                preis_float = preis2_float
            else:
                preis_float = preis_float_basis
                # VK2EK price calculation active? (only on column 3)
                if globals().get('CALCULATE_VK2EK', False):
                    vk2ek_map = globals().get('VK2EK_MAP', {'A':0.10, 'B':0.20, 'C':0.30, 'D':0.40, 'E':0.50, 'F':0.60})
                    if rabattgruppe in vk2ek_map:
                        abschlag = vk2ek_map[rabattgruppe]
                        preis_float_orig = preis_float_basis
                        preis_float = preis_float_basis * (1.0 - abschlag)
                        if rabattgruppe not in vk2ek_printed:
                            print(f"VK2EK Example: Group={rabattgruppe}, Discount={abschlag*100:.1f}%, Original={preis_float_orig:.2f}, New={preis_float:.2f}")
                            vk2ek_printed.add(rabattgruppe)
            preis_int = int(round(preis_float * 100))
            a_fields = [
                'A', 'N', artikelnummer, '00', bezeichnung, zusatztext, '1', '0', 'Stck', str(preis_int), rabattgruppe, ' ', ' ', ' '
            ]
            artikel_lines.append(';'.join(a_fields))
            b_fields = [
                'B', 'N', artikelnummer, ' ', ' ', ' ', '0', '0', '0', ' ', ' ', ' ', '0', '0', ' ', ' ', ' '
            ]
            artikel_lines.append(';'.join(b_fields))
    def pad_fields(fields, total):
        return fields + [' '] * (total - len(fields))
    output_lines = [header.rstrip()]
    for i, line in enumerate(artikel_lines):
        if line.startswith('A;'):
            fields = line.split(';')
            line = ';'.join(pad_fields(fields, 14)).rstrip()
        elif line.startswith('B;'):
            fields = line.split(';')
            line = ';'.join(pad_fields(fields, 14)).rstrip()
        output_lines.append(line)
    if output_encoding == 'hero':
        write_hero_encoding(output_lines, output_path)
    elif output_encoding == 'utf-8-bom':
        write_utf8_bom_encoding(output_lines, output_path)
    elif output_encoding == 'cp850':
        def remove_cp850_invalid(text):
            # Replace typographic inch sign with standard sign
            replaced = text.replace('”', '"').replace('“', '"')
            # Replace superscript numbers with ^number
            replaced = replaced.replace('²', '^2').replace('³', '^3').replace('¹', '^1')
            # Remove registered trademark sign
            replaced = replaced.replace('®', '(R)')
            try:
                replaced.encode('cp850')
                return replaced, replaced != text
            except UnicodeEncodeError:
                cleaned = replaced.encode('cp850', errors='ignore').decode('cp850')
                return cleaned, True
        with open(output_path, 'w', encoding='cp850', newline='\r\n') as out:
            for line in output_lines:
                cleaned_line, changed = remove_cp850_invalid(line)
                out.write(cleaned_line + '\n')
            out.write(chr(26))
    else:
        enc = output_encoding if output_encoding != 'iso-8859-1' else 'latin1'
        with open(output_path, 'w', encoding=enc, newline='\r\n') as out:
            for line in output_lines:
                out.write(line + '\n')
            out.write(chr(26))

def csv_to_datanorm(csv_path, output_path, input_encoding='utf-8', output_encoding='utf-8'):
    DATANORM_NAME = globals().get('DATANORM_NAME', 'Article master data')
    END_LINE_TEXT = "Created by simpleCSV2DATANORMV5"
    today = datetime.now().strftime('%Y%m%d')
    header = f"V;050;A;{today};EUR;{DATANORM_NAME};;;;;;;;;;"
    artikel_lines = []
    if not os.path.isfile(csv_path):
        print(f"❌ Input file not found: {csv_path}")
        return
    vk2ek_printed = set()
    with open(csv_path, newline='', encoding=input_encoding) as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            artikelnummer = row[0] if len(row) > 0 else ''
            # Replace umlauts and special characters in article number
            def replace_umlauts(text):
                orig = text
                text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                text = text.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
                text = text.replace('ß', 'ss')
                if text != orig:
                    print(f"\033[93mArtikelnummer-Umlautersetzung: Original='{orig}' -> Cleaned='{text}'\033[0m")
                return text
            artikelnummer = replace_umlauts(artikelnummer)
            bezeichnung = row[1] if len(row) > 1 else ''
            # Remove quotes and replace semicolon in description
            if bezeichnung.startswith('"') and bezeichnung.endswith('"'):
                bezeichnung = bezeichnung[1:-1].replace(';', ',')
            zusatztext = ''
            rabattgruppe = '001'
            if '*Nettopreis*' in bezeichnung:
                bezeichnung = bezeichnung.replace('*Nettopreis*', '').strip()
                rabattgruppe = ' '
            match = re.search(r'\(([A-Z])\)', bezeichnung)
            if match:
                rabattgruppe = match.group(1)
                bezeichnung = re.sub(r'\([A-Z]\)', '', bezeichnung).strip()
            # VK2EK price calculation active?
            if globals().get('CALCULATE_VK2EK', False):
                vk2ek_map = globals().get('VK2EK_MAP', {'A':0.10, 'B':0.20, 'C':0.30, 'D':0.40, 'E':0.50, 'F':0.60})
                if rabattgruppe in vk2ek_map:
                    abschlag = vk2ek_map[rabattgruppe]
                    try:
                        preis_float = float(preis_clean.replace(',', '.'))
                        preis_float_orig = preis_float
                        preis_float = preis_float * (1.0 - abschlag)
                        preis_int = int(round(preis_float * 100))
                        if rabattgruppe not in vk2ek_printed:
                            print(f"VK2EK Example: Group={rabattgruppe}, Discount={abschlag*100:.1f}%, Original={preis_float_orig:.2f}, New={preis_float:.2f}")
                            vk2ek_printed.add(rabattgruppe)
                    except Exception:
                        preis_int = 0
            # VK-Mapping active?
            if globals().get('VK_MAPPING', False):
                if rabattgruppe in ['A','B','C','D']:
                    rabattgruppe = f"VK{ord(rabattgruppe)-ord('A')+1}"
            preis_raw = row[2] if len(row) > 2 else '0'
            preis2_raw = row[3] if len(row) > 3 else '0'
            preis_clean = re.sub(r'[^0-9,\.]', '', preis_raw)
            preis2_clean = re.sub(r'[^0-9,\.]', '', preis2_raw)
            try:
                preis_float_basis = float(preis_clean.replace(',', '.'))
            except Exception:
                preis_float_basis = 0.0
            try:
                preis2_float = float(preis2_clean.replace(',', '.'))
            except Exception:
                preis2_float = 0.0
            # Price logic: If column 4 > 0, do NOT apply discount
            if preis2_float > 0.0:
                preis_float = preis2_float
            else:
                preis_float = preis_float_basis
                # VK2EK price calculation active? (only on column 3)
                if globals().get('CALCULATE_VK2EK', False):
                    vk2ek_map = globals().get('VK2EK_MAP', {'A':0.10, 'B':0.20, 'C':0.30, 'D':0.40, 'E':0.50, 'F':0.60})
                    if rabattgruppe in vk2ek_map:
                        abschlag = vk2ek_map[rabattgruppe]
                        preis_float_orig = preis_float_basis
                        preis_float = preis_float_basis * (1.0 - abschlag)
                        if rabattgruppe not in vk2ek_printed:
                            print(f"VK2EK Example: Group={rabattgruppe}, Discount={abschlag*100:.1f}%, Original={preis_float_orig:.2f}, New={preis_float:.2f}")
                            vk2ek_printed.add(rabattgruppe)
            preis_int = int(round(preis_float * 100))
            print(f"Price conversion: Original='{preis_raw}', Clean='{preis_clean}', Float={preis_float:.2f}, Cent={preis_int}")
            mengeneinheit = 'PCE'
            menge = '1'
            rabatt = '1'
            artikel_line = f"A;N;{artikelnummer};{bezeichnung};{zusatztext};{mengeneinheit};{menge};{rabatt};{preis_int};{rabattgruppe};;;;;;;;;;;0;;0;;;;;;;"
            artikel_lines.append(artikel_line)
    end_line = f"E;{len(artikel_lines)};{END_LINE_TEXT};"
    output_lines = [header]
    output_lines.extend(artikel_lines)
    output_lines.append(end_line)
    if output_encoding == 'hero':
        write_hero_encoding(output_lines, output_path)
    elif output_encoding == 'utf-8-bom':
        write_utf8_bom_encoding(output_lines, output_path)
    elif output_encoding == 'cp850':
        def remove_cp850_invalid(text):
            # Replace typographic inch sign with standard sign
            replaced = text.replace('”', '"').replace('“', '"')
            # Replace superscript numbers with ^number
            replaced = replaced.replace('²', '^2').replace('³', '^3').replace('¹', '^1')
            try:
                replaced.encode('cp850')
                return replaced, replaced != text
            except UnicodeEncodeError:
                cleaned = replaced.encode('cp850', errors='ignore').decode('cp850')
                return cleaned, True
        with open(output_path, 'w', encoding='cp850', newline='\r\n') as out:
            for line in output_lines:
                cleaned_line, changed = remove_cp850_invalid(line)
                out.write(cleaned_line + '\n')
            out.write(chr(26))
    else:
        enc = output_encoding if output_encoding != 'iso-8859-1' else 'latin1'
        with open(output_path, 'w', encoding=enc, newline='\r\n') as out:
            for line in output_lines:
                out.write(line + '\n')
            out.write(chr(26))

pattern = r"(.*)[-_](\d{8})\.csv$"

if __name__ == "__main__":
    article_master_dir = "example"
    DATANORM_NAME = 'Article master data'
    output_encoding = 'utf-8'  # Default output encoding
    input_encoding = 'utf-8'   # Default input encoding
    vk_mapping = False
    calculate_vk2ek = False
    vk2ek_map = {'A':0.10, 'B':0.20, 'C':0.30, 'D':0.40, 'E':0.50, 'F':0.60}
    for arg in sys.argv[1:]:
        if arg.startswith('--name='):
            DATANORM_NAME = arg.split('=',1)[1]
        if arg.startswith('--input-encoding='):
            enc_value = arg.split('=',1)[1].lower()
            if enc_value == 'ansi':
                input_encoding = 'windows-1252'
            else:
                input_encoding = enc_value
        if arg.startswith('--output-encoding='):
            enc_value = arg.split('=',1)[1].lower()
            if enc_value == 'ansi':
                output_encoding = 'windows-1252'
            else:
                output_encoding = enc_value
        if arg == '--vk-mapping':
            vk_mapping = True
        if arg.startswith('--calculate-vk2ek'):
            calculate_vk2ek = True
            # Flexible values: --calculate-vk2ek=A:0.12,B:0.25,C:0.33,D:0.45
            if '=' in arg:
                param = arg.split('=',1)[1]
                for part in param.split(','):
                    if ':' in part:
                        k,v = part.split(':',1)
                        k = k.strip().upper()
                        try:
                            vk2ek_map[k] = float(v)
                        except Exception:
                            pass
    globals()['DATANORM_NAME'] = DATANORM_NAME
    globals()['VK_MAPPING'] = vk_mapping
    globals()['CALCULATE_VK2EK'] = calculate_vk2ek
    globals()['VK2EK_MAP'] = vk2ek_map
    # ...existing code...
    files = [f for f in os.listdir(article_master_dir) if f.endswith('.csv')]
    def get_date_from_filename(filename):
        global pattern
        match_obj = re.match(pattern, filename)
        if match_obj:
            return match_obj.group(2)
        return ''
    files_with_date = [(f, get_date_from_filename(f)) for f in files]
    files_with_date = [(f, d) for f, d in files_with_date if d]
    if files_with_date:
        max_date = max(d for _, d in files_with_date)
        latest_files = [f for f, d in files_with_date if d == max_date]
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = "datanorm_results"
        os.makedirs(output_dir, exist_ok=True)
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
                csv_to_datanorm(input_csv, output_datanorm, input_encoding=input_encoding, output_encoding=output_encoding)
                print(f"✅ DATANORM V5 file successfully created: {output_datanorm}")
            else:
                csv_to_datanorm_v4(input_csv, output_datanorm, input_encoding=input_encoding, output_encoding=output_encoding)
                print(f"✅ DATANORM V4 file successfully created: {output_datanorm}")
            zip_path = output_datanorm + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(output_datanorm, arcname=os.path.basename(output_datanorm))
            print(f"📦 ZIP archive created: {zip_path}")


