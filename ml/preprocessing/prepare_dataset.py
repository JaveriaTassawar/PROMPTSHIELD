"""Combine every adapter's output into one deduplicated training file.

Task 18. Runs all 19 adapters, concatenates their records, removes duplicate
prompts, tags each row as synthetic or real-world, and writes clean.parquet.

Why deduplication matters here: the old CSV is 2,000,000 rows but only ~1,041
unique prompts, repeated ~192x each. Training on the raw rows produces a model
that memorises those sentences and reports a falsely high accuracy while
staying weak against real attacks phrased differently.

Why real-world rows win ties: Task 20 holds out a test set made only of
real-world rows. If a duplicate were kept from a synthetic source and the
identical real-world row discarded, that prompt could never reach the test
set -- quietly shrinking the honest evaluation. So when the same text appears
in both, the real-world copy is the one kept.

Run:  python preprocessing/prepare_dataset.py
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.map_labels import ALL_ADAPTERS  # noqa: E402

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "clean.parquet"

# Sources that are machine-generated rather than collected from real attacks.
# WildJailbreak is synthetic by its own dataset card; the old CSV is template
# generated. Everything else is scraped or competition-sourced real data.
SYNTHETIC_SOURCES = {"old_csv", "wildjailbreak"}

COLUMNS = ["text", "label_3class", "subtype", "source", "is_synthetic"]


# --- 18.1 -----------------------------------------------------------------
def run_all_adapters(verbose: bool = False) -> list[dict]:
    """Call every adapter and return one combined list of records."""
    combined: list[dict] = []
    for adapter in ALL_ADAPTERS:
        rows = adapter()
        if verbose:
            print(f"  {adapter.__name__:<28} {len(rows):>9,}")
        combined.extend(rows)
    return combined


# --- 18.2 -----------------------------------------------------------------
def normalise_text(text: str) -> str:
    """Key used only for comparing rows. The stored text keeps its own casing.

    Collapsing case and surrounding whitespace catches near-duplicates that
    differ only cosmetically -- the same prompt pasted with different
    capitalisation is still the same prompt for training purposes.
    """
    return text.strip().lower()


# --- 18.3 + 18.4 ----------------------------------------------------------
def is_synthetic(source: str) -> bool:
    return source in SYNTHETIC_SOURCES


def deduplicate(records: list[dict]) -> list[dict]:
    """Drop rows whose normalised text was already seen.

    Real-world rows take precedence: the list is processed real-first, so a
    synthetic duplicate can never displace its real-world twin.
    """
    real_first = sorted(records, key=lambda r: is_synthetic(r["source"]))

    seen: set[str] = set()
    kept: list[dict] = []
    for row in real_first:
        key = normalise_text(row["text"])
        if key in seen:
            continue
        seen.add(key)
        kept.append({**row, "is_synthetic": is_synthetic(row["source"])})
    return kept


# --- 18.5 -----------------------------------------------------------------
def write_parquet(records: list[dict], path: Path = OUTPUT_PATH) -> Path:
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records, columns=COLUMNS)
    frame.to_parquet(path, index=False)
    return path


def _report(before: list[dict], after: list[dict]) -> None:
    removed = len(before) - len(after)
    pct = (removed / len(before) * 100) if before else 0
    print(f"\n{'=' * 62}")
    print(f"combined  {len(before):>9,}")
    print(f"duplicates{removed:>9,}  ({pct:.1f}%)")
    print(f"kept      {len(after):>9,}")

    # The old CSV is the headline case: it should collapse almost entirely.
    old_before = sum(1 for r in before if r["source"] == "old_csv")
    old_after = sum(1 for r in after if r["source"] == "old_csv")
    print(f"\nold_csv: {old_before:,} -> {old_after:,}")

    print("\nBy class:")
    for name, count in Counter(r["label_3class"] for r in after).most_common():
        print(f"  {name:<26} {count:>9,}")

    print("\nBy sub-type:")
    subtypes = Counter(r["subtype"] for r in after if r["subtype"])
    for name, count in subtypes.most_common():
        flag = "  <- thin" if count < 200 else ""
        print(f"  {name:<26} {count:>9,}{flag}")

    print("\nBy origin:")
    synth = Counter(r["is_synthetic"] for r in after)
    print(f"  real-world                {synth[False]:>9,}")
    print(f"  synthetic                 {synth[True]:>9,}")
    print("=" * 62)


def main() -> int:
    print("Running all adapters...")
    combined = run_all_adapters(verbose=True)

    print("\nDeduplicating...")
    kept = deduplicate(combined)

    _report(combined, kept)

    path = write_parquet(kept)
    size_mb = path.stat().st_size / 1_048_576
    print(f"\nwrote {path}  ({size_mb:,.1f} MB)")

    if not kept:
        print("ERROR: no rows survived deduplication")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
