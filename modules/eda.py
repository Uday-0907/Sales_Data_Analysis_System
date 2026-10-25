"""
Exploratory Data Analysis (EDA) Module for Sales Data Analysis System.
Provides dataset structural overviews, column type profiles, missing value audits,
category frequency tables, and distribution summaries.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def get_dataset_overview_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns high-level structural dimensions and memory metrics of the dataset.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = memory_bytes / (1024 * 1024)

    # Count types
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    text_cols = [c for c in df.columns if c not in numeric_cols and c not in date_cols]

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "total_cells": total_cells,
        "memory_mb": memory_mb,
        "numeric_column_count": len(numeric_cols),
        "date_column_count": len(date_cols),
        "categorical_column_count": len(text_cols),
        "numeric_columns": numeric_cols,
        "date_columns": date_cols,
        "categorical_columns": text_cols
    }


def get_column_profile_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a tabular summary profiling every column in the dataset:
    Data type, Non-null count, Null count, Null percentage, and Unique count.
    """
    profiles = []
    total_rows = len(df)

    for col in df.columns:
        series = df[col]
        non_null = int(series.notna().sum())
        null_count = total_rows - non_null
        null_pct = (null_count / total_rows * 100.0) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        dtype_str = str(series.dtype)

        profiles.append({
            "Column Name": col,
            "Detected Data Type": dtype_str,
            "Valid Values": non_null,
            "Missing Values": null_count,
            "Missing %": f"{null_pct:.2f}%",
            "Distinct Values": unique_count
        })

    return pd.DataFrame(profiles)


def get_category_frequency_table(
    df: pd.DataFrame,
    category_col: str,
    top_n: int = 15
) -> pd.DataFrame:
    """
    Calculates frequency and percentage breakdown for a categorical column.
    """
    if category_col not in df.columns:
        return pd.DataFrame()

    counts = df[category_col].dropna().value_counts(ascending=False).head(top_n)
    total = df[category_col].dropna().count()

    result = []
    for val, count in counts.items():
        pct = (count / total * 100.0) if total > 0 else 0.0
        result.append({
            category_col: str(val),
            "Record Count": int(count),
            "Share of Total (%)": f"{pct:.2f}%"
        })

    return pd.DataFrame(result)


def get_date_coverage_summary(df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
    """
    Returns start date, end date, span in days, and missing date count.
    """
    if date_col not in df.columns or not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        return {"available": False, "reason": f"Column '{date_col}' is not a recognized date format."}

    valid_dates = df[date_col].dropna()
    if valid_dates.empty:
        return {"available": False, "reason": f"Column '{date_col}' contains no valid date records."}

    min_date = valid_dates.min()
    max_date = valid_dates.max()
    span_days = (max_date - min_date).days

    return {
        "available": True,
        "earliest_date": min_date.strftime("%Y-%m-%d"),
        "latest_date": max_date.strftime("%Y-%m-%d"),
        "timespan_days": span_days,
        "valid_records": len(valid_dates),
        "missing_records": len(df) - len(valid_dates)
    }
