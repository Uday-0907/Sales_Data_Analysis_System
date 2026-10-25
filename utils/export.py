"""
Export and download utilities for Sales Data Analysis System.
Provides formatting and conversion of DataFrames and analysis summaries to CSV and Excel bytes.
"""

import io
from typing import Dict, Any, Tuple
import pandas as pd

EXCEL_MAX_WORKSHEET_ROWS = 1_048_576


def dataframe_to_csv_bytes(df: pd.DataFrame, index: bool = False, chunksize: int = 100_000) -> bytes:
    """
    Converts a pandas DataFrame to UTF-8 encoded CSV bytes efficiently.
    Uses direct binary streaming via BytesIO with chunking to avoid large intermediate
    Python string copies in memory.
    """
    if df is None or df.empty:
        return b""
    buf = io.BytesIO()
    df.to_csv(buf, index=index, encoding="utf-8", chunksize=chunksize)
    return buf.getvalue()


def can_export_to_excel(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validates whether a DataFrame can be exported into a single Excel worksheet
    without exceeding Microsoft Excel's hard limit of 1,048,576 rows (1 header + 1,048,575 data rows).
    """
    if df is None or df.empty:
        return True, ""
    row_count = len(df)
    if row_count > EXCEL_MAX_WORKSHEET_ROWS - 1:
        return False, (
            f"Dataset contains {row_count:,} rows, exceeding Excel's single-worksheet limit of "
            f"1,048,576 rows. Please use CSV export for complete, un-truncated data."
        )
    return True, ""


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sales_Data") -> bytes:
    """
    Converts a pandas DataFrame to Excel (.xlsx) bytes using OpenPyXL.
    Strictly enforces Excel's 1,048,576 row ceiling to prevent corrupted workbooks.
    """
    if df is None or df.empty:
        return b""
    can_export, reason = can_export_to_excel(df)
    if not can_export:
        raise ValueError(reason)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()


def generate_quality_report_csv(summary: Dict[str, Any]) -> bytes:
    """
    Generates a structured CSV report of data quality and cleaning operations.
    """
    output = io.StringIO()
    output.write("Sales Data Analysis System - Data Quality and Cleaning Report\n")
    output.write("=============================================================\n\n")
    
    # 1. Dataset Dimensions
    output.write("1. DATASET DIMENSIONS\n")
    output.write(f"Original Rows,{summary.get('original_rows', 'N/A')}\n")
    output.write(f"Final Rows,{summary.get('final_rows', 'N/A')}\n")
    output.write(f"Original Columns,{summary.get('original_cols', 'N/A')}\n")
    output.write(f"Final Columns,{summary.get('final_cols', 'N/A')}\n\n")

    # 2. Missing Values
    output.write("2. MISSING VALUES DETECTED\n")
    output.write(f"Total Missing Cells,{summary.get('total_missing_cells', 0)}\n")
    output.write(f"Rows Affected by Missing Values,{summary.get('rows_affected_by_missing', 0)}\n")
    missing_by_col = summary.get("missing_by_column", {})
    if missing_by_col:
        output.write("Column Name,Missing Count,Missing Percentage (%)\n")
        for col, info in missing_by_col.items():
            output.write(f'"{col}",{info.get("count", 0)},{info.get("percentage", 0):.2f}%\n')
    output.write("\n")

    # 3. Duplicate Records
    output.write("3. DUPLICATE RECORDS\n")
    output.write(f"Exact Duplicate Rows Found,{summary.get('duplicates_detected', 0)}\n")
    output.write(f"Duplicate Rows Removed,{summary.get('duplicates_removed', 0)}\n\n")

    # 4. Conversions & Validations
    output.write("4. CONVERSIONS AND DATA PARSING\n")
    output.write(f"Numeric Conversions Attempted,{summary.get('numeric_conversions_attempted', 0)}\n")
    output.write(f"Numeric Conversions Succeeded,{summary.get('numeric_conversions_succeeded', 0)}\n")
    output.write(f"Numeric Conversions Failed/Coerced to NaN,{summary.get('numeric_conversions_failed', 0)}\n")
    output.write(f"Valid Dates Parsed,{summary.get('valid_dates_count', 0)}\n")
    output.write(f"Invalid Dates Coerced to NaT,{summary.get('invalid_dates_count', 0)}\n")
    output.write(f"Negative Sales Values Detected,{summary.get('negative_sales_count', 0)}\n\n")

    # 5. Cleaning Operations Applied
    output.write("5. CLEANING OPERATIONS APPLIED\n")
    ops = summary.get("operations_applied", [])
    if ops:
        for idx, op in enumerate(ops, start=1):
            output.write(f'{idx},"{op}"\n')
    else:
        output.write("No cleaning operations were required.\n")
    output.write("\n")

    # 6. Warnings and Unresolved Issues
    output.write("6. WARNINGS AND UNRESOLVED DATA QUALITY ISSUES\n")
    warnings = summary.get("warnings", [])
    if warnings:
        for idx, w in enumerate(warnings, start=1):
            output.write(f'{idx},"{w}"\n')
    else:
        output.write("No unresolved data-quality warnings detected.\n")

    return output.getvalue().encode("utf-8")
