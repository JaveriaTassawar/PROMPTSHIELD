"""Compute and persist class weights for training.

Task 21.4. The weights have to survive as a file rather than a printout,
because Task 27 (`training/train.py`) loads them when building the Trainer.

Finding: the 3-class training split is close to balanced -- 39.7% Safe,
29.9% Direct Jailbreak, 30.4% Indirect Injection, a largest/smallest ratio
of 1.33x. That is mild enough that down-sampling Safe would throw away
~45,000 usable rows to fix a problem the model can absorb. Weighting costs
nothing and keeps every row, so weighting is the choice.

The sub-type distribution is a different story and is NOT addressed here:
Web Content Injection has 145,354 rows against Role Override's 109, a
1,300x gap. Weighting cannot manufacture signal from 109 examples. That
imbalance is a documented limitation for MODEL_CARD.md, not something to
paper over with a multiplier.

Run:  python preprocessing/class_weights.py
Out:  data/processed/class_weights.json
"""

from __future__ import annotations

import json
from pathlib import Path

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
TRAIN_PATH = PROCESSED / "train.parquet"
OUTPUT_PATH = PROCESSED / "class_weights.json"

LABEL = "label_3class"

# Above this ratio, weighting alone stops being enough and the split needs
# re-balancing. Recorded so the threshold is a stated decision, not a guess
# made silently at training time.
DOWNSAMPLE_THRESHOLD = 1.5


def compute_weights(frame) -> dict:
    """Balanced weights: n_samples / (n_classes * count). This is the same
    formula as sklearn's class_weight='balanced'."""
    counts = frame[LABEL].value_counts().to_dict()
    total = len(frame)
    k = len(counts)
    return {cls: total / (k * count) for cls, count in sorted(counts.items())}


def main() -> int:
    import pandas as pd

    if not TRAIN_PATH.is_file():
        print(f"train.parquet not found at {TRAIN_PATH}")
        print("Run: python preprocessing/split_dataset.py")
        return 1

    frame = pd.read_parquet(TRAIN_PATH)
    counts = frame[LABEL].value_counts().to_dict()
    weights = compute_weights(frame)
    ratio = max(counts.values()) / min(counts.values())

    print(f"train.parquet: {len(frame):,} rows\n")
    print(f"  {'class':<24}{'rows':>10}{'share':>9}{'weight':>10}")
    for cls in sorted(counts):
        share = counts[cls] / len(frame) * 100
        print(f"  {cls:<24}{counts[cls]:>10,}{share:>8.1f}%{weights[cls]:>10.4f}")

    print(f"\n  largest/smallest ratio = {ratio:.2f}x")
    if ratio > DOWNSAMPLE_THRESHOLD:
        print(f"  ABOVE the {DOWNSAMPLE_THRESHOLD}x threshold "
              "- consider down-sampling as well as weighting")
    else:
        print(f"  within the {DOWNSAMPLE_THRESHOLD}x threshold "
              "- weighting alone is enough, no rows discarded")

    payload = {
        "label_field": LABEL,
        "weights": weights,
        "counts": {k: int(v) for k, v in counts.items()},
        "imbalance_ratio": round(ratio, 4),
        "downsampling_applied": False,
        "note": (
            "3-class weights only. The 8 sub-types are far more imbalanced "
            "(Web Content Injection 145,354 vs Role Override 109) and are a "
            "documented limitation, not something weighting can fix."
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {OUTPUT_PATH}")
    print("Task 27 loads this when constructing the Trainer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
