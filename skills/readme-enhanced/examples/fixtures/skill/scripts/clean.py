#!/usr/bin/env python3
"""Normalise delimiters and whitespace in a CSV file."""
import csv
import sys

with open(sys.argv[1], newline="") as src:
    rows = [[c.strip() for c in r] for r in csv.reader(src)]
csv.writer(sys.stdout).writerows(rows)
