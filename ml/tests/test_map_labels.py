"""Safety net for the adapters in preprocessing/map_labels.py.

Task 17. If an adapter silently breaks later -- a renamed column, a changed
schema, a source re-downloaded in a different shape -- these tests catch it
before the damage reaches training.

Speed matters here, because a suite nobody runs protects nothing. Four of the
adapters read very large files (WildJailbreak 506 MB, llmail_phase1 427 MB,
llmail_phase2 65 MB, BIPIA 100 MB) and take minutes. They are marked `slow`
and skipped by default:

    pytest tests/ -v                 fast structural tests (seconds)
    pytest tests/ -v --slow          everything, including the big files

The fast set still covers all 3 classes and 7 of the 8 sub-types. Web Content
Injection comes only from llmail, so it is asserted in the slow set.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.map_labels import (  # noqa: E402
    ALL_ADAPTERS,
    DIRECT,
    INDIRECT,
    SAFE,
    SUBTYPES,
    adapt_bipia,
    adapt_llmail_phase1,
    adapt_llmail_phase2,
    adapt_wildjailbreak,
)

REQUIRED_KEYS = {"text", "label_3class", "subtype", "source"}
VALID_CLASSES = {SAFE, DIRECT, INDIRECT}

# Adapters that read the very large files.
SLOW_ADAPTERS = {
    adapt_wildjailbreak,
    adapt_llmail_phase1,
    adapt_llmail_phase2,
    adapt_bipia,
}
FAST_ADAPTERS = [a for a in ALL_ADAPTERS if a not in SLOW_ADAPTERS]


@pytest.fixture(scope="module")
def fast_rows() -> list[dict]:
    """Every record from the adapters that read small files."""
    rows: list[dict] = []
    for adapter in FAST_ADAPTERS:
        rows.extend(adapter())
    return rows


# --- 17.1 shape -----------------------------------------------------------
@pytest.mark.parametrize("adapter", FAST_ADAPTERS, ids=lambda a: a.__name__)
def test_adapter_returns_required_keys(adapter) -> None:
    """Every record carries exactly the four required keys, nothing more."""
    rows = adapter()
    assert rows, f"{adapter.__name__} returned no rows"
    for row in rows[:200]:
        assert set(row) == REQUIRED_KEYS, (
            f"{adapter.__name__} returned keys {sorted(row)}, "
            f"expected {sorted(REQUIRED_KEYS)}"
        )


@pytest.mark.parametrize("adapter", FAST_ADAPTERS, ids=lambda a: a.__name__)
def test_adapter_uses_valid_class_and_subtype(adapter) -> None:
    """Labels come from the taxonomy, not free text."""
    for row in adapter()[:200]:
        assert row["label_3class"] in VALID_CLASSES, (
            f"{adapter.__name__} produced class {row['label_3class']!r}"
        )
        if row["subtype"] is not None:
            assert row["subtype"] in SUBTYPES, (
                f"{adapter.__name__} produced subtype {row['subtype']!r}"
            )


# --- 17.2 all three classes ----------------------------------------------
def test_all_three_classes_present(fast_rows: list[dict]) -> None:
    found = {row["label_3class"] for row in fast_rows}
    assert found == VALID_CLASSES, f"missing classes: {VALID_CLASSES - found}"


# --- 17.3 sub-types, and Safe carries none -------------------------------
def test_safe_rows_have_no_subtype(fast_rows: list[dict]) -> None:
    """A Safe row with a sub-type means an adapter is mis-wired."""
    offenders = [
        r for r in fast_rows if r["label_3class"] == SAFE and r["subtype"] is not None
    ]
    assert not offenders, (
        f"{len(offenders)} Safe rows carry a sub-type, "
        f"first from {offenders[0]['source']}"
    )


def test_attack_rows_always_have_a_subtype(fast_rows: list[dict]) -> None:
    """Every Direct/Indirect row must be attributable to a sub-type."""
    offenders = [
        r for r in fast_rows if r["label_3class"] != SAFE and r["subtype"] is None
    ]
    assert not offenders, (
        f"{len(offenders)} attack rows have no sub-type, "
        f"first from {offenders[0]['source']}"
    )


def test_fast_adapters_cover_seven_subtypes(fast_rows: list[dict]) -> None:
    """The small sources supply every sub-type except Web Content Injection,
    which only llmail provides (asserted in the slow set)."""
    found = {r["subtype"] for r in fast_rows if r["subtype"]}
    missing = SUBTYPES - found - {"Web Content Injection"}
    assert not missing, f"sub-types missing from the fast set: {sorted(missing)}"


def test_thin_subtypes_are_still_present(fast_rows: list[dict]) -> None:
    """Role Override (158) and System Prompt Overwrite (279) are the smallest
    sub-types, so a mapping regression would wipe them out silently."""
    counts: dict[str, int] = {}
    for row in fast_rows:
        if row["subtype"]:
            counts[row["subtype"]] = counts.get(row["subtype"], 0) + 1
    assert counts.get("Role Override", 0) >= 100, (
        f"Role Override collapsed to {counts.get('Role Override', 0)}"
    )
    assert counts.get("System Prompt Overwrite", 0) >= 100, (
        f"System Prompt Overwrite collapsed to "
        f"{counts.get('System Prompt Overwrite', 0)}"
    )


# --- 17.4 no empty text ---------------------------------------------------
@pytest.mark.parametrize("adapter", FAST_ADAPTERS, ids=lambda a: a.__name__)
def test_no_empty_text(adapter) -> None:
    """Empty or whitespace-only text is useless for training."""
    for row in adapter()[:500]:
        assert row["text"].strip(), f"{adapter.__name__} produced an empty text field"


def test_text_meets_minimum_length(fast_rows: list[dict]) -> None:
    """map_labels filters anything under 10 characters; nothing should slip past."""
    short = [r for r in fast_rows if len(r["text"]) < 10]
    assert not short, (
        f"{len(short)} rows under 10 chars, first: {short[0]['text']!r} "
        f"from {short[0]['source']}"
    )


# --- slow set: the four large-file adapters -------------------------------
@pytest.mark.slow
@pytest.mark.parametrize("adapter", sorted(SLOW_ADAPTERS, key=lambda a: a.__name__),
                         ids=lambda a: a.__name__)
def test_slow_adapter_shape(adapter) -> None:
    rows = adapter()
    assert rows, f"{adapter.__name__} returned no rows"
    for row in rows[:200]:
        assert set(row) == REQUIRED_KEYS
        assert row["label_3class"] in VALID_CLASSES
        assert row["text"].strip()


@pytest.mark.slow
def test_llmail_supplies_web_content_injection() -> None:
    """The one sub-type the fast set cannot cover."""
    rows = adapt_llmail_phase2()
    assert rows, "llmail_phase2 returned no rows"
    assert {r["subtype"] for r in rows} == {"Web Content Injection"}


@pytest.mark.slow
def test_llmail_drops_unclear_rows() -> None:
    """attack_attempt has four forms including 'Unclear'; only true attacks
    are kept. A regression here would pull ambiguous rows into training."""
    import json

    from preprocessing.map_labels import RAW_DIR

    with open(RAW_DIR / "llmail_phase2.json", encoding="utf-8") as handle:
        raw = json.load(handle)

    total = len(raw)
    kept = len(adapt_llmail_phase2())
    assert kept < total, "no rows were filtered -- the Unclear/False filter is not running"
