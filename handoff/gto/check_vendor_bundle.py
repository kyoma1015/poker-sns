#!/usr/bin/env python3
"""Preflight only: inspect vendored dependencies before attempting G12 build.

Usage: python handoff/gto/check_vendor_bundle.py /path/to/extracted/bundle
No source changes, no dependency installation, no builds.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import sys

REQUIRED = [
    "patched/pybind11/include/pybind11/pybind11.h",
    "patched/pybind11/include/pybind11/stl.h",
    "patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.h",
    "patched/open_spiel/abseil-cpp/absl/random/uniform_real_distribution.h",
    "patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.cc",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print("BLOCKED: bundle directory unavailable", file=sys.stderr)
        return 2
    missing = [p for p in REQUIRED if not (root / p).is_file()]
    for p in REQUIRED:
        print(("PASS" if p not in missing else "MISSING"), p)
    if missing:
        print(f"BLOCKED: {len(missing)} direct dependencies missing")
        return 2
    print("PASS: direct dependency paths exist (transitive closure/build NOT verified)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
