"""
Time-Series Analysis Module for Sales Data Analysis System.
Aggregates sales performance across Day, Month, and Year periods
in strict chronological order without forecasting or fake data.
"""

from typing import Tuple, Dict, Any
import pandas as pd


def aggregate_time_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    frequency: str = "Month",
    agg_func: str = "sum"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Groups and aggregates a numeric measure across chronological time intervals.
    Frequencies supported: 'Day', 'Month', 'Year'.
    
    Returns:
      (time_series_df, summary_meta)
    """
    meta = {
        "is_available": False,
        "valid_date_records": 0,
        "excluded_date_records": 0,
        "frequency": frequency,
        "message": ""
    }

    if date_col not in df.columns:
        meta["message"] = f"Date column '{date_col}' not found in dataset."
        return pd.DataFrame(), meta

    if value_col not in df.columns:
        meta["message"] = f"Measure column '{value_col}' not found in dataset."
        return pd.DataFrame(), meta

    # Work on clean copy with parsed dates
    dated = df[[date_col, value_col]].copy()
    dated[value_col] = pd.to_numeric(dated[value_col], errors="coerce")
    
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(dated[date_col]):
        dated[date_col] = pd.to_datetime(dated[date_col], errors="coerce")

    valid_mask = dated[date_col].notna() & dated[value_col].notna()
    valid_df = dated[valid_mask].copy()

    total_records = len(df)
    valid_count = len(valid_df)
    excluded_count = total_records - valid_count

    meta["valid_date_records"] = valid_count
    meta["excluded_date_records"] = excluded_count

    if valid_df.empty:
        meta["message"] = "No valid records with both a recognizable date and numeric measure exist."
        return pd.DataFrame(), meta

    # Group by selected frequency using vectorized PeriodIndex
    freq_map = {
        "Day": "D",
        "Month": "M",
        "Year": "Y"
    }
    freq_code = freq_map.get(frequency, "M")

    # Group by Period first (fast vectorized integer arithmetic), then format resulting aggregate labels
    period_series = valid_df[date_col].dt.to_period(freq_code)
    grouped = valid_df.groupby(period_series, as_index=False)[value_col].agg(agg_func)
    grouped = grouped.sort_values(by=date_col).reset_index(drop=True)

    if freq_code == "D":
        grouped["Period"] = grouped[date_col].dt.strftime("%Y-%m-%d")
    elif freq_code == "M":
        grouped["Period"] = grouped[date_col].dt.strftime("%b %Y")
    else:  # Year
        grouped["Period"] = grouped[date_col].dt.strftime("%Y")

    result_df = grouped[["Period", value_col]].copy()
    result_df.columns = ["Period", f"{value_col} ({agg_func.upper()})"]

    meta["is_available"] = True
    meta["message"] = f"Aggregated {valid_count:,} records by {frequency}."
    return result_df, meta
