from dbm import error
from coordinate_utils import get_corrected_coordinates
from pathlib import Path
from config import (INPUT_FILE, OUTPUT_FOLDER, GREEN_FILL, BLUE_FILL, RED_FILL, YELLOW_FILL)
from excel_loader import prepare_workbook
from service_lookup import (build_service_lookup, get_service_row)
from notice_builder import (build_head, build_notice, build_tail)
from utils import normalize_band, calculate_eirp

# the main function that orchestrates the ITU Notice generation process
def main():
    print("=" * 60)
    print("ITU T11 NOTICE GENERATOR")
    print("=" * 60)

    # Load workbook
    (
        wb,
        ws,
        itu_df,
        service_df,
        frequency_column,
        bandwidth_column
    ) = prepare_workbook()     # Load and validate the workbook

    # Build Service Fixe lookup
    print("\nBuilding Service Fixe lookup...")
    lookup = build_service_lookup(service_df)
    print(f"Lookup entries : {len(lookup):,}")


    # Overall statistics
    total_processed = 0
    total_missing = 0
    total_duplicates = 0
    total_eirp_exceeded = 0

    # Get available EQ_BAND values
    itu_df["NORMALIZED_BAND"] = (
        itu_df["EQ_BAND"]
        .apply(normalize_band)
    )

    bands = sorted(
        itu_df["NORMALIZED_BAND"]
        .unique()
    )

    bands = sorted(bands)
    print("\nBands found:")

    for band in bands:
        print(f"  • {band}")


    # ---*** Process Each Band ***---
    for band in bands:
        print("\n" + "=" * 60)
        print(f"Processing {band} Band")
        print("=" * 60)
        
        notice_counter = 1 # Restart numbering for this band
        band_notice_count = 0   # Number of notices written to this band

        notices = [] # Notices for this band only
        notice_signatures = set()
        notices.append(build_head()) # Add HEAD

        band_df = itu_df[itu_df["NORMALIZED_BAND"] == band] # Filter workbook for current band
        print(f"Records found : {len(band_df)}")

    
    # ---*** PROCESS EACH NOTICE ***---
        for excel_index, itu_row in band_df.iterrows():
            excel_row = excel_index + 2

            try:
                # ----*** Find matching Service Fixe record ***----
                service_row = get_service_row(itu_row, lookup)
                if service_row is None:
                    print(
                        f"Missing Service row: "
                        f"{itu_row['AD_CITY_A']} -> "
                        f"{itu_row['AD_CITY_B']}"
                    )

                    ws[f"A{excel_row}"].fill = RED_FILL
                    total_missing += 1
                    continue

            
                # Build Administration Reference
                band_name = str(band).strip().upper()

                if not band_name.endswith("G") and not band_name.startswith("L"):
                    band_name += "G"

                ref_id = (
                    f"MTN_FX_{band_name}_"
                    f"{notice_counter:05d}"
                )

                # Skip rows where radiated power (EIRP) exceeds 70 dBW
                eirp = calculate_eirp(service_row)
                if eirp is not None and eirp > 70:
                    print(
                        f"\nSKIPPED\n"
                        f"Band : {band}\n"
                        f"Sites : "
                        f"{itu_row['AD_CITY_A']} -> "
                        f"{itu_row['AD_CITY_B']}\n"
                        f"Reason : Radiated power exceeds 70 dBW ({eirp} dBW)"
                    )

                    ws[f"A{excel_row}"].fill = YELLOW_FILL
                    total_eirp_exceeded += 1
                    continue

                # Validating the gain max
                try:
                    gain = float(service_row["EAN_GAIN_A"])
                except (TypeError, ValueError):
                    gain = -1

                if gain < 0 or gain > 70:

                    print(
                        f"\nSKIPPED\n"
                        f"Band : {band}\n"
                        f"Sites : "
                        f"{itu_row['AD_CITY_A']} -> "
                        f"{itu_row['AD_CITY_B']}\n"
                        f"Reason : Invalid antenna gain ({gain} dB)"
                    )

                    ws[f"A{excel_row}"].fill = RED_FILL
                    total_missing += 1
                    continue

#===============================================================================================================
#** ---------- Working on Duplicates and Empty Fields ---------- **
                # Get coordinates
                tx_lat, tx_lon = get_corrected_coordinates(itu_row["LATITUDE_A"], itu_row["LONGITUDE_A"])
                frequency = float(itu_row[frequency_column])

                # Check duplicate BEFORE building the notice
                duplicate_key = (frequency, tx_lat, tx_lon)

                if duplicate_key in notice_signatures:
                    print(
                        f"Duplicate notice detected:\n"
                        f"Reference : {ref_id}\n"
                        f"Frequency : {frequency}\n"
                        f"Latitude  : {tx_lat}\n"
                        f"Longitude : {tx_lon}"
                    )

                    ws[f"A{excel_row}"].fill = BLUE_FILL
                    total_duplicates += 1
                    continue

                notice_signatures.add(duplicate_key)
                notice = build_notice(itu_row, service_row, ref_id, frequency_column, bandwidth_column) # Build the notice only if it isn't a duplicate

               #**-------- Check for empty fields --------
                invalid_notice = False

                for line in notice.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)

                        if value.strip() == "":
                            print(f"Skipping {ref_id}: Empty field -> {key.strip()}")
                            invalid_notice = True
                            break

                if invalid_notice:
                    ws[f"A{excel_row}"].fill = RED_FILL
                    total_missing += 1
                    continue

                notices.append(notice) # notice is valid

# ================================================================================================================
 
#** ---------- Write the notice to the list and mark the Excel row as processed --------            
                # Success
                ws[f"A{excel_row}"].fill = GREEN_FILL
                notice_counter += 1
                band_notice_count += 1
                total_processed += 1

            except Exception as error:
                total_missing += 1
                ws[f"A{excel_row}"].fill = RED_FILL

                print(
                    f"\nERROR\n"
                    f"Band : {band}\n"
                    f"Sites : "
                    f"{itu_row['AD_CITY_A']} -> "
                    f"{itu_row['AD_CITY_B']}\n"
                    f"{error}\n"
                )
            
        # ---*** END PROCESS EACH NOTICE ***---
        # add the TAIL for this band
        notices.append(build_tail(band_notice_count))

        Company_name = "GHA_MTN_FX"
        output_file = (
            Path(OUTPUT_FOLDER) /
            f"{Company_name}{band_name}.txt"
        )

        with open(output_file, "w",encoding="utf-8") as file:
            file.write("\n".join(notices))

        print(f"\nSaved : {output_file.name}")
        print(f"Generated notices : "
            f"{band_notice_count}"
            )

    # ============================================================
    # SAVE UPDATED WORKBOOK
    # ============================================================

    output_excel = (
        Path(OUTPUT_FOLDER) /
        "MTN_DATA_Processed.xlsx"
    )

    wb.save(output_excel)
    print("\nWorkbook saved.")
    print(f"\nSummary:")
    print(f"  Processed   : {total_processed:,}")
    print(f"  Duplicates  : {total_duplicates:,}")
    print(f"  EIRP > 70   : {total_eirp_exceeded:,}")
    print(f"  Skipped/err : {total_missing:,}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()