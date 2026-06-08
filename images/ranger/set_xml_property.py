#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import sys
import os
import xml.etree.ElementTree as ET

def main():
    """Parse command line arguments and update or append the specified XML property atomically."""
    if len(sys.argv) < 4:
        print("Usage: set_xml_property.py <filename> <property> <value>")
        sys.exit(1)

    filename = sys.argv[1]
    prop_name = sys.argv[2]
    prop_val = sys.argv[3]

    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        sys.exit(1)

    try:
        tree = ET.parse(filename)
        root = tree.getroot()

        # Find existing property
        found = False
        for prop in root.findall("property"):
            name_el = prop.find("name")
            if name_el is not None and name_el.text == prop_name:
                val_el = prop.find("value")
                if val_el is None:
                    val_el = ET.SubElement(prop, "value")
                val_el.text = prop_val
                found = True
                break

        if not found:
            prop = ET.SubElement(root, "property")
            name_el = ET.SubElement(prop, "name")
            name_el.text = prop_name
            val_el = ET.SubElement(prop, "value")
            val_el.text = prop_val

        # Write atomically
        tmp_filename = filename + ".tmp"
        tree.write(tmp_filename, encoding="utf-8", xml_declaration=True)
        os.replace(tmp_filename, filename)
        print(f"Successfully set property '{prop_name}' to '{prop_val}' in {filename}")

    except Exception as e:
        print(f"Error updating XML file {filename}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
