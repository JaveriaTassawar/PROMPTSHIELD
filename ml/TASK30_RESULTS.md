# Task 30 — Model Evaluation Pipeline & Evaluation Results

## 1. Purpose

Task 30 implements a reproducible evaluation pipeline for the trained PromptShield DistilBERT classifier.

The purpose of this task is to evaluate the selected model beyond training loss and report its performance using:

- Accuracy
- Weighted precision
- Weighted recall
- Weighted F1-score
- Per-class precision, recall, F1-score, and support
- Confusion matrix
- Per-attack-subtype performance

The evaluation logic is implemented in:

`ml/training/evaluate.py`

The script can evaluate any compatible trained Hugging Face checkpoint against a labelled PromptShield parquet dataset.

---

## 2. Selected Model

The model evaluated in Task 30 is:

- Base model: `distilbert-base-uncased`
- Classification task: 3-class prompt-injection classification
- Classes:
  - Safe
  - Direct Jailbreak
  - Indirect Injection
- Selected training run: Run 01
- Selected checkpoint: `checkpoint-28371`
- Selected epoch: Epoch 1
- Training learning rate: `2e-5`
- Training batch size: `16`
- Maximum sequence length: `512`
- Class-weighted training loss: Enabled

The trained model checkpoint is stored outside Git because model files are too large for normal repository tracking.

---

## 3. Why `checkpoint-28371` Was Selected

Run 01 was originally trained for three epochs.

Validation loss after each epoch was:

| Epoch | Validation Loss |
|---|---:|
| 1 | **0.05065** |
| 2 | 0.05366 |
| 3 | 0.05843 |

Validation loss increased after Epoch 1 even though training loss continued to decrease.

This indicated that additional epochs were beginning to overfit the training data.

Therefore, the Epoch 1 checkpoint:

`run_01/checkpoint-28371`

was selected instead of the final Epoch 3 model.

Task 29 also compared this configuration against a second run using a lower learning rate (`1e-5`). Run 01 produced better validation loss and slightly better validation accuracy/F1.

The model was therefore selected using validation data **before evaluating the held-out test set**.

---

## 4. Evaluation Environment

Evaluation was performed using:

- Platform: Google Colab
- GPU: NVIDIA Tesla T4
- Framework: PyTorch
- Model library: Hugging Face Transformers
- Metrics library: scikit-learn
- Input format: Parquet
- Evaluation batch size: `32`
- Maximum sequence length: `512`

During evaluation:

- The model is placed in evaluation mode using `model.eval()`.
- Gradients are disabled using `torch.no_grad()`.
- No model weights are updated.
- No additional training or fine-tuning occurs.
- Predictions are produced using the class with the highest model logit.

---

## 5. Label Mapping

The evaluation pipeline uses the same 3-class mapping used during model training:

| Label | ID |
|---|---:|
| Safe | 0 |
| Direct Jailbreak | 1 |
| Indirect Injection | 2 |

Maintaining the same label mapping is necessary so that predicted class IDs correspond correctly to the dataset labels.

---

## 6. Evaluation Pipeline

`training/evaluate.py` performs the following steps:

1. Load the labelled parquet dataset.
2. Verify that required columns are available:
   - `text`
   - `label_3class`
3. Load the tokenizer from the selected checkpoint.
4. Load the trained DistilBERT sequence-classification model.
5. Move the model to CUDA when a GPU is available.
6. Tokenize prompts in batches.
7. Truncate sequences to a maximum length of 512 tokens.
8. Run inference with gradients disabled.
9. Select the class with the highest logit as the prediction.
10. Compare predictions with ground-truth labels.
11. Calculate overall metrics.
12. Calculate per-class metrics.
13. Generate the 3 × 3 confusion matrix.
14. Calculate per-subtype performance when subtype information is available.
15. Optionally save all metrics to JSON.

---

## 7. Metric Definitions

### Accuracy

Accuracy measures the proportion of all examples that were classified correctly.

`Accuracy = Correct Predictions / Total Predictions`

### Precision

Precision measures how often a predicted class is correct.

For the overall result, weighted precision is reported so that each class contributes according to its number of examples.

### Recall

Recall measures how many examples belonging to a class were successfully identified.

Weighted recall is reported for the overall result.

### F1-Score

F1 combines precision and recall into a single metric.

Weighted F1 is used for the overall result so that class imbalance is taken into account.

### Support

Support is the number of ground-truth examples belonging to a particular class.

### Confusion Matrix

The confusion matrix shows the exact number of examples belonging to each actual class and the classes predicted by the model.

Rows represent actual labels.

Columns represent predicted labels.

### Per-Subtype Accuracy

For each attack subtype, performance is reported as:

- Total examples
- Correct predictions
- Errors
- Accuracy

Subtype accuracy is calculated as:

`Correct subtype examples / Total subtype examples`

Sample count is reported alongside subtype accuracy because very small subtype groups can produce unstable percentages.

---

# 8. Validation Sanity Check

Before evaluating the held-out test set, the Task 30 evaluator was run on `val.parquet`.

This was done to confirm that the new reusable evaluation pipeline reproduced the metrics previously obtained during Task 29.

Dataset:

`val.parquet`

Total examples:

**50,438**

## 8.1 Overall Validation Metrics

| Metric | Result |
|---|---:|
| Accuracy | **98.54%** |
| Weighted Precision | **98.55%** |
| Weighted Recall | **98.54%** |
| Weighted F1 | **98.54%** |

These results reproduce the Task 29 validation results for `checkpoint-28371`.

This confirms that the evaluation pipeline is consistent with the metric calculation used when selecting the checkpoint.

---

## 8.2 Per-Class Validation Metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Safe | 98.71% | 97.66% | 98.18% | 20,047 |
| Direct Jailbreak | 96.89% | 98.31% | 97.59% | 15,081 |
| Indirect Injection | 99.98% | 99.93% | 99.95% | 15,310 |

---

## 8.3 Validation Confusion Matrix

Rows are actual classes and columns are predicted classes.

| Actual \ Predicted | Safe | Direct Jailbreak | Indirect Injection |
|---|---:|---:|---:|
| Safe | 19,578 | 468 | 1 |
| Direct Jailbreak | 253 | 14,826 | 2 |
| Indirect Injection | 3 | 8 | 15,299 |

The validation confusion matrix totals **50,438 examples**, matching the validation dataset size.

---

## 8.4 Per-Subtype Validation Performance

| Subtype | Correct | Total | Errors | Accuracy |
|---|---:|---:|---:|---:|
| Document Embedding | 3,025 | 3,033 | 8 | 99.74% |
| Multi-Turn Manipulation | 515 | 517 | 2 | 99.61% |
| Persona Hijacking | 117 | 154 | 37 | 75.97% |
| Policy Evasion | 14,068 | 14,278 | 210 | 98.53% |
| Role Override | 3 | 8 | 5 | 37.50% |
| System Prompt Overwrite | 123 | 124 | 1 | 99.19% |
| Tool Output Injection | 56 | 58 | 2 | 96.55% |
| Web Content Injection | 12,218 | 12,219 | 1 | 99.99% |

Role Override contains only eight validation examples. Its 37.50% validation accuracy should therefore not be interpreted as a stable estimate of general performance for that subtype.

---

# 9. Held-Out Real-World Test Evaluation

After the validation sanity check succeeded, the selected checkpoint was evaluated on:

`test.parquet`

Total test examples:

**42,690**

This dataset was held out from model training and hyperparameter selection.

The test results were not used to select a new model or modify the trained checkpoint.

---

## 9.1 Evaluation Command

The real-world test evaluation was executed using:

```bash
python training/evaluate.py \
  --model-path "<path-to-run_01/checkpoint-28371>" \
  --data-path "data/processed/test.parquet" \
  --batch-size 32 \
  --output "task30_test_metrics.json"
```

The checkpoint itself remains outside Git and is stored in Google Drive.

---

## 9.2 Overall Real-World Test Metrics

| Metric | Result |
|---|---:|
| Accuracy | **99.11%** |
| Weighted Precision | **99.13%** |
| Weighted Recall | **99.11%** |
| Weighted F1 | **99.11%** |

The model correctly classified:

**42,309 / 42,690 test examples**

and misclassified:

**381 / 42,690 test examples**

This corresponds to approximately **99.11% overall test accuracy**.

---

## 9.3 Per-Class Real-World Test Metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Safe | 99.08% | 97.98% | 98.53% | 12,570 |
| Direct Jailbreak | 92.12% | 96.38% | 94.20% | 3,119 |
| Indirect Injection | 99.96% | 99.95% | 99.96% | 27,001 |

### Safe

The Safe class achieved:

- Precision: 99.08%
- Recall: 97.98%
- F1: 98.53%

Out of 12,570 Safe examples, 12,316 were correctly classified.

### Direct Jailbreak

Direct Jailbreak achieved:

- Precision: 92.12%
- Recall: 96.38%
- F1: 94.20%

Out of 3,119 Direct Jailbreak examples, 3,006 were correctly classified.

Direct Jailbreak produced the lowest class-level F1 among the three primary classes, although its F1 remained above 94%.

### Indirect Injection

Indirect Injection achieved:

- Precision: 99.96%
- Recall: 99.95%
- F1: 99.96%

Out of 27,001 Indirect Injection examples, 26,987 were correctly classified.

This was the strongest of the three primary classes on the held-out test set.

---

## 9.4 Real-World Test Confusion Matrix

Rows represent actual classes and columns represent predicted classes.

| Actual \ Predicted | Safe | Direct Jailbreak | Indirect Injection |
|---|---:|---:|---:|
| Safe | 12,316 | 244 | 10 |
| Direct Jailbreak | 113 | 3,006 | 0 |
| Indirect Injection | 1 | 13 | 26,987 |

### Confusion Matrix Interpretation

For actual Safe examples:

- 12,316 were correctly predicted as Safe.
- 244 were predicted as Direct Jailbreak.
- 10 were predicted as Indirect Injection.

For actual Direct Jailbreak examples:

- 3,006 were correctly predicted as Direct Jailbreak.
- 113 were predicted as Safe.
- 0 were predicted as Indirect Injection.

For actual Indirect Injection examples:

- 26,987 were correctly predicted as Indirect Injection.
- 13 were predicted as Direct Jailbreak.
- 1 was predicted as Safe.

The largest confusion occurs between **Safe and Direct Jailbreak**.

The model very rarely confuses Indirect Injection with either of the other two classes.

---

# 10. Per-Subtype Real-World Test Performance

| Subtype | Correct | Total | Errors | Accuracy |
|---|---:|---:|---:|---:|
| Document Embedding | 4,971 | 4,984 | 13 | 99.74% |
| Multi-Turn Manipulation | 966 | 968 | 2 | 99.79% |
| Persona Hijacking | 184 | 218 | 34 | 84.40% |
| Policy Evasion | 1,669 | 1,741 | 72 | 95.86% |
| Role Override | 16 | 18 | 2 | 88.89% |
| System Prompt Overwrite | 171 | 174 | 3 | 98.28% |
| Tool Output Injection | 94 | 95 | 1 | 98.95% |
| Web Content Injection | 21,922 | 21,922 | 0 | 100.00% |

---

## 10.1 Document Embedding

- Correct: 4,971 / 4,984
- Errors: 13
- Accuracy: **99.74%**

The model performed strongly on Document Embedding attacks.

---

## 10.2 Multi-Turn Manipulation

- Correct: 966 / 968
- Errors: 2
- Accuracy: **99.79%**

Only two Multi-Turn Manipulation examples were misclassified.

---

## 10.3 Persona Hijacking

- Correct: 184 / 218
- Errors: 34
- Accuracy: **84.40%**

Persona Hijacking was the weakest-performing subtype among the subtypes with more than a very small number of test examples.

This indicates that Persona Hijacking represents a comparatively difficult attack pattern for the selected checkpoint.

No further model tuning was performed using this test result because the test set must remain a held-out evaluation set.

---

## 10.4 Policy Evasion

- Correct: 1,669 / 1,741
- Errors: 72
- Accuracy: **95.86%**

Policy Evasion performance remained strong, although it produced more absolute errors than several smaller subtype groups.

---

## 10.5 Role Override

- Correct: 16 / 18
- Errors: 2
- Accuracy: **88.89%**

Only 18 Role Override examples exist in the held-out test set.

Therefore, the 88.89% result should be interpreted cautiously because the sample size is very small.

Two additional correct or incorrect predictions would substantially change the reported percentage.

---

## 10.6 System Prompt Overwrite

- Correct: 171 / 174
- Errors: 3
- Accuracy: **98.28%**

The model performed strongly on System Prompt Overwrite attacks.

---

## 10.7 Tool Output Injection

- Correct: 94 / 95
- Errors: 1
- Accuracy: **98.95%**

Only one Tool Output Injection example was misclassified.

---

## 10.8 Web Content Injection

- Correct: 21,922 / 21,922
- Errors: 0
- Accuracy: **100.00%**

All Web Content Injection examples in the held-out test set were classified correctly.

This result applies specifically to the 21,922 Web Content Injection examples present in this test dataset and should not be interpreted as proof of perfect performance on every possible future Web Content Injection prompt.

---

# 11. Validation vs Test Comparison

| Metric | Validation | Real-World Test |
|---|---:|---:|
| Accuracy | 98.54% | **99.11%** |
| Precision | 98.55% | **99.13%** |
| Recall | 98.54% | **99.11%** |
| F1 | 98.54% | **99.11%** |

The real-world held-out test results were slightly higher than the validation results.

This does not mean that the model improved after validation; the checkpoint was unchanged.

The difference reflects performance on two different data splits with different example compositions.

---

# 12. Key Findings

1. The Task 30 evaluator successfully reproduced the Task 29 validation metrics.

2. The selected Epoch 1 checkpoint achieved:
   - **99.11% test accuracy**
   - **99.13% weighted precision**
   - **99.11% weighted recall**
   - **99.11% weighted F1**

3. Indirect Injection was classified extremely accurately, with a test F1 of **99.96%**.

4. Direct Jailbreak was comparatively more difficult than the other primary classes, with a test F1 of **94.20%**.

5. The largest class-level confusion occurred between Safe and Direct Jailbreak.

6. Persona Hijacking was the weakest subtype with a meaningful test sample size:
   - 184 / 218 correct
   - 84.40% accuracy

7. Role Override produced an 88.89% test accuracy, but this is based on only 18 examples and should therefore be interpreted cautiously.

8. Web Content Injection achieved 100% accuracy on the 21,922 examples in this particular held-out test set.

---

# 13. Reproducibility

The evaluation is reproducible using:

`ml/training/evaluate.py`

Required inputs are:

1. A compatible trained Hugging Face PromptShield checkpoint.
2. A parquet dataset containing:
   - `text`
   - `label_3class`
3. Optionally, a `subtype` column for subtype analysis.

Example:

```bash
python training/evaluate.py \
  --model-path "<checkpoint-path>" \
  --data-path "<dataset-path>" \
  --batch-size 32 \
  --output "metrics.json"
```

The generated JSON contains:

- Overall metrics
- Per-class metrics
- Confusion matrix
- Per-subtype performance when subtype data is available

---

# 14. Evaluation Integrity

The following separation was maintained:

- Training data was used for model optimization.
- Validation data was used during Task 29 for model/hyperparameter selection.
- The held-out real-world test set was not used to select the checkpoint.
- Test results were obtained only after the model configuration had been selected.
- No further model tuning was performed based on the held-out test results.

This prevents the reported test metrics from being intentionally optimized against the held-out test set.

---

# 15. Limitations and Interpretation Notes

- Overall metrics are weighted and therefore reflect the class distribution of the evaluated dataset.
- Class support is not equal across the three primary classes.
- Subtype sample sizes vary substantially.
- Very small subtype groups, particularly Role Override, should not be interpreted using percentage alone.
- A high score on the current held-out dataset does not guarantee identical performance on future unseen prompt-injection attacks.
- Web Content Injection achieved 100% accuracy on this test set, but this should not be interpreted as universal perfect detection.
- Persona Hijacking remains a comparatively difficult subtype based on the held-out results.
- The model was not modified after viewing the held-out test results.

---

# 16. Task 30 Status

Task 30 evaluation pipeline has been implemented and validated.

Completed components:

- Reusable checkpoint evaluation script
- Overall metrics
- Per-class metrics
- Confusion matrix
- Per-subtype evaluation
- JSON metric export
- Validation reproducibility check
- Held-out real-world test evaluation
- Detailed result documentation

The selected model remains:

`run_01/checkpoint-28371`