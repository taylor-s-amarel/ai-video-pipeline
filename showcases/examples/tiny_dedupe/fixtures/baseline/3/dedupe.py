"""Cluster duplicate contacts.

Usage: python3 dedupe.py contacts.csv clusters.csv
"""

import csv
import re
import sys

KEYS = ['email']


def normalize_email(s):
    s = s.strip().lower()
    return s


def normalize_phone(s):
    d = re.sub(r"\D", "", s)
    return d


def keys_for(row):
    out = []
    if "email" in KEYS:
        out.append("e:" + normalize_email(row["email"]))
    if "phone" in KEYS:
        out.append("p:" + normalize_phone(row["phone"]))
    if "name" in KEYS:
        out.append("n:" + " ".join(row["name"].lower().split()))
    if "name_company" in KEYS:
        out.append("nc:" + " ".join(row["name"].lower().split()) + "|" + row["company"].strip().lower())
    return out


