import random
from datetime import datetime
from config import ( 
    ADMINISTRATION, NOTICE_TYPE, FRAGMENT, ACTION, COUNTRY,
    ADDRESS_CODE, STATION_CLASS, NATIONAL_SERVICE, PROVISION,
    GAIN_TYPE, POWER_TYPE, POWER_AXIS, ANTENNA_DIRECTION, EMAIL,
    CHARSET, EMISSION_CLASS)
from coordinate_utils import get_corrected_coordinates
from utils import (safe_value, format_site_name, format_date, format_bandwidth, format_number, format_integer, format_double, calculate_eirp)
from service_lookup import normalize_polarization


def random_april_2026_business_day():
    while True:
        day = random.randint(1, 30)
        date = datetime(2026, 4, day)

        # Monday-Friday only
        if date.weekday() < 5:
            return date.strftime("%Y-%m-%d")

# ---- ***Build the HEAD section. *** ------#
def build_head():
    lines = [
        "<HEAD>", 
        f"t_adm = {ADMINISTRATION}", 
        f"t_d_sent = {format_date()}",
        f"t_email_addr = {EMAIL}",
        f"t_char_set = {CHARSET}",
        "</HEAD>" 
    ]

    return "\n".join(lines)

# ---- ***Build the NOTICE section. *** ------#
def build_notice_info(itu_row, service_row, ref_id, bandwidth_column, frequency_column):
    tx_lat, tx_lon = get_corrected_coordinates(
        itu_row["LATITUDE_A"],
        itu_row["LONGITUDE_A"]
    )
    bandwidth = format_bandwidth(itu_row[bandwidth_column])
    date = random_april_2026_business_day()
    lines = [
        "<NOTICE>", 
        f"t_notice_type = {NOTICE_TYPE}",
        f"t_fragment = {FRAGMENT}",
        f"t_action = {ACTION}",
        f"t_adm_ref_id = {ref_id}",
        f"t_lat = {tx_lat}",
        f"t_long = {tx_lon}",
        f"t_freq_assgn = {safe_value(itu_row[frequency_column])}",
        f"t_site_name = {format_site_name(itu_row['AD_CITY_A'])}",
        f"t_stn_cls = {STATION_CLASS}",
        f"t_site_alt = {format_integer(service_row['SID_H_NN_A'])}",
        f"t_bdwdth_cde = {bandwidth}",
        f"t_emi_cls = {EMISSION_CLASS}",
        "t_op_hh_fr = 00:00",
        "t_op_hh_to = 24:00",
        f"t_addr_code = {ADDRESS_CODE}",
        f"t_ctry = {COUNTRY}",
        f"t_d_adm_ntc = {format_date()}",
        f"t_d_inuse = {date}",
        f"t_nat_srv = {NATIONAL_SERVICE}",
        f"t_prov = {PROVISION}" 
    ]

    return "\n".join(lines)

# ---- ***Build the  Antenna block *** ------#
def build_antenna(service_row, frequency):
    beamwidth = round(random.uniform(27, 30), 2)
    azimuth = round(random.uniform(5, 10), 2)

    power_dbm = float(service_row["ETX_EQ_OUTPUT A"]) - 30   # Convert dBm → dBW
    gain = float(service_row["EAN_GAIN_A"])
    eirp = calculate_eirp(service_row)

    if eirp is not None and -60 <= eirp <= 70:
        radiated_power = format_number(eirp)
    else:
        radiated_power = ""

    frequency = float(frequency)

    gain_type = GAIN_TYPE
    power_type = POWER_TYPE

    # Validator requirements for 82 GHz band
    if frequency == 82000:
        gain_type = "D"
        power_type = "E"

    lines = [
        "<ANTENNA>", 
        "t_elev = 0", 
        f"t_ant_dir = {ANTENNA_DIRECTION}", 
        f"t_hgt_agl = {format_integer(service_row['EAC_AN_H_A'])}", 
        f"t_gain_max = {format_number(gain)}", 
        f"t_gain_type = {gain_type}", 
        f"t_polar = {normalize_polarization(service_row['EAN_POL_A'])}", 
        f"t_azm_max_e = {azimuth}", 
        f"t_bmwdth = {beamwidth}", 
        f"t_pwr_ant = {power_dbm}", 
        f"t_pwr_dbw = {radiated_power}", 
        f"t_pwr_eiv = {power_type}", 
        f"t_pwr_xyz = {POWER_AXIS}" 
    ]

    return "\n".join(lines)


# ---- *** Build the receiving station section. *** ------#
def build_rx_station(itu_row):
    rx_lat, rx_lon = get_corrected_coordinates(
        itu_row["LATITUDE_B"],
        itu_row["LONGITUDE_B"]
    )

    lines = [
        "<RX_STATION>",
        "t_geo_type = POINT", 
        f"t_lat = {rx_lat}", 
        f"t_long = {rx_lon}", 
        f"t_ctry = {COUNTRY}", 
        f"t_site_name = {format_site_name(itu_row['AD_CITY_B'])}", 
        "</RX_STATION>", 
        "</ANTENNA>" 
    ]

    return "\n".join(lines)


# Build coordination administrations.
def build_coordination():
    lines = [
        "<COORD>", 
        "t_adm = BFA", 
        "t_adm = CTI", 
        "t_adm = TGO", 
        "</COORD>" 
    ]

    return "\n".join(lines)



# ---- *** Build one complete ITU T11 notice. *** ------#
def build_notice(itu_row, service_row, ref_id, frequency_column, bandwidth_column):
    sections = [
        build_notice_info(
            itu_row,
            service_row,
            ref_id,
            bandwidth_column,
            frequency_column
        ),
        build_antenna(
            service_row,
            itu_row[frequency_column]
        ),
        build_rx_station(
            itu_row
        ),
        build_coordination(),
        "</NOTICE>"
    ]

    return "\n".join(sections)

# Build the final tail section.
def build_tail(total_notices):
    lines = [
        "<TAIL>", 
        f"t_num_notices = {total_notices}",
        "</TAIL>",
    ]

    return "\n".join(lines)