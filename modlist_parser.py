import csv
import re
import requests
import sys
import logging

logging.basicConfig(level=logging.INFO)

import logging
import re
import requests

def extract_mods_from_log(input_source):
    logging.info(f"Extracting mods from: {input_source}")

    # Check if input source is a URL or a file path
    if input_source.startswith("http://") or input_source.startswith("https://"):
        response = requests.get(input_source)
        content = response.text
        logging.info(f"Fetched {len(content)} characters from {input_source}")
    else:
        with open(input_source, 'r') as file:
            content = file.read()
        logging.info(f"Read {len(content)} characters from {input_source}")

    # Attempt to find the mod loading section using regex
    mod_section = re.search(r'\[main/INFO]: Loading \d+ mods:\n((?:.*\n)*?)\n\n', content)

    mods = []

    # If no detailed mod loading section found, attempt to find simple mod list entries
    if not mod_section:
        logging.warning(f"No detailed mod loading section found. Attempting to extract simple mod list...")

        # Use regex to find lines starting with '-' or '\--'
        mod_entries = re.findall(r'^[ \t]*[-\\]{1,2}\s*(\S+)\s*(\S+.*)$', content, re.MULTILINE)
        
        if mod_entries:
            for entry in mod_entries:
                mod_name = entry[0].strip()
                version = entry[1].strip()
                mods.append((mod_name, version))
        else:
            logging.warning(f"No mod list found in {input_source}")
            return []

    else:  # Detailed mod loading section case
        for line in mod_section.group(1).splitlines():
            # Updated regex pattern to capture mod names and versions
            mod_regex = r'^\s*-\s*(\S+)\s+([\d+\.\d+(-\w+)?(\+\d+\.\d+)?]+)'  # Updated regex pattern
            match = re.match(mod_regex, line)
            if match:
                mod_name = match.group(1).strip()
                version = match.group(2).strip()
                mods.append((mod_name, version))
            elif line.strip() == "":
                continue  # Ignore empty lines
            else:
                break  # Stop if we hit a line that doesn't match mod formatting

    # Filtering out non-mod entries from the extracted list
    mods = [mod for mod in mods if 'recommended version' not in mod[0].lower() and 'should install' not in mod[0].lower()]

    logging.info(f"Extracted {len(mods)} mods from {input_source}")
    logging.debug(f"First 5 mods: {mods[:5]}")  # Optional: Display a sample

    return mods


def compare_mods(mods1, mods2):
    logging.info("Comparing mods...")

    # Convert to dictionaries for easy comparison
    dict1 = {mod[0]: mod[1] for mod in mods1}
    dict2 = {mod[0]: mod[1] for mod in mods2}

    comparison = []
    all_mods = set(dict1.keys()).union(set(dict2.keys()))

    for mod in sorted(all_mods):  # Sort mod names here
        version1 = dict1.get(mod, "N/A")
        version2 = dict2.get(mod, "N/A")

        if version1 == version2:
            result = "Match" if version1 != "N/A" else "N/A"
        elif version1 == "N/A":
            result = "Missing in Link1"
        elif version2 == "N/A":
            result = "Missing in Link2"
        else:
            result = "Mismatch"

        comparison.append((mod, version1, mod, version2, result))

    logging.info(f"Comparison completed. Total mods compared: {len(comparison)}")
    return comparison

def write_to_csv(data, output_file="mod_comparison.csv"):
    logging.info(f"Writing comparison results to {output_file}...")

    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Mod Name (Link1)", "Version (Link1)", 
                         "Mod Name (Link2)", "Version (Link2)", 
                         "Comparison Result"])
        
        for row in data:
            logging.debug(f"Writing row: {row}")  # Optional: Print each row being written
            writer.writerow(row)

    logging.info("CSV writing completed.")
 

def main():
    if len(sys.argv) < 3:
        print("Usage: python mcmodlist-comparer.py <link1> <link2> [output_file]")
        sys.exit(1)

    link1 = sys.argv[1]
    link2 = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "mod_comparison.csv"

    mods1 = extract_mods_from_log(link1)
    mods2 = extract_mods_from_log(link2)

    comparison = compare_mods(mods1, mods2)

    write_to_csv(comparison, output_file)
    print(f"Comparison completed! Check '{output_file}' for the results.")

if __name__ == "__main__":
    main()
