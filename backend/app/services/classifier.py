"""Bridge between the API and the ML inference wrapper.

Task 56. Wraps `ml/inference/classifier.py` so the router never imports
torch directly and never has to know where the model lives.

THE CENTRAL DECISION: THE IMPORT IS LAZY, AND ITS ABSENCE IS NOT FATAL.

The ML wrapper needs torch and transformers -- roughly 2 GB installed. The
backend venv does not have them, and should not be forced to:

  - the API's 215 tests run in under a minute precisely because nothing
    imports torch; adding it at module level would make every test session
    pay a multi-second import
  - Rana's frontend work needs a running API, not a working model
  - a deployment that only serves the dashboard does not need inference

So the import happens inside the function, on first use, and a missing
model is reported as **503 Service Unavailable** rather than crashing the
process at startup. 503 is the honest code: the endpoint exists and the
request was fine, but this capability is not currently available.

WHAT THIS MODULE GUARANTEES TO ITS CALLER

`classify_prompt()` either returns a complete `ClassificationResult` or
raises `ClassifierUnavailable`. It never returns a half-populated dict, and
it never lets a torch exception escape as a 500 -- the router has no way to
interpret one usefully.

SUB-TYPE AND GUIDANCE ARE OPTIONAL, BY EARLIER DESIGN

Task 35 made the sub-type model optional: `classify()` returns
`subtype=None` when `PROMPTSHIELD_SUBTYPE_MODEL_PATH` is unset, rather
than failing. Task 47 found the frontend renders its own avatar guidance
until Task 82. Both absences are normal and must not be treated as errors.

ROLE OVERRIDE IS FLAGGED, NOT HIDDEN

ML Task 34 measured the sub-type head at 0.00 F1 on Role Override -- never
predicted, with 14 of 18 landing as Policy Evasion. `subtype_reliable`
carries that forward so the API can qualify a sub-type rather than present
it with the same authority as the 3-class label.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.models.analysis import DEFAULT_SEVERITY_BY_TYPE, PROMPT_TYPES
from app.models.subtype import UNRELIABLE_SUBTYPES, is_valid_for

# ml/ sits beside backend/ in the repo, not inside it.
_ML_ROOT = Path(__file__).resolve().parents[3] / "ml"


class ClassifierUnavailable(RuntimeError):
    """The model cannot be used right now.

    Raised for a missing dependency, an unset model path, or a checkpoint
    that will not load. The router turns this into a 503.
    """


@dataclass(frozen=True)
class ClassificationResult:
    """What the API layer needs, already validated."""

    label: str
    confidence: float
    subtype: str | None = None
    subtype_confidence: float | None = None
    subtype_reliable: bool = True

    @property
    def is_attack(self) -> bool:
        return self.label != "Safe"

    @property
    def severity(self) -> str:
        """Default severity for this class, per Task 43's mapping.

        Task 57's mitigation logic may escalate to Critical.
        """
        return DEFAULT_SEVERITY_BY_TYPE[self.label]


def _load_classify():
    """Import the ML wrapper, raising ClassifierUnavailable on failure."""
    settings = get_settings()

    if not settings.model_path:
        raise ClassifierUnavailable(
            "No model configured. Set PROMPTSHIELD_MODEL_PATH to a "
            "checkpoint directory."
        )

    if str(_ML_ROOT) not in sys.path:
        sys.path.insert(0, str(_ML_ROOT))

    try:
        from inference.classifier import classify as _classify
    except ImportError as exc:
        # torch/transformers absent, or ml/ not present in this
        # deployment. Both mean the same thing to a caller.
        raise ClassifierUnavailable(
            f"The ML package could not be imported ({exc}). Install the "
            f"ml/requirements.txt dependencies to enable classification."
        ) from exc

    return _classify


def classify_prompt(text: str) -> ClassificationResult:
    """Classify one prompt.

    Raises:
        ClassifierUnavailable: the model is missing or unusable.
        ValueError: the wrapper returned something unrecognisable.
    """
    classify = _load_classify()

    try:
        raw = classify(text)
    except ClassifierUnavailable:
        raise
    except Exception as exc:
        # A checkpoint that will not load, a CUDA problem, a corrupt
        # tokenizer. The caller cannot act on the detail, and leaking a
        # torch traceback through the API would be worse than useless.
        raise ClassifierUnavailable(
            f"The classifier failed to run ({type(exc).__name__}). Check "
            f"the model path and the server logs."
        ) from exc

    label = raw.get("label")
    if label not in PROMPT_TYPES:
        # Guards the contract the Task 43 drift test also covers: if the
        # ML taxonomy changed, fail here with a clear message rather than
        # at the database CHECK constraint.
        raise ValueError(
            f"The classifier returned {label!r}, which is not one of "
            f"{PROMPT_TYPES}. The ML and backend label sets have drifted."
        )

    subtype = raw.get("subtype")

    # A sub-type that does not belong under this class is a bug upstream;
    # drop it rather than store an impossible pairing. See Task 44.
    if subtype is not None and not is_valid_for(subtype, label):
        subtype = None

    return ClassificationResult(
        label=label,
        confidence=float(raw.get("confidence", 0.0)),
        subtype=subtype,
        subtype_confidence=(
            float(raw["subtype_confidence"])
            if subtype is not None and raw.get("subtype_confidence") is not None
            else None
        ),
        subtype_reliable=subtype not in UNRELIABLE_SUBTYPES,
    )


def is_available() -> bool:
    """True if a classification request would be served.

    Used by /health so a misconfigured deployment is visible before the
    first analyse request rather than after it.
    """
    try:
        _load_classify()
        return True
    except ClassifierUnavailable:
        return False
