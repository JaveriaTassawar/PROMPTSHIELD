"""Turn every raw dataset into one uniform labelled shape.

Task 16. Each source has its own format, so each gets its own adapter. Every
adapter returns a list of records shaped:

    {"text": str, "label_3class": str, "subtype": str | None, "source": str}

The taxonomy is 3 top-level classes and 8 sub-types (ml/TASKS.md section 1).
Safe rows carry subtype=None; every attack row carries one of the eight.

Field names below were confirmed by reading the actual files, not assumed.

Run:  python preprocessing/map_labels.py     (prints a per-adapter summary)
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

csv.field_size_limit(10**9)  # single prompt fields can be very long

# --- 16.1 the three top-level classes -------------------------------------
SAFE = "Safe"
DIRECT = "Direct Jailbreak"
INDIRECT = "Indirect Injection"

# --- the eight sub-types --------------------------------------------------
POLICY_EVASION = "Policy Evasion"
MULTI_TURN = "Multi-Turn Manipulation"
ROLE_OVERRIDE = "Role Override"
PERSONA_HIJACKING = "Persona Hijacking"
SYSTEM_PROMPT_OVERWRITE = "System Prompt Overwrite"
DOCUMENT_EMBEDDING = "Document Embedding"
WEB_CONTENT_INJECTION = "Web Content Injection"
TOOL_OUTPUT_INJECTION = "Tool Output Injection"

SUBTYPES = {
    POLICY_EVASION, MULTI_TURN, ROLE_OVERRIDE, PERSONA_HIJACKING,
    SYSTEM_PROMPT_OVERWRITE, DOCUMENT_EMBEDDING, WEB_CONTENT_INJECTION,
    TOOL_OUTPUT_INJECTION,
}

MIN_CHARS = 10  # shorter than this is not a usable training example


def record(text: str, label: str, subtype: str | None, source: str) -> dict:
    return {
        "text": text.strip(),
        "label_3class": label,
        "subtype": subtype,
        "source": source,
    }


def _usable(text: object) -> bool:
    return isinstance(text, str) and len(text.strip()) >= MIN_CHARS


# --------------------------------------------------------------------------
# Splitting jailbreak prompts into persona vs override
#
# Measured on the 666 jackhhao jailbreak rows: 500 match persona wording, 149
# match override wording, but 125 match BOTH and 142 match NEITHER. The plan's
# rough ~530/~143 split assumed no overlap, so a precedence rule is needed.
#
# Persona wins ties: a DAN-style prompt that also says "ignore your rules" is
# still fundamentally a persona hijack -- the assumed identity is the payload,
# the override clause just supports it. Rows matching neither are real
# jailbreaks too, so they go to Policy Evasion rather than being discarded.
# --------------------------------------------------------------------------
PERSONA_RE = re.compile(
    r"you are (now )?(a|an|going)|pretend|act as|persona|stay in character"
    r"|\bDAN\b|roleplay|role-play|simulator|character named",
    re.I,
)
OVERRIDE_RE = re.compile(
    r"ignore (all |any )?(previous|prior|above|the)|disregard"
    r"|forget (everything|all|your)|no longer (apply|bound)"
    r"|new instructions|override",
    re.I,
)


def classify_jailbreak(text: str) -> str:
    """Pick a Direct Jailbreak sub-type for a free-text jailbreak prompt."""
    if PERSONA_RE.search(text):
        return PERSONA_HIJACKING
    if OVERRIDE_RE.search(text):
        return SYSTEM_PROMPT_OVERWRITE
    return POLICY_EVASION


# --- 16.2 Safe: alpaca -----------------------------------------------------
def adapt_alpaca() -> list[dict]:
    with open(RAW_DIR / "alpaca_data.json", encoding="utf-8") as handle:
        data = json.load(handle)
    return [
        record(row["instruction"], SAFE, None, "alpaca")
        for row in data
        if _usable(row.get("instruction"))
    ]


# --- 16.3 TrustAIRLab in-the-wild parquets --------------------------------
def adapt_trustairlab_regular() -> list[dict]:
    import pandas as pd

    frame = pd.read_parquet(RAW_DIR / "train-00000-of-00001.parquet")
    return [
        record(p, SAFE, None, "trustairlab_regular")
        for p in frame["prompt"]
        if _usable(p)
    ]


def adapt_trustairlab_jailbreak() -> list[dict]:
    import pandas as pd

    # Space and brackets in the filename -- always an exact string, never a glob.
    frame = pd.read_parquet(RAW_DIR / "train-00000-of-00001 (1).parquet")
    return [
        record(p, DIRECT, classify_jailbreak(p), "trustairlab_jailbreak")
        for p in frame["prompt"]
        if _usable(p)
    ]


# --- 16.4 WildJailbreak ----------------------------------------------------
def adapt_wildjailbreak() -> list[dict]:
    """Column depends on data_type: vanilla_* uses `vanilla`, adversarial_*
    uses `adversarial`. The unused column is frequently empty."""
    out: list[dict] = []
    path = RAW_DIR / "train.tsv"
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            data_type = (row.get("data_type") or "").strip()
            text = row.get("vanilla") if data_type.startswith("vanilla") else row.get("adversarial")
            if not _usable(text):
                continue
            if data_type.endswith("benign"):
                out.append(record(text, SAFE, None, "wildjailbreak"))
            elif data_type.endswith("harmful"):
                out.append(record(text, DIRECT, POLICY_EVASION, "wildjailbreak"))
    return out


# --- 16.5 SafeMTData (two different schemas) ------------------------------
def adapt_safemt_attack600() -> list[dict]:
    """multi_turn_queries is a list of strings -- join into one conversation."""
    with open(RAW_DIR / "Attack_600.json", encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for row in data:
        turns = [t for t in row.get("multi_turn_queries", []) if _usable(t)]
        if turns:
            out.append(record("\n".join(turns), DIRECT, MULTI_TURN, "safemt_attack600"))
    return out


def adapt_safemt_1k() -> list[dict]:
    """conversations is a list of {role, content} -- keep the user turns."""
    with open(RAW_DIR / "SafeMTData_1K.json", encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for row in data:
        turns = [
            m["content"]
            for m in row.get("conversations", [])
            if m.get("role") == "user" and _usable(m.get("content"))
        ]
        if turns:
            out.append(record("\n".join(turns), DIRECT, MULTI_TURN, "safemt_1k"))
    return out


# --- 16.6 orq redteam: Role Override --------------------------------------
def adapt_orq() -> list[dict]:
    with open(RAW_DIR / "redteam_dataset.v2.json", encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for sample in data.get("samples", []):
        if sample.get("input", {}).get("vulnerability") != "goal_hijacking":
            continue
        turns = [
            m["content"]
            for m in sample.get("messages", [])
            if m.get("role") == "user" and _usable(m.get("content"))
        ]
        if turns:
            out.append(record("\n".join(turns), DIRECT, ROLE_OVERRIDE, "orq_redteam"))
    return out


# --- 16.7 Microsoft llmail: Web Content Injection -------------------------
def _llmail(filename: str, source: str) -> list[dict]:
    """attack_attempt appears as 'True', 'False', 'Unclear' and boolean True.
    Normalise all four; keep only confirmed attacks, drop 'Unclear'."""
    with open(RAW_DIR / filename, encoding="utf-8") as handle:
        data = json.load(handle)
    out = []
    for email_text, meta in data.items():
        if not isinstance(meta, dict):
            continue
        flag = meta.get("attack_attempt")
        flag = flag.strip().lower() if isinstance(flag, str) else flag
        if flag is not True and flag != "true":  # excludes 'unclear' and false
            continue
        if _usable(email_text):
            out.append(record(email_text, INDIRECT, WEB_CONTENT_INJECTION, source))
    return out


def adapt_llmail_phase1() -> list[dict]:
    return _llmail("llmail_phase1.json", "llmail_phase1")


def adapt_llmail_phase2() -> list[dict]:
    return _llmail("llmail_phase2.json", "llmail_phase2")


# --- 16.8 BIPIA: Document Embedding ---------------------------------------
def adapt_bipia() -> list[dict]:
    """label == 1 is the injected document. Balanced 35k/35k in the file."""
    out = []
    with open(RAW_DIR / "dataset_for_huggingface.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("label")) != "1":
                continue
            if _usable(row.get("context")):
                out.append(
                    record(row["context"], INDIRECT, DOCUMENT_EMBEDDING, "bipia")
                )
    return out


# --- 16.9 Tool Output Injection (three sources) ---------------------------
def adapt_nemotron() -> list[dict]:
    """`injection` is a dict; its `goal` holds the injected instruction."""
    out = []
    with open(RAW_DIR / "train.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            injection = json.loads(line).get("injection")
            goal = injection.get("goal") if isinstance(injection, dict) else injection
            if _usable(goal):
                out.append(record(goal, INDIRECT, TOOL_OUTPUT_INJECTION, "nemotron"))
    return out


def _injecagent(filename: str, source: str) -> list[dict]:
    with open(RAW_DIR / filename, encoding="utf-8") as handle:
        data = json.load(handle)
    return [
        record(row["Attacker Instruction"], INDIRECT, TOOL_OUTPUT_INJECTION, source)
        for row in data
        if _usable(row.get("Attacker Instruction"))
    ]


def adapt_injecagent_dh() -> list[dict]:
    return _injecagent("test_cases_dh_enhanced.json", "injecagent_dh")


def adapt_injecagent_ds() -> list[dict]:
    return _injecagent("test_cases_ds_enhanced.json", "injecagent_ds")


# --- 16.10 the remaining sources ------------------------------------------
def adapt_jackhhao() -> list[dict]:
    """Columns: prompt, type ('benign' | 'jailbreak')."""
    out = []
    with open(RAW_DIR / "jackhhao_jailbreak_classification.csv", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            text = row.get("prompt")
            if not _usable(text):
                continue
            if row.get("type") == "benign":
                out.append(record(text, SAFE, None, "jackhhao"))
            elif row.get("type") == "jailbreak":
                out.append(record(text, DIRECT, classify_jailbreak(text), "jackhhao"))
    return out


def adapt_rubend18() -> list[dict]:
    """79 named ChatGPT jailbreak personas (DAN, DUDE, APOPHIS...)."""
    out = []
    # utf-8-sig: the file carries a BOM, which would corrupt the first header.
    with open(RAW_DIR / "rubend18_chatgpt_jailbreak_prompts.csv", encoding="utf-8-sig") as h:
        for row in csv.DictReader(h):
            text = row.get("Prompt")
            if _usable(text):
                out.append(record(text, DIRECT, classify_jailbreak(text), "rubend18"))
    return out


def adapt_deepset() -> list[dict]:
    """Columns: text, label (0 = benign, 1 = injection)."""
    import pandas as pd

    frame = pd.read_parquet(RAW_DIR / "deepset_prompt_injections.parquet")
    out = []
    for text, label in zip(frame["text"], frame["label"]):
        if not _usable(text):
            continue
        if int(label) == 0:
            out.append(record(text, SAFE, None, "deepset"))
        else:
            out.append(record(text, DIRECT, classify_jailbreak(text), "deepset"))
    return out


def adapt_tomgibbs_benign() -> list[dict]:
    out = []
    with open(RAW_DIR / "Completely-Benign_Dataset.csv", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            text = row.get("Prompt")
            if _usable(text):
                out.append(record(text, SAFE, None, "tomgibbs_benign"))
    return out


def adapt_tomgibbs_harmful() -> list[dict]:
    """Has both `Prompt` and `Multi-turn conversation`; both fully populated.
    The multi-turn column is what makes these Multi-Turn Manipulation."""
    out = []
    with open(RAW_DIR / "Harmful%20Dataset.csv", encoding="utf-8") as h:
        for row in csv.DictReader(h):
            text = row.get("Multi-turn conversation") or row.get("Prompt")
            if _usable(text):
                out.append(record(text, DIRECT, MULTI_TURN, "tomgibbs_harmful"))
    return out


# --- added after the first pass, to strengthen the thinnest sub-types ----
#
# neuralchemy labels each row with one of 31 attack families, which is far
# more specific than the binary labels the other supplementary sources carry.
# Mapping those families onto our 8 sub-types is the whole reason this source
# was added: Role Override and System Prompt Overwrite were down to 51 and 251
# rows after deduplication.
#
# Families are mapped on what the text actually does, checked against real
# examples, not on the name alone. Anything unmapped falls through to Policy
# Evasion rather than being discarded.
NEURALCHEMY_MAP = {
    # assume a new identity -> Persona Hijacking
    "persona_replacement": (DIRECT, PERSONA_HIJACKING),
    # override or extract the system prompt -> System Prompt Overwrite
    "instruction_override": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "system_manipulation": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "system_extraction": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "prompt_extraction": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "prompt_leak": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "training_extraction": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "model_fingerprinting": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    # claim privilege / drive the agent -> Role Override
    "agent_manipulation": (DIRECT, ROLE_OVERRIDE),
    # attacks spread across turns -> Multi-Turn Manipulation
    "multi_turn": (DIRECT, MULTI_TURN),
    "crescendo": (DIRECT, MULTI_TURN),
    "many_shot": (DIRECT, MULTI_TURN),
    # malicious text hidden in content the model reads -> Indirect
    "indirect_injection": (INDIRECT, DOCUMENT_EMBEDDING),
    "rag_poisoning": (INDIRECT, DOCUMENT_EMBEDDING),
    # benign
    "benign": (SAFE, None),
    "edge_case": (SAFE, None),
    "control": (SAFE, None),
}


def adapt_neuralchemy() -> list[dict]:
    """31 attack families mapped onto the 8 sub-types.

    `control` rows are labelled 0 (benign) in the file despite the ambiguous
    name, so they are treated as Safe -- the label is trusted over the family
    name where the two disagree.
    """
    import pandas as pd

    frame = pd.read_parquet(RAW_DIR / "neuralchemy_prompt_injection.parquet")
    out: list[dict] = []
    for text, category, label in zip(
        frame["text"], frame["category"], frame["label"]
    ):
        if not _usable(text):
            continue
        mapped = NEURALCHEMY_MAP.get(str(category))
        if mapped is None:
            # Unmapped family: trust the binary label rather than guessing.
            mapped = (
                (SAFE, None) if int(label) == 0 else (DIRECT, POLICY_EVASION)
            )
        cls, subtype = mapped
        # Where family and label disagree, the label wins.
        if int(label) == 0 and cls != SAFE:
            cls, subtype = SAFE, None
        out.append(record(text, cls, subtype, "neuralchemy"))
    return out


def adapt_slabs() -> list[dict]:
    """Binary text/label (0 = benign, 1 = injection)."""
    out = []
    with open(RAW_DIR / "slabs_prompt_injection.csv", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            text = row.get("text")
            if not _usable(text):
                continue
            if str(row.get("label")) == "0":
                out.append(record(text, SAFE, None, "slabs"))
            else:
                out.append(record(text, DIRECT, classify_jailbreak(text), "slabs"))
    return out


def adapt_safeguard() -> list[dict]:
    """Binary text/label (0 = benign, 1 = injection)."""
    import pandas as pd

    frame = pd.read_parquet(RAW_DIR / "safeguard_prompt_injection.parquet")
    out = []
    for text, label in zip(frame["text"], frame["label"]):
        if not _usable(text):
            continue
        if int(label) == 0:
            out.append(record(text, SAFE, None, "safeguard"))
        else:
            out.append(record(text, DIRECT, classify_jailbreak(text), "safeguard"))
    return out


# Old synthetic CSV: raw label -> (class, subtype).
#
# Only `indirect_injection` maps to Indirect, and it goes to Document
# Embedding. The file's `source_channel` column looks like it could separate
# the three Indirect sub-types but is random noise (ml/TASKS.md section 2d),
# so it is deliberately never read.
OLD_CSV_MAP = {
    "benign": (SAFE, None),
    "indirect_injection": (INDIRECT, DOCUMENT_EMBEDDING),
    "instruction_override": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "role_play_persona": (DIRECT, PERSONA_HIJACKING),
    "context_manipulation": (DIRECT, POLICY_EVASION),
    "hypothetical_framing": (DIRECT, POLICY_EVASION),
    "refusal_suppression": (DIRECT, POLICY_EVASION),
    "delimiter_confusion": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
    "encoding_obfuscation": (DIRECT, POLICY_EVASION),
    "payload_splitting": (DIRECT, POLICY_EVASION),
    "prompt_leak": (DIRECT, SYSTEM_PROMPT_OVERWRITE),
}


def adapt_old_csv() -> list[dict]:
    """2M rows but only ~1,041 unique prompts. Deduplicated here so this
    minor source cannot swamp the real-world data downstream."""
    seen: set[str] = set()
    out: list[dict] = []
    with open(
        RAW_DIR / "llm_prompt_injection_jailbreak_dataset.csv", encoding="utf-8"
    ) as handle:
        for row in csv.DictReader(handle):
            mapped = OLD_CSV_MAP.get(row.get("label", ""))
            if not mapped:
                continue
            text = row.get("prompt_text", "")
            if not _usable(text):
                continue
            key = text.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            label, subtype = mapped
            out.append(record(text, label, subtype, "old_csv"))
    return out


# --- 16.11 every adapter --------------------------------------------------
ALL_ADAPTERS = [
    adapt_alpaca,
    adapt_trustairlab_regular,
    adapt_trustairlab_jailbreak,
    adapt_wildjailbreak,
    adapt_safemt_attack600,
    adapt_safemt_1k,
    adapt_orq,
    adapt_llmail_phase1,
    adapt_llmail_phase2,
    adapt_bipia,
    adapt_nemotron,
    adapt_injecagent_dh,
    adapt_injecagent_ds,
    adapt_jackhhao,
    adapt_rubend18,
    adapt_deepset,
    adapt_tomgibbs_benign,
    adapt_tomgibbs_harmful,
    adapt_neuralchemy,
    adapt_slabs,
    adapt_safeguard,
    adapt_old_csv,
]


def main() -> int:
    from collections import Counter

    totals: Counter[str] = Counter()
    subtypes: Counter[str] = Counter()
    grand = 0

    print(f"{'ADAPTER':<28} {'ROWS':>9}   CLASSES")
    print("-" * 72)
    for adapter in ALL_ADAPTERS:
        rows = adapter()
        grand += len(rows)
        classes = Counter(r["label_3class"] for r in rows)
        for r in rows:
            totals[r["label_3class"]] += 1
            if r["subtype"]:
                subtypes[r["subtype"]] += 1
        summary = ", ".join(f"{k} {v:,}" for k, v in classes.most_common())
        print(f"{adapter.__name__:<28} {len(rows):>9,}   {summary}")

    print("-" * 72)
    print(f"{'TOTAL':<28} {grand:>9,}")
    print("\nBy class:")
    for name, count in totals.most_common():
        print(f"  {name:<26} {count:>9,}")
    print("\nBy sub-type:")
    for name in sorted(SUBTYPES):
        print(f"  {name:<26} {subtypes.get(name, 0):>9,}")

    missing = SUBTYPES - set(subtypes)
    if missing:
        print(f"\nMISSING sub-types: {', '.join(sorted(missing))}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
