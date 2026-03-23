# Python File Automation Demo

A lightweight, config-driven Python automation tool for cleaning, merging, deduplicating, and reporting Excel/CSV files in a repeatable workflow.

## Overview

This project demonstrates a practical Python automation workflow for handling repetitive file-processing tasks. It imports multiple Excel and CSV files, normalizes inconsistent column names, cleans common data issues, removes duplicates, generates summary reports, and archives processed files.

The workflow is designed to be **config-driven**, so many column changes can be handled through configuration updates instead of rewriting the core script.

## Why This Project Matters

Many businesses receive operational or customer data in multiple spreadsheet files with:

- inconsistent column names
- formatting issues
- duplicate records
- missing required values
- repetitive manual cleanup work

This project shows how Python can automate that process in a reusable and maintainable way.

## Key Highlights

- Batch import of CSV and XLSX files
- Column alias mapping through JSON config
- Configurable required fields and output columns
- Email, phone, and date normalization
- Duplicate removal using configurable keys
- Summary report generation
- Rejected rows export
- Process logging
- Archive workflow for processed files

## Project Structure

```text
python-file-automation-demo/
├─ config/
│  ├─ column_mapping.json
│  └─ rules.json
├─ input/
├─ output/
├─ archive/
├─ logs/
├─ samples/
├─ src/
│  ├─ main.py
│  ├─ config_loader.py
│  ├─ reader.py
│  ├─ cleaner.py
│  ├─ merger.py
│  ├─ reporter.py
│  └─ utils.py
├─ tests/
├─ requirements.txt
└─ README.md
```

## How It Works

The workflow follows these steps:

1. Read all supported files from `input/`
2. Normalize incoming column names based on config
3. Validate required fields
4. Clean selected columns
5. Merge all records into a single dataset
6. Remove duplicates using configured keys
7. Export clean output files
8. Write logs and summary reports
9. Move processed files to `archive/`

## Supported File Types

- `.csv`
- `.xlsx`

## Configuration-Driven Design

This project uses external JSON configuration so the workflow is easier to maintain.

### `config/column_mapping.json`

Used to map multiple source column names into standard internal names.

Example:

```json
{
  "Email": "email",
  "E-mail": "email",
  "email_address": "email",
  "Phone": "phone",
  "mobile": "phone",
  "Customer Name": "name"
}
```

### `config/rules.json`

Used to control validation and processing rules.

Example:

```json
{
  "required_columns": ["name", "email"],
  "dedupe_keys": ["email"],
  "output_columns": ["name", "email", "phone", "date"],
  "drop_columns": [],
  "cleaning_rules": {
    "email": "lowercase",
    "phone": "digits_only",
    "date": "date_iso",
    "name": "strip"
  }
}
```

## Why Config Matters

Instead of hardcoding every column rule inside Python logic, this project allows many changes to be handled through config updates.

Examples of changes that can often be handled without rewriting the main workflow:

- renaming columns
- adding new column aliases
- changing required fields
- changing deduplication keys
- changing output column order
- dropping unnecessary columns

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/python-file-automation-demo.git
cd python-file-automation-demo
```

### 2. Create and activate a virtual environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the Project

Place your input files into the `input/` folder, then run:

```bash
python src/main.py
```

## Example Output

After execution, the project will generate files such as:

- `output/master.csv`
- `output/summary.json`
- `output/rejected_rows.csv`
- `logs/process.log`

### Example `summary.json`

```json
{
  "files_processed": 3,
  "rows_read": 120,
  "rows_after_cleaning": 108,
  "duplicates_removed": 9,
  "invalid_rows": 3,
  "output_file": "output/master.csv"
}
```

## Example Use Case

Imagine a team receives multiple files from different sources:

- one file uses `Email`
- another uses `email_address`
- another uses `E-mail`

Some rows contain:

- uppercase emails
- phone numbers with symbols
- inconsistent date formats
- duplicate contacts

This tool standardizes and cleans all of that automatically, then exports one clean master dataset and a summary report.

## Before vs After

### Before

- Multiple messy Excel/CSV files
- Different column names for the same data
- Duplicate records
- Inconsistent formatting
- Manual repetitive cleanup

### After

- One clean merged file
- Standardized columns
- Normalized values
- Duplicate records removed
- Summary report generated
- Process log saved
- Input files archived

## Testing

Run tests with:

```bash
pytest -q
```

## Screenshot Section

You can optionally add screenshots here for stronger portfolio presentation.

Suggested screenshots:

1. messy input files
2. clean `master.csv`
3. `summary.json`
4. `process.log`

Example section:

```markdown
## Screenshots

### Input Files
![Input Files](samples/screenshots/input-files.png)

### Clean Master Output
![Master Output](samples/screenshots/master-output.png)

### Summary Report
![Summary Report](samples/screenshots/summary-report.png)
```

## Portfolio Positioning

This project is suitable for showcasing skills in:

- Python automation
- Excel/CSV processing
- File workflow automation
- Data cleanup automation
- Reporting automation
- Configurable scripting

## Business Value

This project is designed to demonstrate how Python can reduce repetitive manual work in business operations.

It is not just a one-off script. It shows how to build a reusable automation workflow that remains maintainable when file schemas evolve over time.

## Possible Future Improvements

- CLI arguments for custom input/output paths
- YAML config support
- Excel formatting for final reports
- Email notification after processing
- Scheduled execution
- Simple web UI for non-technical users
- Docker packaging
- API trigger support

## Tech Stack

- Python
- pandas
- openpyxl
- pathlib
- logging
- JSON configuration

## License

This project is provided for demonstration and portfolio purposes.

