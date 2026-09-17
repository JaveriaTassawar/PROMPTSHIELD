# Task 29 — Full Training & Hyperparameter Tuning

## Environment
- Model: distilbert-base-uncased
- GPU: Tesla T4
- Max sequence length: 512
- Class weights: enabled
- Training rows: 453,935
- Validation rows: 50,438

## Run 01
- Learning rate: 2e-5
- Batch size: 16
- Epochs: 3

| Epoch | Validation Loss |
|---|---:|
| 1 | 0.05065 |
| 2 | 0.05366 |
| 3 | 0.05843 |

### Overfitting Observation

Validation loss increased after Epoch 1:

- Epoch 1: `0.05065`
- Epoch 2: `0.05366`
- Epoch 3: `0.05843`

Although training loss continued to decrease, validation loss increased after Epoch 1, indicating overfitting beyond the first epoch.

Therefore, `checkpoint-28371` from Epoch 1 was selected as the best Run 01 checkpoint.

Best checkpoint: `checkpoint-28371` (Epoch 1)

Validation metrics for best checkpoint:
- Accuracy: 0.9854
- Precision: 0.9855
- Recall: 0.9854
- F1: 0.9854

These metrics were calculated separately after training using the full validation split (`val.parquet`) and the selected checkpoint.

The reproducible evaluation code is available in `training/validate_checkpoint.py`. It loads the trained checkpoint, predicts all validation examples, and calculates accuracy, weighted precision, weighted recall, and weighted F1 using scikit-learn.

## Run 02
- Learning rate: 1e-5
- Batch size: 16
- Epochs: 1
- Validation loss: 0.05835

Validation metrics:
- Accuracy: 0.9841
- Precision: 0.9841
- Recall: 0.9841
- F1: 0.9841

Run 02 was evaluated using the same full validation split and the same metric calculation procedure as Run 01 to ensure a fair comparison.

## Selection
Run 01 checkpoint 28371 was selected based on validation performance.

Selected configuration:
- Learning rate: 2e-5
- Batch size: 16
- Epoch: 1
- Validation accuracy: 98.54%
- Validation F1: 98.54%

Final real-world test metrics are intentionally deferred to Tasks 30–31.
