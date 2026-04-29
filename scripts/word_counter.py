#!/usr/bin/env python3
"""Count words per chapter in a LaTeX thesis.

Usage:
    python word_counter.py thesis.tex
    python word_counter.py thesis.tex --json
"""

import re
import sys
import json
import argparse


def strip_latex(text):
    """Remove LaTeX commands and environments for word counting."""
    text = re.sub(r"\\[a-zA-Z]+\*?\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"\\(?:begin|end)\{[^}]*\}", "", text)
    text = re.sub(r"[{}$\\%&~^_]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_chapters(content):
    """Find chapter boundaries and count words."""
    ch_pattern = r"\\chapter\*?\{([^}]*)\}"
    chapters = []
    for m in re.finditer(ch_pattern, content):
        chapters.append((m.group(1), m.start()))
    chapters.append(("END", len(content)))

    results = []
    total = 0
    for i in range(len(chapters) - 1):
        name = chapters[i][0]
        start = chapters[i][1]
        end = chapters[i + 1][1]
        ch_text = content[start:end]
        clean = strip_latex(ch_text)
        words = len(clean.split()) if clean else 0
        total += words
        results.append({"chapter": name, "words": words})

    # Count front matter
    front = content[: chapters[0][1]] if chapters else ""
    front_words = len(strip_latex(front).split()) if strip_latex(front) else 0

    return results, front_words, total


def main():
    parser = argparse.ArgumentParser(description="Count words per chapter in LaTeX thesis")
    parser.add_argument("input", help="Path to .tex file")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    with open(args.input) as f:
        content = f.read()

    chapters, front_words, total = count_chapters(content)

    if args.json:
        print(json.dumps({
            "front_matter": front_words,
            "chapters": chapters,
            "total_chapters": total,
            "grand_total": total + front_words,
        }, indent=2))
    else:
        print(f"{'Chapter':<40} {'Words':>8}")
        print("-" * 50)
        for ch in chapters:
            print(f"{ch['chapter']:<40} {ch['words']:>8,}")
        print("-" * 50)
        print(f"{'Front matter':<40} {front_words:>8,}")
        print(f"{'TOTAL (chapters)':<40} {total:>8,}")
        print(f"{'GRAND TOTAL':<40} {total + front_words:>8,}")


if __name__ == "__main__":
    main()
