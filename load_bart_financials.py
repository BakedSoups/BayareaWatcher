"""Load the FY25/FY26 operating sources and uses table from the BART PAFR."""

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "bart_financials.sqlite"
PDF_NAME = "BART_FY25 PAFR_Final.pdf"

ROWS = [
    # section, label, FY25, FY26, change, change_pct, kind
    ("Operating Sources", "Rail Passenger Revenue", 235.1, 259.1, 24.0, 10.2, "detail"),
    ("Operating Sources", "ADA Passenger Revenue", 0.6, 0.6, 0.0, 6.7, "detail"),
    ("Operating Sources", "Parking Revenue", 16.5, 19.9, 3.4, 20.7, "detail"),
    ("Operating Sources", "Other Operating Revenue", 45.3, 45.4, 0.1, 0.3, "detail"),
    ("Operating Sources", "Subtotal - Operating Revenue", 297.5, 325.1, 27.6, 9.3, "subtotal"),
    ("Financial Assistance", "Sales Tax Revenue", 320.3, 314.1, -6.2, -1.9, "detail"),
    ("Financial Assistance", "Property Tax Revenue", 64.3, 68.0, 3.7, 5.8, "detail"),
    ("Financial Assistance", "VTA Financial Assistance", 35.2, 35.9, 0.7, 2.1, "detail"),
    ("Financial Assistance", "State Transit Assistance", 48.8, 45.8, -3.0, -6.1, "detail"),
    ("Financial Assistance", "Low Carbon Funding Programs", 17.0, 32.2, 15.2, 89.4, "detail"),
    ("Financial Assistance", "Local & Other Assistance", 14.8, 15.7, 0.9, 6.1, "detail"),
    ("Financial Assistance", "Subtotal - Financial Assistance", 500.3, 511.8, 11.5, 2.3, "subtotal"),
    ("Operating Sources", "Total - Operating Sources", 797.8, 836.9, 39.1, 4.9, "total"),
    ("Operating Uses", "Labor & Benefits", 780.6, 763.3, -17.3, -2.2, "detail"),
    ("Operating Uses", "ADA Paratransit", 22.5, 26.3, 3.8, 16.9, "detail"),
    ("Operating Uses", "Purchased Transportation", 8.4, 8.5, 0.1, 1.6, "detail"),
    ("Operating Uses", "Traction Power", 61.6, 65.0, 3.4, 5.5, "detail"),
    ("Operating Uses", "Other Non-Labor", 160.7, 143.5, -17.2, -10.7, "detail"),
    ("Operating Uses", "Subtotal - Operating Expense", 1033.9, 1006.7, -27.2, -2.6, "subtotal"),
    ("Debt Service & Allocations", "Bond Debt Service", 60.2, 60.2, 0.0, 0.0, "detail"),
    ("Debt Service & Allocations", "Capital Reinvestment Allocation", 29.1, 43.8, 14.7, 50.6, "detail"),
    ("Debt Service & Allocations", "RHBT Reserve Allocation", 0.0, 38.2, 38.2, None, "detail"),
    ("Debt Service & Allocations", "Other Allocations", 3.0, 3.0, 0.0, -1.1, "detail"),
    ("Debt Service & Allocations", "Subtotal - Debt Service & Allocations", 92.2, 145.2, 53.0, 57.4, "subtotal"),
    ("Operating Uses", "Total Operating Uses", 1126.1, 1151.8, 25.7, 2.3, "total"),
    ("Operating Result", "Net Result Before Emergency Assistance", -328.2, -315.0, 13.2, -4.0, "result"),
    ("Operating Result", "Emergency Assistance", 328.2, 315.0, -13.2, -4.0, "detail"),
    ("Operating Result", "NET RESULT", 0.0, 0.0, 0.0, None, "result"),
]


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE source_document (
                source_id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                document_title TEXT NOT NULL,
                report_period TEXT NOT NULL,
                source_page INTEGER NOT NULL,
                units TEXT NOT NULL
            );
            CREATE TABLE financial_line_item (
                line_item_id INTEGER PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES source_document(source_id),
                section TEXT NOT NULL,
                label TEXT NOT NULL,
                line_kind TEXT NOT NULL CHECK (line_kind IN ('detail', 'subtotal', 'total', 'result')),
                fy25_millions NUMERIC NOT NULL,
                fy26_millions NUMERIC NOT NULL,
                reported_change_millions NUMERIC NOT NULL,
                reported_change_pct NUMERIC,
                UNIQUE(source_id, label)
            );
            CREATE VIEW budget_comparison AS
            SELECT label, section, line_kind, fy25_millions, fy26_millions,
                   ROUND(fy26_millions - fy25_millions, 1) AS calculated_change_millions,
                   reported_change_millions,
                   ROUND(fy26_millions - fy25_millions - reported_change_millions, 1) AS change_check_millions,
                   reported_change_pct
            FROM financial_line_item;
            CREATE VIEW operating_balance_check AS
            SELECT 'FY25' AS fiscal_year,
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Total - Operating Sources') AS sources_millions,
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Total Operating Uses') AS uses_millions,
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Emergency Assistance') AS emergency_assistance_millions,
                   ROUND((SELECT fy25_millions FROM financial_line_item WHERE label = 'Total - Operating Sources')
                       - (SELECT fy25_millions FROM financial_line_item WHERE label = 'Total Operating Uses'), 1) AS pre_emergency_gap_millions
            UNION ALL
            SELECT 'FY26',
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Total - Operating Sources'),
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Total Operating Uses'),
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Emergency Assistance'),
                   ROUND((SELECT fy26_millions FROM financial_line_item WHERE label = 'Total - Operating Sources')
                       - (SELECT fy26_millions FROM financial_line_item WHERE label = 'Total Operating Uses'), 1);
            CREATE VIEW detail_sum_check AS
            SELECT 'Operating Revenue' AS category,
                   ROUND((SELECT SUM(fy25_millions) FROM financial_line_item WHERE section = 'Operating Sources' AND line_kind = 'detail'), 1) AS fy25_detail_sum,
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Subtotal - Operating Revenue') AS fy25_reported_subtotal,
                   ROUND((SELECT SUM(fy26_millions) FROM financial_line_item WHERE section = 'Operating Sources' AND line_kind = 'detail'), 1) AS fy26_detail_sum,
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Subtotal - Operating Revenue') AS fy26_reported_subtotal
            UNION ALL
            SELECT 'Financial Assistance',
                   ROUND((SELECT SUM(fy25_millions) FROM financial_line_item WHERE section = 'Financial Assistance' AND line_kind = 'detail'), 1),
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Subtotal - Financial Assistance'),
                   ROUND((SELECT SUM(fy26_millions) FROM financial_line_item WHERE section = 'Financial Assistance' AND line_kind = 'detail'), 1),
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Subtotal - Financial Assistance')
            UNION ALL
            SELECT 'Operating Expense',
                   ROUND((SELECT SUM(fy25_millions) FROM financial_line_item WHERE section = 'Operating Uses' AND line_kind = 'detail'), 1),
                   (SELECT fy25_millions FROM financial_line_item WHERE label = 'Subtotal - Operating Expense'),
                   ROUND((SELECT SUM(fy26_millions) FROM financial_line_item WHERE section = 'Operating Uses' AND line_kind = 'detail'), 1),
                   (SELECT fy26_millions FROM financial_line_item WHERE label = 'Subtotal - Operating Expense');
            """
        )
        db.execute(
            "INSERT INTO source_document VALUES (?, ?, ?, ?, ?, ?)",
            (1, PDF_NAME, "BART FY25 Popular Annual Financial Report", "FY25/FY26", 11, "$ millions"),
        )
        db.executemany(
            """INSERT INTO financial_line_item
               (source_id, section, label, line_kind, fy25_millions, fy26_millions,
                reported_change_millions, reported_change_pct)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
            [(section, label, kind, fy25, fy26, change, change_pct)
             for section, label, fy25, fy26, change, change_pct, kind in ROWS],
        )
        db.commit()
    print(f"created {DB_PATH} with {len(ROWS)} line items")


if __name__ == "__main__":
    main()
