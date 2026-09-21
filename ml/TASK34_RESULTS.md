# Task 34 — Attack Subtype Classifier

## 1. Purpose

Task 34 implements and evaluates a secondary PromptShield classifier for identifying the specific attack subtype after a prompt has been identified as an attack.

Unlike the primary PromptShield classifier, which predicts:

- Safe
- Direct Jailbreak
- Indirect Injection

the Task 34 classifier operates only on attack examples and predicts one of eight attack subtypes.

Safe examples are excluded from subtype training and evaluation.

---

## 2. Subtype Taxonomy

The subtype classifier predicts the following eight classes:

| ID | Subtype |
|---:|---|
| 0 | Policy Evasion |
| 1 | Multi-Turn Manipulation |
| 2 | Role Override |
| 3 | Persona Hijacking |
| 4 | System Prompt Overwrite |
| 5 | Document Embedding |
| 6 | Web Content Injection |
| 7 | Tool Output Injection |

The mapping is explicitly defined in code and is not derived from dataframe or alphabetical ordering.

---

## 3. Dataset Filtering

Task 34 uses the existing PromptShield train, validation, and test splits.

Only rows whose primary class is:

- `Direct Jailbreak`
- `Indirect Injection`

are retained.

Rows labelled `Safe` are excluded.

Rows with missing or unrecognized subtype labels are also excluded.

This produces a dedicated attack-only dataset for the 8-class subtype classification task.

---

## 4. Training Distribution

Total attack-only training examples:

**273,515**

| Subtype | Training Examples |
|---|---:|
| Policy Evasion | 128,243 |
| Multi-Turn Manipulation | 4,992 |
| Role Override | **83** |
| Persona Hijacking | 1,326 |
| System Prompt Overwrite | 1,083 |
| Document Embedding | 26,072 |
| Web Content Injection | 111,213 |
| Tool Output Injection | 503 |
| **Total** | **273,515** |

The subtype dataset is highly imbalanced.

Policy Evasion and Web Content Injection account for most training examples, while Role Override contains only **83 training examples**.

---

## 5. Validation Distribution

Total attack-only validation examples:

**30,391**

| Subtype | Validation Examples |
|---|---:|
| Policy Evasion | 14,278 |
| Multi-Turn Manipulation | 517 |
| Role Override | **8** |
| Persona Hijacking | 154 |
| System Prompt Overwrite | 124 |
| Document Embedding | 3,033 |
| Web Content Injection | 12,219 |
| Tool Output Injection | 58 |
| **Total** | **30,391** |

Role Override remains extremely small in the validation split.

---

## 6. Class-Imbalance Handling

Because subtype frequencies vary substantially, weighted cross-entropy was used during training.

Raw inverse-frequency weighting was not used because the difference between the largest and smallest subtype is extreme.

Instead, square-root moderated inverse-frequency weighting was calculated from the training distribution.

The resulting weights were:

| Subtype | Weight |
|---|---:|
| Policy Evasion | 0.0937 |
| Multi-Turn Manipulation | 0.4751 |
| Role Override | **3.6843** |
| Persona Hijacking | 0.9218 |
| System Prompt Overwrite | 1.0200 |
| Document Embedding | 0.2079 |
| Web Content Injection | 0.1007 |
| Tool Output Injection | 1.4966 |

Rare subtypes therefore receive additional influence during optimization without using the much more extreme raw inverse-frequency ratios.

---

## 7. Smoke Test

Before full GPU training, the subtype training pipeline was smoke-tested using a small balanced subset.

Smoke-test training examples:

**32**

Smoke-test validation examples:

**16**

Results:

- Train loss: approximately **2.072**
- Validation loss: approximately **2.041**
- Training completed successfully
- Validation completed successfully
- Model checkpoint saved successfully

For an untrained 8-class classifier, uniform cross-entropy is approximately `ln(8) ≈ 2.079`.

The smoke-test losses were therefore reasonable for the tiny test run.

The purpose of the smoke test was to validate the training pipeline rather than measure classifier performance.

---

## 8. Full Training Configuration

The subtype classifier was trained using:

| Parameter | Value |
|---|---|
| Base model | `distilbert-base-uncased` |
| Number of classes | 8 |
| Epochs | 1 |
| Learning rate | `2e-5` |
| Batch size | 16 |
| Maximum sequence length | 512 |
| Loss | Weighted cross-entropy |
| Weighting strategy | Square-root moderated inverse frequency |
| GPU | NVIDIA Tesla T4 |
| Training environment | Google Colab |
| Training examples | 273,515 |
| Validation examples | 30,391 |

Training required approximately **68 minutes** on the T4 GPU.

---

## 9. Training Result

Full training completed successfully.

Final training loss:

**0.09669**

Validation loss:

**0.05839**

The trained model was saved to Google Drive at:

`PromptShield/checkpoints/subtype_run_01/final`

---

# 10. Validation Evaluation

The trained subtype classifier was first evaluated on the attack-only validation split.

## 10.1 Overall Validation Metrics

| Metric | Result |
|---|---:|
| Accuracy | **99.70%** |
| Macro F1 | **83.47%** |
| Weighted F1 | **99.68%** |

The difference between weighted F1 and macro F1 is important.

Weighted F1 is dominated by the large subtype classes, whereas macro F1 gives each of the eight subtypes equal importance.

The lower macro F1 therefore reveals weaknesses that are not visible from overall accuracy alone.

---

## 10.2 Validation Per-Subtype Metrics

| Subtype | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Policy Evasion | 99.55% | 99.86% | **99.70%** | 14,278 |
| Multi-Turn Manipulation | 99.80% | 98.65% | **99.22%** | 517 |
| Role Override | **0.00%** | **0.00%** | **0.00%** | 8 |
| Persona Hijacking | 93.71% | 87.01% | **90.24%** | 154 |
| System Prompt Overwrite | 88.57% | 75.00% | **81.22%** | 124 |
| Document Embedding | 99.97% | 99.84% | **99.90%** | 3,033 |
| Web Content Injection | 100.00% | 100.00% | **100.00%** | 12,219 |
| Tool Output Injection | 95.08% | 100.00% | **97.48%** | 58 |

---

## 10.3 Validation Confusion Matrix

Rows represent actual subtype and columns represent predicted subtype in the fixed subtype order.

```text
[[14258,    1,    0,    8,    9,    1,     0,    1],
 [    7,  510,    0,    0,    0,    0,     0,    0],
 [    7,    0,    0,    0,    0,    0,     0,    1],
 [   18,    0,    0,  134,    2,    0,     0,    0],
 [   29,    0,    0,    1,   93,    0,     0,    1],
 [    4,    0,    0,    0,    1, 3028,     0,    0],
 [    0,    0,    0,    0,    0,    0, 12219,    0],
 [    0,    0,    0,    0,    0,    0,     0,   58]]
```

---

# 11. Held-Out Real-World Test Evaluation

The subtype classifier was then evaluated on the attack examples contained in the held-out real-world `test.parquet` split.

This test data was not used to train the subtype classifier.

## 11.1 Overall Real-World Metrics

| Metric | Result |
|---|---:|
| Accuracy | **99.52%** |
| Macro F1 | **82.83%** |
| Weighted F1 | **99.48%** |

The held-out result closely follows the validation pattern.

Overall accuracy and weighted F1 are extremely high, while macro F1 is substantially lower because performance is uneven across the eight subtypes.

---

## 11.2 Real-World Per-Subtype Metrics

| Subtype | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Policy Evasion | 94.32% | 98.28% | **96.26%** | 1,741 |
| Multi-Turn Manipulation | 100.00% | 99.07% | **99.53%** | 968 |
| Role Override | **0.00%** | **0.00%** | **0.00%** | 18 |
| Persona Hijacking | 93.40% | 84.40% | **88.67%** | 218 |
| System Prompt Overwrite | 85.43% | 74.14% | **79.38%** | 174 |
| Document Embedding | 99.88% | 99.84% | **99.86%** | 4,984 |
| Web Content Injection | 100.00% | 100.00% | **100.00%** | 21,922 |
| Tool Output Injection | 98.95% | 98.95% | **98.95%** | 95 |

---

## 11.3 Real-World Confusion Matrix

Rows represent actual subtype and columns represent predicted subtype.

```text
[[ 1711,    0,    0,    7,   18,    5,     0,    0],
 [    9,  959,    0,    0,    0,    0,     0,    0],
 [   14,    0,    0,    0,    2,    1,     0,    1],
 [   33,    0,    0,  184,    1,    0,     0,    0],
 [   39,    0,    0,    6,  129,    0,     0,    0],
 [    7,    0,    0,    0,    1, 4976,     0,    0],
 [    0,    0,    0,    0,    0,    0, 21922,    0],
 [    1,    0,    0,    0,    0,    0,     0,   94]]
```

---

# 12. Role Override Failure

Role Override is the clearest limitation of the subtype classifier.

Available examples:

| Split | Examples |
|---|---:|
| Training | **83** |
| Validation | **8** |
| Held-out real-world test | **18** |

Performance:

| Split | Correct | Recall / Accuracy |
|---|---:|---:|
| Validation | **0 / 8** | **0.00%** |
| Real-world test | **0 / 18** | **0.00%** |

On the held-out test set, the 18 Role Override examples were predicted as:

- Policy Evasion: **14**
- System Prompt Overwrite: **2**
- Document Embedding: **1**
- Tool Output Injection: **1**
- Role Override: **0**

The model therefore did not learn Role Override as a reliable distinct subtype.

This result is consistent with the severe shortage of Role Override training examples.

Class weighting increased the influence of Role Override examples during optimization, but weighting alone could not compensate for the limited number and diversity of available examples.

Additional high-quality Role Override data is the most direct future improvement for this subtype.

---

# 13. System Prompt Overwrite

System Prompt Overwrite is the second weakest subtype on the held-out test set.

Results:

- Precision: **85.43%**
- Recall: **74.14%**
- F1: **79.38%**
- Support: **174**

The confusion matrix shows that many System Prompt Overwrite examples were classified as Policy Evasion.

This indicates overlap between the language used in general policy-evasion attacks and instructions attempting to overwrite system behavior.

---

# 14. Persona Hijacking

Persona Hijacking achieved:

- Precision: **93.40%**
- Recall: **84.40%**
- F1: **88.67%**
- Support: **218**

Performance is substantially stronger than Role Override but remains below the dominant attack subtypes.

The model missed 34 Persona Hijacking examples on the held-out real-world test set.

---

# 15. Strongest Subtypes

Several subtypes achieved very strong held-out performance.

### Web Content Injection

F1:

**100.00%**

Support:

**21,922**

### Document Embedding

F1:

**99.86%**

Support:

**4,984**

### Multi-Turn Manipulation

F1:

**99.53%**

Support:

**968**

### Tool Output Injection

F1:

**98.95%**

Support:

**95**

These results should still be interpreted together with each subtype's sample size and dataset characteristics.

---

# 16. Why Macro F1 Matters

The subtype classifier achieved:

- Accuracy: **99.52%**
- Weighted F1: **99.48%**
- Macro F1: **82.83%**

The approximately 16.65 percentage-point difference between weighted F1 and macro F1 reflects the severe imbalance of the subtype dataset.

Large classes such as:

- Policy Evasion
- Web Content Injection
- Document Embedding

perform extremely well and dominate weighted metrics.

Macro F1 gives every subtype equal weight and therefore exposes the complete failure on Role Override and weaker performance on System Prompt Overwrite.

For this task, macro F1 and per-subtype results provide important context alongside overall accuracy.

---

# 17. Relationship to the Primary Classifier

The Task 34 subtype classifier does **not** replace the primary PromptShield classifier.

The primary model predicts:

```text
Safe
Direct Jailbreak
Indirect Injection
```

The subtype model is intended as a secondary classification stage for prompts identified as attacks.

Conceptually:

```text
Input Prompt
     |
     v
Primary 3-Class Classifier
     |
     +---- Safe
     |
     +---- Direct Jailbreak ----+
     |                          |
     +---- Indirect Injection --+
                                |
                                v
                       8-Class Subtype
                          Classifier
```

The primary and subtype evaluation results must therefore be reported separately.

---

# 18. Known Limitations

## 18.1 Severe Class Imbalance

Subtype training data ranges from:

**83 Role Override examples**

to:

**128,243 Policy Evasion examples**

This is an extreme imbalance.

Moderated class weighting helps but cannot replace missing data diversity.

## 18.2 Role Override

Role Override achieved 0% recall on both validation and held-out real-world evaluation.

This subtype should not currently be considered reliably classified.

## 18.3 System Prompt Overwrite

System Prompt Overwrite achieved only 74.14% recall and 79.38% F1 on the held-out test set.

## 18.4 Context Length

The classifier inherits DistilBERT's 512-token maximum context length.

Long Multi-Turn Manipulation and other long-context examples may be truncated.

## 18.5 Weighted Metrics

Weighted accuracy/F1 can hide weak rare classes.

Macro F1 and individual subtype metrics must therefore be considered when evaluating this classifier.

## 18.6 Future Attack Patterns

Performance on the current datasets does not guarantee equivalent performance on new or previously unseen attack techniques.

---

# 19. Implementation

Task 34 adds:

`training/subtype_dataset.py`

Responsibilities:

- Exclude Safe rows
- Validate subtype labels
- Apply fixed 8-class mapping
- Tokenize examples
- Produce integer subtype targets
- Report subtype counts

Task 34 also adds:

`training/train_subtype.py`

Responsibilities:

- Build the 8-class DistilBERT model
- Calculate moderated class weights
- Apply weighted cross-entropy
- Support smoke testing
- Train and validate the subtype model
- Save the final checkpoint

Evaluation is implemented in:

`training/evaluate_subtype.py`

Responsibilities:

- Load a trained subtype checkpoint
- Evaluate attack-only data
- Calculate accuracy
- Calculate macro F1
- Calculate weighted F1
- Calculate precision/recall/F1 per subtype
- Generate the 8x8 confusion matrix
- Export machine-readable JSON metrics

---

# 20. Reproducibility

Full subtype training was performed using:

```bash
python -m training.train_subtype \
  --train-path "data/processed/train.parquet" \
  --val-path "data/processed/val.parquet" \
  --output-dir "<checkpoint-output>" \
  --epochs 1 \
  --batch-size 16 \
  --learning-rate 2e-5
```

Validation evaluation:

```bash
python -m training.evaluate_subtype \
  --model-path "<subtype-checkpoint>" \
  --data-path "data/processed/val.parquet" \
  --batch-size 32 \
  --output "subtype_val_metrics.json"
```

Held-out real-world evaluation:

```bash
python -m training.evaluate_subtype \
  --model-path "<subtype-checkpoint>" \
  --data-path "data/processed/test.parquet" \
  --batch-size 32 \
  --output "subtype_test_metrics.json"
```

---

# 21. Final Task 34 Summary

Task 34 successfully implemented and trained an **8-class attack subtype classifier**.

Held-out real-world performance:

| Metric | Result |
|---|---:|
| Accuracy | **99.52%** |
| Weighted F1 | **99.48%** |
| Macro F1 | **82.83%** |

The classifier performs extremely well on several well-represented subtypes, including Web Content Injection, Document Embedding, and Multi-Turn Manipulation.

However, performance is not uniform across the taxonomy.

The most important limitation is:

**Role Override — 0.00% F1 on 18 held-out examples.**

System Prompt Overwrite is also comparatively weak at:

**79.38% F1.**

These results demonstrate why subtype-level and macro-averaged evaluation is necessary alongside overall accuracy.

Task 34 is therefore considered complete as a stretch implementation, with the Role Override data shortage documented as a known limitation and future improvement area.