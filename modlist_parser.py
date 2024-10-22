import csv
import re
import requests
import sys
import logging

logging.basicConfig(level=logging.INFO)

def extract_mods_from_log(input_source):
    logging.info(f"Extracting mods from: {input_source}")  

    try:
        if input_source.startswith("http://") or input_source.startswith("https://"):
            response = requests.get(input_source)
            response.raise_for_status()
            content = response.text
            logging.info(f"Fetched {len(content)} characters from {input_source}")  
        else:
            with open(input_source, 'r') as file:
                content = file.read()
            logging.info(f"Read {len(content)} characters from {input_source}")  

        # First, try to extract from the mod loading section
        mod_section = re.search(r'\[main/INFO]: Loading \d+ mods:\s*([\s\S]*?)(?=\n\n)', content)
        
        if mod_section:
            logging.info("Mod section found. Extracting mods from log...")
            return parse_mod_section(mod_section.group(1))

        # If the standard section is not found, look for a simple list of mods
        logging.warning(f"No mod list found in {input_source}. Trying to extract simple mod list...")
        return parse_simple_mod_list(content)
    
    except Exception as e:
        logging.error(f"Error extracting mods: {e}")
        return []

def parse_mod_section(mod_section):
    mods = []
    for line in mod_section.splitlines():
        if line.startswith('- '):
            parts = line[2:].split(' ', 1)  
            mod_name = parts[0]
            version = parts[1] if len(parts) > 1 else "N/A"
            mods.append((mod_name, version))

    logging.info(f"Extracted {len(mods)} mods from log section.")
    return mods

def parse_simple_mod_list(content):
    mods = []
    lines = content.splitlines()

    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            parts = line[2:].split(' ', 1)  
            mod_name = parts[0]
            version = parts[1] if len(parts) > 1 else "N/A"
            mods.append((mod_name, version))
        elif '|' in line or '\\' in line:  # Handle sub-mods indicated by "|--" or "\--"
            sub_mods = line.replace('|--', '-').replace('\\--', '-').strip().split('-')
            for sub_mod in sub_mods:
                sub_mod = sub_mod.strip()
                if sub_mod:
                    parts = sub_mod.split(' ', 1)
                    mod_name = parts[0]
                    version = parts[1] if len(parts) > 1 else "N/A"
                    mods.append((mod_name, version))

    logging.info(f"Extracted {len(mods)} mods from simple list.")
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
