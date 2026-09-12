"""Report what each raw dataset actually contains.

Task 15. Prints row count, columns/keys and two example records for every file
in ml/data/raw/, so each source can be checked against the inventory in
ml/TASKS.md section 2 before any mapping logic is written.

Several sources are large (llmail_phase1.json is 448 MB, train.tsv is 530 MB),
so line-oriented formats are streamed rather than loaded whole, and only the
first few records are ever held in memory.

Run:  python preprocessing/inspect_sources.py
      python preprocessing/inspect_sources.py data/raw/alpaca_data.json
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Counts verified when the inventory was built. A mismatch means the file is
# truncated or was replaced, which would quietly corrupt every later task.
EXPECTED_ROWS: dict[str, int] = {
    "dataset_for_huggingface.jsonl": 70_000,
    "llmail_phase1.json": 160_741,
    "llmail_phase2.json": 37_303,
    "train.tsv": 261_559,
    "Attack_600.json": 600,
    "alpaca_data.json": 52_002,
    "train-00000-of-00001.parquet": 13_735,
    "train-00000-of-00001 (1).parquet": 1_405,
    "SafeMTData_1K.json": 1_680,
    "Harmful%20Dataset.csv": 4_136,
    "Completely-Benign_Dataset.csv": 1_200,
    "redteam_dataset.v2.json": 819,
    "train.jsonl": 1_272,
    "test_cases_dh_enhanced.json": 510,
    "test_cases_ds_enhanced.json": 544,
    "jackhhao_jailbreak_classification.csv": 1_998,
    "rubend18_chatgpt_jailbreak_prompts.csv": 79,
    "deepset_prompt_injections.parquet": 546,
}

csv.field_size_limit(10**9)  # some prompts are very long single fields

PREVIEW_CHARS = 160


def _short(value: object) -> str:
    """One-line, length-capped preview of any value."""
    text = str(value).replace("\n", " ").replace("\r", " ")
    return text[:PREVIEW_CHARS] + ("..." if len(text) > PREVIEW_CHARS else "")


def _show_records(records: list[dict], keys: list[str]) -> None:
    print(f"  keys/columns ({len(keys)}): {', '.join(keys)}")
    for i, record in enumerate(records[:2], start=1):
        print(f"  example {i}:")
        for key in keys[:6]:  # first few fields are enough to identify a source
            print(f"    {key}: {_short(record.get(key, ''))}")


def _describe_json(path: Path) -> int:
    """Whole-file JSON: either a list of records or a dict keyed by text."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        count = len(data)
        if data and isinstance(data[0], dict):
            _show_records(data, list(data[0].keys()))
        return count

    if isinstance(data, dict):
        # orq wraps its records in {"metadata": ..., "samples": [...]}
        for key, value in data.items():
            if isinstance(value, list) and value:
                print(f"  (records live under the '{key}' key)")
                if isinstance(value[0], dict):
                    _show_records(value, list(value[0].keys()))
                return len(value)

        # llmail: the email text is the key, the label is the value
        count = len(data)
        items = list(data.items())[:2]
        print(f"  shape: dict of {count} entries (key = text, value = label)")
        for i, (key, value) in enumerate(items, start=1):
            print(f"  example {i}:")
            print(f"    key:   {_short(key)}")
            print(f"    value: {_short(value)}")
        return count

    return 0


def _describe_jsonl(path: Path) -> int:
    """Line-delimited JSON, streamed so a 100 MB+ file stays cheap."""
    count = 0
    samples: list[dict] = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            if len(samples) < 2:
                samples.append(json.loads(line))
            count += 1
    if samples:
        _show_records(samples, list(samples[0].keys()))
    return count


def _describe_delimited(path: Path, delimiter: str) -> int:
    """CSV/TSV, streamed row by row."""
    count = 0
    samples: list[dict] = []
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        for row in reader:
            if len(samples) < 2:
                samples.append(row)
            count += 1
    if samples:
        _show_records(samples, list(samples[0].keys()))
    return count


def _describe_parquet(path: Path) -> int:
    import pandas as pd

    frame = pd.read_parquet(path)
    records = frame.head(2).to_dict("records")
    if records:
        _show_records(records, list(frame.columns))
    return len(frame)


def describe(path: str | Path) -> int:
    """Print a summary of one dataset file and return its row count."""
    path = Path(path)
    size_mb = path.stat().st_size / 1_048_576
    print(f"\n{'=' * 70}\n{path.name}  ({size_mb:,.1f} MB)\n{'-' * 70}")

    suffix = path.suffix.lower()
    try:
        if suffix == ".jsonl":
            count = _describe_jsonl(path)
        elif suffix == ".json":
            count = _describe_json(path)
        elif suffix == ".csv":
            count = _describe_delimited(path, ",")
        elif suffix == ".tsv":
            count = _describe_delimited(path, "\t")
        elif suffix == ".parquet":
            count = _describe_parquet(path)
        elif suffix == ".txt":
            print("  (reference file, not a dataset)")
            return -1
        else:
            print(f"  unsupported format: {suffix}")
            return -1
    except Exception as exc:  # noqa: BLE001 - report and move to the next file
        print(f"  ERROR reading file: {exc}")
        return -1

    print(f"  rows: {count:,}")

    expected = EXPECTED_ROWS.get(path.name)
    if expected is not None:
        if count == expected:
            print(f"  check: matches expected {expected:,}")
        else:
            print(f"  MISMATCH: expected {expected:,}, found {count:,}")
            print("  -> file is truncated or changed; re-download before continuing")
    return count


def main() -> int:
    if len(sys.argv) > 1:
        describe(sys.argv[1])
        return 0

    files = sorted(p for p in RAW_DIR.iterdir() if p.is_file())
    if not files:
        print(f"No files in {RAW_DIR}. Run download_datasets.py first.")
        return 1

    mismatches: list[str] = []
    for path in files:
        count = describe(path)
        expected = EXPECTED_ROWS.get(path.name)
        if expected is not None and count != expected:
            mismatches.append(path.name)

    print(f"\n{'=' * 70}")
    print(f"inspected {len(files)} files")
    if mismatches:
        print(f"MISMATCHED ({len(mismatches)}): {', '.join(mismatches)}")
        return 1
    print("all row counts match the inventory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
