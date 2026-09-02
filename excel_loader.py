import pandas as pd
from openpyxl import load_workbook
from config import (INPUT_FILE, ITU_SHEET, SERVICE_SHEET)


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================
def clean_columns(df):
    """
    Remove extra spaces and line breaks from column names.
    """
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\n", " ", regex=False))
    return df


# ============================================================
# LOAD WORKBOOK
# ============================================================

def load_excel():
    """
    Load workbook, worksheets and DataFrames.
    """
    wb = load_workbook(INPUT_FILE)
    ws = wb[ITU_SHEET]

    itu_df = pd.read_excel(INPUT_FILE, sheet_name=ITU_SHEET)
    service_df = pd.read_excel(INPUT_FILE, sheet_name=SERVICE_SHEET)

    itu_df = clean_columns(itu_df)
    service_df = clean_columns(service_df)
    return wb, ws, itu_df, service_df


# ============================================================
# FIND FREQUENCY COLUMN
# ============================================================
def find_frequency_column(df):
    """
    Automatically locate the transmit frequency column.
    """
    for col in df.columns:
        cleaned = col.strip().upper()
        if "EFL_FREQ_A_T" in cleaned:
            return col

    raise ValueError(
        "Frequency column not found."
    )

# ============================================================
# FIND BANDWIDTH COLUMN
# ============================================================
def find_bandwidth_column(df):
    """
    Automatically locate the bandwidth column.
    """
    for col in df.columns:
        cleaned = col.strip().upper()

        if (
            "EFL_RF_BWIDTH" in cleaned
            or
            "EFL_RF_BWDTH" in cleaned
            or
            "CHANNEL_SPACE" in cleaned
            or
            "CHANNEL_SPACING" in cleaned
        ):
            return col

    raise ValueError(
        "Bandwidth column not found."
    )

# ============================================================
# REQUIRED COLUMNS
# ============================================================
def validate_columns(df):
    """
    Ensure the ITU worksheet contains all mandatory columns.
    """
    required = [
        "AD_CITY_A",
        "AD_CITY_B",
        "LATITUDE_A",
        "LONGITUDE_A",
        "LATITUDE_B",
        "LONGITUDE_B",
        "EQ_BAND"
    ]

    missing = []

    for column in required:
        if column not in df.columns:
            missing.append(column)

    if missing:
        raise ValueError(
            f"Missing columns: {', '.join(missing)}")


# ============================================================
# PREPARE WORKBOOK
# ============================================================
def prepare_workbook():
    """
    Load and validate the workbook.
    """
    wb, ws, itu_df, service_df = load_excel()

    validate_columns(itu_df)
    frequency_column = find_frequency_column(itu_df)
    bandwidth_column = find_bandwidth_column(itu_df)

    print("\nWorkbook loaded successfully.")
    print(f"Frequency column : {frequency_column}")
    print(f"Bandwidth column : {bandwidth_column}")
    return (wb, ws, itu_df, service_df, frequency_column, bandwidth_column)