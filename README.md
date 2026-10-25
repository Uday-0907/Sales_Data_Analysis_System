# Sales Data Analysis System

A professional, reliable Python and Streamlit web application designed for retail business owners and academic evaluation. The system inspects, cleans, and analyzes rough or imperfect retail sales datasets (CSV and Excel `.xlsx`) without requiring manual spreadsheet data cleaning.

---

## Key Features

1. **Robust Multi-Format File Ingestion**
   - Supports CSV (`.csv`) and Excel (`.xlsx`, `.xls`).
   - Automatically handles common encodings: UTF-8, UTF-8 with BOM (`utf-8-sig`), Windows-1252 (`cp1252`), Latin-1 (`iso-8859-1`).
   - Automatically sniffs delimiters (commas `,`, semicolons `;`, tabs `\t`, pipes `|`).
   - Supports multi-worksheet Excel files with an interactive sheet selector.
   - Detects empty files, corrupted headers, and invalid formats with clear error guidance.

2. **Automated Rough & Unclean Data Preprocessing**
   - **Column Normalization:** Strips whitespace, canonicalizes column names, and resolves naming collisions.
   - **Missing Value Handling:** Detects missing markers (`NA`, `N/A`, `-`, `null`, `None`, whitespace) without blindly dropping entire rows; reports missing percentages and rows affected.
   - **Exact Duplicate Detection:** Identifies exact duplicate records and provides an option to deduplicate.
   - **Numeric Parsing:** Cleans currency symbols (`$`, `₹`, `€`, `£`), thousand-separator commas (`1,500`), and accounting negatives `(100)` -> `-100`.
   - **Date Standardization:** Safely parses dates and allows user format overrides (`DD/MM/YYYY`, `MM/DD/YYYY`).
   - **Data Quality Audit Report:** Distinguishes between detected issues and corrected operations; explicitly warns if unresolved issues remain.

3. **Dynamic Column Detection & Interactive Mapping**
   - Intelligent synonym matching detects column roles (`sales_amount`, `sale_date`, `quantity_sold`, `product_category`, `region`, etc.).
   - Allows users to adjust or skip any column mapping.
   - Gracefully adapts when optional columns (e.g., region, sales rep, date) are absent.

4. **Executive Sales Dashboard & Real-Time Filtering**
   - KPI Cards: Total Sales / Revenue, Units Sold, Valid Transactions, Average Sale per Transaction, Total Profit (when validated).
   - Dynamic interactive filters: Date range, Region, Product Category, Sales Rep, Sales Channel, Customer Type, Payment Method.
   - All charts, metrics, and summary tables strictly update to match the active filters.

5. **Mathematically Validated Profit Calculations**
   - Inspects revenue, unit cost, and quantity scale before computing profit.
   - Warns users if cost exceeds revenue on a majority of rows (preventing misleading figures).
   - Documents the exact formula applied (`Profit = Sales - (Unit Cost × Quantity)`).

6. **Exploratory Data Analysis (EDA) & Descriptive Statistics**
   - Dataset dimensions, data types, and non-null profile tables.
   - Category frequency analysis with bar charts.
   - Distribution histograms for numeric measures.
   - Comprehensive statistics: Count, Mean, Median, Standard Deviation, Min, Q1 (25%), Q2 (50%), Q3 (75%), Max, and Range.

7. **Custom Grouping & Aggregation**
   - Pair any categorical attribute with any numeric measure.
   - Supported aggregation functions: Sum, Mean, Count, Minimum, Maximum.
   - Interactive data table with percentage contribution and corresponding Matplotlib chart.

8. **Chronological Time-Series Analysis**
   - Aggregates sales by Day, Month, or Year.
   - Ordered chronologically with line trends and period breakdown.

9. **Data Export & Download**
   - Download Cleaned Working Dataset (CSV).
   - Download Active Filtered Dataset (CSV).
   - Download Data Quality & Audit Report (CSV).
   - Download Descriptive Statistics (CSV).

10. **Clean Matplotlib Visualizations**
    - High-quality professional light-themed charts matching the executive interface.
    - Crisp slate typography, slate axes, subtle gridlines, and vivid business palettes.
    - Zero external UI dependencies; memory-safe figure management.

---

## Project Structure

```
Sales-Data-Analysis-System/
├── app.py                     # Main Streamlit application
├── requirements.txt           # Verified runtime dependencies
├── README.md                  # System documentation and execution guide
├── .gitignore                 # Standard Python/Streamlit gitignore
├── modules/
│   ├── __init__.py
│   ├── data_loader.py         # CSV & Excel loading with encoding/delimiter fallbacks
│   ├── column_mapping.py      # Column role detection, synonyms, and normalization
│   ├── data_cleaning.py       # Rough data cleaning, missing values, duplicates, currencies
│   ├── eda.py                 # Exploratory data analysis, profiles, frequency tables
│   ├── statistics.py          # Descriptive summary statistics (Pandas & NumPy)
│   ├── sales_analysis.py      # KPIs, sales breakdowns, aggregation logic
│   ├── time_series.py         # Chronological time-series aggregation (Day/Month/Year)
│   └── visualizations.py      # Matplotlib figures (bar, horizontal bar, donut, line, histogram)
├── utils/
│   ├── __init__.py
│   ├── validation.py          # Profit formula validation, capability audits
│   └── export.py              # CSV bytes generation & audit report formatting
└── tests/
    └── test_system.py         # Automated test suite covering all 14 required test cases
```

---

## Technology Stack

- **Python 3.10+** (Application logic)
- **Streamlit** (Interactive web application framework)
- **Pandas & NumPy** (Tabular data cleaning, manipulation, and numerical calculations)
- **Matplotlib** (Data visualization)
- **OpenPyXL** (Excel `.xlsx` ingestion)

---

## Windows PowerShell Setup & Execution Guide

Follow these exact steps in Windows PowerShell to set up and run the application:

### Step 1: Open Windows PowerShell and Navigate to the Project Folder
```powershell
cd "c:\Users\UDAY KIRAN\OneDrive\Desktop\DAE"
```

### Step 2: Create a Python Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` and retry activation).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Start the Streamlit Application
```powershell
streamlit run app.py
```
Streamlit will launch the web application in your default browser at `http://localhost:8501`.

---

## User Workflow Guide

1. **Upload Dataset:**
   - Use the file uploader in the sidebar to upload any retail CSV or Excel (`.xlsx`) file.
   - If an Excel file has multiple worksheets, select the desired worksheet from the dropdown.
2. **Review Column Mapping:**
   - The application automatically detects columns like Sales Amount, Date, Category, etc.
   - Click **⚙️ Column Mapping & Settings** in the sidebar to review or adjust mappings.
3. **Inspect the Data Quality Report:**
   - Switch to the **🔍 Data Quality & Cleaning** tab to view detected missing values, duplicates, and applied transformations.
4. **Explore the Dashboard & Apply Filters:**
   - View KPIs, Category Sales, Regional Sales, and Monthly Trends in the **📊 Executive Dashboard** tab.
   - Use the sidebar filters to drill down into specific dates, regions, or categories.
5. **Conduct In-Depth Analysis:**
   - **📈 Exploratory Data Analysis:** Check column profiles and value distributions.
   - **📐 Descriptive Statistics:** View mean, median, standard deviation, and quartiles.
   - **🔄 Custom Grouping & Aggregation:** Group any category and measure with custom operations.
   - **📅 Time-Series Analysis:** View revenue trends grouped by Day, Month, or Year.
6. **Download Results:**
   - Open the **💾 Export & Downloads** tab to download the cleaned dataset, filtered records, data quality audit, or statistical tables as CSV.

---

## Troubleshooting Common File-Loading Errors

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"Could not read the CSV file"** | Non-standard encoding or unusual separator. | The system automatically checks UTF-8, UTF-8-BOM, CP1252, and Latin-1, and tests comma, semicolon, tab, and pipe delimiters. Ensure the file is not corrupted or password-protected. |
| **"Uploaded file is empty (0 bytes)"** | The file contains no data or was saved incorrectly. | Re-export or save the file from Excel/database ensuring rows are populated. |
| **"Sales Amount / Revenue column is not mapped"** | The column header has an unconventional name. | Expand **⚙️ Column Mapping & Settings** in the sidebar and choose the column representing sales or revenue. |
| **"Cost exceeds revenue scale notice on Profit"** | The dataset's unit cost and sales amount columns have mismatched units or synthetic mock values. | Check the acknowledgment box in the sidebar if you wish to override the warning, or map a valid profit column. |
| **"Worksheet is empty"** | Selected sheet in Excel workbook has no data. | Select a different worksheet from the sheet dropdown in the sidebar. |

---

## Running the Automated Test Suite

To run the complete automated verification and performance suite covering all 20 test cases:
```powershell
python -m pytest tests/ -v
```
or run individual test modules:
```powershell
# Core functionality test suite (14 tests)
python -m pytest tests/test_system.py -v

# Export performance and large dataset suite (6 tests)
python -m pytest tests/test_performance_and_exports.py -v
```
