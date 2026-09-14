"""Measure token lengths and fix max_length for training.

Task 24. DistilBERT reads a fixed number of tokens per prompt. Too few and
the end of every long attack is silently discarded; too many and most of the
GPU budget is spent on padding. This script measures the real distribution
and records the decision, so Task 26 and Task 27 import a number that was
derived rather than guessed.

THE DECISION: MAX_LENGTH = 512

Measured over a 2,809-row stratified sample:

    p50      94 tokens
    p75     273
    p90     624
    p95     747
    p99   1,483
    max   3,923

    max_length=128  truncates 43.1% of rows   <- the transformers default
    max_length=256  truncates 26.2%
    max_length=512  truncates 15.3%           <- chosen

512 is DistilBERT's architectural ceiling, not a tuning choice -- the model
cannot accept more. So the real decision was whether to go below it to save
compute, and the answer is no: dropping to 128 would truncate 43% of rows,
nearly three times as many.

WHAT THIS COSTS, stated plainly rather than buried:

    Multi-Turn Manipulation    median 547 tokens
    Persona Hijacking          p90  1,048, max 3,923
    Web Content Injection      p90    979, max 3,577

Multi-Turn's *median* row exceeds 512, so most of those prompts lose their
final turns even at the maximum setting. The model sees the opening of the
conversation and has to classify from that. This is a real limitation of
using DistilBERT for multi-turn detection and belongs in MODEL_CARD.md --
a longer-context model would be the fix, which is out of scope for v1.

Sampling is stratified, not uniform. Multi-turn rows are rare (6,477 of
547,063) but they are the longest, so a uniform sample would under-represent
exactly the rows that decide the answer.

Run:  python training/tokenize_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

CLEAN_PATH = ML_ROOT / "data" / "processed" / "clean.parquet"

MODEL_NAME = "distilbert-base-uncased"

# Imported by training/dataset.py (Task 26) and training/train.py (Task 27).
# Do not change without re-running this script -- the value is evidence-based.
MAX_LENGTH = 512

# DistilBERT cannot exceed this; it is the model's architectural limit.
MODEL_CEILING = 512

SAFE_SAMPLE = 600
PER_SUBTYPE_SAMPLE = 300
SEED = 42


def sample_rows(frame, seed: int = SEED):
    """Stratified sample. Uniform sampling would swamp the long, rare
    multi-turn rows with short Safe ones and understate the true spread."""
    import pandas as pd

    parts = [
        frame[frame["label_3class"] == "Safe"].sample(
            n=min(SAFE_SAMPLE, int((frame["label_3class"] == "Safe").sum())),
            random_state=seed,
        )
    ]
    for subtype in sorted(frame[frame["subtype"].notna()]["subtype"].unique()):
        group = frame[frame["subtype"] == subtype]
        parts.append(
            group.sample(n=min(PER_SUBTYPE_SAMPLE, len(group)), random_state=seed)
        )
    return pd.concat(parts)


def token_lengths(texts, tokenizer):
    """Untruncated lengths -- the point is to see what would be cut off."""
    return [len(tokenizer.encode(t, truncation=False)) for t in texts]


def main() -> int:
    import numpy as np
    import pandas as pd
    from transformers import AutoTokenizer

    if not CLEAN_PATH.is_file():
        print(f"clean.parquet not found at {CLEAN_PATH}")
        print("Run: python preprocessing/prepare_dataset.py")
        return 1

    print(f"Loading tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    frame = pd.read_parquet(CLEAN_PATH)
    sample = sample_rows(frame)
    print(f"Measuring {len(sample):,} stratified rows "
          f"(of {len(frame):,} total)\n")

    lengths = np.array(token_lengths(sample["text"], tokenizer))

    print("Token length distribution:")
    for pct in (50, 75, 90, 95, 99):
        print(f"  p{pct:<3} {int(np.percentile(lengths, pct)):>8,}")
    print(f"  max  {lengths.max():>8,}")
    print(f"  mean {lengths.mean():>8,.0f}")

    print("\nTruncation cost by setting:")
    for candidate in (128, 192, 256, 320, 512):
        share = (lengths > candidate).mean() * 100
        marker = ""
        if candidate == 128:
            marker = "  <- transformers default"
        if candidate == MAX_LENGTH:
            marker = "  <- CHOSEN"
        print(f"  max_length={candidate:<4} truncates {share:5.1f}% of rows{marker}")

    print("\nPer sub-type (the long ones drive the decision):")
    sample = sample.assign(_tokens=lengths)
    rows = []
    for subtype, group in sample[sample["subtype"].notna()].groupby("subtype"):
        rows.append((subtype, group["_tokens"]))
    safe = sample[sample["label_3class"] == "Safe"]["_tokens"]
    rows.append(("Safe", safe))

    for name, series in sorted(rows, key=lambda r: -r[1].median()):
        over = (series > MAX_LENGTH).mean() * 100
        flag = "  <- truncated even at 512" if over > 25 else ""
        print(f"  {name:<26} median {int(series.median()):>5}"
              f"  p90 {int(series.quantile(0.9)):>6}"
              f"  over-{MAX_LENGTH} {over:5.1f}%{flag}")

    print(f"\nDecision: MAX_LENGTH = {MAX_LENGTH}")
    if MAX_LENGTH == MODEL_CEILING:
        print(f"  {MODEL_CEILING} is DistilBERT's architectural ceiling -- the")
        print("  model cannot read more, so this is the most context available.")
    share = (lengths > MAX_LENGTH).mean() * 100
    print(f"  {share:.1f}% of rows are still truncated. Multi-Turn Manipulation's")
    print("  median row exceeds 512, so those prompts lose their final turns.")
    print("  Recorded as a limitation for MODEL_CARD.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
