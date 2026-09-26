"""PromptShield inference wrapper.

Provides a backend-friendly classify(text) function using:
1. The primary 3-class PromptShield classifier.
2. The optional 8-class attack subtype classifier.

Models are loaded lazily and cached so they are not reloaded on every request.
"""

from __future__ import annotations

import os
from typing import Any

import torch
import torch.nn.functional as F
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from training.dataset import ID2LABEL
from training.subtype_dataset import ID2SUBTYPE


PRIMARY_MODEL_ENV = "PROMPTSHIELD_MODEL_PATH"
SUBTYPE_MODEL_ENV = "PROMPTSHIELD_SUBTYPE_MODEL_PATH"

MAX_LENGTH = 512


_primary_tokenizer = None
_primary_model = None

_subtype_tokenizer = None
_subtype_model = None


def _device() -> torch.device:
    """Return the best available inference device."""

    return torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )


def _get_required_env(name: str) -> str:
    """Read a required model path from the environment."""

    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Environment variable {name} is not set."
        )

    return value


def load_primary_model():
    """Load and cache the primary 3-class classifier."""

    global _primary_tokenizer
    global _primary_model

    if _primary_model is not None:
        return _primary_tokenizer, _primary_model

    model_path = _get_required_env(PRIMARY_MODEL_ENV)

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path
    )

    model.to(_device())
    model.eval()

    _primary_tokenizer = tokenizer
    _primary_model = model

    return tokenizer, model


def load_subtype_model():
    """Load and cache the optional 8-class subtype classifier."""

    global _subtype_tokenizer
    global _subtype_model

    if _subtype_model is not None:
        return _subtype_tokenizer, _subtype_model

    model_path = _get_required_env(SUBTYPE_MODEL_ENV)

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path
    )

    model.to(_device())
    model.eval()

    _subtype_tokenizer = tokenizer
    _subtype_model = model

    return tokenizer, model


def _predict(
    text: str,
    tokenizer,
    model,
) -> tuple[int, float]:
    """Return predicted class ID and confidence."""

    encoded = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    encoded = {
        key: value.to(_device())
        for key, value in encoded.items()
        if key != "token_type_ids"
    }

    with torch.no_grad():
        logits = model(**encoded).logits

    probabilities = F.softmax(
        logits,
        dim=-1,
    )

    confidence, predicted_id = torch.max(
        probabilities,
        dim=-1,
    )

    return (
        int(predicted_id.item()),
        float(confidence.item()),
    )


def classify(text: str) -> dict[str, Any]:
    """Classify one prompt using PromptShield.

    Returns a dictionary suitable for backend/API use.

    Safe prompts return:
        {
            "label": "Safe",
            "confidence": ...,
            "subtype": None,
            "subtype_confidence": None
        }

    Attack prompts run the subtype classifier only when the optional
    subtype model path is configured.

    If the subtype model is not configured, the primary attack result
    is still returned successfully with subtype fields set to None.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()

    if not text:
        raise ValueError("text must not be empty")

    primary_tokenizer, primary_model = load_primary_model()

    primary_id, primary_confidence = _predict(
        text,
        primary_tokenizer,
        primary_model,
    )

    label = ID2LABEL[primary_id]

    result = {
        "label": label,
        "confidence": primary_confidence,
        "subtype": None,
        "subtype_confidence": None,
    }

    if label == "Safe":
        return result

    # The subtype classifier is optional.
    # If no subtype checkpoint is configured, preserve the primary
    # attack detection instead of failing the whole request.
    if not os.getenv(SUBTYPE_MODEL_ENV):
        return result

    subtype_tokenizer, subtype_model = load_subtype_model()

    subtype_id, subtype_confidence = _predict(
        text,
        subtype_tokenizer,
        subtype_model,
    )

    result["subtype"] = ID2SUBTYPE[subtype_id]
    result["subtype_confidence"] = subtype_confidence

    return result


def reset_model_cache():
    """Clear cached models.

    Mainly useful for testing.
    """

    global _primary_tokenizer
    global _primary_model
    global _subtype_tokenizer
    global _subtype_model

    _primary_tokenizer = None
    _primary_model = None

    _subtype_tokenizer = None
    _subtype_model = None