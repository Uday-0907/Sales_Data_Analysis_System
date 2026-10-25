"""
Sales Analysis and Aggregation Module for Sales Data Analysis System.
Calculates validated business KPIs, category breakdowns, regional performance,
sales rep rankings, and custom user-selected group aggregations.
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np


def compute_kpis(
    df: pd.DataFrame,
    mapped_columns: Dict[str, Optional[str]],
    profit_validation_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculates executive KPIs based strictly on available and validated data.
    Never fabricates values or substitutes 0 for missing columns.
    """
    kpis = {
        "total_records": len(df),
        "total_sales": None,
        "valid_sales_records": 0,
        "excluded_sales_records": 0,
        "average_sale": None,
        "total_quantity": None,
        "valid_quantity_records": 0,
        "profit": None,
        "profit_status": "unavailable",
        "profit_formula": "N/A",
        "profit_explanation": "Profit calculation requires validated revenue and cost columns."
    }

    # 1. Total Sales & Average Sale
    sales_col = mapped_columns.get("sales_amount")
    if sales_col and sales_col in df.columns:
        valid_sales = pd.to_numeric(df[sales_col], errors="coerce").dropna()
        if not valid_sales.empty:
            kpis["total_sales"] = float(valid_sales.sum())
            kpis["average_sale"] = float(valid_sales.mean())
            kpis["valid_sales_records"] = len(valid_sales)
            kpis["excluded_sales_records"] = len(df) - len(valid_sales)

    # 2. Total Quantity Sold
    qty_col = mapped_columns.get("quantity_sold")
    if qty_col and qty_col in df.columns:
        valid_qty = pd.to_numeric(df[qty_col], errors="coerce").dropna()
        if not valid_qty.empty:
            kpis["total_quantity"] = float(valid_qty.sum())
            kpis["valid_quantity_records"] = len(valid_qty)

    # 3. Profit Calculation
    if profit_validation_result and profit_validation_result.get("is_valid"):
        series = profit_validation_result.get("profit_series")
        if series is not None:
            # Align series index to filtered DataFrame if necessary
            aligned = series.loc[series.index.intersection(df.index)].dropna()
            if not aligned.empty:
                kpis["profit"] = float(aligned.sum())
                kpis["profit_status"] = "verified"
                kpis["profit_formula"] = profit_validation_result.get("formula_description", "")
                kpis["profit_explanation"] = profit_validation_result.get("explanation", "")
    elif profit_validation_result:
        kpis["profit_status"] = profit_validation_result.get("status", "unavailable")
        kpis["profit_explanation"] = profit_validation_result.get("explanation", "")
        kpis["profit_formula"] = profit_validation_result.get("formula_description", "N/A")

    return kpis


def aggregate_breakdown(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    agg_func: str = "sum",
    top_n: Optional[int] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Performs grouping and aggregation of a value column by a categorical column.
    Supports: 'sum', 'mean', 'count', 'min', 'max'.
    
    Returns:
      (aggregated_df, error_or_warning_message)
    """
    if group_col not in df.columns:
        return pd.DataFrame(), f"Grouping column '{group_col}' not found in dataset."
    if value_col not in df.columns:
        return pd.DataFrame(), f"Measure column '{value_col}' not found in dataset."

    # Copy and ensure value is numeric
    sub_df = df[[group_col, value_col]].copy()
    sub_df[value_col] = pd.to_numeric(sub_df[value_col], errors="coerce")
    valid_df = sub_df.dropna(subset=[value_col, group_col])

    if valid_df.empty:
        return pd.DataFrame(), f"No valid rows found for '{group_col}' and '{value_col}'."

    agg_func_map = {
        "sum": "sum",
        "mean": "mean",
        "count": "count",
        "min": "min",
        "max": "max"
    }

    chosen_func = agg_func_map.get(agg_func.lower(), "sum")

    grouped = valid_df.groupby(group_col, as_index=False)[value_col].agg(chosen_func)
    grouped.columns = [group_col, f"{value_col} ({chosen_func.upper()})"]

    # Sort descending
    sort_col = grouped.columns[1]
    grouped = grouped.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

    # Compute percentage share if sum
    if chosen_func == "sum" and grouped[sort_col].sum() > 0:
        total_sum = grouped[sort_col].sum()
        grouped["Share of Total (%)"] = (grouped[sort_col] / total_sum * 100.0).round(2)

    if top_n and top_n > 0:
        grouped = grouped.head(top_n)

    return grouped, ""
