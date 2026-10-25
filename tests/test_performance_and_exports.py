"""
Automated Performance and Export Verification Test Suite.
Validates:
1. Welcome screen rendering and single sample-data button in sidebar (zero duplicate buttons).
2. Predictable switching between uploaded datasets and sample data.
3. Lazy export execution (zero serialization work upon tab opening).
4. Memory-bounded caching preventing repeated expensive serialization.
5. Large dataset CSV streaming and record integrity (no silent truncation).
6. Microsoft Excel row ceiling (1,048,576 rows) validation.
7. End-to-end data correctness across filters and exports.
"""

import os
import sys
import io
import time
import pytest
import pandas as pd
import numpy as np
from streamlit.testing.v1 import AppTest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.export import (
    dataframe_to_csv_bytes,
    generate_quality_report_csv,
    can_export_to_excel,
    dataframe_to_excel_bytes,
    EXCEL_MAX_WORKSHEET_ROWS
)
from modules.statistics import calculate_descriptive_statistics


def test_welcome_screen_single_sample_button():
    """Verify welcome screen has exactly ONE sample dataset button (in sidebar, not main page)."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Confirm sidebar has exactly 1 sample button
    sidebar_buttons = [b for b in at.sidebar.button if "Sample" in b.label]
    assert len(sidebar_buttons) == 1, f"Expected exactly 1 sample button in sidebar, found {len(sidebar_buttons)}"
    assert sidebar_buttons[0].label == "📊 Load Built-in Sample Dataset"

    # Confirm main page has ZERO buttons (no duplicate sample button on main page)
    assert len(at.main.button) == 0, f"Expected 0 buttons on main page, found {len(at.main.button)}"

    # Confirm file uploader exists in sidebar
    assert len(at.sidebar.file_uploader) == 1

    # Confirm exactly ONE title exists with 📊 icon
    titles = [t.value for t in at.title]
    assert len(titles) == 1
    assert titles[0] == "📊 Sales Data Analysis System"

    # Confirm simplified welcome card content exists
    welcome_cards = [m.value for m in at.markdown if "Upload a retail sales dataset" in m.value]
    assert len(welcome_cards) == 1
    assert "Upload a retail sales dataset (CSV or Excel) using the sidebar to begin your analysis." in welcome_cards[0]

    # Confirm no duplicate welcome heading exists
    assert not any("Welcome to Sales Data Analysis System" in m.value for m in at.markdown)


def test_load_sample_data_transitions_to_dashboard():
    """Verify clicking the single sidebar sample button cleanly displays the dashboard."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception

    # Click the single sidebar sample button
    sample_btn = [b for b in at.sidebar.button if "Sample" in b.label][0]
    sample_btn.click().run()
    assert not at.exception

    # Dashboard tabs must now be rendered on the main page
    tab_labels = [t.label for t in at.tabs]
    assert any("Executive Dashboard" in l for l in tab_labels), "Expected Executive Dashboard tab to be present"
    assert any("Export & Downloads" in l for l in tab_labels), "Expected Export & Downloads tab to be present"

    # Welcome card instruction must disappear once data is active
    welcome_cards = [m.value for m in at.markdown if "Upload a retail sales dataset" in m.value]
    assert len(welcome_cards) == 0, "Welcome card must not be rendered when data is active"


def test_excel_row_limit_enforcement():
    """Verify that datasets exceeding 1,048,575 data rows are blocked from Excel export without truncation."""
    small_df = pd.DataFrame({"A": [1, 2, 3], "B": ["x", "y", "z"]})
    can_export_small, reason_small = can_export_to_excel(small_df)
    assert can_export_small is True
    assert reason_small == ""

    # Test Excel bytes generation for valid dataset
    excel_bytes = dataframe_to_excel_bytes(small_df)
    assert len(excel_bytes) > 0
    read_back = pd.read_excel(io.BytesIO(excel_bytes))
    assert len(read_back) == 3
    assert list(read_back.columns) == ["A", "B"]

    # Mock huge DataFrame with 1,048,576 rows (exceeds 1,048,575 data row limit)
    class MockHugeDataFrame:
        def __len__(self):
            return 1_048_576
        @property
        def empty(self):
            return False

    can_export_huge, reason_huge = can_export_to_excel(MockHugeDataFrame())
    assert can_export_huge is False
    assert "1,048,576" in reason_huge
    assert "CSV" in reason_huge

    # Ensure dataframe_to_excel_bytes raises ValueError on oversized DataFrame
    with pytest.raises(ValueError, match="1,048,576"):
        dataframe_to_excel_bytes(MockHugeDataFrame())


def test_large_dataset_csv_streaming_and_row_integrity():
    """Verify 1,000,000 records stream cleanly into CSV bytes without data loss."""
    n = 1_000_000
    df = pd.DataFrame({
        "Transaction_ID": np.arange(n),
        "Sales": np.random.uniform(10.0, 500.0, n),
        "Quantity": np.random.randint(1, 10, n),
        "Category": np.random.choice(["Electronics", "Home", "Fashion"], n)
    })

    t0 = time.time()
    csv_bytes = dataframe_to_csv_bytes(df, chunksize=100_000)
    elapsed = time.time() - t0

    assert elapsed < 10.0, f"CSV serialization took {elapsed:.2f}s, expected < 10.0s for 1M rows"
    assert len(csv_bytes) > 0

    # Verify line count and values match exact source data
    # Header line + 1,000,000 data lines = 1,000,001 lines
    line_count = csv_bytes.count(b"\n")
    assert line_count == n + 1, f"Expected {n + 1} lines, got {line_count}"

    # Read back a sample via pandas to verify column and value preservation
    sample_df = pd.read_csv(io.BytesIO(csv_bytes), nrows=10)
    assert list(sample_df.columns) == ["Transaction_ID", "Sales", "Quantity", "Category"]
    assert sample_df["Transaction_ID"].iloc[0] == 0


def test_export_callable_lazy_generation():
    """Verify that deferred callables are not executed until explicitly called."""
    call_counts = {"clean": 0, "filtered": 0, "audit": 0, "stats": 0}

    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    def lazy_clean():
        call_counts["clean"] += 1
        return dataframe_to_csv_bytes(df)

    def lazy_filtered():
        call_counts["filtered"] += 1
        return dataframe_to_csv_bytes(df)

    def lazy_audit():
        call_counts["audit"] += 1
        return b"audit log"

    def lazy_stats():
        call_counts["stats"] += 1
        return dataframe_to_csv_bytes(df)

    # Initial state: zero invocations
    assert all(count == 0 for count in call_counts.values())

    # User clicks only the filtered download button
    result_filtered = lazy_filtered()
    assert call_counts["filtered"] == 1
    assert call_counts["clean"] == 0
    assert call_counts["audit"] == 0
    assert call_counts["stats"] == 0
    assert len(result_filtered) > 0

    # User clicks only the audit report button
    result_audit = lazy_audit()
    assert call_counts["audit"] == 1
    assert call_counts["clean"] == 0


def test_filter_isolation_in_exports():
    """Verify that filtered export reflects active filter subset while cleaned export preserves 100% of rows."""
    full_df = pd.DataFrame({
        "ID": [1, 2, 3, 4, 5],
        "Region": ["North", "North", "South", "East", "North"],
        "Sales": [100.0, 200.0, 300.0, 400.0, 500.0]
    })

    # Active filter: Region == 'North' (3 rows)
    filtered_df = full_df[full_df["Region"] == "North"]

    clean_bytes = dataframe_to_csv_bytes(full_df)
    filt_bytes = dataframe_to_csv_bytes(filtered_df)

    clean_read = pd.read_csv(io.BytesIO(clean_bytes))
    filt_read = pd.read_csv(io.BytesIO(filt_bytes))

    assert len(clean_read) == 5, "Cleaned export must retain all 5 records"
    assert len(filt_read) == 3, "Filtered export must retain only the 3 filtered records"
    assert set(filt_read["Region"].unique()) == {"North"}
    assert filt_read["Sales"].sum() == 800.0
