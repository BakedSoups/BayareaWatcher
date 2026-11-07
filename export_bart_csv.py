"""Export the PDF-derived BART financial table and its column dictionary."""

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "bart_financials.sqlite"
DATA_PATH = ROOT / "bart_financials.csv"
DICT_PATH = ROOT / "bart_financials_columns.csv"

DATA_COLUMNS = [
    "source_file", "report_title", "source_page", "units", "section", "label",
    "line_kind", "fy25_millions", "fy26_millions", "reported_change_millions",
    "reported_change_pct", "extraction_note",
]

COLUMN_NOTES = [
    ("source_file", "Source PDF filename", "Copied from source_document.filename", "BART_FY25 PAFR_Final.pdf"),
    ("report_title", "Human-readable report name", "Copied from source_document.document_title", "BART FY25 Popular Annual Financial Report"),
    ("source_page", "Printed report page containing the table", "Copied from source_document.source_page", "Page 11"),
    ("units", "Units used by the report", "Copied from source_document.units", "$ millions"),
    ("section", "Financial grouping", "Transcribed from the table section heading", "Operating Sources, Financial Assistance, Operating Uses, Debt Service & Allocations, or Operating Result"),
    ("label", "Line-item name", "Transcribed from the table row label", "Table row text"),
    ("line_kind", "Detail versus subtotal/total/result classification", "Assigned while transcribing the table hierarchy", "detail, subtotal, total, or result"),
    ("fy25_millions", "FY25 budget amount", "Transcribed from the FY25 Budget column", "Numeric value in millions; report dashes represented as 0.0 only where the line is structurally zero"),
    ("fy26_millions", "FY26 budget amount", "Transcribed from the FY26 Budget column", "Numeric value in millions"),
    ("reported_change_millions", "Report-reported FY25-to-FY26 dollar change", "Transcribed from the report's change column", "Parentheses converted to negative numbers"),
    ("reported_change_pct", "Report-reported FY25-to-FY26 percentage change", "Transcribed from the report's percentage column", "Blank when the report shows a dash or no meaningful percentage"),
    ("extraction_note", "Provenance and interpretation note", "Added during export", "Values are rounded to the report's displayed precision; source page is retained for audit"),
]


def main() -> None:
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            """
            SELECT d.filename, d.document_title, d.source_page, d.units,
                   f.section, f.label, f.line_kind, f.fy25_millions,
                   f.fy26_millions, f.reported_change_millions,
                   f.reported_change_pct
            FROM financial_line_item AS f
            JOIN source_document AS d ON d.source_id = f.source_id
            ORDER BY f.line_item_id
            """
        ).fetchall()

    with DATA_PATH.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(DATA_COLUMNS)
        for row in rows:
            writer.writerow((*row, "Transcribed from the FY25/FY26 Operating Sources and Uses table; values are reported in $ millions."))

    with DICT_PATH.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["column_name", "meaning", "population_method", "allowed_or_source_values"])
        writer.writerows(COLUMN_NOTES)

    print(f"created {DATA_PATH} with {len(rows)} rows")
    print(f"created {DICT_PATH} with {len(COLUMN_NOTES)} column notes")


if __name__ == "__main__":
    main()
