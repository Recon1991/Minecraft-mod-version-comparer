import csv
import re
import requests
import sys

def extract_mods_from_log(input_source):
    # Check if input source is a URL or a file path
    if input_source.startswith("http://") or input_source.startswith("https://"):
        response = requests.get(input_source)
        content = response.text
    else:
        with open(input_source, 'r') as file:
            content = file.read()

    # Look for the mod loading section
    mod_section = re.search(r'\[main/INFO]: Loading \d+ mods:\n((?:.*\n)*?)\n\n', content)
    if not mod_section:
        print(f"No mod list found in {input_source}")
        return []

    mods = []
    for line in mod_section.group(1).splitlines():
        if line.startswith('- '):
            parts = line[2:].split(' ', 1)  # Split on the first space
            mod_name = parts[0]
            version = parts[1] if len(parts) > 1 else "N/A"
            mods.append((mod_name, version))

    return mods


def compare_mods(mods1, mods2):
    # Convert to dictionaries for easy comparison
    dict1 = {mod[0]: mod[1] for mod in mods1}
    dict2 = {mod[0]: mod[1] for mod in mods2}

    comparison = []

    # Check for matches, mismatches, and missing mods
    all_mods = set(dict1.keys()).union(set(dict2.keys()))

    for mod in all_mods:
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

    return comparison

def write_to_csv(data, output_file="mod_comparison.csv"):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Mod Name (Link1)", "Version (Link1)", 
                         "Mod Name (Link2)", "Version (Link2)", 
                         "Comparison Result"])
        writer.writerows(data)

def main():
    if len(sys.argv) < 3:
        print("Usage: python mcmodlist-comparer.py <link1> <link2>")
        sys.exit(1)

    link1 = sys.argv[1]
    link2 = sys.argv[2]

    mods1 = extract_mods_from_log(link1)
    mods2 = extract_mods_from_log(link2)

    comparison = compare_mods(mods1, mods2)

    write_to_csv(comparison)
    print("Comparison completed! Check 'mod_comparison.csv' for the results.")

if __name__ == "__main__":
    main()
