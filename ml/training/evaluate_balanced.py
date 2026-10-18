"""Re-score the model on a composition-capped test set.

WHY THIS EXISTS

The Task 31 headline is 99.11% accuracy on `test.parquet`. That figure is
real -- the rows are genuinely held out -- but its *composition* flatters it:

    Web Content Injection   21,922 of 42,690 rows   51.4%   scored 100.00%
    llmail_phase1 alone     18,807 rows             44.1%

So over half the headline is one sub-type, drawn almost entirely from one
source (Microsoft llmail), on which the model is perfect. A reader seeing
"99.11%" reasonably assumes broad competence; what it mostly measures is
"can it recognise llmail emails?"

This script answers a narrower, more defensible question: **how does the
model score when no single sub-type or source is allowed to dominate?**

WHAT IT DOES NOT DO

It does not replace Task 31. The honest headline remains 99.11% on the full
held-out set, and that is what the SRS target was checked against. This is a
*secondary* figure for the limitations section -- the number to quote when an
examiner asks whether the test set was balanced.

It also cannot fix the deeper limitation: every source in the test set also
appears in training, so this still measures generalisation to unseen *rows*,
not unseen *data*. Task 36's hand-written prompts (0 of 3) remain the real
evidence on that, and no amount of re-weighting an existing test set
substitutes for it.

TWO CAPS, NOT ONE

Capping only the sub-type would still let llmail supply every Web Content
Injection row. Capping only the source would still let one sub-type dominate
across sources. Both caps apply, sub-type first, then source within it.

Role Override has 18 rows and stays at 18 -- capping cannot create data.
Its score remains statistically meaningless and is reported with that note
rather than silently averaged in.

Run:  PROMPTSHIELD_MODEL_PATH=models/run01_ck28371 \
      python training/evaluate_balanced.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

PROCESSED = ML_ROOT / "data" / "processed"
DEFAULT_TEST = PROCESSED / "test.parquet"
DEFAULT_OUT = ML_ROOT / "results" / "metrics_balanced.json"

# Per-sub-type ceiling. 1,000 is large enough that the common sub-types keep
# a usable sample, small enough that Web Content Injection drops from 51.4%
# of the set to roughly a seventh of it.
SUBTYPE_CAP = 1_000

# Per-source ceiling *within* a sub-type, so one dataset cannot supply a
# whole category on its own.
SOURCE_CAP = 400

# Safe has no sub-type, so it is capped separately. Kept near the attack
# total so the set does not become overwhelmingly benign or overwhelmingly
# adversarial -- neither reflects a real prompt stream.
SAFE_CAP = 1_500

SEED = 42

# A sub-type below this is reported but flagged as statistically unreliable
# rather than presented as a score.
MIN_RELIABLE = 50


def build_balanced(frame, subtype_cap=SUBTYPE_CAP, source_cap=SOURCE_CAP,
                   safe_cap=SAFE_CAP, seed=SEED):
    """Cap rows per sub-type, and per source within each sub-type.

    Returns (balanced_frame, report_rows).
    """
    import pandas as pd

    report = []
    parts = []

    safe = frame[frame["label_3class"] == "Safe"]
    take = min(safe_cap, len(safe))
    parts.append(safe.sample(n=take, random_state=seed))
    report.append(("Safe", len(safe), take, "-"))

    attacks = frame[frame["label_3class"] != "Safe"]
    for subtype in sorted(attacks[attacks["subtype"].notna()]["subtype"].unique()):
        group = attacks[attacks["subtype"] == subtype]

        # Cap per source first, so no single dataset fills the quota.
        capped_sources = []
        for source in sorted(group["source"].unique()):
            rows = group[group["source"] == source]
            n = min(source_cap, len(rows))
            capped_sources.append(rows.sample(n=n, random_state=seed))
        pooled = pd.concat(capped_sources)

        # Then cap the sub-type as a whole.
        n = min(subtype_cap, len(pooled))
        picked = pooled.sample(n=n, random_state=seed)
        parts.append(picked)
        report.append((subtype, len(group), n, len(group["source"].unique())))

    return pd.concat(parts).reset_index(drop=True), report


def score(frame, model_path, batch_size=32):
    """Predict and compute metrics. Reuses the Task 30 pipeline."""
    from training.evaluate import compute_metrics
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from training.dataset import LABEL2ID

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    texts = frame["text"].astype(str).tolist()
    y_true = [LABEL2ID[v] for v in frame["label_3class"]]
    y_pred = []

    for start in range(0, len(texts), batch_size):
        encoded = tokenizer(
            texts[start:start + batch_size],
            truncation=True, padding=True, max_length=512,
            return_tensors="pt",
        )
        encoded = {k: v.to(device) for k, v in encoded.items()
                   if k != "token_type_ids"}
        with torch.no_grad():
            logits = model(**encoded).logits
        y_pred.extend(torch.argmax(logits, dim=-1).cpu().numpy().tolist())
        done = min(start + batch_size, len(texts))
        print(f"\r  scored {done:,}/{len(texts):,}", end="", flush=True)

    print()
    return compute_metrics(frame, y_true, y_pred)


def main(argv=None) -> int:
    import os
    import pandas as pd

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model-path", default=os.getenv("PROMPTSHIELD_MODEL_PATH"))
    parser.add_argument("--data-path", default=str(DEFAULT_TEST))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--subtype-cap", type=int, default=SUBTYPE_CAP)
    parser.add_argument("--source-cap", type=int, default=SOURCE_CAP)
    args = parser.parse_args(argv)

    if not args.model_path:
        print("No model path. Pass --model-path or set PROMPTSHIELD_MODEL_PATH.")
        return 1

    frame = pd.read_parquet(args.data_path)
    print(f"full test set: {len(frame):,} rows\n")

    balanced, report = build_balanced(
        frame, subtype_cap=args.subtype_cap, source_cap=args.source_cap
    )

    print(f"{'group':<26}{'available':>11}{'taken':>8}{'sources':>9}{'share':>8}")
    for name, available, taken, sources in report:
        share = taken / len(balanced) * 100
        print(f"{name:<26}{available:>11,}{taken:>8,}{str(sources):>9}{share:>7.1f}%")
    print(f"\nbalanced set: {len(balanced):,} rows")

    before = (frame["subtype"] == "Web Content Injection").mean() * 100
    after = (balanced["subtype"] == "Web Content Injection").mean() * 100
    print(f"Web Content Injection share: {before:.1f}% -> {after:.1f}%\n")

    metrics = score(balanced, args.model_path, args.batch_size)

    o = metrics["overall"]
    macro = metrics["per_class"]["macro avg"]["f1-score"]
    print("\nBALANCED RESULTS")
    print(f"  accuracy     {o['accuracy']:.4f}")
    print(f"  weighted F1  {o['f1_weighted']:.4f}")
    print(f"  macro F1     {macro:.4f}")

    print("\nper sub-type:")
    for name, v in sorted(metrics.get("per_subtype", {}).items(),
                          key=lambda kv: -kv[1]["accuracy"]):
        flag = "  <- too few rows to interpret" if v["count"] < MIN_RELIABLE else ""
        print(f"  {name:<26}{v['accuracy']:>8.4f}  ({v['correct']}/{v['count']}){flag}")

    payload = {
        "note": (
            "Secondary figure. Caps rows per sub-type and per source so no "
            "single category or dataset dominates. Does NOT replace the "
            "Task 31 headline of 99.11% on the full held-out set, which is "
            "what the SRS target was checked against. Still measures unseen "
            "rows from seen sources -- see MODEL_CARD 19.8 for the novel-prompt "
            "result."
        ),
        "caps": {
            "subtype": args.subtype_cap,
            "source_within_subtype": args.source_cap,
            "safe": SAFE_CAP,
            "seed": SEED,
        },
        "rows": len(balanced),
        "web_content_injection_share": {
            "full_test_pct": round(before, 2),
            "balanced_pct": round(after, 2),
        },
        **metrics,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
