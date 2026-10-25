"""
Data Cleaning and Quality Assurance Module for Sales Data Analysis System.
Safely cleans rough and imperfect datasets, handles missing values, detects duplicates,
parses text-formatted numbers and currencies, validates dates, and produces a transparent audit report.
"""

import re
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np


MISSING_MARKERS = {
    "", " ", "na", "n/a", "nan", "null", "none", "-", "--", "?", "nil", "unknown", "n.a."
}


def clean_numeric_value(val: Any) -> Tuple[Optional[float], bool]:
    """
    Safely converts a single rough text or numeric value into a float.
    Handles commas, currency symbols ($, ₹, €, £), and parenthesized negatives (e.g., '(1500)').
    
    Returns:
      (converted_float_or_None, conversion_succeeded_or_was_already_none)
    """
    if pd.isna(val):
        return None, True

    if isinstance(val, (int, float, np.integer, np.floating)):
        if np.isnan(val):
            return None, True
        return float(val), True

    s = str(val).strip()
    if s.lower() in MISSING_MARKERS:
        return None, True

    # Check for parenthesized negative format: (123.45) -> -123.45
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()

    # Remove recognized currency symbols
    s = re.sub(r"[\$₹€£¥]", "", s).strip()

    # Remove commas used as thousand separators (e.g. 1,500.00 -> 1500.00)
    # Be careful not to remove decimal commas if European format like 1.500,00
    if re.search(r"^\d{1,3}(,\d{3})+(\.\d+)?$", s):
        s = s.replace(",", "")
    elif re.search(r"^\d+(,\d+)?$", s) and "," in s:
        # Simple single comma: check if it's 1,500 vs 1,5
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")

    try:
        num = float(s)
        if is_negative:
            num = -num
        return num, True
    except (ValueError, TypeError):
        return None, False


def clean_numeric_column(series: pd.Series) -> Tuple[pd.Series, int, int, int]:
    """
    Cleans a pandas Series suspected to be numeric.
    
    Returns:
      (cleaned_series, attempted_count, succeeded_count, failed_count)
    """
    attempted = 0
    succeeded = 0
    failed = 0
    cleaned_vals = []

    for val in series:
        if pd.isna(val) or (isinstance(val, str) and val.strip().lower() in MISSING_MARKERS):
            cleaned_vals.append(np.nan)
        else:
            attempted += 1
            conv, ok = clean_numeric_value(val)
            if ok and conv is not None:
                succeeded += 1
                cleaned_vals.append(conv)
            else:
                failed += 1
                cleaned_vals.append(np.nan)

    return pd.Series(cleaned_vals, index=series.index, dtype="float64"), attempted, succeeded, failed


def clean_dataset(
    raw_df: pd.DataFrame,
    mapped_columns: Dict[str, Optional[str]],
    options: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Performs safe, non-destructive cleaning on the uploaded dataset according to options.
    Never alters the original uploaded DataFrame.
    
    Returns:
      (cleaned_df, cleaning_summary_dict)
    """
    if options is None:
        options = {}

    remove_duplicates = options.get("remove_duplicates", True)
    date_format = options.get("date_format", "auto")
    strip_whitespace = options.get("strip_whitespace", True)

    df = raw_df.copy()
    original_rows = len(df)
    original_cols = len(df.columns)

    operations_applied = []
    warnings = []
    unresolved_issues = []

    # 1. Standardize column names (strip whitespace)
    cleaned_colnames = [str(c).strip() for c in df.columns]
    if cleaned_colnames != list(df.columns):
        df.columns = cleaned_colnames
        operations_applied.append("Trimmed surrounding whitespace from column headers.")

    # 2. Standardize string missing-value representations to np.nan across object columns
    standardized_markers_count = 0
    for col in df.columns:
        if df[col].dtype == "object":
            mask = df[col].astype(str).str.strip().str.lower().isin(MISSING_MARKERS)
            count = mask.sum()
            if count > 0:
                df.loc[mask, col] = np.nan
                standardized_markers_count += count

    if standardized_markers_count > 0:
        operations_applied.append(
            f"Standardized {standardized_markers_count} empty or marker cells ('NA', '-', etc.) to genuine missing values."
        )

    # 3. Missing values analysis (Detected before dropping)
    missing_by_column = {}
    total_missing_cells = 0
    for col in df.columns:
        m_count = int(df[col].isna().sum())
        m_pct = (m_count / original_rows * 100.0) if original_rows > 0 else 0.0
        missing_by_column[col] = {
            "count": m_count,
            "percentage": m_pct
        }
        total_missing_cells += m_count

    rows_affected_by_missing = int(df.isna().any(axis=1).sum())

    # 4. Duplicate rows detection & optional removal
    exact_duplicates = int(df.duplicated().sum())
    duplicates_removed = 0
    if exact_duplicates > 0:
        warnings.append(f"Detected {exact_duplicates} exact duplicate rows.")
        if remove_duplicates:
            df = df.drop_duplicates(keep="first").reset_index(drop=True)
            duplicates_removed = exact_duplicates
            operations_applied.append(f"Removed {duplicates_removed} exact duplicate rows from the working dataset.")
        else:
            operations_applied.append(f"Retained {exact_duplicates} duplicate rows as requested in cleaning options.")
            unresolved_issues.append(f"{exact_duplicates} duplicate records retained in working data.")

    # 5. Clean text columns (strip whitespace)
    if strip_whitespace:
        text_cols_stripped = 0
        for col in df.columns:
            if df[col].dtype == "object":
                # Strip leading and trailing whitespace
                non_null_mask = df[col].notna()
                df.loc[non_null_mask, col] = df.loc[non_null_mask, col].astype(str).str.strip()
                text_cols_stripped += 1
        if text_cols_stripped > 0:
            operations_applied.append(f"Normalized leading and trailing whitespace across {text_cols_stripped} text columns.")

    # 6. Clean numeric columns
    numeric_roles = ["sales_amount", "quantity_sold", "unit_cost", "unit_price", "discount", "profit"]
    total_numeric_attempted = 0
    total_numeric_succeeded = 0
    total_numeric_failed = 0
    negative_sales_count = 0

    for role in numeric_roles:
        col_name = mapped_columns.get(role)
        if col_name and col_name in df.columns:
            cleaned_series, attempted, succeeded, failed = clean_numeric_column(df[col_name])
            df[col_name] = cleaned_series
            total_numeric_attempted += attempted
            total_numeric_succeeded += succeeded
            total_numeric_failed += failed

            if failed > 0:
                warnings.append(
                    f"Column '{col_name}' contained {failed} values that could not be parsed as numbers (coerced to NaN)."
                )
                unresolved_issues.append(f"{failed} unparseable values in '{col_name}'.")

            if role == "sales_amount":
                negs = (df[col_name] < 0).sum()
                if negs > 0:
                    negative_sales_count = int(negs)
                    warnings.append(
                        f"Detected {negative_sales_count} negative sales values in '{col_name}' (flagged as potential returns/adjustments, preserved for analysis)."
                    )

    if total_numeric_succeeded > 0:
        operations_applied.append(
            f"Parsed and converted numeric text fields: {total_numeric_succeeded} values converted successfully."
        )

    # 7. Date cleaning
    valid_dates_count = 0
    invalid_dates_count = 0
    date_col = mapped_columns.get("sale_date")
    if date_col and date_col in df.columns:
        date_series = df[date_col].copy()
        
        # Parse dates according to chosen format
        if date_format == "DD/MM/YYYY":
            parsed_dates = pd.to_datetime(date_series, format="%d/%m/%Y", errors="coerce", dayfirst=True)
        elif date_format == "MM/DD/YYYY":
            parsed_dates = pd.to_datetime(date_series, format="%m/%d/%Y", errors="coerce", dayfirst=False)
        else:
            # Auto parsing
            parsed_dates = pd.to_datetime(date_series, errors="coerce")

        valid_dates_count = int(parsed_dates.notna().sum())
        invalid_dates_count = int(date_series.notna().sum() - valid_dates_count)

        df[date_col] = parsed_dates
        operations_applied.append(
            f"Parsed date column '{date_col}': {valid_dates_count} valid dates recognized, {invalid_dates_count} invalid date records coerced to NaT."
        )

        if invalid_dates_count > 0:
            warnings.append(f"{invalid_dates_count} date records could not be interpreted reliably and were set to NaT.")
            unresolved_issues.append(f"{invalid_dates_count} invalid date values in '{date_col}'.")

    # 8. Assess calculation exclusions
    records_excluded = {}
    sales_col = mapped_columns.get("sales_amount")
    if sales_col and sales_col in df.columns:
        missing_sales = int(df[sales_col].isna().sum())
        if missing_sales > 0:
            records_excluded["sales_metrics"] = missing_sales
            warnings.append(
                f"{missing_sales} records have missing sales amounts and will be safely excluded from revenue calculations without deleting rows."
            )

    qty_col = mapped_columns.get("quantity_sold")
    if qty_col and qty_col in df.columns:
        missing_qty = int(df[qty_col].isna().sum())
        if missing_qty > 0:
            records_excluded["quantity_metrics"] = missing_qty

    final_rows = len(df)
    final_cols = len(df.columns)

    cleaning_summary = {
        "original_rows": original_rows,
        "final_rows": final_rows,
        "original_cols": original_cols,
        "final_cols": final_cols,
        "total_missing_cells": total_missing_cells,
        "rows_affected_by_missing": rows_affected_by_missing,
        "missing_by_column": missing_by_column,
        "duplicates_detected": exact_duplicates,
        "duplicates_removed": duplicates_removed,
        "numeric_conversions_attempted": total_numeric_attempted,
        "numeric_conversions_succeeded": total_numeric_succeeded,
        "numeric_conversions_failed": total_numeric_failed,
        "valid_dates_count": valid_dates_count,
        "invalid_dates_count": invalid_dates_count,
        "negative_sales_count": negative_sales_count,
        "records_excluded_per_metric": records_excluded,
        "operations_applied": operations_applied,
        "warnings": warnings,
        "unresolved_issues": unresolved_issues,
        "is_completely_clean": len(unresolved_issues) == 0 and total_missing_cells == 0
    }

    return df, cleaning_summary
