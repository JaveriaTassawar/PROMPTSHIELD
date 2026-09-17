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

Best checkpoint: `checkpoint-28371` (Epoch 1)

Validation metrics for best checkpoint:
- Accuracy: 0.9854
- Precision: 0.9855
- Recall: 0.9854
- F1: 0.9854

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

## Selection
Run 01 checkpoint 28371 was selected based on validation performance.

Selected configuration:
- Learning rate: 2e-5
- Batch size: 16
- Epoch: 1
- Validation accuracy: 98.54%
- Validation F1: 98.54%

Final real-world test metrics are intentionally deferred to Tasks 30–31.
