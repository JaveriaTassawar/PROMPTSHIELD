"""Collect every raw dataset into ml/data/raw/.

Task 14. All 20 sources are already downloaded to the local dataset folder,
so the normal path here is a fast local copy. Anything missing is fetched
from its original URL instead.

Two sources (WildJailbreak's train.tsv and BIPIA's dataset_for_huggingface.jsonl)
are gated on Hugging Face. They are already present locally, so no token is
normally needed. If one is ever missing, set HF_TOKEN in the environment or run
`huggingface-cli login` first -- never hardcode a token in this file, it is
committed to GitHub.

Run:  python preprocessing/download_datasets.py
"""

from __future__ import annotations

import os
import shutil
import sys
import urllib.request
from pathlib import Path

# Where the already-downloaded files live. Change this one line if the
# dataset folder ever moves.
LOCAL_DATASET_DIR = Path(r"C:\Users\DELL\Desktop\FYP\dataset")

# Destination inside the repo. Gitignored -- nothing here is ever committed.
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Filenames are the exact names on disk. Several contain spaces, brackets or a
# literal "%20", so they are always used as plain strings, never globbed.
#
# Note the two TrustAIRLab parquets share a base name and differ only by the
# " (1)" suffix, so each maps to its own distinct URL.
HF = "https://huggingface.co/datasets"
TRUSTAIRLAB_REV = "a4589b1ec3bfe2755308d72b08e038af3fa3c62e"

SOURCES: dict[str, str] = {
    # --- Safe (benign) ---
    "alpaca_data.json": (
        "https://raw.githubusercontent.com/tatsu-lab/stanford_alpaca/main/alpaca_data.json"
    ),
    "train-00000-of-00001.parquet": (
        f"{HF}/TrustAIRLab/in-the-wild-jailbreak-prompts/resolve/"
        f"{TRUSTAIRLAB_REV}/regular_2023_12_25/train-00000-of-00001.parquet"
    ),
    "Completely-Benign_Dataset.csv": (
        f"{HF}/tom-gibbs/multi-turn_jailbreak_attack_datasets/resolve/main/"
        "Completely-Benign%20Dataset.csv"
    ),
    # --- Direct Jailbreak: Policy Evasion ---
    "train-00000-of-00001 (1).parquet": (
        f"{HF}/TrustAIRLab/in-the-wild-jailbreak-prompts/resolve/"
        f"{TRUSTAIRLAB_REV}/jailbreak_2023_12_25/train-00000-of-00001.parquet"
    ),
    "train.tsv": (  # gated: allenai/wildjailbreak
        f"{HF}/allenai/wildjailbreak/resolve/main/train/train.tsv"
    ),
    # --- Direct Jailbreak: Multi-Turn Manipulation ---
    "Attack_600.json": (
        f"{HF}/SafeMTData/SafeMTData/resolve/main/SafeMTData/Attack_600.json"
    ),
    "SafeMTData_1K.json": (
        f"{HF}/SafeMTData/SafeMTData/resolve/main/SafeMTData/SafeMTData_1K.json"
    ),
    "Harmful%20Dataset.csv": (
        f"{HF}/tom-gibbs/multi-turn_jailbreak_attack_datasets/resolve/main/"
        "Harmful%20Dataset.csv"
    ),
    # --- Direct Jailbreak: Role Override ---
    "redteam_dataset.v2.json": (
        f"{HF}/orq/redteam-vulnerabilities/resolve/main/redteam_dataset.v2.json"
    ),
    # --- Direct Jailbreak: Persona Hijacking / System Prompt Overwrite ---
    "jackhhao_jailbreak_classification.csv": (
        f"{HF}/jackhhao/jailbreak-classification/resolve/main/"
        "default/jailbreak_dataset_full.csv"
    ),
    "rubend18_chatgpt_jailbreak_prompts.csv": (
        f"{HF}/rubend18/ChatGPT-Jailbreak-Prompts/resolve/main/dataset.csv"
    ),
    "deepset_prompt_injections.parquet": (
        f"{HF}/deepset/prompt-injections/resolve/main/"
        "data/train-00000-of-00001-9564e8b05b4757ab.parquet"
    ),
    # --- Indirect Injection: Document Embedding ---
    "dataset_for_huggingface.jsonl": (  # gated: MAlmasabi/...BIPIA-GPT
        f"{HF}/MAlmasabi/Indirect-Prompt-Injection-BIPIA-GPT/resolve/main/"
        "dataset_for_huggingface.jsonl"
    ),
    # --- Indirect Injection: Web Content Injection ---
    "llmail_phase1.json": (
        f"{HF}/microsoft/llmail-inject-challenge/resolve/main/"
        "data/labelled_unique_submissions_phase1.json"
    ),
    "llmail_phase2.json": (
        f"{HF}/microsoft/llmail-inject-challenge/resolve/main/"
        "data/labelled_unique_submissions_phase2.json"
    ),
    # --- Indirect Injection: Tool Output Injection ---
    "train.jsonl": (
        f"{HF}/nvidia/Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1/"
        "resolve/main/train.jsonl"
    ),
    "test_cases_dh_enhanced.json": "",  # InjecAgent-style, supplied locally
    "test_cases_ds_enhanced.json": "",  # InjecAgent-style, supplied locally
    # --- Original synthetic dataset ---
    "llm_prompt_injection_jailbreak_dataset.csv": "",  # supplied locally
    # --- Reference ---
    "all data set links.txt": "",  # the source URL list, supplied locally
}

# Sources needing a Hugging Face token if they ever have to be re-fetched.
GATED = {"train.tsv", "dataset_for_huggingface.jsonl"}


def copy_local(name: str) -> bool:
    """Copy one file from the local dataset folder into data/raw/.

    Returns True if the file was copied, False if it was not available locally.
    """
    source = LOCAL_DATASET_DIR / name
    if not source.is_file():
        return False
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, RAW_DIR / name)
    return True


def fetch(name: str, url: str) -> bool:
    """Download one file into data/raw/. Returns True on success.

    Skips silently if the file is already present. A Hugging Face token is read
    from the environment only -- it is never stored in this file.
    """
    target = RAW_DIR / name
    if target.is_file():
        return True
    if not url:
        return False

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url)

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if token and "huggingface.co" in url:
        request.add_header("Authorization", f"Bearer {token}")

    tmp = target.with_suffix(target.suffix + ".part")
    try:
        with urllib.request.urlopen(request) as response, open(tmp, "wb") as out:
            shutil.copyfileobj(response, out)
        tmp.replace(target)  # only becomes the real file once complete
        return True
    except Exception as exc:  # noqa: BLE001 - report and continue to next source
        tmp.unlink(missing_ok=True)
        print(f"    failed: {exc}")
        return False


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[str]] = {
        "skipped": [], "copied": [], "downloaded": [], "failed": [],
    }

    for name, url in SOURCES.items():
        if (RAW_DIR / name).is_file():
            results["skipped"].append(name)
            continue
        if copy_local(name):
            results["copied"].append(name)
            continue
        if url:
            note = " (gated - needs HF_TOKEN)" if name in GATED else ""
            print(f"  fetching {name}{note}")
            if fetch(name, url):
                results["downloaded"].append(name)
            else:
                results["failed"].append(name)
        else:
            results["failed"].append(name)

    print("\n" + "=" * 62)
    print(f"{'STATUS':<12} {'COUNT':>5}   FILES")
    print("-" * 62)
    for status in ("copied", "downloaded", "skipped", "failed"):
        names = results[status]
        if not names:
            continue
        print(f"{status:<12} {len(names):>5}   {names[0]}")
        for extra in names[1:]:
            print(f"{'':<12} {'':>5}   {extra}")
    print("=" * 62)

    total = sum(len(v) for v in results.values())
    print(f"total sources: {total}    in data/raw/: {len(list(RAW_DIR.iterdir()))}")

    if results["failed"]:
        print("\nSome sources are missing. If a gated one failed, set HF_TOKEN")
        print("or run `huggingface-cli login`, then re-run this script.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
