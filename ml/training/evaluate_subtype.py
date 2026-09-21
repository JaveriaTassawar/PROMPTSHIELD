"""Evaluate the PromptShield 8-class attack subtype classifier."""

import argparse
import json

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from training.subtype_dataset import (
    ID2SUBTYPE,
    SUBTYPES,
    SubtypeDataset,
)


def evaluate(model_path, data_path, batch_size=32, output=None):
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("device  :", device)
    print("model   :", model_path)
    print("dataset :", data_path)

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    dataset = SubtypeDataset(
        data_path,
        tokenizer_name=model_path,
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path
    )
    model.to(device)
    model.eval()

    y_true = []
    y_pred = []

    with torch.no_grad():
        for batch in loader:
            labels = batch.pop("labels")

            batch = {
                key: value.to(device)
                for key, value in batch.items()
            }

            outputs = model(**batch)

            predictions = torch.argmax(
                outputs.logits,
                dim=-1,
            )

            y_true.extend(labels.numpy().tolist())
            y_pred.extend(
                predictions.cpu().numpy().tolist()
            )

    accuracy = accuracy_score(y_true, y_pred)

    macro_f1 = f1_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0,
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(SUBTYPES))),
        target_names=SUBTYPES,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(SUBTYPES))),
    )

    print("\nOverall Metrics")
    print("----------------")
    print(f"Accuracy    : {accuracy:.4f}")
    print(f"Macro F1    : {macro_f1:.4f}")
    print(f"Weighted F1 : {weighted_f1:.4f}")

    print("\nPer-Subtype Metrics")
    print("-------------------")

    for subtype in SUBTYPES:
        values = report[subtype]

        print(
            f"{subtype}: "
            f"precision={values['precision']:.4f}, "
            f"recall={values['recall']:.4f}, "
            f"f1={values['f1-score']:.4f}, "
            f"support={int(values['support'])}"
        )

    print("\nConfusion Matrix")
    print("----------------")
    print(matrix)

    results = {
        "overall": {
            "accuracy": float(accuracy),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1),
        },
        "per_subtype": {},
        "confusion_matrix": matrix.tolist(),
    }

    for subtype in SUBTYPES:
        values = report[subtype]

        results["per_subtype"][subtype] = {
            "precision": float(values["precision"]),
            "recall": float(values["recall"]),
            "f1": float(values["f1-score"]),
            "support": int(values["support"]),
        }

    if output:
        with open(output, "w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                indent=2,
            )

        print(f"\nMetrics saved to: {output}")

    return results


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the PromptShield "
            "8-class subtype classifier."
        )
    )

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

    parser.add_argument(
        "--output",
        default=None,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    evaluate(
        model_path=args.model_path,
        data_path=args.data_path,
        batch_size=args.batch_size,
        output=args.output,
    )


if __name__ == "__main__":
    main()