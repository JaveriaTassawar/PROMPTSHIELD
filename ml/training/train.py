"""Fine-tune DistilBERT on the 3-class prompt-injection dataset.

Task 27. This file is the training entry point for both environments:

    local CPU smoke test   python training/train.py --smoke-test
    Colab T4 full run      from training.train import run; run()

Nothing executes on import -- every piece of work lives in a function, so the
Colab notebook (section 3 of the plan) can import `run` and call it with its
own arguments without a training job starting the moment the cell is
evaluated. That is the 27.4 requirement.

FOUR DECISIONS HERE THAT ARE NOT OBVIOUS:

1. CLASS WEIGHTS ARE LOOKED UP BY NAME, NEVER BY FILE ORDER.

   class_weights.json stores {"Direct Jailbreak": 1.11, "Indirect Injection":
   1.10, "Safe": 0.84}. Reading .values() into a tensor would bind 1.11 to
   index 0 -- which LABEL2ID says is Safe. The model would then up-weight the
   majority class and down-weight a minority one, and the only symptom would
   be quietly worse recall on the classes that matter most. build_weights()
   indexes through LABEL2ID so the order is enforced, and it raises if a class
   is missing rather than filling in a default.

2. fp16 IS DERIVED, NOT HARDCODED.

   fp16=True raises on a CPU-only machine; fp16=False wastes roughly half the
   throughput on Colab's T4. torch.cuda.is_available() decides, so the same
   file runs in both places with no edit between them.

3. THE WEIGHTED LOSS OVERRIDE TAKES num_items_in_batch.

   transformers 5.x calls compute_loss(model, inputs, return_outputs,
   num_items_in_batch). A subclass written against the older three-argument
   signature still *imports* cleanly and only fails once a training step
   runs -- i.e. partway into a paid GPU session. The signature below matches
   the installed version, verified by inspect.

4. EVALUATION IS ON val, NEVER test.

   test.parquet is the real-world-only held-out set that produces the headline
   number in Task 31. Using it for eval_dataset here would let checkpoint
   selection peek at it via load_best_model_at_end, and the Task 31 score
   would no longer be honest. val.parquet is the tuning signal.

Run:  python training/train.py --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ML_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ML_ROOT))

from training.dataset import (  # noqa: E402
    ID2LABEL,
    LABEL2ID,
    NUM_LABELS,
    PromptDataset,
)
from training.tokenize_check import MAX_LENGTH, MODEL_NAME  # noqa: E402

PROCESSED = ML_ROOT / "data" / "processed"
WEIGHTS_PATH = PROCESSED / "class_weights.json"
DEFAULT_OUTPUT_DIR = ML_ROOT / "models" / "checkpoints"

# Starting points, not tuned values. Task 29.5 is the tuning pass.
DEFAULT_EPOCHS = 3
DEFAULT_TRAIN_BATCH = 16
DEFAULT_EVAL_BATCH = 32
DEFAULT_LR = 2e-5
DEFAULT_WEIGHT_DECAY = 0.01
DEFAULT_WARMUP_STEPS = 500
SEED = 42


# --- 27.1 ------------------------------------------------------------------
def build_model(model_name: str = MODEL_NAME):
    """DistilBERT with a fresh 3-way classification head.

    id2label/label2id are baked into the model config so a saved checkpoint
    reports class names on its own. Without them the inference wrapper in
    Task 35 would have to re-declare the mapping, and a mismatch there would
    mislabel every prediction.
    """
    from transformers import AutoModelForSequenceClassification

    return AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )


# --- 27.2 ------------------------------------------------------------------
def build_args(
    output_dir=DEFAULT_OUTPUT_DIR,
    epochs: float = DEFAULT_EPOCHS,
    train_batch: int = DEFAULT_TRAIN_BATCH,
    eval_batch: int = DEFAULT_EVAL_BATCH,
    learning_rate: float = DEFAULT_LR,
    warmup_steps: int = DEFAULT_WARMUP_STEPS,
    logging_steps: int = 50,
    seed: int = SEED,
):
    """TrainingArguments for transformers 5.x.

    Two version-specific names worth flagging, both verified against the
    installed library rather than recalled: the parameter is `eval_strategy`
    (`evaluation_strategy` was removed), and there is no `warmup_ratio`, so
    warmup is expressed in steps.

    load_best_model_at_end with metric_for_best_model="eval_loss" means the
    checkpoint that gets saved is the best-scoring one, not merely the last.
    On a 3-epoch run the final epoch is often slightly overfit.
    """
    import torch
    from transformers import TrainingArguments

    return TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=train_batch,
        per_device_eval_batch_size=eval_batch,
        learning_rate=learning_rate,
        weight_decay=DEFAULT_WEIGHT_DECAY,
        warmup_steps=warmup_steps,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,          # checkpoints are ~265 MB each
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=logging_steps,
        seed=seed,
        # See decision 2 in the module docstring.
        fp16=torch.cuda.is_available(),
        report_to=[],                # no wandb/tensorboard prompts in Colab
    )


# --- 27.3 ------------------------------------------------------------------
def build_weights(path=WEIGHTS_PATH):
    """Class-weight tensor ordered by LABEL2ID, or None if the file is absent.

    See decision 1 in the module docstring -- the ordering here is the whole
    point of the function.
    """
    import torch

    path = Path(path)
    if not path.is_file():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    weights = payload["weights"]

    missing = set(LABEL2ID) - set(weights)
    if missing:
        raise ValueError(
            f"{path.name} has no weight for {sorted(missing)}. "
            f"Re-run preprocessing/class_weights.py."
        )

    ordered = [float(weights[name]) for name, _ in
               sorted(LABEL2ID.items(), key=lambda kv: kv[1])]
    return torch.tensor(ordered, dtype=torch.float)


def build_trainer(model, args, train_dataset, eval_dataset, tokenizer=None,
                  class_weights=None):
    """Assemble the Trainer, with weighted loss when weights are supplied.

    `processing_class` replaced `tokenizer` in transformers 5.x. Passing the
    tokenizer matters beyond convenience: it is saved alongside the checkpoint,
    so Task 33's Drive upload is self-contained and Task 35 does not have to
    guess which tokenizer produced the weights.
    """
    import torch
    from torch import nn
    from transformers import Trainer

    class WeightedTrainer(Trainer):
        """Applies per-class weights to the loss.

        The signature must include num_items_in_batch -- see decision 3.
        """

        def compute_loss(self, model, inputs, return_outputs=False,
                         num_items_in_batch=None):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            loss_fn = nn.CrossEntropyLoss(
                weight=class_weights.to(logits.device)
            )
            loss = loss_fn(
                logits.view(-1, NUM_LABELS), labels.view(-1)
            )
            # Restore it: Trainer reuses the dict for metric computation.
            inputs["labels"] = labels
            return (loss, outputs) if return_outputs else loss

    trainer_cls = WeightedTrainer if class_weights is not None else Trainer

    kwargs = dict(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )
    if tokenizer is not None:
        kwargs["processing_class"] = tokenizer

    return trainer_cls(**kwargs)


# --- 27.4 ------------------------------------------------------------------
def load_splits(tokenizer, limit: int | None = None):
    """train and val as PromptDatasets, sharing one tokenizer instance.

    `limit` takes the first N rows for the Task 28 smoke test. The splits were
    shuffled when they were written, so a head slice is already mixed across
    classes -- but it is not stratified, and a smoke test only needs the code
    path to execute, not a meaningful score.
    """
    train_path = PROCESSED / "train.parquet"
    val_path = PROCESSED / "val.parquet"

    for path in (train_path, val_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"{path} not found. Run preprocessing/split_dataset.py first."
            )

    train = PromptDataset(train_path, tokenizer=tokenizer)
    val = PromptDataset(val_path, tokenizer=tokenizer)

    if limit:
        train = _Subset(train, limit)
        val = _Subset(val, max(limit // 4, 8))

    return train, val


class _Subset:
    """First N rows of a PromptDataset, for the smoke test."""

    def __init__(self, dataset, size: int):
        self.dataset = dataset
        self.size = min(size, len(dataset))

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, index: int):
        return self.dataset[index]


def run(output_dir=DEFAULT_OUTPUT_DIR, epochs: float = DEFAULT_EPOCHS,
        train_batch: int = DEFAULT_TRAIN_BATCH, learning_rate: float = DEFAULT_LR,
        limit: int | None = None, use_class_weights: bool = True,
        resume_from_checkpoint: str | None = None):
    """Full training run. Importable from Colab; nothing runs on import.

    Returns the Trainer so the notebook can reach .state.log_history and
    .save_model() without rebuilding anything.
    """
    import torch
    from transformers import AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device       {device}")
    print(f"model        {MODEL_NAME}")
    print(f"max_length   {MAX_LENGTH}")
    print(f"output_dir   {output_dir}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dataset, eval_dataset = load_splits(tokenizer, limit=limit)
    print(f"train        {len(train_dataset):,} rows")
    print(f"val          {len(eval_dataset):,} rows")

    class_weights = build_weights() if use_class_weights else None
    if class_weights is None:
        print("class weights  none -- unweighted loss")
    else:
        pairs = ", ".join(
            f"{ID2LABEL[i]} {w:.4f}" for i, w in enumerate(class_weights.tolist())
        )
        print(f"class weights  {pairs}")

    model = build_model()
    args = build_args(
        output_dir=output_dir,
        epochs=epochs,
        train_batch=train_batch,
        learning_rate=learning_rate,
        # A 100-row smoke test has fewer total steps than the default warmup,
        # which would leave the LR at ~0 and produce a flat loss that looks
        # like a bug. Scale warmup down with the run.
        warmup_steps=0 if limit else DEFAULT_WARMUP_STEPS,
        logging_steps=5 if limit else 50,
    )
    trainer = build_trainer(
        model, args, train_dataset, eval_dataset,
        tokenizer=tokenizer, class_weights=class_weights,
    )

    print("\nstarting training\n")
    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    final_dir = Path(output_dir) / "final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"\nsaved to {final_dir}")

    return trainer


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Fine-tune DistilBERT for prompt-injection detection."
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--epochs", type=float, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_TRAIN_BATCH)
    parser.add_argument("--learning-rate", type=float, default=DEFAULT_LR)
    parser.add_argument(
        "--limit", type=int, default=None,
        help="train on the first N rows only (Task 28 smoke test)",
    )
    parser.add_argument(
        "--smoke-test", action="store_true",
        help="shorthand for --limit 100 --epochs 1 --batch-size 8",
    )
    parser.add_argument(
        "--no-class-weights", action="store_true",
        help="train with unweighted loss",
    )
    parser.add_argument(
        "--resume-from-checkpoint", default=None,
        help="resume training from a saved Hugging Face Trainer checkpoint",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    parsed = parse_args(argv)

    limit = parsed.limit
    epochs = parsed.epochs
    batch_size = parsed.batch_size
    if parsed.smoke_test:
        limit = parsed.limit or 100
        epochs = 1
        batch_size = 8

    run(
        output_dir=parsed.output_dir,
        epochs=epochs,
        train_batch=batch_size,
        learning_rate=parsed.learning_rate,
        limit=limit,
        use_class_weights=not parsed.no_class_weights,
        resume_from_checkpoint=parsed.resume_from_checkpoint,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
