#!/usr/bin/env python3
"""Convert natbib \citet/\citep commands to manual APA format.

Usage:
    python citation_converter.py input.tex > output.tex
    python citation_converter.py --in-place input.tex

The citation map is loaded from a JSON file (default: citation_map.json).
If the map file doesn't exist, use --dry-run to see unmapped keys.
"""

import re
import json
import sys
import argparse
from pathlib import Path

# Default citation map — extend this for your project
DEFAULT_MAP = {
    "biesta2020": {"text": "Biesta (2020)", "paren": "Biesta, 2020"},
    "biesta2015": {"text": "Biesta (2015)", "paren": "Biesta, 2015"},
    "biesta2013": {"text": "Biesta (2013)", "paren": "Biesta, 2013"},
    "biesta2006": {"text": "Biesta (2006)", "paren": "Biesta, 2006"},
}


def load_map(map_path=None):
    if map_path and Path(map_path).exists():
        with open(map_path) as f:
            return json.load(f)
    return dict(DEFAULT_MAP)


def convert_citet(keys_str, cite_map):
    keys = [k.strip() for k in keys_str.split(",")]
    parts = []
    for k in keys:
        entry = cite_map.get(k) or cite_map.get(k.lower())
        if entry:
            parts.append(entry["text"])
        else:
            parts.append(f"{k} (YEAR)")
            print(f"WARNING: Unknown key '{k}'", file=sys.stderr)
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + ", and " + parts[-1]


def convert_citep(keys_str, cite_map):
    keys = [k.strip() for k in keys_str.split(",")]
    parts = []
    for k in keys:
        entry = cite_map.get(k) or cite_map.get(k.lower())
        if entry:
            parts.append(entry["paren"])
        else:
            parts.append(f"{k}, YEAR")
            print(f"WARNING: Unknown key '{k}'", file=sys.stderr)
    if len(parts) == 1:
        return f"({parts[0]})"
    return f"({'; '.join(parts)})"


def convert(content, cite_map):
    content = re.sub(r"\\citet\{([^}]+)\}", lambda m: convert_citet(m.group(1), cite_map), content)
    content = re.sub(r"\\citep\{([^}]+)\}", lambda m: convert_citep(m.group(1), cite_map), content)
    content = re.sub(r"\\cite\{([^}]+)\}", lambda m: convert_citep(m.group(1), cite_map), content)
    return content


def main():
    parser = argparse.ArgumentParser(description="Convert natbib citations to manual APA")
    parser.add_argument("input", help="Input .tex file")
    parser.add_argument("--in-place", "-i", action="store_true", help="Edit file in place")
    parser.add_argument("--map", "-m", help="Path to citation map JSON")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show unmapped keys only")
    args = parser.parse_args()

    with open(args.input) as f:
        content = f.read()

    cite_map = load_map(args.map)

    if args.dry_run:
        keys = set(re.findall(r"\\cite[tp]?\{([^}]+)\}", content))
        for k in sorted(keys):
            for subkey in [s.strip() for s in k.split(",")]:
                if subkey not in cite_map and subkey.lower() not in cite_map:
                    print(f"MISSING: {subkey}")
        return

    converted = convert(content, cite_map)

    if args.in_place:
        with open(args.input, "w") as f:
            f.write(converted)
        print(f"Converted {args.input} in place")
    else:
        sys.stdout.write(converted)


if __name__ == "__main__":
    main()
