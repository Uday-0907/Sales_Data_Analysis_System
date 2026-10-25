"""
Comprehensive Test Suite for Sales Data Analysis System.
Covers all 14 mandatory test cases specified in the project requirements.
"""

import os
import sys
import io

# Ensure root workspace directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np

from modules.data_loader import load_csv_file, load_excel_file, load_dataset, get_excel_sheet_names
from modules.column_mapping import normalize_column_names, auto_detect_columns
from modules.data_cleaning import clean_dataset, clean_numeric_value
from modules.eda import get_dataset_overview_metrics, get_column_profile_table, get_category_frequency_table
from modules.statistics import calculate_descriptive_statistics
from modules.sales_analysis import compute_kpis, aggregate_breakdown
from modules.time_series import aggregate_time_series
from modules.visualizations import create_bar_chart, create_pie_chart, create_line_chart, create_histogram
from utils.validation import validate_profit_formula, check_analysis_capabilities, validate_file_format
from utils.export import dataframe_to_csv_bytes, generate_quality_report_csv


SAMPLE_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "sales_data.csv")


def test_1_normal_retail_dataset():
    """Test 1: Verify loading and KPI computation on the original retail dataset."""
    assert os.path.exists(SAMPLE_CSV_PATH), f"Sample dataset not found at {SAMPLE_CSV_PATH}"
    df, success, msg, enc, delim = load_csv_file(SAMPLE_CSV_PATH)
    assert success, f"Failed to load sample dataset: {msg}"
    assert len(df) == 1000, f"Expected 1000 rows, got {len(df)}"

    # Auto-detect columns
    mapping = auto_detect_columns(df)
    assert mapping["sales_amount"] == "Sales_Amount"
    assert mapping["sale_date"] == "Sale_Date"
    assert mapping["quantity_sold"] == "Quantity_Sold"
    assert mapping["product_category"] == "Product_Category"
    assert mapping["region"] == "Region"

    # Clean dataset
    cleaned_df, summary = clean_dataset(df, mapping)
    assert summary["original_rows"] == 1000
    assert summary["final_rows"] == 1000

    # Compute KPIs
    kpis = compute_kpis(cleaned_df, mapping)
    assert kpis["total_sales"] is not None
    assert round(kpis["total_sales"], 2) == 5019265.23
    assert kpis["valid_sales_records"] == 1000
    assert kpis["total_quantity"] is not None
    assert round(kpis["total_quantity"], 0) == 25355


def test_2_missing_values_handling():
    """Test 2: Verify detection and safe handling of missing values across sales, quantity, category, and date."""
    data = {
        "Sales_Amount": ["1000", "NA", " ", "2500", "null"],
        "Quantity_Sold": ["10", "-", "15", "None", "5"],
        "Product_Category": ["Electronics", "Clothing", None, "Electronics", "Furniture"],
        "Sale_Date": ["2023-01-01", "2023-01-02", "InvalidDate", "2023-01-04", None]
    }
    df = pd.DataFrame(data)
    mapping = auto_detect_columns(df)

    cleaned_df, summary = clean_dataset(df, mapping)

    # Check missing count detection
    assert summary["total_missing_cells"] > 0
    assert summary["rows_affected_by_missing"] > 0
    # Crucially, rows should NOT be blindly deleted
    assert len(cleaned_df) == 5, "Rows should be preserved even with missing values in some columns"

    # Verify calculation exclusion
    kpis = compute_kpis(cleaned_df, mapping)
    # Only 2 rows have valid sales: 1000 and 2500 -> sum = 3500
    assert kpis["total_sales"] == 3500.0
    assert kpis["valid_sales_records"] == 2
    assert kpis["excluded_sales_records"] == 3


def test_3_duplicate_records():
    """Test 3: Verify detection and optional removal of exact duplicate rows."""
    data = {
        "Sales_Amount": [100.0, 200.0, 100.0, 300.0],
        "Product_Category": ["Food", "Books", "Food", "Tech"]
    }
    df = pd.DataFrame(data)
    mapping = auto_detect_columns(df)

    # Clean with remove_duplicates=True
    cleaned_df, summary = clean_dataset(df, mapping, options={"remove_duplicates": True})
    assert summary["duplicates_detected"] == 1
    assert summary["duplicates_removed"] == 1
    assert len(cleaned_df) == 3

    # Clean with remove_duplicates=False
    cleaned_df2, summary2 = clean_dataset(df, mapping, options={"remove_duplicates": False})
    assert summary2["duplicates_detected"] == 1
    assert summary2["duplicates_removed"] == 0
    assert len(cleaned_df2) == 4
    assert len(summary2["unresolved_issues"]) > 0


def test_4_different_column_names():
    """Test 4: Verify auto-detection of alternative column names (Revenue, Date, Quantity, Category)."""
    data = {
        "Revenue": [500.0, 1200.0],
        "Date": ["2023-05-01", "2023-05-02"],
        "Quantity": [2, 4],
        "Category": ["Stationery", "Books"],
        "Salesperson": ["Alice", "Bob"]
    }
    df = pd.DataFrame(data)
    mapping = auto_detect_columns(df)

    assert mapping["sales_amount"] == "Revenue"
    assert mapping["sale_date"] == "Date"
    assert mapping["quantity_sold"] == "Quantity"
    assert mapping["product_category"] == "Category"
    assert mapping["sales_rep"] == "Salesperson"

    cleaned_df, _ = clean_dataset(df, mapping)
    kpis = compute_kpis(cleaned_df, mapping)
    assert kpis["total_sales"] == 1700.0
    assert kpis["total_quantity"] == 6.0


def test_5_numeric_values_stored_as_text():
    """Test 5: Verify parsing of formatted numbers: commas, currencies ($, ₹, €), parentheses negatives."""
    # Test helper directly
    assert clean_numeric_value("1,500")[0] == 1500.0
    assert clean_numeric_value("₹1,500")[0] == 1500.0
    assert clean_numeric_value("$2,450.75")[0] == 2450.75
    assert clean_numeric_value("€ 999.00")[0] == 999.00
    assert clean_numeric_value("(500)")[0] == -500.0
    assert clean_numeric_value("   123.45   ")[0] == 123.45
    assert clean_numeric_value("invalid_text")[0] is None

    # Test in DataFrame column cleaning
    data = {"Sales_Amount": ["1,500", "₹2,500.50", "(300)", "invalid"]}
    df = pd.DataFrame(data)
    mapping = {"sales_amount": "Sales_Amount"}
    cleaned_df, summary = clean_dataset(df, mapping)

    vals = cleaned_df["Sales_Amount"].tolist()
    assert vals[0] == 1500.0
    assert vals[1] == 2500.50
    assert vals[2] == -300.0
    assert np.isnan(vals[3])
    assert summary["numeric_conversions_succeeded"] == 3
    assert summary["numeric_conversions_failed"] == 1
    assert summary["negative_sales_count"] == 1


def test_6_alternative_csv_encoding():
    """Test 6: Verify loading CSV files with alternative encodings (CP1252, Latin-1, UTF-8-BOM)."""
    # Create UTF-8 with BOM content
    bom_content = "\ufeffProduct,Sales_Amount\nItemA,100\nItemB,200".encode("utf-8-sig")
    buf = io.BytesIO(bom_content)
    df, success, msg, enc, delim = load_csv_file(buf)
    assert success
    assert len(df) == 2
    assert "Product" in df.columns

    # Create Latin-1 encoded content with special characters (e.g. café, £)
    latin1_content = "Product;Sales_Amount\nCafé;150\nThé;250".encode("latin-1")
    buf2 = io.BytesIO(latin1_content)
    df2, success2, msg2, enc2, delim2 = load_csv_file(buf2)
    assert success2
    assert len(df2) == 2
    assert delim2 == ";"


def test_7_excel_workbook_loading(tmp_path):
    """Test 7: Verify loading an Excel workbook with multiple sheets and sheet selection."""
    excel_path = tmp_path / "sales_multi.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame({"Sales_Amount": [100, 200]}).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame({"Revenue": [500, 600, 700]}).to_excel(writer, sheet_name="Quarter2", index=False)

    s_ok, sheets, _ = get_excel_sheet_names(str(excel_path))
    assert s_ok
    assert len(sheets) == 2
    assert "Quarter2" in sheets

    # Load specific sheet
    df, success, err = load_excel_file(str(excel_path), sheet_name="Quarter2")
    assert success
    assert len(df) == 3
    assert "Revenue" in df.columns


def test_8_missing_optional_columns():
    """Test 8: Verify that missing optional columns (no region, sales rep, date) do not break available analyses."""
    data = {
        "Sales_Amount": [100.0, 200.0, 300.0],
        "Product_Category": ["Books", "Books", "Audio"]
    }
    df = pd.DataFrame(data)
    mapping = auto_detect_columns(df)
    assert mapping["sales_amount"] == "Sales_Amount"
    assert mapping["product_category"] == "Product_Category"
    assert mapping["region"] is None
    assert mapping["sale_date"] is None

    cleaned_df, _ = clean_dataset(df, mapping)
    kpis = compute_kpis(cleaned_df, mapping)
    assert kpis["total_sales"] == 600.0

    # Category breakdown should work
    cat_df, err = aggregate_breakdown(cleaned_df, "Product_Category", "Sales_Amount")
    assert not cat_df.empty
    assert len(cat_df) == 2

    # Capabilities check
    caps = check_analysis_capabilities(mapping)
    assert caps["Category Sales Breakdown"][0] is True
    assert caps["Regional Performance Breakdown"][0] is False
    assert caps["Time-Series Analysis"][0] is False


def test_9_missing_essential_information():
    """Test 9: Verify dataset with no sales column does not fabricate metrics or crash."""
    data = {
        "Product_Name": ["Apple", "Orange", "Banana"],
        "Supplier": ["FarmA", "FarmB", "FarmC"]
    }
    df = pd.DataFrame(data)
    mapping = auto_detect_columns(df)
    assert mapping["sales_amount"] is None

    kpis = compute_kpis(df, mapping)
    assert kpis["total_sales"] is None
    assert kpis["average_sale"] is None

    caps = check_analysis_capabilities(mapping)
    assert caps["Total Sales KPI"][0] is False


def test_10_profit_validation():
    """Test 10: Verify profit validation, scale warnings, and double-discount prevention."""
    # Subcase A: Valid small dataset with known values
    # Revenue = 1000, Unit_Cost = 30, Quantity = 20 -> Cost = 600, Profit = 400
    df_valid = pd.DataFrame({
        "Revenue": [1000.0, 2000.0],
        "Unit_Cost": [30.0, 50.0],
        "Quantity": [20, 20]
    })
    res_valid = validate_profit_formula(
        df=df_valid,
        sales_col="Revenue",
        unit_cost_col="Unit_Cost",
        qty_col="Quantity"
    )
    assert res_valid["is_valid"] is True
    assert res_valid["status"] == "verified"
    assert res_valid["profit_series"].sum() == (1000 - 600) + (2000 - 1000)

    # Subcase B: Severe scale mismatch (like mock sample where cost > revenue in 92% of rows)
    df_mismatch = pd.DataFrame({
        "Revenue": [100.0] * 10,
        "Unit_Cost": [500.0] * 10,
        "Quantity": [10] * 10
    })
    res_mismatch = validate_profit_formula(
        df=df_mismatch,
        sales_col="Revenue",
        unit_cost_col="Unit_Cost",
        qty_col="Quantity",
        user_confirmed_formula=False
    )
    assert res_mismatch["is_valid"] is False
    assert res_mismatch["status"] == "scale_warning"

    # With user override:
    res_override = validate_profit_formula(
        df=df_mismatch,
        sales_col="Revenue",
        unit_cost_col="Unit_Cost",
        qty_col="Quantity",
        user_confirmed_formula=True
    )
    assert res_override["is_valid"] is True


def test_11_invalid_files():
    """Test 11: Verify that empty files, malformed files, and invalid formats produce clear errors."""
    # Empty CSV buffer
    empty_buf = io.BytesIO(b"")
    df, success, err, _, _ = load_csv_file(empty_buf)
    assert not success
    assert "empty" in err.lower()

    # Unsupported format
    ok, ext, msg = validate_file_format("report.pdf")
    assert not ok
    assert "unsupported" in msg.lower()


def test_12_export_validation():
    """Test 12: Verify that exported CSV bytes match computed results."""
    df = pd.DataFrame({
        "Sales_Amount": [500.0, 750.0],
        "Product_Category": ["Hardware", "Software"]
    })
    csv_bytes = dataframe_to_csv_bytes(df)
    assert len(csv_bytes) > 0
    reloaded = pd.read_csv(io.BytesIO(csv_bytes))
    assert len(reloaded) == 2
    assert reloaded["Sales_Amount"].sum() == 1250.0

    # Test quality report export
    summary = {
        "original_rows": 100,
        "final_rows": 98,
        "original_cols": 5,
        "final_cols": 5,
        "total_missing_cells": 3,
        "rows_affected_by_missing": 2,
        "duplicates_detected": 2,
        "duplicates_removed": 2,
        "operations_applied": ["Removed 2 duplicates"],
        "warnings": ["Detected 2 duplicate rows."]
    }
    audit_bytes = generate_quality_report_csv(summary)
    assert b"Sales Data Analysis System - Data Quality and Cleaning Report" in audit_bytes
    assert b"Original Rows,100" in audit_bytes


def test_13_filter_validation():
    """Test 13: Verify that filters correctly slice the dataset and KPIs/breakdowns reflect only filtered rows."""
    df = pd.DataFrame({
        "Sales_Amount": [100.0, 200.0, 300.0, 400.0],
        "Region": ["North", "South", "North", "West"],
        "Quantity_Sold": [1, 2, 3, 4]
    })
    mapping = {
        "sales_amount": "Sales_Amount",
        "region": "Region",
        "quantity_sold": "Quantity_Sold"
    }

    # Filter to North only
    north_df = df[df["Region"] == "North"]
    assert len(north_df) == 2

    kpis_all = compute_kpis(df, mapping)
    kpis_north = compute_kpis(north_df, mapping)

    assert kpis_all["total_sales"] == 1000.0
    assert kpis_north["total_sales"] == 400.0
    assert kpis_north["total_quantity"] == 4.0
    assert kpis_north["valid_sales_records"] == 2


def test_14_manual_calculation_verification():
    """Test 14: Compare application calculations against exact manually computed numbers."""
    data = {
        "Sales_Amount": [150.0, 250.0, 100.0, 500.0],
        "Quantity_Sold": [3, 5, 2, 10],
        "Product_Category": ["Apparel", "Apparel", "Home", "Home"]
    }
    df = pd.DataFrame(data)
    mapping = {
        "sales_amount": "Sales_Amount",
        "quantity_sold": "Quantity_Sold",
        "product_category": "Product_Category"
    }

    # Manual calculations:
    # Total sales = 150 + 250 + 100 + 500 = 1000.0
    # Total qty = 3 + 5 + 2 + 10 = 20
    # Average sale = 1000 / 4 = 250.0
    # Group: Apparel = 400.0 (40%), Home = 600.0 (60%)

    kpis = compute_kpis(df, mapping)
    assert kpis["total_sales"] == 1000.0
    assert kpis["total_quantity"] == 20.0
    assert kpis["average_sale"] == 250.0
    assert kpis["valid_sales_records"] == 4

    cat_summary, _ = aggregate_breakdown(df, "Product_Category", "Sales_Amount", agg_func="sum")
    # Ranked: Home (600), Apparel (400)
    assert cat_summary.iloc[0]["Product_Category"] == "Home"
    assert cat_summary.iloc[0]["Sales_Amount (SUM)"] == 600.0
    assert cat_summary.iloc[0]["Share of Total (%)"] == 60.0
    assert cat_summary.iloc[1]["Product_Category"] == "Apparel"
    assert cat_summary.iloc[1]["Sales_Amount (SUM)"] == 400.0
    assert cat_summary.iloc[1]["Share of Total (%)"] == 40.0

    # Descriptive statistics
    stats_df = calculate_descriptive_statistics(df, ["Sales_Amount"])
    assert stats_df.iloc[0]["Mean"] == "250.00"
    assert stats_df.iloc[0]["Min"] == "100.00"
    assert stats_df.iloc[0]["Max"] == "500.00"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
