"""Build the small labelled sample that gets committed to git.

Task 22. Everything else in data/ stays out of the repository, so this 1,000
row file is the only training data teammates and the examiner ever open. Two
things follow from that:

  1. It must cover all 3 classes and all 8 sub-types, so the taxonomy is
     visible from the sample alone.

  2. It must contain nothing embarrassing. The TrustAIRLab and WildJailbreak
     sources are real scraped jailbreak attempts and include graphic sexual
     content. An explicit row surfacing during a viva demo is a real risk, so
     the filter here is deliberately aggressive: it would rather drop a
     borderline-clean row than keep a borderline-dirty one.

The filter runs on the candidate pool BEFORE stratified selection, not after.
Filtering afterwards would punch holes in the quotas -- a sub-type could lose
most of its picks and end up barely represented.

This is a machine pre-filter, not a substitute for reading the file. Task 22.2
still requires a human pass over the output.

Run:  python preprocessing/make_sample.py
Out:  data/sample_1000.csv
"""

from __future__ import annotations

import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
CLEAN_PATH = DATA / "processed" / "clean.parquet"
OUTPUT_PATH = DATA / "sample_1000.csv"

TARGET_ROWS = 1_000
SEED = 42

# Cap any single row so the CSV stays readable in a spreadsheet. Some prompts
# run to thousands of characters.
MAX_CHARS = 600

# Explicit-content filter. Deliberately blunt: these terms are rare in
# legitimate security prompts, so the false-positive cost is low and the
# false-negative cost (explicit text in a viva) is high.
BLOCKLIST = re.compile(
    r"\b("
    r"cum|cock|dick|pussy|penis|vagina|anal|blowjob|handjob|"
    r"porn|pornographic|nsfw|erotic|erotica|hentai|"
    r"fuck|fucking|fucked|motherfuck|"
    r"rape|raping|rapist|incest|pedophil|paedophil|molest|"
    r"horny|orgasm|masturbat|ejaculat|semen|genital|"
    r"boob|tits|titties|nipple|breast size|"
    r"slut|whore|bitch|bastard|"
    r"sex|sexual|sexy|nude|naked|nudity|xxx|"
    r"bestiality|necrophil|"
    r"kill yourself|suicide method|how to die"
    r")\b",
    re.I,
)

# Rows shorter than this are usually fragments and read poorly as examples.
MIN_CHARS = 20


def is_clean(text: str) -> bool:
    """True if the row is safe to show in a demo or report."""
    if not isinstance(text, str):
        return False
    stripped = text.strip()
    if len(stripped) < MIN_CHARS:
        return False
    return BLOCKLIST.search(stripped) is None


def truncate(text: str) -> str:
    """Keep the CSV readable. Truncation is marked so nobody mistakes a cut
    row for the complete prompt."""
    text = " ".join(str(text).split())  # collapse newlines and runs of spaces
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + " ...[truncated]"


def build_sample(frame, target: int = TARGET_ROWS, seed: int = SEED):
    """Stratified pick across the 8 sub-types plus Safe.

    Quotas are proportional but floored, so a thin sub-type is still visible.
    Role Override has only 109 rows in the whole dataset, so without a floor
    it would contribute one or two rows and effectively vanish.
    """
    import pandas as pd

    groups: dict[str, "pd.DataFrame"] = {"Safe": frame[frame["label_3class"] == "Safe"]}
    for subtype in sorted(frame[frame["subtype"].notna()]["subtype"].unique()):
        groups[subtype] = frame[frame["subtype"] == subtype]

    # Roughly a third Safe, the rest spread evenly across the 8 sub-types so
    # every one is legible in the file.
    safe_quota = target // 3
    per_subtype = (target - safe_quota) // (len(groups) - 1)

    picked = []
    report: list[tuple[str, int, int, int]] = []
    for name, group in groups.items():
        quota = safe_quota if name == "Safe" else per_subtype
        available = len(group)
        clean = group[group["text"].map(is_clean)]
        take = min(quota, len(clean))
        if take:
            picked.append(clean.sample(n=take, random_state=seed))
        report.append((name, available, len(clean), take))

    sample = pd.concat(picked).sample(frac=1, random_state=seed)  # shuffle
    return sample, report


def main() -> int:
    import pandas as pd

    if not CLEAN_PATH.is_file():
        print(f"clean.parquet not found at {CLEAN_PATH}")
        print("Run: python preprocessing/prepare_dataset.py")
        return 1

    frame = pd.read_parquet(CLEAN_PATH)
    print(f"Loaded {len(frame):,} rows\n")

    sample, report = build_sample(frame)

    print("Stratified selection (explicit rows removed before sampling):")
    print(f"  {'group':<26}{'in dataset':>12}{'clean':>10}{'taken':>8}{'dropped':>9}")
    total_dropped = 0
    for name, available, clean, take in report:
        dropped = available - clean
        total_dropped += dropped
        pct = f"{dropped / available * 100:.1f}%" if available else "-"
        print(f"  {name:<26}{available:>12,}{clean:>10,}{take:>8,}   {pct:>6}")

    print(f"\n  {total_dropped:,} rows across the dataset failed the content filter")

    # Verify coverage -- a missing sub-type means the sample misrepresents
    # the taxonomy.
    expected_subtypes = set(frame[frame["subtype"].notna()]["subtype"].unique())
    got_subtypes = set(sample[sample["subtype"].notna()]["subtype"].unique())
    missing = expected_subtypes - got_subtypes

    print(f"\nSample: {len(sample):,} rows")
    print("\n  By class:")
    for name, count in sample["label_3class"].value_counts().items():
        print(f"    {name:<24}{count:>6,}")
    print("\n  By sub-type:")
    for name, count in sample["subtype"].value_counts().items():
        print(f"    {name:<24}{count:>6,}")

    if missing:
        print(f"\n  FAIL: sub-types missing from the sample: {sorted(missing)}")
        return 1
    print(f"\n  OK: all {len(expected_subtypes)} sub-types present")

    out = sample.copy()
    out["text"] = out["text"].map(truncate)
    out = out[["text", "label_3class", "subtype", "source", "is_synthetic"]]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\nwrote {OUTPUT_PATH}  ({size_kb:,.0f} KB)")

    print("\nThis is a machine pre-filter, not a substitute for reading the")
    print("file. Task 22.2 needs a human pass before it is committed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
