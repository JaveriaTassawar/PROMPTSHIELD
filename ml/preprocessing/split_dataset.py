"""Split clean.parquet into train / val / test.

Task 20. Two rules make this split different from a standard one, and both
exist to keep the headline accuracy honest:

  1. The test set contains ONLY real-world rows (is_synthetic == False).
     Synthetic sources -- the old template CSV and WildJailbreak -- make up
     48% of the data. Testing on them measures memorisation of generated
     patterns, not detection of real attacks. The number reported in Task 31
     has to mean something when an examiner types their own jailbreak.

  2. No `text` value appears in more than one split. Deduplication in
     prepare_dataset.py already guarantees this, but it is verified here
     rather than assumed: if dedup ever changes, a leak between train and
     test would inflate the score invisibly.

Order matters. The test set is carved from the real-world pool FIRST, then
train/val are taken from everything left over. Splitting the whole frame and
filtering afterwards would let stratification hand real-world rows to train
and leave the test set short.

Outputs, all in data/processed/:
    train.parquet           model fits on this
    val.parquet             tuning decisions (Task 29)
    test.parquet            the honest metric (Task 31) -- real-world only
    synthetic_test.parquet  comparison metric only, never the headline

Run:  python preprocessing/split_dataset.py
"""

from __future__ import annotations

from pathlib import Path

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
CLEAN_PATH = PROCESSED / "clean.parquet"

TEST_FRACTION = 0.15   # of the real-world pool
VAL_FRACTION = 0.10    # of what remains after the test set is removed
SEED = 42              # fixed so the split is reproducible across machines

LABEL = "label_3class"


def split(frame, seed: int = SEED):
    """Return (train, val, test, synthetic_test).

    `frame` is the full clean.parquet. Stratified on the 3-class label so
    every split keeps the same class balance.
    """
    from sklearn.model_selection import train_test_split

    real = frame[~frame["is_synthetic"]]
    synthetic = frame[frame["is_synthetic"]]

    # --- rule 1: the test set comes only from real-world rows -------------
    real_rest, test = train_test_split(
        real,
        test_size=TEST_FRACTION,
        stratify=real[LABEL],
        random_state=seed,
    )

    # Everything not in the test set is available for fitting.
    trainable = __import__("pandas").concat([real_rest, synthetic])

    train, val = train_test_split(
        trainable,
        test_size=VAL_FRACTION,
        stratify=trainable[LABEL],
        random_state=seed,
    )

    # --- a synthetic-only test set, for the comparison in Task 31 ---------
    # Sampled from synthetic rows that are already in train, so it is
    # deliberately NOT a held-out set. Its only job is to show how much
    # higher a synthetic score looks -- which is the point being made.
    synth_in_train = train[train["is_synthetic"]]
    synthetic_test = synth_in_train.sample(
        n=min(len(test), len(synth_in_train)), random_state=seed
    )

    return train, val, test, synthetic_test


def check_no_overlap(train, val, test) -> list[str]:
    """Verify rule 2. Returns a list of problems, empty if clean."""
    problems: list[str] = []
    sets = {
        "train": set(train["text"]),
        "val": set(val["text"]),
        "test": set(test["text"]),
    }
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        shared = sets[a] & sets[b]
        if shared:
            problems.append(f"{a} and {b} share {len(shared):,} texts")
    return problems


def _describe(name: str, part) -> None:
    counts = part[LABEL].value_counts()
    share = ", ".join(
        f"{cls} {counts.get(cls, 0) / len(part) * 100:.1f}%"
        for cls in ("Safe", "Direct Jailbreak", "Indirect Injection")
    )
    print(f"  {name:<16} {len(part):>9,}   {share}")


def main() -> int:
    import pandas as pd

    if not CLEAN_PATH.is_file():
        print(f"clean.parquet not found at {CLEAN_PATH}")
        print("Run: python preprocessing/prepare_dataset.py")
        return 1

    frame = pd.read_parquet(CLEAN_PATH)
    print(f"Loaded {len(frame):,} rows\n")

    train, val, test, synthetic_test = split(frame)

    print("Splits (class balance preserved by stratification):")
    _describe("train", train)
    _describe("val", val)
    _describe("test", test)
    _describe("synthetic_test", synthetic_test)

    # --- rule 1 -----------------------------------------------------------
    print("\nRule 1 - test set is real-world only:")
    origins = set(test["is_synthetic"].unique())
    if origins == {False}:
        print(f"  OK: all {len(test):,} test rows are real-world")
    else:
        print(f"  FAIL: test set contains {origins}")
        return 1

    # --- rule 2 -----------------------------------------------------------
    print("\nRule 2 - no text shared between splits:")
    problems = check_no_overlap(train, val, test)
    if problems:
        for problem in problems:
            print(f"  FAIL: {problem}")
        return 1
    print("  OK: train/val, train/test and val/test all disjoint")

    # --- how thin is the test set per class? ------------------------------
    print("\nTest set by class (this is what Task 31 reports on):")
    for cls, count in test[LABEL].value_counts().items():
        flag = "  <- thin" if count < 500 else ""
        print(f"  {cls:<24} {count:>8,}{flag}")

    print("\nTest set by sub-type:")
    sub = test[test["subtype"].notna()]["subtype"].value_counts()
    for name, count in sub.items():
        flag = "  <- thin" if count < 30 else ""
        print(f"  {name:<24} {count:>8,}{flag}")

    # --- write ------------------------------------------------------------
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, part in (
        ("train", train),
        ("val", val),
        ("test", test),
        ("synthetic_test", synthetic_test),
    ):
        path = PROCESSED / f"{name}.parquet"
        part.to_parquet(path, index=False)
        print(f"\nwrote {path.name:<24} {len(part):>9,} rows"
              f"  ({path.stat().st_size / 1_048_576:,.1f} MB)", end="")

    print("\n\nReminder: test.parquet gives the headline metric in Task 31.")
    print("synthetic_test.parquet is for comparison only - never report it")
    print("as the project's accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
