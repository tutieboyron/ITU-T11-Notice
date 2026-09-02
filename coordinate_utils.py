import re
import pandas as pd


# CLEAN COORDINATE
def clean_coordinate(coord):
    """
    Remove unnecessary symbols and spaces.
    """
    if pd.isna(coord):
        raise ValueError("Empty coordinate")

    coord = str(coord).strip().upper()
    coord = coord.replace("°", " ")
    coord = coord.replace("'", " ")
    coord = coord.replace('"', " ")
    coord = re.sub(r"\s+", " ", coord)
    return coord


# Returns True if the coordinate is in DMS format.
def is_dms(coord):
    """
    Returns True only for real DMS coordinates.

    Examples:
        5°45'58.84"N
        5 45 58 N
        005 45 58 W
    """

    coord = clean_coordinate(coord)

    pattern = (
        r"^\d{1,3}\s+"
        r"\d{1,2}\s+"
        r"\d{1,2}(?:\.\d+)?\s*"
        r"[NSEW]$"
    )

    return bool(re.match(pattern, coord))


# Convert DMS coordinates into ITU format.
def dms_to_itu(coord, is_lat=True):
    coord = clean_coordinate(coord)
    parts = coord.split()

    if len(parts) < 4:
        raise ValueError(
            f"Invalid DMS coordinate: {coord}"
        )

    degrees = int(float(parts[0]))
    minutes = int(float(parts[1]))
    seconds = int(round(float(parts[2])))

    direction = parts[3]

    # Handle rollover
    if seconds == 60:
        seconds = 0
        minutes += 1

    if minutes == 60:
        minutes = 0
        degrees += 1

    sign = "+"

    if direction in ["S", "W"]:
        sign = "-"

    if is_lat:
        return (
            f"{sign}"
            f"{degrees:02d}"
            f"{minutes:02d}"
            f"{seconds:02d}"
        )

    return (
        f"{sign}"
        f"{degrees:03d}"
        f"{minutes:02d}"
        f"{seconds:02d}"
    )


# Convert decimal coordinates into ITU format.
def decimal_to_itu(value, is_lat=True):
    value = float(value)
    sign = "+"

    if value < 0:
        sign = "-"

    value = abs(value)
    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = int(
        round(
            (minutes_float - minutes) * 60
        )
    )

    # Handle rollover
    if seconds == 60:
        seconds = 0
        minutes += 1

    if minutes == 60:
        minutes = 0
        degrees += 1

    if is_lat:
        return (
            f"{sign}"
            f"{degrees:02d}"
            f"{minutes:02d}"
            f"{seconds:02d}"
        )
    return (
        f"{sign}"
        f"{degrees:03d}"
        f"{minutes:02d}"
        f"{seconds:02d}"
    )


# Automatically detect coordinate type
def convert_coordinate(coord, is_lat=True):
    if is_dms(coord):
        return dms_to_itu(
            coord,
            is_lat=is_lat
        )

    return decimal_to_itu(
        coord,
        is_lat=is_lat
    )


# ============================================================
# SMART COORDINATE CORRECTION
# ============================================================

def get_corrected_coordinates(lat_value, lon_value):
    """
    Convert coordinates into ITU format.
    Also detects swapped decimal coordinates.
    """

    # DMS coordinates
    if is_dms(lat_value) and is_dms(lon_value):

        final_lat = convert_coordinate(
            lat_value,
            is_lat=True
        )

        final_lon = convert_coordinate(
            lon_value,
            is_lat=False
        )

        return final_lat, final_lon

    # Decimal coordinates
    lat_num = float(lat_value)
    lon_num = float(lon_value)

    # Detect swapped coordinates
    lat_looks_like_lon = -4 <= lat_num <= 2
    lon_looks_like_lat = 4 <= lon_num <= 12

    if lat_looks_like_lon and lon_looks_like_lat:
        real_lat = lon_num
        real_lon = lat_num
    else:
        real_lat = lat_num
        real_lon = lon_num

    # Validate Ghana coordinates
    if not (4 <= real_lat <= 12):
        raise ValueError(
            f"Invalid Ghana latitude: {real_lat}"
        )

    if not (-4 <= real_lon <= 2):
        raise ValueError(
            f"Invalid Ghana longitude: {real_lon}"
        )

    final_lat = decimal_to_itu(
        real_lat,
        is_lat=True
    )

    final_lon = decimal_to_itu(
        real_lon,
        is_lat=False
    )

    return final_lat, final_lon