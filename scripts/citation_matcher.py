#!/usr/bin/env python3
"""Bidirectional citation ↔ reference checker for manual APA theses.

Checks:
1. Every Author (Year) in body text has a matching reference entry
2. Every reference entry is cited somewhere in the body

Usage:
    python citation_matcher.py thesis.tex
"""

import re
import sys
import argparse
from collections import defaultdict


def extract_body_citations(text):
    """Extract all Author (Year) or (Author, Year) patterns from body text.
    Excludes the reference list section."""
    # Split at References section
    ref_match = re.search(r"\\chapter\*\{References?\}", text)
    body = text[: ref_match.start()] if ref_match else text

    # Match patterns like: "Author (Year)" or "(Author, Year; Author2, Year2)"
    citations = set()

    # Textual: Author (Year)
    for m in re.finditer(r"([A-Z][a-z]+(?:\s(?:et al\.|van der |de |van |von )?[A-Z][a-z]+)*)\s\((\d{4})\)", body):
        author = m.group(1).strip()
        year = m.group(2)
        citations.add(f"{author} ({year})")

    # Parenthetical: (Author, Year)
    for m in re.finditer(r"\(([^)]+?\d{4})\)", body):
        inner = m.group(1)
        parts = [p.strip() for p in inner.split(";")]
        for part in parts:
            # Match "Author, Year" pattern
            m2 = re.match(r"(.+),\s(\d{4})$", part)
            if m2:
                citations.add(f"{m2.group(1).strip()} ({m2.group(2)})")

    return citations


def extract_reference_entries(text):
    """Extract all reference entries from the reference list."""
    ref_match = re.search(r"\\chapter\*\{References?\}", text)
    if not ref_match:
        return set()

    refs_text = text[ref_match.start():]

    # Match each reference entry: Author(s) (Year). Title...
    entries = set()
    for m in re.finditer(
        r"(?:\\noindent\\hangindent=[^\n]*\n)?([A-Z][^\(]+)\s\((\d{4})\)",
        refs_text,
    ):
        author = m.group(1).strip().rstrip(",")
        year = m.group(2)
        # Normalize: take first author surname + et al.
        first_author = author.split(",")[0].strip()
        entries.add(f"{first_author} ({year})")
        entries.add(f"{author} ({year})")

    return entries


def main():
    parser = argparse.ArgumentParser(description="Check citation ↔ reference consistency")
    parser.add_argument("input", help="Path to .tex file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show matched citations")
    args = parser.parse_args()

    with open(args.input) as f:
        text = f.read()

    body_cites = extract_body_citations(text)
    ref_entries = extract_reference_entries(text)

    # Exact match is hard with manual format — do fuzzy matching by first author + year
    body_simple = set()
    for c in body_cites:
        # Extract first author surname and year
        m = re.match(r"([A-Z][a-z]+).*\((\d{4})\)", c)
        if m:
            body_simple.add(f"{m.group(1)} ({m.group(2)})")

    ref_simple = set()
    for r in ref_entries:
        m = re.match(r"([A-Z][a-z]+).*\((\d{4})\)", r)
        if m:
            ref_simple.add(f"{m.group(1)} ({m.group(2)})")

    uncited = ref_simple - body_simple  # In references but not in body
    missing = body_simple - ref_simple  # In body but not in references

    print(f"Body citations found: {len(body_simple)}")
    print(f"Reference entries found: {len(ref_simple)}")
    print(f"Matched: {len(body_simple & ref_simple)}")
    print()

    if missing:
        print(f"⚠️  IN BODY but MISSING from references ({len(missing)}):")
        for m in sorted(missing):
            print(f"  - {m}")
    else:
        print("✅ All body citations found in reference list")

    print()

    if uncited:
        print(f"⚠️  IN REFERENCES but UNCITED in body ({len(uncited)}):")
        for u in sorted(uncited):
            print(f"  - {u}")
    else:
        print("✅ All reference entries cited in body")

    if missing or uncited:
        sys.exit(1)


if __name__ == "__main__":
    main()
