import re
from datetime import datetime

def normalize_band(band):
    if band is None:
        return ""

    band = str(band).strip().upper()
    band = band.replace(" ", "") # Remove spaces
    band = band.replace("GHZ", "") # Remove GHz

    # Leave L bands unchanged
    if band.startswith("L"):
        return band

    # Extract the number
    match = re.search(r"\d+", band)

    if match:
        return f"{match.group()}G"

    return band
# -----------------------------------------------------------
# -----------------------------------------------------------

# Clean and standardize text values.
def clean_text(text):
    if text is None:
        return ""

    text = str(text).strip().upper()
    text = re.sub(r"\s+", " ", text)

    return text


# Return a safe string value.
def safe_value(value, default=""):
    if value is None:
        return default

    text = str(value).strip()

    if text == "":
        return default

    if text.lower() == "nan":
        return default

    return text


# Normalize frequency values for dictionary lookup.
def normalize_frequency(freq):
    if freq is None or freq == "":
        return ""

    try:
        return f"{float(freq):.6f}"

    except (TypeError, ValueError):
        return str(freq).strip()


# Build a unique lookup key for Service Fixe records.
def build_lookup_key(city_a, city_b, frequency):
    return (
        clean_text(city_a),
        clean_text(city_b),
        normalize_frequency(frequency)
    )


# Convert bandwidth into ITU format.
def format_bandwidth(value):
    if value is None:
        return ""

    text = str(value).strip().upper()
    if text == "" or text == "NAN":
        return ""
    
    # Remove spaces
    text = text.replace(" ", "")
    # Remove MHz suffix
    text = text.replace("MHZ", "")
    match = re.fullmatch(r"(\d+)M(\d+)", text) # Convert 13M75 -> 13.75

    if match:
        text = f"{match.group(1)}.{match.group(2)}"
    elif text.endswith("M"):
        text = text[:-1]

    bandwidth = float(text)
    if bandwidth.is_integer():
        bandwidth = int(bandwidth)

    bandwidth = round(bandwidth)
    if bandwidth < 10:
        return f"H{bandwidth}00"
    
    if bandwidth >= 100:
        return f"{bandwidth}M"

    return f"{bandwidth}M0"


# Build a unique administration reference ID.
def build_reference_id(tx_site, rx_site, frequency):
    tx = clean_text(tx_site).replace(" ", "_")
    rx = clean_text(rx_site).replace(" ", "_")
    freq = normalize_frequency(frequency)

    return f"{tx}_{rx}_{freq}"

# FORMAT DATE
def format_date():
    return datetime.today().strftime("%Y-%m-%d")


# format for integer values without unnecessary decimal points
def format_integer(value):
    if value in ("", None):
        return ""

    text = str(value).strip()
    if "/" in text:  # If there are multiple values, use the first one
        text = text.split("/")[0].strip()

    match = re.search(r"\d+(?:\.\d+)?", text) # Extract the first integer or decimal number
    if not match:
        return ""

    return str(int(round(float(match.group()))))


# Format numeric values without unnecessary zeros.
def format_number(value, decimals=2):
    if value is None or value == "":
        return ""

    try:
        value = float(value)
        if value.is_integer():
            return str(int(value))

        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


# Check if a value is empty
def is_empty(value):
    if value is None:
        return True

    text = str(value).strip()
    return text == "" or text.lower() == "nan"


# responsible for checking if a value is a valid number
def format_double(value): 
    if value in ("", None):
        return ""

    text = str(value).strip()
    match = re.match(r"^[-+]?\d+(?:\.\d+)?", text) # Match a signed integer or decimal at the start of the string

    if match:
        return match.group()
    match = re.match(r"^[-+]?\d+(?:\.\d+)?", text.replace("_", "-")) # Handle cases like "20_ATPC" or "20.8-ATPC"

    if match:
        return match.group()

    return ""


# format site_name
def format_site_name(value):
    if value in ("", None):
        return ""

    text = str(value).strip().upper()
    text = text.replace(".", " ")   # Replace periods with spaces
    text = re.sub(r"[^A-Z0-9 _-]", "", text)  # Remove any unsupported characters
    text = " ".join(text.split())  # Collapse multiple spaces
    text = text[:30]
    return text