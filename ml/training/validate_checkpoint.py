"""Validate a trained PromptShield checkpoint on the validation split."""

from __future__ import annotations

import argparse

import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
)

from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


LABEL2ID = {
    "Safe": 0,
    "Direct Jailbreak": 1,
    "Indirect Injection": 2,
}


def evaluate_checkpoint(
    model_path: str,
    data_path: str,
    batch_size: int = 32,
) -> dict:
    df = pd.read_parquet(data_path)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model.to(device)
    model.eval()

    texts = df["text"].astype(str).tolist()
    labels = [LABEL2ID[label] for label in df["label_3class"]]

    predictions = []

    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start : start + batch_size]

        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            logits = model(**encoded).logits

        predictions.extend(
            torch.argmax(logits, dim=-1).cpu().numpy().tolist()
        )

    accuracy = accuracy_score(labels, predictions)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model-path",
        required=True,
    )

    parser.add_argument(
        "--data-path",
        required=True,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    args = parser.parse_args()

    metrics = evaluate_checkpoint(
        model_path=args.model_path,
        data_path=args.data_path,
        batch_size=args.batch_size,
    )

    print("\nValidation metrics")
    print("------------------")

    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()