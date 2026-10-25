"""
Validation utilities for Sales Data Analysis System.
Provides sanity checks for file formats, schema mappings, and profit formula verification.
"""

from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np


def validate_file_format(filename: str) -> Tuple[bool, str, str]:
    """
    Validates file extension and identifies format.
    Returns: (is_valid, extension, message)
    """
    if not filename:
        return False, "", "No filename provided."
    
    parts = filename.lower().rsplit(".", 1)
    if len(parts) < 2:
        return False, "", "File has no extension. Please upload a .csv or .xlsx file."
    
    ext = parts[1]
    if ext == "csv":
        return True, "csv", "Valid CSV file."
    elif ext in ["xlsx", "xls"]:
        return True, "xlsx", "Valid Excel file."
    else:
        return False, ext, f"Unsupported file format '.{ext}'. Supported formats are CSV (.csv) and Excel (.xlsx)."


def validate_profit_formula(
    df: pd.DataFrame,
    sales_col: Optional[str] = None,
    unit_cost_col: Optional[str] = None,
    qty_col: Optional[str] = None,
    unit_price_col: Optional[str] = None,
    discount_col: Optional[str] = None,
    profit_col: Optional[str] = None,
    user_confirmed_formula: bool = False
) -> Dict[str, Any]:
    """
    Validates whether profit can be reliably calculated from available columns.
    
    Returns a dict with:
      - is_valid: bool
      - status: 'verified', 'scale_warning', 'ambiguous', 'unavailable'
      - formula_name: str
      - formula_description: str
      - profit_series: Optional[pd.Series]
      - explanation: str
    """
    # Case 1: Pre-existing explicit profit column
    if profit_col and profit_col in df.columns:
        series = pd.to_numeric(df[profit_col], errors="coerce")
        valid_count = series.notna().sum()
        if valid_count > 0:
            return {
                "is_valid": True,
                "status": "verified",
                "formula_name": f"Existing '{profit_col}' Column",
                "formula_description": f"Directly sourced from existing column: {profit_col}",
                "profit_series": series,
                "explanation": f"Using verified profit values directly from column '{profit_col}'."
            }
        else:
            return {
                "is_valid": False,
                "status": "unavailable",
                "formula_name": "None",
                "formula_description": "N/A",
                "profit_series": None,
                "explanation": f"Column '{profit_col}' contains no valid numeric values."
            }

    # Case 2: Required columns missing for derivation
    if not sales_col or sales_col not in df.columns:
        return {
            "is_valid": False,
            "status": "unavailable",
            "formula_name": "None",
            "formula_description": "N/A",
            "profit_series": None,
            "explanation": "Sales/Revenue column is required to calculate profit."
        }

    if not unit_cost_col or unit_cost_col not in df.columns:
        return {
            "is_valid": False,
            "status": "unavailable",
            "formula_name": "None",
            "formula_description": "N/A",
            "profit_series": None,
            "explanation": "Unit Cost column is not available; profit cannot be calculated reliably."
        }

    # If Unit_Cost is present, do we have Quantity?
    has_qty = qty_col and qty_col in df.columns

    sales = pd.to_numeric(df[sales_col], errors="coerce")
    cost = pd.to_numeric(df[unit_cost_col], errors="coerce")

    if has_qty:
        qty = pd.to_numeric(df[qty_col], errors="coerce")
        # Check potential total cost: Unit Cost * Quantity
        total_cost = cost * qty
        formula_desc = f"Profit = {sales_col} - ({unit_cost_col} × {qty_col})"
    else:
        # Without quantity, is cost total cost or unit cost?
        total_cost = cost
        formula_desc = f"Profit = {sales_col} - {unit_cost_col} (Assuming {unit_cost_col} represents Total Cost)"

    # Inspect data alignment and scale:
    # Filter rows where both sales and calculated cost are positive and valid
    valid_mask = sales.notna() & total_cost.notna() & (sales > 0)
    if valid_mask.sum() == 0:
        return {
            "is_valid": False,
            "status": "unavailable",
            "formula_name": "None",
            "formula_description": "N/A",
            "profit_series": None,
            "explanation": "No valid overlapping numeric rows between sales and cost columns."
        }

    # Check whether calculated cost drastically exceeds sales across the majority of rows
    cost_exceeds = (total_cost[valid_mask] > sales[valid_mask])
    cost_exceeds_ratio = cost_exceeds.mean()

    # Check discount ambiguity if discount and unit_price are also present
    discount_note = ""
    if discount_col and discount_col in df.columns and unit_price_col and unit_price_col in df.columns and has_qty:
        disc = pd.to_numeric(df[discount_col], errors="coerce")
        uprice = pd.to_numeric(df[unit_price_col], errors="coerce")
        
        # Check if sales is already net of discount:
        # e.g., compare sales vs qty * uprice vs qty * uprice * (1 - disc)
        mask = valid_mask & disc.notna() & uprice.notna() & (uprice > 0)
        if mask.sum() > 10:
            gross = (qty[mask] * uprice[mask]).mean()
            net_disc = (qty[mask] * uprice[mask] * (1 - disc[mask])).mean()
            actual_sales_mean = sales[mask].mean()
            if abs(actual_sales_mean - net_disc) < abs(actual_sales_mean - gross):
                discount_note = " (Note: Evidence indicates Sales Amount is already net of discounts. Discounts must not be subtracted again.)"

    profit = sales - total_cost

    # If >70% of rows have cost > sales (like the sample dataset where unit_cost is $3000 and sales is $4000 for 20 units),
    # this indicates a significant scale mismatch (e.g. Unit Cost might not be per-unit, or dataset columns are synthetic).
    if cost_exceeds_ratio > 0.70 and not user_confirmed_formula:
        return {
            "is_valid": False,
            "status": "scale_warning",
            "formula_name": f"Unverified: {formula_desc}",
            "formula_description": formula_desc,
            "profit_series": profit,
            "cost_exceeds_ratio": cost_exceeds_ratio,
            "explanation": (
                f"Data quality notice: Calculated cost ({unit_cost_col} × {qty_col if has_qty else '1'}) "
                f"exceeds sales amount in {cost_exceeds_ratio:.1%} of records, resulting in massive negative profits. "
                f"Column scale or definitions appear inconsistent. Profit calculation is held pending user confirmation "
                f"to prevent displaying misleading business metrics.{discount_note}"
            )
        }

    return {
        "is_valid": True,
        "status": "verified",
        "formula_name": f"Verified Formula: {formula_desc}",
        "formula_description": formula_desc,
        "profit_series": profit,
        "explanation": f"Profit calculated using: {formula_desc}.{discount_note}"
    }


def check_analysis_capabilities(mapped_cols: Dict[str, Optional[str]]) -> Dict[str, Tuple[bool, str]]:
    """
    Determines which analyses are possible given the mapped columns.
    Returns dict: {analysis_name: (is_available, reason_or_status)}
    """
    capabilities = {}
    
    # 1. Total Sales / Revenue KPIs
    if mapped_cols.get("sales_amount"):
        capabilities["Total Sales KPI"] = (True, f"Enabled via column '{mapped_cols['sales_amount']}'")
    else:
        capabilities["Total Sales KPI"] = (False, "Disabled: Sales amount / revenue column not mapped.")

    # 2. Units Sold KPI
    if mapped_cols.get("quantity_sold"):
        capabilities["Units Sold KPI"] = (True, f"Enabled via column '{mapped_cols['quantity_sold']}'")
    else:
        capabilities["Units Sold KPI"] = (False, "Disabled: Quantity sold column not mapped.")

    # 3. Category Sales Breakdown
    if mapped_cols.get("sales_amount") and mapped_cols.get("product_category"):
        capabilities["Category Sales Breakdown"] = (True, f"Enabled via '{mapped_cols['product_category']}' and '{mapped_cols['sales_amount']}'")
    else:
        missing = []
        if not mapped_cols.get("sales_amount"): missing.append("Sales Amount")
        if not mapped_cols.get("product_category"): missing.append("Product Category")
        capabilities["Category Sales Breakdown"] = (False, f"Disabled: Missing {', '.join(missing)}")

    # 4. Regional Sales Breakdown
    if mapped_cols.get("sales_amount") and mapped_cols.get("region"):
        capabilities["Regional Performance Breakdown"] = (True, f"Enabled via '{mapped_cols['region']}' and '{mapped_cols['sales_amount']}'")
    else:
        missing = []
        if not mapped_cols.get("sales_amount"): missing.append("Sales Amount")
        if not mapped_cols.get("region"): missing.append("Region")
        capabilities["Regional Performance Breakdown"] = (False, f"Disabled: Missing {', '.join(missing)}")

    # 5. Sales Representative Breakdown
    if mapped_cols.get("sales_amount") and mapped_cols.get("sales_rep"):
        capabilities["Sales Rep Performance"] = (True, f"Enabled via '{mapped_cols['sales_rep']}' and '{mapped_cols['sales_amount']}'")
    else:
        capabilities["Sales Rep Performance"] = (False, "Disabled: Sales Rep or Sales column not mapped.")

    # 6. Sales Channel Breakdown
    if mapped_cols.get("sales_amount") and mapped_cols.get("sales_channel"):
        capabilities["Sales Channel Breakdown"] = (True, f"Enabled via '{mapped_cols['sales_channel']}' and '{mapped_cols['sales_amount']}'")
    else:
        capabilities["Sales Channel Breakdown"] = (False, "Disabled: Sales Channel or Sales column not mapped.")

    # 7. Time-Series Analysis
    if mapped_cols.get("sales_amount") and mapped_cols.get("sale_date"):
        capabilities["Time-Series Analysis"] = (True, f"Enabled via '{mapped_cols['sale_date']}' and '{mapped_cols['sales_amount']}'")
    else:
        missing = []
        if not mapped_cols.get("sales_amount"): missing.append("Sales Amount")
        if not mapped_cols.get("sale_date"): missing.append("Sale Date")
        capabilities["Time-Series Analysis"] = (False, f"Disabled: Missing {', '.join(missing)}")

    # 8. Profit Analysis
    if mapped_cols.get("sales_amount") and mapped_cols.get("unit_cost"):
        capabilities["Profit Analysis"] = (True, "Columns available (subject to formula validation)")
    else:
        capabilities["Profit Analysis"] = (False, "Disabled: Unit Cost or Sales Amount not mapped.")

    # 9. Descriptive Statistics (always available if any numeric column exists)
    capabilities["Descriptive Statistics"] = (True, "Available for all recognized numeric columns.")

    # 10. Custom Aggregation (available if at least one category and one numeric column exist)
    capabilities["Custom Grouping & Aggregation"] = (True, "Available for user-selected category and numeric pairs.")

    return capabilities
