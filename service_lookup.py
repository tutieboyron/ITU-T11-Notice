import re
from utils import build_lookup_key


# ============================================================
# NORMALIZE POLARIZATION
# ============================================================
def normalize_polarization(value):
    if value is None:
        return ""

    pol = str(value).upper().strip()
    pol = re.sub(r"\(.*?\)", "", pol)   # Remove text in brackets
    pol = " ".join(pol.split())         # Normalize whitespace

    mapping = {
        # Single
        "V": "V",
        "VERTICAL": "V",
        "V ONLY": "V",

        "H": "H",
        "HORIZONTAL": "H",
        "H ONLY": "H",

        # Mixed / dual
        "V/H": "M",
        "H/V": "M",
        "V+H": "M",
        "H+V": "M",
        "2*V/H": "M",
        "V/H SD": "M",

        # Already valid ITU values
        "M": "M",
        "SR": "SR",
        "SL": "SL",
        "CR": "CR",
        "CL": "CL",
        "D": "D",
        "L": "L",
    }

    return mapping.get(pol, "")

# ============================================================
# BUILD LOOKUP INDEX
# ============================================================

def build_service_lookup(service_df):
    """
    Build lookup dictionary from Service Fixe sheet.
    """

    lookup = {}

    for _, row in service_df.iterrows():

        key = build_lookup_key(
            row["AD_CITY_A"],
            row["AD_CITY_B"],
            row["EFL_FREQ_A_TX"]
        )

        lookup[key] = row
    return lookup


# ============================================================
# FIND MATCH
# ============================================================

def get_service_row(itu_row, lookup):
    """
    Return matching Service Fixe row.
    """
    key = build_lookup_key(
        itu_row["AD_CITY_A"],
        itu_row["AD_CITY_B"],
        itu_row["EFL_FREQ_A_TX"]
    )

    service_row = lookup.get(key)
    if service_row is None:
        return None

    # Work on a copy so the lookup dictionary isn't modified
    service_row = service_row.copy()

    service_row["EAN_POL_A"] = normalize_polarization(
        service_row["EAN_POL_A"]
    )

    return service_row