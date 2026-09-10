#!/usr/bin/env python3
"""
🐾 Purr Changelog Compactor & Formatter
Project Tuki / Purr Ecosystem

Validates Two-Tier release notes (Tier 1: Human-First Outcomes, Tier 2: Engineering Under the Hood)
and extracts clean markdown for GitHub Releases.
"""

import sys
import os
import re
import argparse
from typing import Optional, Dict, Tuple, List


def parse_changelog(changelog_path: str) -> List[Dict[str, str]]:
    """
    Parses CHANGELOG.md into structured version entries.
    """
    if not os.path.exists(changelog_path):
        raise FileNotFoundError(f"Changelog file not found at: {changelog_path}")

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match lines like:
    # ## [1.1.0] - 2026-09-11 — *Prionailurus bengalensis* (Purr Recipes & Android Native Subsystem)
    # ## [1.0.0] - 2026-08-27 (Project Tuki Universal Edition)
    # ## [n.e.x.t] - YYYY-MM-DD
    # Use [ \t] instead of \s so \n is not matched across lines
    version_regex = re.compile(
        r"^##[ \t]+\[(.*?)\][ \t]*-[ \t]*([0-9A-Za-z\.-]+)(?:[ \t]*(?:—|-)[ \t]*(.*?)|[ \t]+(.*?))?$",
        re.MULTILINE
    )
    matches = list(version_regex.finditer(content))

    entries = []
    for i, match in enumerate(matches):
        ver = match.group(1).strip()
        date = match.group(2).strip()
        desc = (match.group(3) or match.group(4) or "").strip()
        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start_idx:end_idx].strip()

        entries.append({
            "version": ver,
            "date": date,
            "raw_header": match.group(0),
            "description": desc,
            "body": body
        })

    return entries


def validate_entry(entry: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verifies that a changelog entry conforms to Purr's Two-Tier standard.
    """
    issues = []
    body = entry["body"]

    has_tier1 = ("What's New For You" in body or "🌟 What's New" in body)
    has_tier2 = ("Under the Hood" in body or "🔧 Under the Hood" in body)

    if not has_tier1:
        issues.append("Missing Tier 1 section: '### 🌟 What's New For You' (Human-First Outcomes)")
    if not has_tier2:
        issues.append("Missing Tier 2 section: '### 🔧 Under the Hood' (Technical Engineering Specs)")

    return len(issues) == 0, issues


def extract_release_notes(entry: Dict[str, str]) -> str:
    """
    Returns markdown-formatted release notes suitable for a GitHub Release.
    """
    header_title = entry["raw_header"].lstrip("#").strip()
    return f"# {header_title}\n\n{entry['body']}\n"


def main():
    parser = argparse.ArgumentParser(
        prog="compact_changelog.py",
        description="🐾 Purr Changelog Compactor & Two-Tier Formatter"
    )
    parser.add_argument("--file", "-f", default=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "CHANGELOG.md"),
                        help="Path to CHANGELOG.md")
    parser.add_argument("--check", "-c", action="store_true", help="Validate Two-Tier format on the latest entry")
    parser.add_argument("--extract", "-e", nargs="?", const="latest", help="Extract release notes for version (or 'latest')")
    parser.add_argument("--output", "-o", help="Write extracted notes to output file")

    args = parser.parse_args()

    try:
        entries = parse_changelog(args.file)
    except Exception as e:
        print(f"Error parsing changelog: {e}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print("No version entries found in CHANGELOG.md", file=sys.stderr)
        sys.exit(1)

    if args.check:
        # Check target: if n.e.x.t is empty, check the first real released version
        target = entries[0]
        if target["version"].lower() == "n.e.x.t" and not target["body"] and len(entries) > 1:
            target = entries[1]

        ok, issues = validate_entry(target)
        if not ok:
            print(f"❌ Changelog validation failed for [{target['version']}]:", file=sys.stderr)
            for iss in issues:
                print(f"   • {iss}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"✔ Changelog entry [{target['version']}] satisfies Two-Tier standard.")
            sys.exit(0)

    if args.extract:
        target_ver = args.extract
        selected = None
        if target_ver == "latest":
            # Pick first non-n.e.x.t entry or the first entry
            selected = next((e for e in entries if e["version"].lower() != "n.e.x.t"), entries[0])
        else:
            selected = next((e for e in entries if e["version"] == target_ver), None)

        if not selected:
            print(f"Version '{target_ver}' not found in CHANGELOG.md", file=sys.stderr)
            sys.exit(1)

        notes = extract_release_notes(selected)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out:
                out.write(notes)
            print(f"Wrote release notes for [{selected['version']}] to {args.output}")
        else:
            print(notes)
        sys.exit(0)

    # Default action if no flags: show summary
    print(f"🐾 Found {len(entries)} release entries in {args.file}:")
    for e in entries:
        print(f"  • [{e['version']}] {e['date']} — {e['description']}")


if __name__ == "__main__":
    main()
