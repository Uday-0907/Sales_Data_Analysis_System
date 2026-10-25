"""
Descriptive Statistics Module for Sales Data Analysis System.
Calculates core summary statistics (count, mean, median, std, min, max, quartiles, range)
for user-selected numeric columns using Pandas and NumPy.
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def calculate_descriptive_statistics(
    df: pd.DataFrame,
    selected_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Computes summary statistics for specified numeric columns.
    
    Returns:
      Formatted DataFrame with metrics as rows and columns as headers.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Identify valid numeric columns
    numeric_cols = [
        col for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col])
    ]

    if selected_columns:
        target_cols = [c for c in selected_columns if c in numeric_cols]
    else:
        target_cols = numeric_cols

    if not target_cols:
        return pd.DataFrame()

    stats_list = []

    for col in target_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        valid_count = len(series)

        if valid_count == 0:
            stats_list.append({
                "Metric": col,
                "Valid Count": 0,
                "Mean": np.nan,
                "Median": np.nan,
                "Std Deviation": np.nan,
                "Min": np.nan,
                "25% (Q1)": np.nan,
                "50% (Q2)": np.nan,
                "75% (Q3)": np.nan,
                "Max": np.nan,
                "Range": np.nan
            })
            continue

        mean_val = float(series.mean())
        median_val = float(series.median())
        std_val = float(series.std(ddof=1)) if valid_count > 1 else 0.0
        min_val = float(series.min())
        max_val = float(series.max())
        q1_val = float(series.quantile(0.25))
        q2_val = median_val
        q3_val = float(series.quantile(0.75))
        range_val = max_val - min_val

        stats_list.append({
            "Column Name": col,
            "Valid Count": f"{valid_count:,}",
            "Mean": f"{mean_val:,.2f}",
            "Median": f"{median_val:,.2f}",
            "Std Deviation": f"{std_val:,.2f}",
            "Min": f"{min_val:,.2f}",
            "25% (Q1)": f"{q1_val:,.2f}",
            "50% (Median)": f"{q2_val:,.2f}",
            "75% (Q3)": f"{q3_val:,.2f}",
            "Max": f"{max_val:,.2f}",
            "Range": f"{range_val:,.2f}"
        })

    return pd.DataFrame(stats_list)
