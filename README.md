## Command line parameters

**General usage:**

```
python main.py [options]
```
python main.py --input-encoding=utf-8 --output-encoding=cp850 --vk-mapping --calculate-vk2ek=A:0.25,B:0.30,C:0.35,D:0.40,E:0.45,F:0.50

**Options:**

- `--version=v4|v5`  
   Select DATANORM version (default: v4)
- `--name="Your Company Name"`  
   Set custom name for header line (default: "Article master data")
- `--input-encoding=<encoding>`  
   Encoding for reading the CSV input file. Supported values:
      - `utf-8` (default)
      - `ansi` (Windows-1252)
      - `iso-8859-1`
      - `cp850`
- `--output-encoding=<encoding>`  
   Encoding for writing the DATANORM output file. Supported values:
      - `utf-8` (default)
      - `utf-8-bom` (UTF-8 with BOM)
      - `ansi` (Windows-1252)
      - `iso-8859-1`
      - `cp850` (DOS)
      - `hero` (special: writes as cp850 for Hero platform)
- `--vk-mapping`  
   Enable VK-Mapping: maps sales groups A,B,C,D to VK1,VK2,VK3,VK4
- `--calculate-vk2ek`  
   Enable VK2EK price reduction logic (default discounts: A:10%, B:20%, ... F:60%)
- `--calculate-vk2ek=MAP`  
   Custom VK2EK discounts for groups (A-F), comma-separated (e.g. A:0.12,B:0.25,...)

**Examples:**

```
python main.py --version=v5 --name="My Company" --input-encoding=utf-8 --output-encoding=ansi
python main.py --input-encoding=utf-8 --output-encoding=utf-8-bom
python main.py --input-encoding=ansi --output-encoding=cp850
python main.py --output-encoding=hero
python main.py --vk-mapping
python main.py --calculate-vk2ek
python main.py --calculate-vk2ek=A:0.12,B:0.25,C:0.33,D:0.45,E:0.55,F:0.66
```

**Encoding notes:**
- Use `utf-8` for maximum compatibility and correct umlauts.
- Use `ansi` or `iso-8859-1` for legacy Windows systems.
- Use `cp850` for DOS-based platforms.
- Use `utf-8-bom` if the target system requires a BOM.
- Use `hero` for Hero platform compatibility (cp850 output).


# simpleCSV2DATANORMV5

Tool for converting CSV article master data into DATANORM V4 and V5 format.

## Usage

1. Use the provided example file for testing: `example/article_master_data_minified_20251002.csv`.
   This file contains various test cases (umlauts, special characters, price logic, superscript numbers, etc.) and can be used directly as input.

   All CSV files placed in the `example` folder will be processed automatically. You can add your own test files to this folder for batch conversion.

   Example content:
   ```csv
   ART-00001;Sample Article 1;100.00;Supplier Name
   ART-00002;Sample Article 2;200.50;Supplier Name
   ...
   ```
   - Column 1: Article number
   - Column 2: Description
   - Column 3: Price (e.g. 123.45)
   - Column 4: Supplier (ignored)

2. Run the script with `python main.py`.
   - By default, DATANORM V4 is generated.
   - For DATANORM V5 use: `python main.py --version=v5`
   - You can set the name for the header line: `python main.py --name="Your Company Name"`
   - Default value for the name is "Article master data" (used if no parameter is given).
3. The DATANORM file will be saved in the `datanorm_results` folder.
4. Additionally, the DATANORM file will be automatically zipped (same name, `.zip` extension).

## Output file format (DATANORM V4)

The generated file matches the DATANORM V4 format and fulfills legacy requirements:

- The header line is always exactly 129 characters long, regardless of the name.
- "04EUR" is always at the same position as in the template.
- Line endings are Windows-compliant (CRLF).
- At the end of the file, the SUB character (ASCII 0x1A) is written as legacy EOF.

Example:
```
V 141025Your Company Name Artikeldaten                                                                                           04EUR
A;N;ART-00001;00;Sample Article 1; ;1;0;Stck;10000;001; ; ; 
B;N;ART-00001; ; ; ;0;0;0; ; ; ;0;0; ; ; 
...
```

**Notes:**
- The price is output as cents (integer, e.g. 12345 for 123.45 EUR).
- Supplier is not included.
- The header line is always 129 characters long, "04EUR" is at position 125.
- The file is automatically zipped.
- Header and end line are configurable.

## Output file format (DATANORM V5)

The generated file matches the DATANORM V5 format and fulfills legacy requirements:

- The header line is always exactly 129 characters long, regardless of the name.
- "04EUR" is always at the same position as in the template.
- Line endings are Windows-compliant (CRLF).
- At the end of the file, the SUB character (ASCII 0x1A) is written as legacy EOF.

```
V;050;A;20251014;EUR;Your Company Name Artikeldaten;;;;;;;;;;
A;N;ART-00001;Sample Article 1;;PCE;1;1;10000;001;;;;;;;;;;;0;;0;;;;;;;
A;N;ART-00002;Sample Article 2;;PCE;1;1;20050;001;;;;;;;;;;;0;;0;;;;;;;
...
E;10;Created by simpleCSV2DATANORMV5;
```

**Notes:**
- The price is output as cents (integer, e.g. 12345 for 123.45 EUR).
- The field for short text 2 remains empty.
- Supplier is not included.
- The header line is always 129 characters long, "04EUR" is at position 125.
- The file is automatically zipped.
- Header and end line are configurable.

# VK-Mapping and VK2EK price reduction

## VK-Mapping
- Enable with `--vk-mapping`
- Maps sales groups A,B,C,D to VK1,VK2,VK3,VK4 in the output
- Useful for systems expecting VK1-VK4 instead of A-D

## VK2EK price reduction
- Enable with `--calculate-vk2ek`
- Applies a discount to the price for sales groups A-F
- Default discounts: A:10%, B:20%, C:30%, D:40%, E:50%, F:60%
- Custom discounts: `--calculate-vk2ek=A:0.12,B:0.25,C:0.33,D:0.45,E:0.55,F:0.66`
- Only one example per group is printed to the console for verification
- Example output:
  - VK2EK Example: Group=A, Discount=12.0%, Original=100.00, New=88.00

## Full parameter overview

| Parameter                | Description                                                                                 | Example                                                      |
|--------------------------|--------------------------------------------------------------------------------------------|--------------------------------------------------------------|
| --version=v4/v5          | DATANORM version (default: v4)                                                             | --version=v5                                                 |
| --name=NAME              | Name for DATANORM file header                                                               | --name="Article master data"                                |
| --input-encoding=ENC     | Input CSV encoding: utf-8, windows-1252 (ANSI), iso-8859-1, cp850, utf-8-bom, hero          | --input-encoding=utf-8                                       |
| --output-encoding=ENC    | Output DATANORM encoding: utf-8, windows-1252 (ANSI), iso-8859-1, cp850, utf-8-bom, hero    | --output-encoding=cp850                                      |
| --vk-mapping             | Enable VK-Mapping: maps sales groups A,B,C,D to VK1,VK2,VK3,VK4                             | --vk-mapping                                                 |
| --calculate-vk2ek        | Enable VK2EK price reduction logic (default discounts: A:10%, B:20%, ... F:60%)            | --calculate-vk2ek                                            |
| --calculate-vk2ek=MAP    | Custom VK2EK discounts for groups (A-F), comma-separated (e.g. A:0.12,B:0.25,...)          | --calculate-vk2ek=A:0.12,B:0.25,C:0.33,D:0.45,E:0.55,F:0.66   |

## Example usage
```bash
python main.py --input-encoding=utf-8 --output-encoding=cp850 --vk-mapping --calculate-vk2ek=A:0.12,B:0.25,C:0.33,D:0.45,E:0.55,F:0.66
```