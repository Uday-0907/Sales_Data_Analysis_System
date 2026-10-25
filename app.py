"""
Sales Data Analysis System
A comprehensive, reliable Streamlit web application designed for retail sales data analysis.
Compliant with Academic Level-1 requirements.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from modules.data_loader import load_dataset, get_excel_sheet_names
from modules.column_mapping import normalize_column_names, auto_detect_columns, ROLE_LABELS
from modules.data_cleaning import clean_dataset
from modules.eda import (
    get_dataset_overview_metrics,
    get_column_profile_table,
    get_category_frequency_table,
    get_date_coverage_summary
)
from modules.statistics import calculate_descriptive_statistics
from modules.sales_analysis import compute_kpis, aggregate_breakdown
from modules.time_series import aggregate_time_series
from modules.visualizations import (
    create_bar_chart,
    create_pie_chart,
    create_line_chart,
    create_histogram
)
from utils.validation import validate_profit_formula, check_analysis_capabilities
from utils.export import dataframe_to_csv_bytes, generate_quality_report_csv


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Sales Data Analysis System",
    page_icon="📈",
    layout="wide"
)

# ---------------- MODERN PROFESSIONAL LIGHT THEME STYLING ----------------

st.markdown("""
<style>
/* Global Application Background & Typography */
.stApp {
    background-color: #F5F7FB !important;
    color: #1E293B !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Eliminate contrasting top white bar and blend header seamlessly into page */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    background: transparent !important;
}

/* Remove excessive 5-6rem top padding above title while maintaining comfortable spacing */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 2.25rem !important;
    padding-right: 2.25rem !important;
    max-width: 100% !important;
}

/* Sidebar Styling: Clean white background with crisp border and dark text */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #0F172A !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span {
    color: #1E293B !important;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #64748B !important;
}

/* Sidebar File Uploader Container */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background-color: #F8FAFC !important;
    border: 1px dashed #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
    border-color: #2563EB !important;
}

/* Dashboard Metric Cards: White background, subtle border, gentle elevation */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    padding: 18px 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05) !important;
    border-color: #CBD5E1 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
    font-size: 0.825rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
}
[data-testid="stMetricLabel"] * {
    color: #64748B !important;
}
[data-testid="stMetricValue"] {
    color: #0F172A !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricValue"] * {
    color: #0F172A !important;
}

/* Headings & Dividers */
h1 {
    color: #0F172A !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    margin-bottom: 0.2rem !important;
}
h2 {
    color: #1E293B !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    margin-top: 0.5rem !important;
}
h3, h4 {
    color: #1E293B !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
}
hr {
    border-color: #E2E8F0 !important;
    margin: 1.25rem 0 !important;
}

/* Navigation Tabs: Light theme with active blue indicator */
[data-testid="stTabs"] {
    margin-top: 0.5rem !important;
    margin-bottom: 1.25rem !important;
}
[data-testid="stTabs"] button[role="tab"] {
    color: #64748B !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    background-color: transparent !important;
    border: none !important;
    border-bottom: 2.5px solid transparent !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: #1E293B !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #2563EB !important;
    font-weight: 600 !important;
    border-bottom: 2.5px solid #2563EB !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: #2563EB !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] {
    background-color: #E2E8F0 !important;
}

/* Dataframe and Tables */
[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stExpander"] summary {
    color: #1E293B !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] summary:hover {
    color: #2563EB !important;
}

/* Buttons */
.stButton > button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #2563EB !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    padding: 0.5rem 1rem !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease-in-out !important;
}
.stButton > button:hover {
    background-color: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}
.stDownloadButton > button {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: 1px solid #2563EB !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    width: 100% !important;
    padding: 0.5rem 1rem !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    transition: all 0.15s ease-in-out !important;
}
.stDownloadButton > button:hover {
    background-color: #1D4ED8 !important;
    border-color: #1D4ED8 !important;
    color: #FFFFFF !important;
}

/* Chart Container Cards */
[data-testid="stImage"] img {
    border-radius: 10px !important;
    border: 1px solid #E2E8F0 !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04) !important;
}

/* Status Badges */
.clean-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.825rem;
    font-weight: 600;
}
.pill-clean { background-color: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
.pill-warning { background-color: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
.pill-info { background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
</style>
""", unsafe_allow_html=True)


# ---------------- APPLICATION HEADER ----------------

st.title("Sales Data Analysis System")
st.caption("A reliable retail sales data processing, cleaning, and analytics platform.")
st.divider()


# ---------------- SIDEBAR: DATA UPLOAD ----------------

st.sidebar.header("📁 Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload Retail Sales File",
    type=["csv", "xlsx", "xls"],
    help="Upload your retail sales data in CSV or Excel (.xlsx) format."
)

# Support loading sample file if present in workspace or desktop
SAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sales_data.csv")
has_sample = os.path.exists(SAMPLE_PATH)

use_sample = False
if uploaded_file is None:
    if has_sample:
        st.info("👈 Upload your retail sales CSV or Excel file from the sidebar to begin, or load the built-in sample dataset below.")
        if st.button("Load Built-in Sample Dataset (sales_data.csv)"):
            st.session_state["load_sample"] = True
            st.rerun()

    if st.session_state.get("load_sample", False) and has_sample:
        use_sample = True
        active_file_source = SAMPLE_PATH
    else:
        st.stop()
else:
    st.session_state["load_sample"] = False
    active_file_source = uploaded_file


# ---------------- FILE LOADING & SHEET SELECTION ----------------

# Check sheet selection if Excel
sheet_names = []
selected_sheet = None
filename = getattr(active_file_source, "name", str(active_file_source)).lower()

if filename.endswith(".xlsx") or filename.endswith(".xls"):
    s_ok, sheets, _ = get_excel_sheet_names(active_file_source)
    if s_ok and len(sheets) > 1:
        selected_sheet = st.sidebar.selectbox("Select Excel Worksheet", options=sheets)

raw_df, load_success, load_message, load_meta = load_dataset(active_file_source, sheet_name=selected_sheet)

if not load_success:
    st.error(f"❌ File Loading Error: {load_message}")
    st.stop()


# ---------------- COLUMN NORMALIZATION ----------------

orig_columns = list(raw_df.columns)
cleaned_columns, col_mapping_dict, col_collisions = normalize_column_names(orig_columns)
raw_df.columns = cleaned_columns

if col_collisions:
    for c_warn in col_collisions:
        st.warning(f"⚠️ {c_warn}")


# ---------------- AUTO-DETECTION & USER COLUMN MAPPING ----------------

auto_detected = auto_detect_columns(raw_df)

with st.sidebar.expander("⚙️ Column Mapping & Settings", expanded=False):
    st.write("Confirm or adjust column roles:")
    all_col_options = ["(None / Skip)"] + list(raw_df.columns)

    mapped_columns = {}
    for role, label in ROLE_LABELS.items():
        detected_col = auto_detected.get(role)
        default_idx = (all_col_options.index(detected_col)) if (detected_col in all_col_options) else 0

        chosen = st.selectbox(
            label,
            options=all_col_options,
            index=default_idx,
            key=f"col_map_{role}"
        )
        mapped_columns[role] = None if chosen == "(None / Skip)" else chosen

    st.divider()
    st.write("**Cleaning Preferences**")
    remove_duplicates_opt = st.checkbox("Remove exact duplicate rows", value=True)
    date_format_opt = st.selectbox(
        "Date parsing format",
        options=["auto", "YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
        index=0
    )


# ---------------- DATA CLEANING PIPELINE ----------------

cleaning_options = {
    "remove_duplicates": remove_duplicates_opt,
    "date_format": date_format_opt,
    "strip_whitespace": True
}

cleaned_df, cleaning_summary = clean_dataset(raw_df, mapped_columns, cleaning_options)


# ---------------- PROFIT FORMULA VERIFICATION ----------------

user_confirmed_profit = st.sidebar.checkbox(
    "Acknowledge profit formula override if flagged",
    value=False,
    help="Enable if you have confirmed that revenue and cost scales are intentional."
)

profit_validation = validate_profit_formula(
    df=cleaned_df,
    sales_col=mapped_columns.get("sales_amount"),
    unit_cost_col=mapped_columns.get("unit_cost"),
    qty_col=mapped_columns.get("quantity_sold"),
    unit_price_col=mapped_columns.get("unit_price"),
    discount_col=mapped_columns.get("discount"),
    profit_col=mapped_columns.get("profit"),
    user_confirmed_formula=user_confirmed_profit
)


# ---------------- SIDEBAR INTERACTIVE FILTERS ----------------

st.sidebar.divider()
st.sidebar.subheader("🔍 Dashboard Filters")

filtered_df = cleaned_df.copy()

# 1. Date Range Filter
date_col = mapped_columns.get("sale_date")
if date_col and date_col in filtered_df.columns:
    valid_dates = filtered_df[date_col].dropna()
    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        if min_date < max_date:
            date_range = st.sidebar.date_input(
                "Filter Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_d, end_d = date_range
                date_mask = filtered_df[date_col].dt.date.between(start_d, end_d)
                filtered_df = filtered_df[date_mask]

# 2. Categorical Filters
filter_roles = [
    ("region", "Region"),
    ("product_category", "Product Category"),
    ("sales_rep", "Sales Representative"),
    ("sales_channel", "Sales Channel"),
    ("customer_type", "Customer Type"),
    ("payment_method", "Payment Method")
]

for role_key, role_name in filter_roles:
    col = mapped_columns.get(role_key)
    if col and col in filtered_df.columns:
        unique_vals = sorted(filtered_df[col].dropna().astype(str).unique().tolist())
        if len(unique_vals) > 1:
            selected_vals = st.sidebar.multiselect(
                f"Filter {role_name}",
                options=unique_vals,
                default=unique_vals,
                key=f"filter_{role_key}"
            )
            if selected_vals:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]
            else:
                filtered_df = filtered_df.iloc[0:0]

# Display filter record count in sidebar
st.sidebar.caption(f"Active records: {len(filtered_df):,} of {len(cleaned_df):,}")


# ---------------- EMPTY FILTER HANDLING ----------------

if filtered_df.empty:
    st.warning("⚠️ No records match the active filter criteria. Please adjust or reset the filters in the sidebar to continue.")
    st.stop()


# ---------------- CAPABILITIES AUDIT ----------------

capabilities = check_analysis_capabilities(mapped_columns)


# ---------------- MAIN APPLICATION TABS ----------------

tabs = st.tabs([
    "📊 Executive Dashboard",
    "🔍 Data Quality & Cleaning",
    "📈 Exploratory Data Analysis",
    "📐 Descriptive Statistics",
    "🔄 Custom Grouping & Aggregation",
    "📅 Time-Series Analysis",
    "💾 Export & Downloads"
])


# ==============================================================================
# TAB 1: EXECUTIVE DASHBOARD
# ==============================================================================

with tabs[0]:
    st.subheader("Business Performance Overview")

    sales_col = mapped_columns.get("sales_amount")
    if not sales_col:
        st.error(
            "⚠️ Sales Amount / Revenue column is not mapped. Please expand 'Column Mapping & Settings' in the sidebar "
            "to map the column representing sales or revenue."
        )
    else:
        # Calculate KPIs
        kpis = compute_kpis(filtered_df, mapped_columns, profit_validation)

        # Responsive KPI Cards Grid
        if kpis["profit_status"] == "verified":
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Sales", f"${kpis['total_sales']:,.2f}" if kpis["total_sales"] is not None else "Unavailable")
            c2.metric("Total Units Sold", f"{kpis['total_quantity']:,.0f}" if kpis["total_quantity"] is not None else "Not Mapped")
            c3.metric("Valid Transactions", f"{kpis['valid_sales_records']:,}")
            c4.metric("Average Sale / Row", f"${kpis['average_sale']:,.2f}" if kpis["average_sale"] is not None else "Unavailable")
            c5.metric("Total Profit", f"${kpis['profit']:,.2f}", help=kpis["profit_formula"])
            st.caption(f"✅ {kpis['profit_explanation']}")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Sales", f"${kpis['total_sales']:,.2f}" if kpis["total_sales"] is not None else "Unavailable")
            c2.metric("Total Units Sold", f"{kpis['total_quantity']:,.0f}" if kpis["total_quantity"] is not None else "Not Mapped")
            c3.metric("Valid Transactions", f"{kpis['valid_sales_records']:,}")
            c4.metric("Average Sale / Row", f"${kpis['average_sale']:,.2f}" if kpis["average_sale"] is not None else "Unavailable")

            if kpis["profit_status"] == "scale_warning":
                st.warning(
                    f"⚠️ Profit metric held: {kpis['profit_explanation']} "
                    "(To display calculated profit anyway, check the acknowledgment box in the sidebar)."
                )
            elif kpis["profit_status"] == "unavailable":
                st.caption("ℹ️ Profit metric is omitted: Unit Cost or formula validation columns are not mapped.")

        if kpis["excluded_sales_records"] > 0:
            st.caption(
                f"ℹ️ Note: {kpis['excluded_sales_records']:,} records in current view lack valid sales amounts and were excluded from sales totals."
            )

        st.divider()

        # Dashboard Visualizations
        col_left, col_right = st.columns(2)

        # 1. Sales by Product Category
        with col_left:
            st.subheader("Sales by Product Category")
            cat_col = mapped_columns.get("product_category")
            if cat_col and cat_col in filtered_df.columns:
                cat_summary, err = aggregate_breakdown(filtered_df, cat_col, sales_col, agg_func="sum")
                if not cat_summary.empty:
                    val_col_name = cat_summary.columns[1]
                    fig = create_bar_chart(
                        cat_summary,
                        cat_col=cat_col,
                        val_col=val_col_name,
                        title="Total Sales by Category",
                        x_label=cat_col,
                        y_label="Sales Amount ($)"
                    )
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)
                else:
                    st.info("No valid category sales data available.")
            else:
                st.info("Product Category column is not mapped. Configure mapping in sidebar to display.")

        # 2. Regional Sales Breakdown
        with col_right:
            st.subheader("Regional Performance")
            reg_col = mapped_columns.get("region")
            if reg_col and reg_col in filtered_df.columns:
                reg_summary, err = aggregate_breakdown(filtered_df, reg_col, sales_col, agg_func="sum")
                if not reg_summary.empty:
                    val_col_name = reg_summary.columns[1]
                    fig = create_pie_chart(
                        reg_summary,
                        cat_col=reg_col,
                        val_col=val_col_name,
                        title="Sales Share by Region"
                    )
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)
                else:
                    st.info("No valid regional sales data available.")
            else:
                st.info("Region column is not mapped. Configure mapping in sidebar to display.")

        # Row 2 Visualizations
        col_left2, col_right2 = st.columns(2)

        # 3. Sales Representative or Sales Channel Breakdown
        with col_left2:
            st.subheader("Sales Performance by Representative")
            rep_col = mapped_columns.get("sales_rep")
            if rep_col and rep_col in filtered_df.columns:
                rep_summary, err = aggregate_breakdown(filtered_df, rep_col, sales_col, agg_func="sum", top_n=8)
                if not rep_summary.empty:
                    val_col_name = rep_summary.columns[1]
                    fig = create_bar_chart(
                        rep_summary,
                        cat_col=rep_col,
                        val_col=val_col_name,
                        title="Top Sales Representatives by Revenue",
                        x_label=rep_col,
                        y_label="Sales Amount ($)"
                    )
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)
                else:
                    st.info("No sales representative data available.")
            else:
                # Fallback to Channel if sales rep is not mapped
                chan_col = mapped_columns.get("sales_channel")
                if chan_col and chan_col in filtered_df.columns:
                    st.caption("Showing Sales by Channel (Sales Rep column not mapped):")
                    chan_summary, _ = aggregate_breakdown(filtered_df, chan_col, sales_col, agg_func="sum")
                    if not chan_summary.empty:
                        fig = create_bar_chart(
                            chan_summary,
                            cat_col=chan_col,
                            val_col=chan_summary.columns[1],
                            title="Sales by Channel"
                        )
                        if fig:
                            st.pyplot(fig, use_container_width=True)
                            plt.close(fig)
                else:
                    st.info("Neither Sales Representative nor Sales Channel column is mapped.")

        # 4. Monthly Trend Line Chart
        with col_right2:
            st.subheader("Revenue Over Time")
            date_col = mapped_columns.get("sale_date")
            if date_col and date_col in filtered_df.columns:
                ts_df, ts_meta = aggregate_time_series(filtered_df, date_col, sales_col, frequency="Month", agg_func="sum")
                if ts_meta["is_available"] and not ts_df.empty:
                    val_col_name = ts_df.columns[1]
                    fig = create_line_chart(
                        ts_df,
                        date_col="Period",
                        val_col=val_col_name,
                        title="Monthly Revenue Trend",
                        x_label="Month",
                        y_label="Total Revenue ($)"
                    )
                    if fig:
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)
                else:
                    st.info(f"Time-series trend unavailable: {ts_meta.get('message', 'No valid date records.')}")
            else:
                st.info("Sale Date column is not mapped. Configure mapping in sidebar to display trend.")

        st.divider()

        # Business Highlights
        st.subheader("Summary Highlights")
        cat_col = mapped_columns.get("product_category")
        reg_col = mapped_columns.get("region")
        rep_col = mapped_columns.get("sales_rep")

        h_cols = st.columns(3)
        if cat_col and cat_col in filtered_df.columns:
            cat_sum = filtered_df.groupby(cat_col)[sales_col].sum()
            if not cat_sum.empty:
                h_cols[0].markdown(
                    f"""<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; border-left: 4px solid #2563EB; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.03);">
                        <div style="color: #64748B; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">Top Category</div>
                        <div style="color: #0F172A; font-size: 1.15rem; font-weight: 700; margin-top: 4px;">{cat_sum.idxmax()}</div>
                        <div style="color: #2563EB; font-size: 0.875rem; font-weight: 600; margin-top: 2px;">${cat_sum.max():,.2f} in sales</div>
                    </div>""",
                    unsafe_allow_html=True
                )

        if reg_col and reg_col in filtered_df.columns:
            reg_sum = filtered_df.groupby(reg_col)[sales_col].sum()
            if not reg_sum.empty:
                h_cols[1].markdown(
                    f"""<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; border-left: 4px solid #0EA5E9; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.03);">
                        <div style="color: #64748B; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">Leading Region</div>
                        <div style="color: #0F172A; font-size: 1.15rem; font-weight: 700; margin-top: 4px;">{reg_sum.idxmax()}</div>
                        <div style="color: #0EA5E9; font-size: 0.875rem; font-weight: 600; margin-top: 2px;">${reg_sum.max():,.2f} in sales</div>
                    </div>""",
                    unsafe_allow_html=True
                )

        if rep_col and rep_col in filtered_df.columns:
            rep_sum = filtered_df.groupby(rep_col)[sales_col].sum()
            if not rep_sum.empty:
                h_cols[2].markdown(
                    f"""<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; border-left: 4px solid #10B981; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.03);">
                        <div style="color: #64748B; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">Top Sales Rep</div>
                        <div style="color: #0F172A; font-size: 1.15rem; font-weight: 700; margin-top: 4px;">{rep_sum.idxmax()}</div>
                        <div style="color: #10B981; font-size: 0.875rem; font-weight: 600; margin-top: 2px;">${rep_sum.max():,.2f} in sales</div>
                    </div>""",
                    unsafe_allow_html=True
                )

        # Filtered Records Table
        with st.expander(f"View Active Filtered Dataset ({len(filtered_df):,} records)", expanded=False):
            st.dataframe(filtered_df, use_container_width=True)


# ==============================================================================
# TAB 2: DATA QUALITY & CLEANING
# ==============================================================================

with tabs[1]:
    st.subheader("Data Quality Audit & Cleaning Report")

    # Cleanliness badge
    if cleaning_summary.get("is_completely_clean"):
        st.markdown(
            '<span class="clean-pill pill-clean">✓ Completely Clean: Zero Unresolved Issues</span>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<span class="clean-pill pill-warning">⚠️ Quality Alerts Present: Review Unresolved Items</span>',
            unsafe_allow_html=True
        )

    st.write("")

    # Dimensions comparison
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Original Rows", f"{cleaning_summary['original_rows']:,}")
    d2.metric("Working Rows", f"{cleaning_summary['final_rows']:,}")
    d3.metric("Missing Cells Detected", f"{cleaning_summary['total_missing_cells']:,}")
    d4.metric("Exact Duplicates Removed", f"{cleaning_summary['duplicates_removed']:,}")

    st.divider()

    # Operations Applied & Warnings
    col_ops, col_warn = st.columns(2)

    with col_ops:
        st.subheader("Cleaning Operations Applied")
        ops = cleaning_summary.get("operations_applied", [])
        if ops:
            for idx, op in enumerate(ops, start=1):
                st.write(f"**{idx}.** {op}")
        else:
            st.info("No cleaning operations were required for this dataset.")

    with col_warn:
        st.subheader("Warnings & Unresolved Issues")
        warns = cleaning_summary.get("warnings", [])
        if warns:
            for idx, w in enumerate(warns, start=1):
                st.warning(f"**{idx}.** {w}")
        else:
            st.success("No unresolved data-quality warnings detected.")

    st.divider()

    # Missing Values by Column Table
    st.subheader("Missing Value Summary by Column")
    missing_data = []
    for col, info in cleaning_summary.get("missing_by_column", {}).items():
        missing_data.append({
            "Column Name": col,
            "Missing Count": info["count"],
            "Missing Percentage": f"{info['percentage']:.2f}%",
            "Valid Values": cleaning_summary["original_rows"] - info["count"]
        })
    missing_df = pd.DataFrame(missing_data)
    st.dataframe(missing_df, use_container_width=True)

    # Preview Raw vs Cleaned Data
    st.divider()
    st.subheader("Dataset Comparison Preview")
    p_tab1, p_tab2 = st.tabs(["Cleaned Working Data (Head)", "Original Uploaded Data (Head)"])
    with p_tab1:
        st.dataframe(cleaned_df.head(10), use_container_width=True)
    with p_tab2:
        st.dataframe(raw_df.head(10), use_container_width=True)


# ==============================================================================
# TAB 3: EXPLORATORY DATA ANALYSIS (EDA)
# ==============================================================================

with tabs[2]:
    st.subheader("Exploratory Data Analysis")

    overview = get_dataset_overview_metrics(cleaned_df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows", f"{overview['total_rows']:,}")
    m2.metric("Total Columns", f"{overview['total_columns']:,}")
    m3.metric("Numeric Columns", f"{overview['numeric_column_count']}")
    m4.metric("Date Columns", f"{overview['date_column_count']}")

    st.divider()

    # Column profiles
    st.subheader("Dataset Column Profiles")
    profile_df = get_column_profile_table(cleaned_df)
    st.dataframe(profile_df, use_container_width=True)

    st.divider()

    # Interactive Category Frequency Explorer
    st.subheader("Categorical Frequency Analysis")
    cat_columns = overview["categorical_columns"]
    if cat_columns:
        chosen_cat = st.selectbox("Select Categorical Column to Inspect", options=cat_columns)
        if chosen_cat:
            freq_df = get_category_frequency_table(cleaned_df, chosen_cat, top_n=15)
            col_f1, col_f2 = st.columns([1, 1])
            with col_f1:
                st.write(f"Frequency Distribution: **{chosen_cat}**")
                st.dataframe(freq_df, use_container_width=True)
            with col_f2:
                fig = create_bar_chart(
                    freq_df,
                    cat_col=chosen_cat,
                    val_col="Record Count",
                    title=f"Record Frequency by {chosen_cat}",
                    x_label=chosen_cat,
                    y_label="Count"
                )
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
    else:
        st.info("No categorical columns available for frequency analysis.")

    st.divider()

    # Distribution of Numeric Variables
    st.subheader("Numeric Distributions")
    num_columns = overview["numeric_columns"]
    if num_columns:
        chosen_num = st.selectbox("Select Numeric Column for Histogram", options=num_columns)
        if chosen_num:
            col_h1, col_h2 = st.columns([1, 1])
            with col_h1:
                series = cleaned_df[chosen_num].dropna()
                st.write(f"Distribution Statistics: **{chosen_num}**")
                st.write(f"- **Valid Count:** {len(series):,}")
                st.write(f"- **Mean:** {series.mean():,.2f}")
                st.write(f"- **Median:** {series.median():,.2f}")
                st.write(f"- **Minimum:** {series.min():,.2f}")
                st.write(f"- **Maximum:** {series.max():,.2f}")
                st.write(f"- **Standard Deviation:** {series.std():,.2f}")
            with col_h2:
                fig = create_histogram(
                    cleaned_df[chosen_num],
                    title=f"Distribution of {chosen_num}",
                    x_label=chosen_num,
                    bins=20
                )
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
    else:
        st.info("No numeric columns available for distribution analysis.")


# ==============================================================================
# TAB 4: DESCRIPTIVE STATISTICS
# ==============================================================================

with tabs[3]:
    st.subheader("Descriptive Statistics")
    st.caption("Summary statistics describe the historical distribution of the uploaded dataset and do not represent a predictive forecast.")

    all_numeric = [col for col in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[col])]
    if not all_numeric:
        st.warning("No recognized numeric columns found in the dataset.")
    else:
        selected_stats_cols = st.multiselect(
            "Select Numeric Columns to Analyze",
            options=all_numeric,
            default=all_numeric
        )

        if selected_stats_cols:
            stats_table = calculate_descriptive_statistics(cleaned_df, selected_stats_cols)
            st.dataframe(stats_table, use_container_width=True)
        else:
            st.info("Please select at least one numeric column from the multiselect above.")


# ==============================================================================
# TAB 5: CUSTOM GROUPING & AGGREGATION
# ==============================================================================

with tabs[4]:
    st.subheader("Custom Data Grouping & Aggregation")
    st.caption("Select a category and numeric measure to aggregate using the active cleaned dataset.")

    group_cols = [c for c in cleaned_df.columns if not pd.api.types.is_numeric_dtype(cleaned_df[c])]
    measure_cols = [c for c in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[c])]

    if not group_cols or not measure_cols:
        st.warning("Custom grouping requires at least one categorical column and one numeric column.")
    else:
        g_c1, g_c2, g_c3 = st.columns(3)
        chosen_group = g_c1.selectbox("Group By (Category)", options=group_cols, key="custom_grp_cat")
        chosen_measure = g_c2.selectbox("Measure (Numeric)", options=measure_cols, key="custom_grp_num")
        chosen_agg = g_c3.selectbox("Aggregation Method", options=["Sum", "Mean", "Count", "Minimum", "Maximum"], key="custom_grp_agg")

        agg_method_map = {
            "Sum": "sum",
            "Mean": "mean",
            "Count": "count",
            "Minimum": "min",
            "Maximum": "max"
        }

        agg_result, agg_err = aggregate_breakdown(
            filtered_df,
            group_col=chosen_group,
            value_col=chosen_measure,
            agg_func=agg_method_map[chosen_agg]
        )

        if not agg_result.empty:
            ag_col1, ag_col2 = st.columns([1, 1])
            with ag_col1:
                st.write(f"Aggregated Table ({chosen_agg} of {chosen_measure} by {chosen_group})")
                st.dataframe(agg_result, use_container_width=True)
            with ag_col2:
                val_col = agg_result.columns[1]
                fig = create_bar_chart(
                    agg_result.head(12),
                    cat_col=chosen_group,
                    val_col=val_col,
                    title=f"{chosen_agg} of {chosen_measure} by {chosen_group}",
                    x_label=chosen_group,
                    y_label=val_col
                )
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
        else:
            st.info(f"Could not compute aggregation: {agg_err}")


# ==============================================================================
# TAB 6: TIME-SERIES ANALYSIS
# ==============================================================================

with tabs[5]:
    st.subheader("Time-Series Trend Analysis")

    date_col = mapped_columns.get("sale_date")
    sales_col = mapped_columns.get("sales_amount")

    if not date_col or date_col not in cleaned_df.columns:
        st.info("Time-series analysis is unavailable: Transaction/Sale Date column is not mapped.")
    elif not sales_col or sales_col not in cleaned_df.columns:
        st.info("Time-series analysis is unavailable: Sales Amount column is not mapped.")
    else:
        # Check date coverage
        cov = get_date_coverage_summary(cleaned_df, date_col)
        if not cov.get("available"):
            st.warning(f"Time-series unavailable: {cov.get('reason')}")
        else:
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("Earliest Date", cov["earliest_date"])
            tc2.metric("Latest Date", cov["latest_date"])
            tc3.metric("Timespan", f"{cov['timespan_days']:,} Days")

            st.write("")
            ts_freq = st.radio(
                "Select Time Interval Frequency",
                options=["Month", "Day", "Year"],
                horizontal=True
            )

            ts_table, ts_info = aggregate_time_series(
                filtered_df,
                date_col=date_col,
                value_col=sales_col,
                frequency=ts_freq,
                agg_func="sum"
            )

            if ts_info["is_available"] and not ts_table.empty:
                val_col = ts_table.columns[1]
                fig = create_line_chart(
                    ts_table,
                    date_col="Period",
                    val_col=val_col,
                    title=f"Sales Trend by {ts_freq}",
                    x_label=ts_freq,
                    y_label="Sales Amount ($)"
                )
                if fig:
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)

                with st.expander(f"View Chronological Trend Table ({len(ts_table)} periods)", expanded=False):
                    st.dataframe(ts_table, use_container_width=True)
            else:
                st.info(f"Could not construct time-series trend: {ts_info.get('message')}")


# ==============================================================================
# TAB 7: EXPORT & DOWNLOADS
# ==============================================================================

with tabs[6]:
    st.subheader("Export Results & Cleaned Data")
    st.caption("Download computed results and cleaned datasets in standard CSV format.")

    e_col1, e_col2 = st.columns(2)

    with e_col1:
        st.markdown("#### 1. Cleaned Full Dataset")
        st.write(f"Contains {len(cleaned_df):,} cleaned records reflecting all preprocessing rules.")
        clean_bytes = dataframe_to_csv_bytes(cleaned_df)
        st.download_button(
            label="📥 Download Cleaned Dataset (CSV)",
            data=clean_bytes,
            file_name="cleaned_sales_dataset.csv",
            mime="text/csv",
            key="btn_download_clean"
        )

        st.markdown("#### 2. Active Filtered Records")
        st.write(f"Contains {len(filtered_df):,} records currently matching your active filters.")
        filt_bytes = dataframe_to_csv_bytes(filtered_df)
        st.download_button(
            label="📥 Download Filtered Dataset (CSV)",
            data=filt_bytes,
            file_name="filtered_sales_dataset.csv",
            mime="text/csv",
            key="btn_download_filtered"
        )

    with e_col2:
        st.markdown("#### 3. Data Quality & Cleaning Audit")
        st.write("Structured audit log of missing cells, duplicates, conversions, and warnings.")
        audit_bytes = generate_quality_report_csv(cleaning_summary)
        st.download_button(
            label="📥 Download Quality Audit Report (CSV)",
            data=audit_bytes,
            file_name="data_quality_report.csv",
            mime="text/csv",
            key="btn_download_audit"
        )

        st.markdown("#### 4. Descriptive Statistics Summary")
        st.write("Table of mean, median, standard deviation, quartiles, and min/max metrics.")
        all_numeric = [col for col in cleaned_df.columns if pd.api.types.is_numeric_dtype(cleaned_df[col])]
        if all_numeric:
            stats_df = calculate_descriptive_statistics(cleaned_df, all_numeric)
            stats_bytes = dataframe_to_csv_bytes(stats_df)
            st.download_button(
                label="📥 Download Descriptive Statistics (CSV)",
                data=stats_bytes,
                file_name="descriptive_statistics.csv",
                mime="text/csv",
                key="btn_download_stats"
            )


# ---------------- FOOTER ----------------

st.divider()
st.caption("Sales Data Analysis System | Developed for Retail Sales Analytics and Quality Inspection")
