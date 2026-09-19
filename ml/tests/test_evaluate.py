"""Tests for the PromptShield evaluation pipeline."""

import pandas as pd

from training.evaluate import compute_metrics


def test_compute_metrics_overall_and_confusion_matrix():
    """Overall accuracy and confusion matrix should be calculated correctly."""

    df = pd.DataFrame(
        {
            "text": ["a", "b", "c", "d"],
            "label_3class": [
                "Safe",
                "Direct Jailbreak",
                "Indirect Injection",
                "Safe",
            ],
        }
    )

    y_true = [0, 1, 2, 0]
    y_pred = [0, 1, 2, 1]

    metrics = compute_metrics(df, y_true, y_pred)

    assert metrics["overall"]["accuracy"] == 0.75

    assert metrics["confusion_matrix"] == [
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


def test_compute_metrics_per_class():
    """Per-class metrics should contain all three PromptShield classes."""

    df = pd.DataFrame(
        {
            "text": ["a", "b", "c"],
            "label_3class": [
                "Safe",
                "Direct Jailbreak",
                "Indirect Injection",
            ],
        }
    )

    y_true = [0, 1, 2]
    y_pred = [0, 1, 2]

    metrics = compute_metrics(df, y_true, y_pred)

    assert "Safe" in metrics["per_class"]
    assert "Direct Jailbreak" in metrics["per_class"]
    assert "Indirect Injection" in metrics["per_class"]

    assert metrics["overall"]["accuracy"] == 1.0
    assert metrics["overall"]["f1_weighted"] == 1.0


def test_compute_metrics_subtypes():
    """Subtype correct/error counts should be calculated correctly."""

    df = pd.DataFrame(
        {
            "text": ["a", "b", "c", "d"],
            "label_3class": [
                "Direct Jailbreak",
                "Direct Jailbreak",
                "Indirect Injection",
                "Indirect Injection",
            ],
            "subtype": [
                "Policy Evasion",
                "Policy Evasion",
                "Document Embedding",
                "Document Embedding",
            ],
        }
    )

    y_true = [1, 1, 2, 2]
    y_pred = [1, 0, 2, 2]

    metrics = compute_metrics(df, y_true, y_pred)

    policy = metrics["per_subtype"]["Policy Evasion"]

    assert policy["count"] == 2
    assert policy["correct"] == 1
    assert policy["errors"] == 1
    assert policy["accuracy"] == 0.5

    document = metrics["per_subtype"]["Document Embedding"]

    assert document["count"] == 2
    assert document["correct"] == 2
    assert document["errors"] == 0
    assert document["accuracy"] == 1.0


def test_no_subtype_column():
    """Evaluation should still work when subtype information is unavailable."""

    df = pd.DataFrame(
        {
            "text": ["a", "b"],
            "label_3class": [
                "Safe",
                "Direct Jailbreak",
            ],
        }
    )

    y_true = [0, 1]
    y_pred = [0, 1]

    metrics = compute_metrics(df, y_true, y_pred)

    assert "per_subtype" not in metrics
    assert metrics["overall"]["accuracy"] == 1.0