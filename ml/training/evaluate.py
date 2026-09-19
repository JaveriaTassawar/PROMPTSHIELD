"""Evaluate a trained PromptShield checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
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

ID2LABEL = {value: key for key, value in LABEL2ID.items()}


def predict(
    model_path: str,
    data_path: str,
    batch_size: int = 32,
) -> tuple[pd.DataFrame, list[int], list[int]]:
    """Load a checkpoint and generate predictions for a parquet dataset."""

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"device  : {device}")
    print(f"model   : {model_path}")
    print(f"dataset : {data_path}")

    df = pd.read_parquet(data_path)

    required_columns = {"text", "label_3class"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Dataset missing required columns: {sorted(missing)}"
        )

    print(f"rows    : {len(df):,}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path
    )

    model.to(device)
    model.eval()

    texts = df["text"].astype(str).tolist()

    y_true = [
        LABEL2ID[label]
        for label in df["label_3class"]
    ]

    y_pred: list[int] = []

    for start in range(0, len(texts), batch_size):
        batch_texts = texts[start:start + batch_size]

        encoded = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            logits = model(**encoded).logits

        predictions = torch.argmax(
            logits,
            dim=-1,
        )

        y_pred.extend(
            predictions.cpu().numpy().tolist()
        )

    return df, y_true, y_pred


def compute_metrics(
    df: pd.DataFrame,
    y_true: list[int],
    y_pred: list[int],
) -> dict:
    """Calculate overall, per-class, confusion-matrix and subtype metrics."""

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    class_report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=[
            ID2LABEL[0],
            ID2LABEL[1],
            ID2LABEL[2],
        ],
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1, 2],
    )

    results = {
        "overall": {
            "accuracy": float(accuracy),
            "precision_weighted": float(precision),
            "recall_weighted": float(recall),
            "f1_weighted": float(f1),
        },
        "per_class": class_report,
        "confusion_matrix": matrix.tolist(),
    }

    # Per-subtype performance, if subtype information exists.
    if "subtype" in df.columns:
        subtype_results = {}

        temp = df.copy()
        temp["y_true"] = y_true
        temp["y_pred"] = y_pred

        for subtype, group in temp.groupby("subtype"):
            if pd.isna(subtype):
                continue

            count = len(group)

            correct = int(
                (group["y_true"] == group["y_pred"]).sum()
            )

            errors = count - correct

            subtype_accuracy = (
                correct / count
                if count
                else 0.0
            )

            subtype_results[str(subtype)] = {
                "count": int(count),
                "correct": correct,
                "errors": int(errors),
                "accuracy": float(subtype_accuracy),
            }

        results["per_subtype"] = subtype_results

    return results


def print_results(metrics: dict) -> None:
    """Print human-readable evaluation results."""

    overall = metrics["overall"]

    print("\nOverall Metrics")
    print("----------------")
    print(f"Accuracy : {overall['accuracy']:.4f}")
    print(f"Precision: {overall['precision_weighted']:.4f}")
    print(f"Recall   : {overall['recall_weighted']:.4f}")
    print(f"F1       : {overall['f1_weighted']:.4f}")

    print("\nPer-Class Metrics")
    print("-----------------")

    for label in LABEL2ID:
        class_metrics = metrics["per_class"][label]

        print(
            f"{label}: "
            f"precision={class_metrics['precision']:.4f}, "
            f"recall={class_metrics['recall']:.4f}, "
            f"f1={class_metrics['f1-score']:.4f}, "
            f"support={int(class_metrics['support'])}"
        )

    print("\nConfusion Matrix")
    print("----------------")
    print(np.array(metrics["confusion_matrix"]))

    if "per_subtype" in metrics:
        print("\nPer-Subtype Performance")
        print("-----------------------")

        for subtype, values in metrics["per_subtype"].items():
            print(
                f"{subtype}: "
                f"accuracy={values['accuracy']:.4f}, "
                f"correct={values['correct']}/{values['count']}, "
                f"errors={values['errors']}"
            )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate a trained PromptShield checkpoint."
    )

    parser.add_argument(
        "--model-path",
        required=True,
        help="Path to trained Hugging Face checkpoint.",
    )

    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to labelled parquet dataset.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Evaluation batch size.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional JSON output path.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    df, y_true, y_pred = predict(
        model_path=args.model_path,
        data_path=args.data_path,
        batch_size=args.batch_size,
    )

    metrics = compute_metrics(
        df=df,
        y_true=y_true,
        y_pred=y_pred,
    )

    print_results(metrics)

    if args.output:
        output_path = Path(args.output)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metrics,
                file,
                indent=2,
            )

        print(
            f"\nMetrics saved to: {output_path}"
        )


if __name__ == "__main__":
    main()