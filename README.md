# DATANORM V5 Converter

This Python script reads a CSV file with article data and converts it to the DATANORM V5 XML format.

## Features

- Automatic selection of the newest CSV file from the `Artikelstamm` folder (date in filename, format: YYYYMMDD).
- Results are saved in the `datanorm_results` folder, with the original filename included in the output name.
- Summary of found and converted records, including a list of any records that could not be converted.
- Simple validation of the generated XML (checks for required fields, price format, duplicates, and supplier blocks).

## Usage

1. Place your CSV file(s) in the `Artikelstamm` folder. The script will automatically use the newest file based on the date in the filename.
2. Run the script:

    ```pwsh
    python main.py
    ```

3. The XML file will be created in the `datanorm_results` folder, named like `<original>_DATANORMv5_<timestamp>.dat`.
4. The console output will show a summary of the conversion and validation results.

## Requirements

- Python 3.7+
- No external packages required (only standard library)

## Customization

You can adjust field names and structure in the script as needed.

## License

This project is licensed under the MIT License.