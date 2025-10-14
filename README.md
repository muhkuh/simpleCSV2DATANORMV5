

# simpleCSV2DATANORMV5

Tool for converting CSV article master data into DATANORM V4 and V5 format.

## Usage

1. Place your CSV file in the `Artikelstamm` folder. The format should look like this:
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
   - Default value for the name is "Artikelstammdaten" (used if no parameter is given).
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

## DATANORM V4/V5 Standard

You can find the DATANORM V5 specification e.g. at: https://www.datanorm.de/

Key fields:
- Article number
- Description
- Unit (PCE)
- Quantity (1)
- Discount (1)
- Price (cents)
- Product group (001)

Alle weiteren Felder werden leer gelassen, sofern nicht anders benötigt.