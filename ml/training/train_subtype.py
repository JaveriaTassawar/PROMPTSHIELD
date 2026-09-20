"""Train the PromptShield 8-class attack subtype classifier."""

import argparse
import math
from collections import Counter
from pathlib import Path

import torch
import torch.nn.functional as F
from transformers import (
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)

from training.subtype_dataset import (
    ID2SUBTYPE,
    SUBTYPE2ID,
    SUBTYPES,
    SubtypeDataset,
)


MODEL_NAME = "distilbert-base-uncased"


def build_model(model_name=MODEL_NAME):
    """Create an 8-class DistilBERT subtype classifier."""

    return AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(SUBTYPES),
        id2label=ID2SUBTYPE,
        label2id=SUBTYPE2ID,
    )


def compute_class_weights(dataset):
    """
    Compute moderated class weights from the training dataset.

    Square-root inverse-frequency weighting is used instead of raw inverse
    frequency because the subtype distribution is extremely imbalanced.
    """

    labels = [
        SUBTYPE2ID[subtype]
        for subtype in dataset.df["subtype"]
    ]

    counts = Counter(labels)
    total = len(labels)
    num_classes = len(SUBTYPES)

    weights = []

    for class_id in range(num_classes):
        count = counts.get(class_id, 0)

        if count == 0:
            raise ValueError(
                f"No training examples for subtype "
                f"{ID2SUBTYPE[class_id]}"
            )

        # Balanced inverse-frequency weight.
        balanced_weight = total / (num_classes * count)

        # Moderate extreme weights.
        weight = math.sqrt(balanced_weight)

        weights.append(weight)

    # Normalize so average class weight is approximately 1.
    mean_weight = sum(weights) / len(weights)
    weights = [weight / mean_weight for weight in weights]

    return torch.tensor(weights, dtype=torch.float32)


class WeightedSubtypeTrainer(Trainer):
    """Trainer using weighted cross-entropy for subtype imbalance."""

    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)

        if class_weights is None:
            raise ValueError("class_weights must be provided")

        self.class_weights = class_weights

    def compute_loss(
        self,
        model,
        inputs,
        return_outputs=False,
        num_items_in_batch=None,
    ):
        labels = inputs.pop("labels")

        outputs = model(**inputs)
        logits = outputs.logits

        weights = self.class_weights.to(logits.device)

        loss = F.cross_entropy(
            logits,
            labels,
            weight=weights,
        )

        # Restore labels so Trainer callbacks/evaluation can still access them.
        inputs["labels"] = labels

        if return_outputs:
            return loss, outputs

        return loss


def build_args(
    output_dir,
    epochs=1,
    batch_size=16,
    learning_rate=2e-5,
    max_steps=-1,
):
    """Create Hugging Face TrainingArguments."""

    return TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=torch.cuda.is_available(),
        report_to="none",
        max_steps=max_steps,
    )


def print_distribution(dataset, title):
    """Print subtype distribution."""

    print(f"\n{title}")
    print("-" * len(title))

    counts = dataset.subtype_counts()

    for subtype in SUBTYPES:
        print(f"{subtype}: {counts[subtype]:,}")

    print(f"Total: {len(dataset):,}")


def print_weights(weights):
    """Print class weights alongside subtype names."""

    print("\nClass Weights")
    print("-------------")

    for class_id, weight in enumerate(weights.tolist()):
        print(
            f"{ID2SUBTYPE[class_id]}: "
            f"{weight:.4f}"
        )


def run(
    train_path,
    val_path,
    output_dir,
    epochs=1,
    batch_size=16,
    learning_rate=2e-5,
    smoke_test=False,
):
    """Train the attack subtype classifier."""

    train_dataset = SubtypeDataset(train_path)
    val_dataset = SubtypeDataset(val_path)

    print_distribution(
        train_dataset,
        "Training Subtype Distribution",
    )

    print_distribution(
        val_dataset,
        "Validation Subtype Distribution",
    )

    class_weights = compute_class_weights(train_dataset)
    print_weights(class_weights)

    if smoke_test:
        print("\nSMOKE TEST MODE")
        print("----------------")

        # Keep every subtype represented if possible.
        smoke_indices = []

        for subtype in SUBTYPES:
            rows = train_dataset.df[
                train_dataset.df["subtype"] == subtype
            ].index.tolist()

            smoke_indices.extend(rows[:4])

        train_dataset.df = (
            train_dataset.df.loc[smoke_indices]
            .reset_index(drop=True)
        )

        val_indices = []

        for subtype in SUBTYPES:
            rows = val_dataset.df[
                val_dataset.df["subtype"] == subtype
            ].index.tolist()

            val_indices.extend(rows[:2])

        val_dataset.df = (
            val_dataset.df.loc[val_indices]
            .reset_index(drop=True)
        )

        print(
            f"Smoke train rows: {len(train_dataset)}"
        )
        print(
            f"Smoke validation rows: {len(val_dataset)}"
        )

    model = build_model()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    args = build_args(
        output_dir=output_dir,
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=learning_rate,
    )

    trainer = WeightedSubtypeTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=train_dataset.tokenizer,
        class_weights=class_weights,
    )

    print("\nStarting subtype training...")
    trainer.train()

    final_dir = output_dir / "final"

    trainer.save_model(final_dir)
    train_dataset.tokenizer.save_pretrained(final_dir)

    print(
        f"\nSubtype model saved to: {final_dir}"
    )

    return trainer


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Train the PromptShield 8-class "
            "attack subtype classifier."
        )
    )

    parser.add_argument(
        "--train-path",
        default="data/processed/train.parquet",
    )

    parser.add_argument(
        "--val-path",
        default="data/processed/val.parquet",
    )

    parser.add_argument(
        "--output-dir",
        default="outputs/subtype",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
    )

    parser.add_argument(
        "--smoke-test",
        action="store_true",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    run(
        train_path=args.train_path,
        val_path=args.val_path,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        smoke_test=args.smoke_test,
    )


if __name__ == "__main__":
    main()