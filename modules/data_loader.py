"""
Data Loader Module for Sales Data Analysis System.
Provides robust loading of CSV and Excel (.xlsx) files with encoding fallbacks,
delimiter auto-detection, empty file validation, and multiple sheet support.
"""

import io
import csv
from typing import List, Tuple, Optional, Any, Dict
import pandas as pd


def get_excel_sheet_names(file_source: Any) -> Tuple[bool, List[str], str]:
    """
    Inspects an Excel file to extract available sheet names.
    Returns: (success, sheet_names, error_message)
    """
    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        excel_file = pd.ExcelFile(file_source, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        if not sheet_names:
            return False, [], "The uploaded Excel workbook contains no worksheets."
        return True, sheet_names, ""
    except Exception as e:
        return False, [], f"Could not inspect Excel workbook: {str(e)}"


def load_csv_file(
    file_source: Any,
    encoding_override: Optional[str] = None,
    delimiter_override: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], bool, str, str, str]:
    """
    Robustly loads a CSV file with automatic encoding fallback and delimiter detection.
    
    Returns:
      (df, success, error_message, encoding_used, delimiter_used)
    """
    # Read raw bytes safely
    try:
        if hasattr(file_source, "read"):
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            raw_bytes = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(0)
        else:
            with open(file_source, "rb") as f:
                raw_bytes = f.read()
    except Exception as e:
        return None, False, f"Failed to read file from disk or buffer: {str(e)}", "", ""

    if not raw_bytes or len(raw_bytes.strip()) == 0:
        return None, False, "The uploaded file is empty (0 bytes). Please upload a file containing data.", "", ""

    # Controlled list of encodings to try
    encodings_to_try = [encoding_override] if encoding_override else ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    delimiters_to_try = [delimiter_override] if delimiter_override else [",", ";", "\t", "|"]

    best_df = None
    best_encoding = ""
    best_delimiter = ""
    last_error = ""

    for enc in encodings_to_try:
        try:
            text = raw_bytes.decode(enc)
        except (UnicodeDecodeError, LookupError) as e:
            last_error = f"Encoding {enc} failed: {e}"
            continue

        # Check if text has content
        stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not stripped_lines:
            return None, False, "The file text is empty or contains only whitespace.", enc, ""

        # Delimiter detection
        chosen_delim = ","
        if delimiter_override:
            chosen_delim = delimiter_override
        else:
            # Sniff delimiter on sample header lines
            sample_text = "\n".join(stripped_lines[:5])
            try:
                sniffer = csv.Sniffer()
                sniffed = sniffer.sniff(sample_text, delimiters=",;\t|")
                chosen_delim = sniffed.delimiter
            except Exception:
                # Fallback: check which delimiter produces the most columns on header line
                first_line = stripped_lines[0]
                counts = {d: first_line.count(d) for d in delimiters_to_try}
                chosen_delim = max(counts, key=counts.get)
                if counts[chosen_delim] == 0:
                    chosen_delim = ","

        try:
            df = pd.read_csv(
                io.StringIO(text),
                sep=chosen_delim,
                engine="python",
                on_bad_lines="warn"
            )

            # Validate resulting DataFrame
            if df.empty:
                return None, False, "The CSV file was parsed but contains 0 data rows.", enc, chosen_delim

            # Ensure we didn't end up with an unparsed single column containing delimiter characters
            if len(df.columns) == 1 and chosen_delim == ",":
                col_name = str(df.columns[0])
                if ";" in col_name or "\t" in col_name:
                    # Retry with semicolon
                    for alt_delim in [";", "\t", "|"]:
                        try:
                            alt_df = pd.read_csv(
                                io.StringIO(text),
                                sep=alt_delim,
                                engine="python"
                            )
                            if len(alt_df.columns) > 1:
                                df = alt_df
                                chosen_delim = alt_delim
                                break
                        except Exception:
                            pass

            best_df = df
            best_encoding = enc
            best_delimiter = chosen_delim
            break

        except Exception as parse_err:
            last_error = f"CSV parsing error using encoding {enc} and delimiter '{chosen_delim}': {str(parse_err)}"
            continue

    if best_df is not None:
        return best_df, True, "", best_encoding, best_delimiter
    else:
        return None, False, f"Could not reliably load CSV file. Reason: {last_error}. Please ensure the file is a standard comma- or semicolon-separated text file.", "", ""


def load_excel_file(
    file_source: Any,
    sheet_name: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], bool, str]:
    """
    Loads an Excel workbook (.xlsx) with sheet handling and empty sheet detection.
    
    Returns:
      (df, success, error_message)
    """
    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)
            
        excel_file = pd.ExcelFile(file_source, engine="openpyxl")
        sheet_names = excel_file.sheet_names

        if not sheet_names:
            return None, False, "The Excel workbook has no sheets."

        target_sheet = sheet_name if (sheet_name and sheet_name in sheet_names) else sheet_names[0]

        df = pd.read_excel(excel_file, sheet_name=target_sheet, engine="openpyxl")

        if df is None or df.empty:
            return None, False, f"Worksheet '{target_sheet}' is empty. Please choose a worksheet containing sales data."

        # Check if all rows or columns are unnamed/null
        if df.columns.astype(str).str.contains("^Unnamed").all() and df.dropna(how="all").empty:
            return None, False, f"Worksheet '{target_sheet}' contains no recognizable header or data rows."

        return df, True, ""

    except Exception as e:
        return None, False, f"Failed to load Excel file: {str(e)}. Please verify that the file is a valid .xlsx document."


def load_dataset(
    uploaded_file: Any,
    sheet_name: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], bool, str, Dict[str, Any]]:
    """
    Unified entry point for loading any uploaded file (CSV or Excel).
    
    Returns:
      (df, success, message, metadata_dict)
    """
    if uploaded_file is None:
        return None, False, "No file uploaded.", {}

    filename = getattr(uploaded_file, "name", "dataset.csv").lower()
    meta = {
        "filename": filename,
        "format": "csv" if filename.endswith(".csv") else "excel",
        "sheet_names": [],
        "encoding": "N/A",
        "delimiter": "N/A"
    }

    if filename.endswith(".csv"):
        df, success, err, enc, delim = load_csv_file(uploaded_file)
        meta["encoding"] = enc
        meta["delimiter"] = delim
        if not success:
            return None, False, err, meta
        return df, True, f"CSV loaded successfully (Encoding: {enc}, Delimiter: '{delim}').", meta

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        # Check sheet names first
        s_ok, sheets, s_err = get_excel_sheet_names(uploaded_file)
        if not s_ok:
            return None, False, s_err, meta
        meta["sheet_names"] = sheets
        meta["format"] = "excel"

        chosen_sheet = sheet_name if sheet_name in sheets else sheets[0]
        meta["active_sheet"] = chosen_sheet

        df, success, err = load_excel_file(uploaded_file, sheet_name=chosen_sheet)
        if not success:
            return None, False, err, meta
        return df, True, f"Excel worksheet '{chosen_sheet}' loaded successfully.", meta

    else:
        return None, False, f"Unsupported file extension for '{filename}'. Only .csv and .xlsx files are supported.", meta
