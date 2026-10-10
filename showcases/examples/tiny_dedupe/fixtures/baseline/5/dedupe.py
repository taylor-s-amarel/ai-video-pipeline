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


def cluster(rows):
    parent = {r["id"]: r["id"] for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first = {}
    for r in rows:
        for k in keys_for(r):
            if k in first:
                parent[find(r["id"])] = find(first[k])
            else:
                first[k] = r["id"]
    roots = {}
    return {r["id"]: "c%03d" % roots.setdefault(find(r["id"]), len(roots) + 1) for r in rows}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, newline="") as fh:
        rows = list(csv.DictReader(fh))
    labels = cluster(rows)
    with open(dst, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "cluster"])
        for r in rows:
            w.writerow([r["id"], labels[r["id"]]])
