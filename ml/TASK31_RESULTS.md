# Task 31 — Final Metrics & Target Check

## 1. Purpose

Task 31 records the final machine-generated evaluation metrics for the selected PromptShield model and formally checks whether the project performance targets were achieved.

The selected model remains:

`run_01/checkpoint-28371`

The final metrics were generated using:

`ml/training/evaluate.py`

and saved as:

- `ml/results/metrics_real.json`
- `ml/results/metrics_synthetic.json`

These JSON files were generated directly by the evaluation pipeline rather than manually entering the reported metric values.

---

## 2. Selected Model

The final model used for Task 31 is:

- Base model: `distilbert-base-uncased`
- Selected training run: Run 01
- Selected checkpoint: `checkpoint-28371`
- Selected epoch: Epoch 1
- Classification task: 3-class prompt-injection classification
- Classes:
  - Safe
  - Direct Jailbreak
  - Indirect Injection

The checkpoint was selected during Task 29 using validation performance before the held-out test sets were evaluated.

No additional model training or hyperparameter tuning was performed during Task 31.

---

## 3. Machine-Generated Metric Files

Task 31 adds two machine-readable evaluation files:

### Real-World Metrics

`ml/results/metrics_real.json`

Generated from:

`test.parquet`

### Synthetic Metrics

`ml/results/metrics_synthetic.json`

Generated from:

`synthetic_test.parquet`

The JSON files contain:

- Overall accuracy
- Weighted precision
- Weighted recall
- Weighted F1
- Per-class metrics
- Class support
- Confusion matrix
- Per-subtype performance

---

## 4. Final Real-World Metrics

Dataset:

`test.parquet`

Total examples:

**42,690**

The real-world held-out test set is used for the primary final performance result.

| Metric | Result |
|---|---:|
| Accuracy | **99.11%** |
| Weighted Precision | **99.13%** |
| Weighted Recall | **99.11%** |
| Weighted F1 | **99.11%** |

The machine-generated JSON contains the full-precision metric values.

The model correctly classified:

**42,309 / 42,690 examples**

and misclassified:

**381 / 42,690 examples**

---

## 5. Real-World Per-Class Results

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Safe | 99.08% | 97.98% | 98.53% | 12,570 |
| Direct Jailbreak | 92.12% | 96.38% | 94.20% | 3,119 |
| Indirect Injection | 99.96% | 99.95% | 99.96% | 27,001 |

Indirect Injection achieved the strongest class-level performance.

Direct Jailbreak had the lowest class-level F1 of the three primary classes, although its F1 remained above 94%.

---

## 6. Real-World Confusion Matrix

Rows represent actual classes and columns represent predicted classes.

| Actual \ Predicted | Safe | Direct Jailbreak | Indirect Injection |
|---|---:|---:|---:|
| Safe | 12,316 | 244 | 10 |
| Direct Jailbreak | 113 | 3,006 | 0 |
| Indirect Injection | 1 | 13 | 26,987 |

The largest confusion occurs between Safe and Direct Jailbreak.

Indirect Injection is very rarely confused with either of the other primary classes.

---

## 7. Real-World Per-Subtype Results

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

Persona Hijacking was the weakest-performing subtype with a meaningful number of real-world test examples:

- Correct: 184 / 218
- Errors: 34
- Accuracy: **84.40%**

Role Override achieved 88.89%, but this result is based on only 18 examples and should therefore be interpreted cautiously.

---

## 8. Synthetic Comparison Metrics

Dataset:

`synthetic_test.parquet`

Total examples:

**42,690**

| Metric | Result |
|---|---:|
| Accuracy | **98.91%** |
| Weighted Precision | **98.92%** |
| Weighted Recall | **98.91%** |
| Weighted F1 | **98.91%** |

The model correctly classified:

**42,225 / 42,690 examples**

and misclassified:

**465 / 42,690 examples**

The synthetic metrics are included for comparison and are not used as the headline project result.

---

## 9. Synthetic Per-Class Results

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Safe | 99.40% | 98.38% | 98.89% | 21,040 |
| Direct Jailbreak | 98.44% | 99.43% | 98.93% | 21,641 |
| Indirect Injection | 100.00% | 100.00% | 100.00% | 9 |

The synthetic dataset contains only **9 Indirect Injection examples**.

Therefore, the 100% result for this class should not be interpreted as evidence of perfect generalization.

---

## 10. Synthetic Confusion Matrix

Rows represent actual classes and columns represent predicted classes.

| Actual \ Predicted | Safe | Direct Jailbreak | Indirect Injection |
|---|---:|---:|---:|
| Safe | 20,699 | 341 | 0 |
| Direct Jailbreak | 124 | 21,517 | 0 |
| Indirect Injection | 0 | 0 | 9 |

---

## 11. Synthetic Per-Subtype Results

| Subtype | Correct | Total | Errors | Accuracy |
|---|---:|---:|---:|---:|
| Document Embedding | 9 | 9 | 0 | 100.00% |
| Persona Hijacking | 14 | 14 | 0 | 100.00% |
| Policy Evasion | 21,479 | 21,603 | 124 | 99.43% |
| System Prompt Overwrite | 24 | 24 | 0 | 100.00% |

Several synthetic subtype groups contain very few examples.

Their percentages should therefore always be interpreted together with their sample counts.

---

## 12. Real-World vs Synthetic Comparison

| Metric | Real-World Test | Synthetic Test |
|---|---:|---:|
| Accuracy | **99.11%** | 98.91% |
| Weighted Precision | **99.13%** | 98.92% |
| Weighted Recall | **99.11%** | 98.91% |
| Weighted F1 | **99.11%** | 98.91% |

The selected checkpoint performed strongly on both datasets.

Real-world test accuracy was approximately **0.20 percentage points higher** than synthetic test accuracy.

The two datasets have different class and subtype distributions.

In particular:

- Real-world Indirect Injection support: **27,001**
- Synthetic Indirect Injection support: **9**

Therefore, the two overall scores should be compared with their dataset compositions in mind.

The **real-world held-out test result remains the headline project result**.

---

## 13. Formal Target Check

The final project targets are checked against the **held-out real-world test set**.

| Performance Target | Required | Actual | Status |
|---|---:|---:|---|
| Accuracy | > 90% | **99.11%** | **PASS** |
| Weighted F1 | > 85% | **99.11%** | **PASS** |

### Accuracy Target

Required:

**> 90%**

Achieved:

**99.11%**

Status:

**PASS**

The achieved real-world accuracy exceeds the required target by approximately **9.11 percentage points**.

### F1 Target

Required:

**> 85%**

Achieved:

**99.11%**

Status:

**PASS**

The achieved weighted F1 exceeds the required target by approximately **14.11 percentage points**.

Both primary final performance targets were achieved.

---

## 14. Reproducibility

The final JSON files were generated directly from the selected checkpoint using the Task 30 evaluation pipeline.

### Real-World Metrics Generation

The real-world metrics were generated using:

```bash
python training/evaluate.py \
  --model-path "<checkpoint-path>" \
  --data-path "data/processed/test.parquet" \
  --batch-size 32 \
  --output "results/metrics_real.json"
```

This generated:

`ml/results/metrics_real.json`

### Synthetic Metrics Generation

The synthetic metrics were generated using:

```bash
python training/evaluate.py \
  --model-path "<checkpoint-path>" \
  --data-path "data/processed/synthetic_test.parquet" \
  --batch-size 32 \
  --output "results/metrics_synthetic.json"
```

This generated:

`ml/results/metrics_synthetic.json`

The metric values in the JSON files are machine-generated from model predictions and are not manually entered.

---

## 15. Evaluation Integrity

The following separation was maintained:

- Training data was used for model optimization.
- Validation data was used for model and hyperparameter selection.
- `checkpoint-28371` was selected before final test evaluation.
- The held-out real-world test set was not used for model selection.
- The synthetic test set was used only for comparison.
- No additional training was performed during Task 31.
- No fine-tuning was performed after examining test results.
- No checkpoint was reselected based on real-world or synthetic test performance.
- Final JSON metrics were regenerated directly from the already-selected checkpoint.

This preserves the integrity of the final evaluation.

---

## 16. Interpretation Notes

- The real-world result is used as the headline performance result.
- Overall metrics are weighted and therefore reflect dataset class distributions.
- Real-world and synthetic datasets have different class compositions.
- Subtype sample sizes vary substantially.
- Small subtype groups should not be judged from percentage alone.
- Persona Hijacking remains a comparatively difficult real-world subtype at 84.40% accuracy.
- Role Override contains only 18 real-world examples.
- Synthetic Indirect Injection contains only 9 examples.
- Web Content Injection achieved 100% accuracy on this specific real-world test set, but this does not imply perfect detection on every future example.
- High performance on the current held-out datasets does not guarantee identical performance on future unseen attacks.

---

## 17. Final Evaluation Summary

The selected PromptShield checkpoint:

`run_01/checkpoint-28371`

achieved the following final held-out real-world results:

- **Accuracy: 99.11%**
- **Weighted Precision: 99.13%**
- **Weighted Recall: 99.11%**
- **Weighted F1: 99.11%**

The synthetic comparison produced:

- **Accuracy: 98.91%**
- **Weighted Precision: 98.92%**
- **Weighted Recall: 98.91%**
- **Weighted F1: 98.91%**

Both formal project performance targets were achieved on the held-out real-world test set.

---

## 18. Task 31 Status

Task 31 is complete.

Completed items:

- Machine-generated real-world metrics JSON
- Machine-generated synthetic metrics JSON
- Full-precision final metrics committed to the repository
- Real-world performance record
- Synthetic comparison record
- Per-class results
- Confusion matrices
- Per-subtype results
- Formal accuracy target check
- Formal weighted F1 target check
- Reproducibility commands
- Evaluation integrity documentation
- Final performance summary

Final machine-readable result files:

- `ml/results/metrics_real.json`
- `ml/results/metrics_synthetic.json`

Final headline result:

**99.11% held-out real-world accuracy with 99.11% weighted F1.**