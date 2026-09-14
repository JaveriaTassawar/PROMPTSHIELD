"""PyTorch Dataset over the split parquet files.

Task 26. Wraps train/val/test.parquet so the HuggingFace Trainer can read
them. The 3-class label is the target; `subtype` is carried through
untouched for the stretch sub-type head in Task 34 and for the per-sub-type
metrics in Task 30.

Two decisions here matter more than they look:

1. LABEL ORDER IS PINNED, not derived.

   If the string -> int mapping came from sorted(unique()) or pandas'
   iteration order, train and test could assign different integers to the
   same class. The model would then score near-random and nothing in the
   output would say why. LABEL2ID below is the single source of truth, and
   ID2LABEL is exported so Task 30 can report class names rather than bare
   integers.

2. TOKENIZATION IS LAZY.

   train.parquet is 453,935 rows. Tokenizing all of it in __init__ would
   stall for minutes and hold a large array in RAM before training starts,
   which matters on a free Colab instance. __getitem__ tokenizes one row at
   a time instead.

MAX_LENGTH is imported from tokenize_check rather than redefined, so the
512 decided in Task 24 cannot drift out of sync with the evidence behind it.

Run:  python training/dataset.py     (self-check over the real splits)
"""

from __future__ import annotations

import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

from training.tokenize_check import MAX_LENGTH, MODEL_NAME  # noqa: E402

PROCESSED = ML_ROOT / "data" / "processed"

# Pinned. Never derive this from the data -- see note 1 above.
LABEL2ID: dict[str, int] = {
    "Safe": 0,
    "Direct Jailbreak": 1,
    "Indirect Injection": 2,
}
ID2LABEL: dict[int, str] = {v: k for k, v in LABEL2ID.items()}
NUM_LABELS = len(LABEL2ID)


class PromptDataset:
    """One split of the dataset, tokenized on demand.

    Args:
        path: parquet file, e.g. data/processed/train.parquet
        tokenizer: a preloaded tokenizer. Passing one in lets train.py share
            a single instance across train/val/test instead of loading three.
        max_length: defaults to the value fixed in Task 24.
    """

    def __init__(self, path, tokenizer=None, max_length: int = MAX_LENGTH):
        import pandas as pd

        path = Path(path)
        if not path.is_absolute():
            candidate = ML_ROOT / path
            path = candidate if candidate.is_file() else path
        if not path.is_file():
            raise FileNotFoundError(
                f"{path} not found. Run preprocessing/split_dataset.py first."
            )

        frame = pd.read_parquet(path)

        unknown = set(frame["label_3class"]) - set(LABEL2ID)
        if unknown:
            raise ValueError(
                f"{path.name} contains unmapped labels: {sorted(unknown)}. "
                f"Expected only {sorted(LABEL2ID)}."
            )

        self.path = path
        self.texts = frame["text"].tolist()
        self.labels = [LABEL2ID[v] for v in frame["label_3class"]]
        self.subtypes = frame["subtype"].tolist()
        self.is_synthetic = frame["is_synthetic"].tolist()
        self.max_length = max_length

        if tokenizer is None:
            from transformers import AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, index: int) -> dict:
        encoded = self.tokenizer(
            self.texts[index],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        # DistilBERT's forward() has no token_type_ids parameter -- it is a
        # single-segment model. The Trainer silently drops unexpected keys,
        # but a hand-rolled model(**batch) loop in Task 27 or the inference
        # wrapper in Task 35 would raise a TypeError. Dropping it here keeps
        # the batch usable everywhere.
        item = {
            key: value.squeeze(0)
            for key, value in encoded.items()
            if key != "token_type_ids"
        }
        # Trainer expects the key to be exactly "labels".
        item["labels"] = self.labels[index]
        return item

    def label_counts(self) -> dict[str, int]:
        """Rows per class, by name. Used by the self-check below."""
        counts: dict[str, int] = {}
        for label_id in self.labels:
            name = ID2LABEL[label_id]
            counts[name] = counts.get(name, 0) + 1
        return counts

    def __repr__(self) -> str:
        return (
            f"PromptDataset({self.path.name}, n={len(self):,}, "
            f"max_length={self.max_length})"
        )


def _self_check() -> int:
    """Covers 26.1, 26.2 and 26.3 against the real split files."""
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoTokenizer

    print(f"MAX_LENGTH = {MAX_LENGTH} (from tokenize_check, Task 24)")
    print(f"LABEL2ID   = {LABEL2ID}\n")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    problems: list[str] = []
    datasets = {}
    for name in ("train", "val", "test"):
        path = PROCESSED / f"{name}.parquet"
        if not path.is_file():
            problems.append(f"{name}.parquet missing")
            continue
        dataset = PromptDataset(path, tokenizer=tokenizer)
        datasets[name] = dataset
        print(f"{name:<6} {len(dataset):>9,} rows   {dataset.label_counts()}")

    if problems:
        for problem in problems:
            print(f"  MISSING: {problem}")
        return 1

    train = datasets["train"]

    # --- 26.1 one item ----------------------------------------------------
    print("\n26.1  single item")
    item = train[0]
    for key, value in item.items():
        shape = tuple(value.shape) if hasattr(value, "shape") else type(value).__name__
        print(f"  {key:<16} {shape}")
    expected_keys = {"input_ids", "attention_mask", "labels"}
    if not expected_keys.issubset(item):
        print(f"  FAIL: missing {expected_keys - set(item)}")
        return 1
    if tuple(item["input_ids"].shape) != (MAX_LENGTH,):
        print(f"  FAIL: input_ids is {tuple(item['input_ids'].shape)}, "
              f"expected ({MAX_LENGTH},)")
        return 1
    print(f"  OK: padded to {MAX_LENGTH}")

    # --- 26.2 labels are ints ---------------------------------------------
    print("\n26.2  label type")
    label = item["labels"]
    print(f"  value {label}  type {type(label).__name__}")
    if not isinstance(label, int) or label not in ID2LABEL:
        print(f"  FAIL: expected an int in {sorted(ID2LABEL)}")
        return 1
    print(f"  OK: {label} -> {ID2LABEL[label]!r}")

    # --- 26.3 DataLoader --------------------------------------------------
    print("\n26.3  DataLoader batch")
    batch = next(iter(DataLoader(train, batch_size=4)))
    for key, value in batch.items():
        print(f"  {key:<16} {tuple(value.shape)}  {value.dtype}")
    if tuple(batch["input_ids"].shape) != (4, MAX_LENGTH):
        print("  FAIL: unexpected batch shape")
        return 1
    if batch["labels"].dtype != torch.int64:
        print(f"  FAIL: labels dtype is {batch['labels'].dtype}, expected int64")
        return 1
    print("  OK: batch of 4, no shape errors")

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
