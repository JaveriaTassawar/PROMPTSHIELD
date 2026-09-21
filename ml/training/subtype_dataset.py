"""Dataset utilities for the PromptShield 8-class attack subtype classifier."""

from pathlib import Path

import pandas as pd
from torch.utils.data import Dataset
from transformers import AutoTokenizer

from training.tokenize_check import MAX_LENGTH


# Keep this order fixed.
# Never derive subtype IDs from alphabetical order or dataframe order.
SUBTYPES = [
    "Policy Evasion",
    "Multi-Turn Manipulation",
    "Role Override",
    "Persona Hijacking",
    "System Prompt Overwrite",
    "Document Embedding",
    "Web Content Injection",
    "Tool Output Injection",
]

SUBTYPE2ID = {name: idx for idx, name in enumerate(SUBTYPES)}
ID2SUBTYPE = {idx: name for name, idx in SUBTYPE2ID.items()}

ATTACK_LABELS = {
    "Direct Jailbreak",
    "Indirect Injection",
}


class SubtypeDataset(Dataset):
    """PyTorch dataset for attack-only 8-class subtype classification."""

    def __init__(
        self,
        parquet_path,
        tokenizer_name="distilbert-base-uncased",
        max_length=MAX_LENGTH,
    ):
        self.parquet_path = Path(parquet_path)
        self.max_length = max_length

        if not self.parquet_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.parquet_path}"
            )

        df = pd.read_parquet(self.parquet_path)

        required_columns = {
            "text",
            "label_3class",
            "subtype",
        }

        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(
                f"Dataset is missing required columns: {sorted(missing)}"
            )

        # Task 34.1:
        # only attack examples belong in the subtype classifier.
        df = df[df["label_3class"].isin(ATTACK_LABELS)].copy()

        # Remove missing subtype labels.
        df = df[df["subtype"].notna()].copy()

        # Normalize string values.
        df["text"] = df["text"].astype(str).str.strip()
        df["subtype"] = df["subtype"].astype(str).str.strip()

        # Remove empty text.
        df = df[df["text"] != ""].copy()

        # Keep only the authoritative eight subtypes.
        df = df[df["subtype"].isin(SUBTYPE2ID)].copy()

        df.reset_index(drop=True, inplace=True)

        if df.empty:
            raise ValueError(
                "No valid attack subtype rows remain after filtering."
            )

        self.df = df

        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name
        )

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]

        encoded = self.tokenizer(
            row["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value in encoded.items()
        }

        # DistilBERT does not use token_type_ids.
        item.pop("token_type_ids", None)

        item["labels"] = int(
            SUBTYPE2ID[row["subtype"]]
        )

        return item

    def subtype_counts(self):
        """Return attack subtype counts in the fixed label order."""

        counts = self.df["subtype"].value_counts()

        return {
            subtype: int(counts.get(subtype, 0))
            for subtype in SUBTYPES
        }