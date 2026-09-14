"""Audit clean.parquet and report what actually ended up in it.

Task 19. prepare_dataset.py builds the file; this script independently reads
it back and answers the questions that decide whether training can proceed:

  - did the old CSV's 2,000,000 rows really collapse to ~1,041 unique?
  - are all 3 classes present and non-empty?
  - are all 8 sub-types present?
  - which sub-types are too thin to train reliably?
  - how much real-world data is available per class for the held-out test set?

Kept separate from prepare_dataset.py on purpose: a builder that grades its
own output can hide a bug behind the same wrong assumption twice. This reads
the artifact fresh.

Run:  python preprocessing/verify_dataset.py
Exit: 0 if every check passes, 1 if anything needs attention.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
CLEAN_PATH = PROCESSED / "clean.parquet"

EXPECTED_CLASSES = {"Safe", "Direct Jailbreak", "Indirect Injection"}
EXPECTED_SUBTYPES = {
    "Policy Evasion",
    "Multi-Turn Manipulation",
    "Role Override",
    "Persona Hijacking",
    "System Prompt Overwrite",
    "Document Embedding",
    "Web Content Injection",
    "Tool Output Injection",
}

# The old CSV is the headline dedup case. Anything far above this means the
# deduplication silently stopped working.
OLD_CSV_RAW_ROWS = 2_000_000
OLD_CSV_MAX_UNIQUE = 1_200

# Below this a sub-type cannot support a meaningful train/val/test split.
THIN_THRESHOLD = 200


def _rule(title: str) -> None:
    print(f"\n{'=' * 66}\n{title}\n{'-' * 66}")


def main() -> int:
    import pandas as pd

    if not CLEAN_PATH.is_file():
        print(f"clean.parquet not found at {CLEAN_PATH}")
        print("Run: python preprocessing/prepare_dataset.py")
        return 1

    frame = pd.read_parquet(CLEAN_PATH)
    size_mb = CLEAN_PATH.stat().st_size / 1_048_576
    problems: list[str] = []

    # --- 19.1 the artifact exists and is readable -------------------------
    _rule("19.1  File")
    print(f"  path   {CLEAN_PATH}")
    print(f"  size   {size_mb:,.1f} MB")
    print(f"  shape  {frame.shape[0]:,} rows x {frame.shape[1]} columns")
    print(f"  cols   {', '.join(frame.columns)}")

    # --- 19.2 the old CSV collapse ---------------------------------------
    _rule("19.2  Old CSV deduplication")
    old = int((frame["source"] == "old_csv").sum())
    ratio = OLD_CSV_RAW_ROWS / old if old else 0
    print(f"  raw rows in source file   {OLD_CSV_RAW_ROWS:>9,}")
    print(f"  unique rows kept          {old:>9,}")
    print(f"  duplication factor        {ratio:>9,.0f}x")
    if old > OLD_CSV_MAX_UNIQUE:
        problems.append(
            f"old_csv kept {old:,} rows, expected under {OLD_CSV_MAX_UNIQUE:,} "
            "- deduplication may not be running"
        )
        print("  FAIL: far more rows than expected")
    else:
        print("  OK: collapsed as expected")

    # --- 19.3 classes -----------------------------------------------------
    _rule("19.3  Rows per class")
    classes = frame["label_3class"].value_counts()
    for name, count in classes.items():
        print(f"  {name:<24} {count:>9,}")
    missing_classes = EXPECTED_CLASSES - set(classes.index)
    if missing_classes:
        problems.append(f"missing classes: {', '.join(sorted(missing_classes))}")
        print(f"  FAIL: missing {', '.join(sorted(missing_classes))}")
    else:
        print("  OK: all 3 classes present")

    # --- 19.4 sub-types ---------------------------------------------------
    _rule("19.4  Rows per sub-type")
    subtypes = frame[frame["subtype"].notna()]["subtype"].value_counts()
    for name, count in subtypes.items():
        print(f"  {name:<24} {count:>9,}")
    missing_subtypes = EXPECTED_SUBTYPES - set(subtypes.index)
    if missing_subtypes:
        problems.append(f"missing sub-types: {', '.join(sorted(missing_subtypes))}")
        print(f"  FAIL: missing {', '.join(sorted(missing_subtypes))}")
    else:
        print("  OK: all 8 sub-types present")

    # --- 19.5 thin sub-types, and how much is real ------------------------
    _rule(f"19.5  Sub-types under {THIN_THRESHOLD} rows (for MODEL_CARD.md)")
    real = frame[~frame["is_synthetic"]]
    real_subtypes = real[real["subtype"].notna()]["subtype"].value_counts()

    thin = [(n, c) for n, c in subtypes.items() if c < THIN_THRESHOLD]
    if thin:
        for name, count in thin:
            print(f"  {name:<24} {count:>9,} total, {real_subtypes.get(name, 0):>6,} real-world")
    else:
        print("  none")

    print(f"\n  Real-world rows available per class (Task 20 draws its test set here):")
    for name, count in real["label_3class"].value_counts().items():
        total = int(classes.get(name, 0))
        share = count / total * 100 if total else 0
        flag = "  <- thin pool" if share < 20 else ""
        print(f"    {name:<22} {count:>9,} of {total:>9,}  ({share:4.1f}%){flag}")

    # --- verdict ----------------------------------------------------------
    _rule("Verdict")
    if problems:
        for problem in problems:
            print(f"  PROBLEM: {problem}")
        return 1

    print("  All structural checks passed.")
    if thin:
        names = ", ".join(f"{n} ({c:,})" for n, c in thin)
        print(f"  Note for MODEL_CARD.md - thin sub-types: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
