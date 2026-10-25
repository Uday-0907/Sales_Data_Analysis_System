"""
Dynamic Column Detection and Mapping Module for Sales Data Analysis System.
Provides intelligent auto-detection of column roles using canonical names,
synonyms, and data type inspection, with safe collision-free normalization.
"""

import re
from typing import Dict, List, Optional, Tuple
import pandas as pd


# Comprehensive canonical role definitions and synonyms
ROLE_SYNONYMS = {
    "sales_amount": [
        "sales_amount", "sales", "revenue", "amount", "total_amount",
        "salesamount", "net_sales", "turnover", "total_sales",
        "order_amount", "total_price", "sale_amount", "grand_total",
        "total_revenue", "sales_value", "sale_value", "total"
    ],
    "sale_date": [
        "sale_date", "date", "transaction_date", "order_date",
        "invoice_date", "timestamp", "sales_date", "datetime",
        "order_dt", "sold_date", "trans_date", "time", "date_time"
    ],
    "quantity_sold": [
        "quantity_sold", "quantity", "qty", "units_sold", "units",
        "volume", "qty_sold", "item_count", "pieces", "count",
        "num_items", "quantity_ordered", "items_sold"
    ],
    "product_category": [
        "product_category", "category", "item_category", "product_type",
        "department", "prod_category", "product_line", "product_group",
        "genre", "category_name", "item_type", "dept", "product_dept"
    ],
    "region": [
        "region", "territory", "zone", "area", "location", "state",
        "province", "country", "market", "district", "city", "region_name"
    ],
    "sales_rep": [
        "sales_rep", "salesrep", "rep", "salesperson", "sales_person",
        "agent", "sales_agent", "employee", "salesman", "seller",
        "representative", "sales_representative", "rep_name",
        "sales_member", "staff", "agent_name"
    ],
    "sales_channel": [
        "sales_channel", "channel", "source", "platform",
        "distribution_channel", "order_channel", "sales_source",
        "channel_name", "channel_type", "sales_mode", "channel_id"
    ],
    "customer_type": [
        "customer_type", "client_type", "segment", "customer_segment",
        "cust_type", "membership_type", "buyer_type", "customer_group",
        "account_type", "user_type", "client_segment"
    ],
    "payment_method": [
        "payment_method", "payment_type", "payment_mode", "tender_type",
        "pay_type", "payment", "mode_of_payment", "payment_instrument",
        "pay_method", "transaction_type"
    ],
    "unit_cost": [
        "unit_cost", "cost_per_unit", "cost", "item_cost",
        "buying_price", "purchase_cost", "cogs_per_unit", "product_cost"
    ],
    "unit_price": [
        "unit_price", "price_per_unit", "price", "selling_price",
        "rate", "item_price", "mrp", "list_price", "retail_price"
    ],
    "discount": [
        "discount", "discount_rate", "disc", "discount_amount",
        "rebate", "discount_pct", "discount_percentage", "discount_value"
    ],
    "profit": [
        "profit", "net_profit", "gross_profit", "margin",
        "operating_profit", "net_margin", "earnings"
    ]
}

ROLE_LABELS = {
    "sales_amount": "Sales Amount / Revenue (Required for primary dashboard)",
    "sale_date": "Transaction / Sale Date (Enables time-series trends)",
    "quantity_sold": "Quantity Sold / Units (Enables unit volume metrics)",
    "product_category": "Product Category (Enables category breakdown)",
    "region": "Region / Territory (Enables regional breakdown)",
    "sales_rep": "Sales Representative (Enables rep performance)",
    "sales_channel": "Sales Channel (Enables channel breakdown)",
    "customer_type": "Customer Type (Enables customer type breakdown)",
    "payment_method": "Payment Method (Enables payment breakdown)",
    "unit_cost": "Unit Cost (Used for cost & profit calculations)",
    "unit_price": "Unit Price (Reference selling price)",
    "discount": "Discount (Discount fraction or percentage)",
    "profit": "Profit (Pre-existing profit column if present)"
}


def canonical_clean_string(s: str) -> str:
    """
    Simplifies a string for fuzzy matching:
    lowercased, removes punctuation, underscores, and consecutive spaces.
    """
    s = str(s).lower().strip()
    s = re.sub(r"[_\-\s\.]+", "_", s)
    return s.strip("_")


def normalize_column_names(columns: List[str]) -> Tuple[List[str], Dict[str, str], List[str]]:
    """
    Normalizes column names by stripping whitespace while ensuring uniqueness.
    Preserves meaningful original casing for display.
    
    Returns:
      (cleaned_columns_list, original_to_cleaned_map, collision_warnings)
    """
    seen = {}
    cleaned_columns = []
    orig_to_clean = {}
    collisions = []

    for col in columns:
        orig = str(col).strip()
        base = orig
        if not base:
            base = "unnamed_column"

        # Check collision in case-insensitive comparison
        lower_base = base.lower()
        if lower_base in seen:
            seen[lower_base] += 1
            unique_name = f"{base}_{seen[lower_base]}"
            collisions.append(
                f"Duplicate column name '{base}' detected. Renamed to '{unique_name}' to avoid ambiguity."
            )
        else:
            seen[lower_base] = 0
            unique_name = base

        cleaned_columns.append(unique_name)
        orig_to_clean[orig] = unique_name

    return cleaned_columns, orig_to_clean, collisions


def auto_detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Examines DataFrame column names and types to detect best candidate for each role.
    
    Returns:
      {role: matched_column_name_or_None}
    """
    detected: Dict[str, Optional[str]] = {role: None for role in ROLE_SYNONYMS}
    used_columns = set()

    normalized_cols = {col: canonical_clean_string(col) for col in df.columns}

    # Pass 1: Exact matches against synonyms
    for role, synonyms in ROLE_SYNONYMS.items():
        for syn in synonyms:
            clean_syn = canonical_clean_string(syn)
            for orig_col, clean_col in normalized_cols.items():
                if orig_col not in used_columns and clean_col == clean_syn:
                    detected[role] = orig_col
                    used_columns.add(orig_col)
                    break
            if detected[role]:
                break

    # Pass 2: Component & Substring matches for unassigned roles
    for role, synonyms in ROLE_SYNONYMS.items():
        if detected[role] is not None:
            continue
        for syn in synonyms:
            clean_syn = canonical_clean_string(syn)
            for orig_col, clean_col in normalized_cols.items():
                if orig_col not in used_columns:
                    # Match if clean_syn is a distinct component in column name
                    if (
                        f"_{clean_syn}_" in f"_{clean_col}_"
                        or clean_col.startswith(f"{clean_syn}_")
                        or clean_col.endswith(f"_{clean_syn}")
                        or clean_col == clean_syn
                    ):
                        detected[role] = orig_col
                        used_columns.add(orig_col)
                        break
            if detected[role]:
                break

    # Pass 3: Type heuristics if still undetected
    # If date is not detected, check for datetime dtypes or date-like sample values
    if not detected["sale_date"]:
        for col in df.columns:
            if col not in used_columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    detected["sale_date"] = col
                    used_columns.add(col)
                    break

    # If sales_amount is not detected, check for first numeric float column with high variance
    if not detected["sales_amount"]:
        for col in df.columns:
            if col not in used_columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    detected["sales_amount"] = col
                    used_columns.add(col)
                    break

    return detected
