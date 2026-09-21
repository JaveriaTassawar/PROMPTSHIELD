# PromptShield — Model Card

## 1. Model Overview

PromptShield is a DistilBERT-based text classification model developed to detect prompt-injection and jailbreak attacks against AI systems.

The primary classifier assigns an input prompt to one of three classes:

1. Safe
2. Direct Jailbreak
3. Indirect Injection

The selected model is based on:

`distilbert-base-uncased`

Final selected checkpoint:

`run_01/checkpoint-28371`

The checkpoint corresponds to Epoch 1 of the selected training run.

---

## 2. Intended Use

PromptShield is intended to act as a security classification component for systems that accept natural-language prompts.

The model can be used to identify whether an incoming prompt appears to be:

- Benign/safe
- A direct jailbreak attempt
- An indirect prompt-injection attempt

The classifier is intended to support the PromptShield application's prompt-analysis pipeline.

It should be treated as a detection component rather than a complete security solution.

---

## 3. Classification Taxonomy

### 3.1 Primary Classes

| ID | Class |
|---:|---|
| 0 | Safe |
| 1 | Direct Jailbreak |
| 2 | Indirect Injection |

The primary DistilBERT classifier predicts these three classes.

### 3.2 Attack Subtypes

The project taxonomy contains eight attack subtypes.

#### Direct Jailbreak

1. Policy Evasion
2. Multi-Turn Manipulation
3. Role Override
4. Persona Hijacking
5. System Prompt Overwrite

#### Indirect Injection

6. Document Embedding
7. Web Content Injection
8. Tool Output Injection

Safe prompts do not have an attack subtype.

The subtype field is retained in the dataset and is used for evaluation and analysis.

---

# 4. Dataset Sources

PromptShield was trained and evaluated using multiple public datasets rather than relying on a single prompt-injection dataset.

The data pipeline maps the different source schemas into a common format:

```text
text
label_3class
subtype
source
```

The source inventory includes benign prompts, real-world jailbreak attempts, synthetic jailbreaks, indirect prompt injections, multi-turn attacks, email/web-content attacks, and tool-output attacks.

---

## 4.1 Safe / Benign Sources

### Alpaca

File:

`alpaca_data.json`

Original rows:

**52,002**

The `instruction` field is used as the model input.

Primary label:

`Safe`

### TrustAIRLab Regular Prompts

File:

`train-00000-of-00001.parquet`

Original rows:

**13,735**

These are regular/non-jailbreak prompts from the TrustAIRLab dataset.

Primary label:

`Safe`

### WildJailbreak Benign Data

File:

`train.tsv`

Relevant categories:

- `vanilla_benign`
- `adversarial_benign`

Original benign rows:

**128,781**

Primary label:

`Safe`

### Completely Benign Dataset

File:

`Completely-Benign_Dataset.csv`

Original rows:

**1,200**

Primary label:

`Safe`

### JackHao Jailbreak Classification — Benign Rows

File:

`jackhhao_jailbreak_classification.csv`

Benign rows:

**1,332**

Primary label:

`Safe`

### Deepset Prompt Injections — Benign Rows

File:

`deepset_prompt_injections.parquet`

Rows with `label == 0`:

**343**

Primary label:

`Safe`

### Legacy Prompt Dataset — Benign

After deduplication, the legacy dataset contributes approximately:

**594 unique benign prompts**

The legacy dataset is treated as a minor contributor because of extensive duplication.

---

# 5. Direct Jailbreak Sources

## 5.1 Policy Evasion

Sources include:

### TrustAIRLab Jailbreak Prompts

Approximately:

**1,405 rows**

These contain real in-the-wild jailbreak attempts.

### WildJailbreak Harmful Data

Relevant categories include:

- `adversarial_harmful`
- `vanilla_harmful`

Original row counts:

- Adversarial harmful: **82,728**
- Vanilla harmful: **50,050**

### Legacy Prompt Dataset

Several legacy attack labels are mapped into Policy Evasion.

Because the legacy dataset contains extensive template duplication, it is treated as a minor source after deduplication.

---

## 5.2 Multi-Turn Manipulation

Sources include:

### SafeMTData Attack_600

File:

`Attack_600.json`

Contains:

**600 records / approximately 2,996 turns**

### SafeMTData 1K

File:

`SafeMTData_1K.json`

Contains:

**1,680 records**

### Harmful Dataset

File:

`Harmful%20Dataset.csv`

Contains:

**4,136 rows**

Multi-turn structures from these sources are normalized by the preprocessing adapters.

---

## 5.3 Role Override

Role Override was one of the thinnest attack subtypes in the available source data.

Sources include goal-hijacking and related role/authority manipulation examples from:

- ORQ red-team data
- Neuralchemy prompt-injection data
- Other mapped sources

This subtype remains an important limitation because substantially fewer examples were available compared with major categories such as Policy Evasion.

---

## 5.4 Persona Hijacking

Sources include:

- JackHao jailbreak classification data
- RubenD18 ChatGPT jailbreak prompts
- Legacy role-play/persona prompts

Examples include attacks that attempt to make the model adopt an alternative identity, persona, or unrestricted role.

---

## 5.5 System Prompt Overwrite

Sources include:

- JackHao jailbreak data
- Deepset prompt-injection examples
- Legacy instruction-override examples
- Neuralchemy prompt-injection data
- SLABS prompt-injection data

These prompts attempt to replace, ignore, overwrite, or supersede existing system instructions.

---

# 6. Indirect Injection Sources

## 6.1 Document Embedding

Primary source:

`dataset_for_huggingface.jsonl`

BIPIA dataset size:

**70,000 rows**

The dataset is balanced between injected and non-injected examples.

This is the strongest source for Document Embedding attacks.

---

## 6.2 Web Content Injection

Primary sources:

### Microsoft LLMail Phase 1

File:

`llmail_phase1.json`

Rows:

**160,741**

### Microsoft LLMail Phase 2

File:

`llmail_phase2.json`

Rows:

**37,303**

The preprocessing pipeline normalizes the different representations of attack labels and removes unclear examples.

---

## 6.3 Tool Output Injection

Sources include:

### NVIDIA Nemotron

File:

`train.jsonl`

Rows:

**1,272**

### InjecAgent-style Test Cases

Files:

- `test_cases_dh_enhanced.json`
- `test_cases_ds_enhanced.json`

Rows:

- **510**
- **544**

These examples represent malicious instructions embedded in tool outputs or agent interactions.

---

# 7. Additional Dataset Sources

Three additional sources were later added to strengthen underrepresented attack types:

### Neuralchemy Prompt Injection

File:

`neuralchemy_prompt_injection.parquet`

Rows:

**14,036**

Contains multiple attack families that are mapped onto the PromptShield taxonomy.

### SLABS Prompt Injection

File:

`slabs_prompt_injection.csv`

Rows:

**11,089**

Includes override-style injections and benign examples.

### Safeguard Prompt Injection

File:

`safeguard_prompt_injection.parquet`

Rows:

**8,236**

Provides additional binary injection/benign examples.

---

# 8. Deduplication

Deduplication was performed before model training.

This was particularly important because one legacy dataset contained approximately:

**2,000,000 raw rows**

but only approximately:

**1,041 unique prompt templates**

Training directly on those raw rows would allow the model to repeatedly observe the same templates and could produce misleadingly high evaluation scores.

Therefore, duplicate prompts were removed before downstream splitting and training.

After the expanded dataset sources were incorporated, the rebuilt clean dataset contained approximately:

**547,063 rows**

During that rebuild:

**12,025 duplicate rows were removed**

representing approximately:

**2.2% of the combined data at that stage**

The legacy two-million-row source was therefore treated only as a minor contributor after deduplication rather than allowing repeated templates to dominate training.

This deduplication step reduces the risk of reporting performance caused primarily by memorizing duplicated prompts.

---

# 9. Tokenization

Tokenizer:

`distilbert-base-uncased`

Maximum sequence length:

**512 tokens**

A stratified token-length analysis found approximately:

| Statistic | Tokens |
|---|---:|
| Median | 94 |
| 75th percentile | 273 |
| 90th percentile | 624 |
| 95th percentile | 747 |
| 99th percentile | 1,483 |
| Maximum observed | 3,923 |

At a maximum length of 512 tokens, approximately **15.3%** of sampled examples were truncated.

512 tokens is the architectural maximum for the selected DistilBERT model.

---

## 9.1 Long-Context Limitation

Several attack subtypes contain long prompts.

The tokenization analysis found approximately:

| Subtype | Median Tokens | Over 512 Tokens |
|---|---:|---:|
| Multi-Turn Manipulation | 547 | 55.0% |
| Persona Hijacking | 267 | 34.0% |
| Web Content Injection | 225 | 26.3% |
| Document Embedding | 312 | 23.0% |

Multi-Turn Manipulation is particularly affected because its median sequence length exceeds the model's 512-token context window.

As a result, later conversation turns may be truncated.

A longer-context transformer could reduce this limitation in a future version.

---

# 10. Training Configuration

Selected training configuration:

| Parameter | Value |
|---|---|
| Base model | `distilbert-base-uncased` |
| Learning rate | `2e-5` |
| Batch size | `16` |
| Selected epoch | `1` |
| Maximum sequence length | `512` |
| Class weights | Enabled |
| GPU | NVIDIA Tesla T4 |
| Training environment | Google Colab |

Training rows:

**453,935**

Validation rows:

**50,438**

---

# 11. Checkpoint Selection

Run 01 was trained for three epochs.

Validation loss was:

| Epoch | Validation Loss |
|---|---:|
| 1 | **0.05065** |
| 2 | 0.05366 |
| 3 | 0.05843 |

Validation loss increased after Epoch 1 while training loss continued to decrease.

This indicated overfitting beyond the first epoch.

Therefore:

`checkpoint-28371`

from Epoch 1 was selected as the final checkpoint rather than the Epoch 3 model.

A second tuning run using a learning rate of `1e-5` produced slightly weaker validation performance.

---

# 12. Validation Performance

The selected checkpoint was evaluated on:

`val.parquet`

Validation examples:

**50,438**

| Metric | Result |
|---|---:|
| Accuracy | **98.54%** |
| Weighted Precision | **98.55%** |
| Weighted Recall | **98.54%** |
| Weighted F1 | **98.54%** |

---

# 13. Held-Out Real-World Test Performance

The primary final evaluation was performed on:

`test.parquet`

Total examples:

**42,690**

This dataset was held out from model selection.

Final results:

| Metric | Result |
|---|---:|
| Accuracy | **99.11%** |
| Weighted Precision | **99.13%** |
| Weighted Recall | **99.11%** |
| Weighted F1 | **99.11%** |
| Macro F1 | **97.56%** |

### Macro F1

The held-out real-world test set achieved a **macro F1 of 97.56%**.

Unlike weighted F1, macro F1 gives each of the three classes equal importance regardless of class size. This provides an additional view of model performance because the real-world test set is not evenly distributed across the three classes.

Correct predictions:

**42,309 / 42,690**

Errors:

**381**

The **99.11% real-world accuracy and 99.11% weighted F1 are the headline PromptShield results**.

---

## 13.1 Per-Class Real-World Performance

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Safe | 99.08% | 97.98% | 98.53% | 12,570 |
| Direct Jailbreak | 92.12% | 96.38% | 94.20% | 3,119 |
| Indirect Injection | 99.96% | 99.95% | 99.96% | 27,001 |

Direct Jailbreak is comparatively more difficult than the other two primary classes.

## 13.2 False-Positive Analysis

The largest single error category on the held-out real-world test set was:

**Safe → Direct Jailbreak: 244 examples**

Out of the model's **381 total errors**, 244 were Safe prompts incorrectly classified as Direct Jailbreak.

This represents approximately **64.0% of all test-set errors**.

This is an important practical failure mode because these predictions are false positives: legitimate prompts may be blocked or flagged as attacks.

Other confusion-matrix errors were:

- Safe → Indirect Injection: 10
- Direct Jailbreak → Safe: 113
- Direct Jailbreak → Indirect Injection: 0
- Indirect Injection → Safe: 1
- Indirect Injection → Direct Jailbreak: 13

Therefore, although overall accuracy is high, the most common observed failure is the model being overly cautious and classifying some legitimate Safe prompts as Direct Jailbreak attempts.

---

# 14. Real-World Subtype Performance

| Subtype | Correct | Total | Accuracy |
|---|---:|---:|---:|
| Document Embedding | 4,971 | 4,984 | 99.74% |
| Multi-Turn Manipulation | 966 | 968 | 99.79% |
| Persona Hijacking | 184 | 218 | **84.40%** |
| Policy Evasion | 1,669 | 1,741 | 95.86% |
| Role Override | 16 | 18 | **88.89%** |
| System Prompt Overwrite | 171 | 174 | 98.28% |
| Tool Output Injection | 94 | 95 | 98.95% |
| Web Content Injection | 21,922 | 21,922 | 100.00% |

---

# 15. Weak and Underrepresented Subtypes

Overall accuracy alone does not represent every attack subtype equally.

## Persona Hijacking

Real-world accuracy:

**84.40%**

Correct:

**184 / 218**

Errors:

**34**

Persona Hijacking is the clearest weaker subtype with a meaningful test sample size.

## Role Override

Real-world accuracy:

**88.89%**

Correct:

**16 / 18**

Although the percentage is lower than the overall score, only 18 Role Override examples occur in the held-out real-world test set.

The percentage should therefore be interpreted cautiously.

Role Override was also one of the thinnest categories in the source dataset.

## System Prompt Overwrite

Real-world accuracy:

**98.28%**

Correct:

**171 / 174**

The current test performance is strong, but the subtype historically had fewer source examples than the largest categories and should continue to be monitored.

These subtype-level results are reported explicitly so weaknesses are not hidden behind the approximately 99% overall score.

---

# 16. Synthetic Test Performance

The selected checkpoint was also evaluated on:

`synthetic_test.parquet`

Total examples:

**42,690**

Results:

| Metric | Result |
|---|---:|
| Accuracy | **98.91%** |
| Weighted Precision | **98.92%** |
| Weighted Recall | **98.91%** |
| Weighted F1 | **98.91%** |

---

## 16.1 Synthetic Dataset Limitation

The synthetic test set contains only:

**9 Indirect Injection examples**

compared with:

**27,001 Indirect Injection examples**

in the real-world test set.

Therefore, the synthetic and real-world scores should not be treated as measurements from equivalent populations.

---

# 17. Real-World vs Synthetic Results

| Metric | Real-World | Synthetic |
|---|---:|---:|
| Accuracy | **99.11%** | 98.91% |
| Weighted Precision | **99.13%** | 98.92% |
| Weighted Recall | **99.11%** | 98.91% |
| Weighted F1 | **99.11%** | 98.91% |

In this experiment, the real-world test accuracy was approximately **0.20 percentage points higher** than the synthetic result.

The real-world score remains the headline metric because it measures performance on held-out real-world examples rather than serving only as a synthetic comparison.

---

# 18. Performance Targets

Primary project targets:

- Accuracy > 90%
- F1 > 0.85

Actual held-out real-world performance:

| Target | Required | Actual | Status |
|---|---:|---:|---|
| Accuracy | > 90% | **99.11%** | **PASS** |
| Weighted F1 | > 85% | **99.11%** | **PASS** |

The primary targets were achieved.

The documented fallback target of ≥80% accuracy was therefore **not required or used**.

---

# 19. Known Limitations

## 19.1 Context Length

DistilBERT accepts a maximum of 512 tokens.

Long multi-turn prompts may therefore be truncated.

Multi-Turn Manipulation is particularly affected.

## 19.2 Uneven Subtype Representation

The number of available examples varies substantially across attack subtypes.

Role Override remains especially underrepresented compared with categories such as Policy Evasion and Web Content Injection.

## 19.3 Persona Hijacking

Persona Hijacking achieved only **84.40%** accuracy on the real-world test set.

This is a known weakness of the selected checkpoint.

## 19.4 Dataset Distribution

Overall weighted metrics reflect the distribution of the evaluation dataset.

Strong performance on large categories can make overall metrics appear stronger than performance on smaller subtypes.

For this reason, per-class and per-subtype metrics are reported separately.

## 19.5 Future Attacks

High performance on the current held-out datasets does not guarantee identical performance on future jailbreak or prompt-injection techniques.

Attack strategies evolve, and future versions should be periodically evaluated on new real-world attack data.

## 19.6 Language Coverage

The selected base model is `distilbert-base-uncased`, which is primarily designed for English-language text.

Performance on non-English or heavily multilingual prompts has not been established by the current evaluation.

## 19.7 Role Override Subtype-Head Limitation

The secondary 8-class attack subtype classifier shows a significant limitation for the **Role Override** subtype.

Only **83 Role Override examples** were available in the training split. The evaluation sets also contained very few examples:

- Training: **83**
- Validation: **8**
- Held-out real-world test: **18**

The subtype classifier achieved:

- Validation F1: **0.00%**
- Held-out real-world F1: **0.00%**
- Validation correct predictions: **0 / 8**
- Held-out real-world correct predictions: **0 / 18**

On the held-out real-world test set, most Role Override examples were classified as **Policy Evasion**.

This indicates that the subtype classifier has not learned Role Override as a reliable distinct subtype. Although class weighting was applied during Task 34, weighting alone was not sufficient to compensate for the very small and limited Role Override training set.

Additional diverse, high-quality Role Override examples are therefore an important area for future improvement.

---

# 20. Evaluation Integrity

The following separation was maintained:

- Training data was used for model optimization.
- Validation data was used for model and hyperparameter selection.
- The final checkpoint was selected before test evaluation.
- The held-out real-world test set was not used for model selection.
- The synthetic test set was used only for comparison.
- No additional fine-tuning was performed after examining test results.
- The checkpoint was not reselected based on test-set performance.

Final metrics were generated directly from model predictions and committed as machine-readable JSON files:

- `results/metrics_real.json`
- `results/metrics_synthetic.json`

---

# 21. Reproducibility

Evaluation code:

`training/evaluate.py`

Real-world metrics can be regenerated with:

```bash
python training/evaluate.py \
  --model-path "<checkpoint-path>" \
  --data-path "data/processed/test.parquet" \
  --batch-size 32 \
  --output "results/metrics_real.json"
```

Synthetic metrics can be regenerated with:

```bash
python training/evaluate.py \
  --model-path "<checkpoint-path>" \
  --data-path "data/processed/synthetic_test.parquet" \
  --batch-size 32 \
  --output "results/metrics_synthetic.json"
```

Automated metric tests are located at:

`tests/test_evaluate.py`

Task 30 evaluation tests:

**4 passed**

---

# 22. Model Checkpoint

Selected checkpoint:

`run_01/checkpoint-28371`

The trained model weights are intentionally not committed to Git because of their size.

Checkpoint storage:

**Google Drive**

Shareable checkpoint link:

https://drive.google.com/drive/folders/1FHMfwe2MEiKZoB4f2M20WVbcG7OICXrd?usp=sharing

---

# 23. Safety and Responsible Use

PromptShield should be treated as an additional security layer rather than a guarantee that every malicious prompt will be detected.

A classification of `Safe` does not prove that an input is harmless.

Likewise, legitimate prompts may occasionally be classified as attacks.

The system should therefore be combined with:

- Application-level authorization
- Input validation
- Output filtering
- Tool permission controls
- System-prompt protections
- Logging and monitoring
- Human review where appropriate

The model should not be used as the sole security control for high-risk applications.

---

# 24. Final Model Summary

Model:

`distilbert-base-uncased`

Selected checkpoint:

`run_01/checkpoint-28371`

Primary task:

**3-class prompt security classification**

Classes:

- Safe
- Direct Jailbreak
- Indirect Injection

Attack taxonomy:

**8 subtypes**

Headline held-out real-world performance:

- **Accuracy: 99.11%**
- **Weighted Precision: 99.13%**
- **Weighted Recall: 99.11%**
- **Weighted F1: 99.11%**

Synthetic comparison:

- **Accuracy: 98.91%**
- **Weighted F1: 98.91%**

Primary project targets:

**Passed**

Known important limitations:

- Persona Hijacking performance
- Role Override data scarcity
- 512-token context limit
- Uneven subtype representation
- English-focused base model
- Unknown future attack patterns

The final model is suitable for continued integration and inference testing within the PromptShield project, subject to the limitations documented above.