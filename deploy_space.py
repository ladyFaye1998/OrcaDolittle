"""Deploy OrcaDolittle to HuggingFace Spaces.

Copies the relevant source directories to a staging folder, writes
``requirements.txt`` and a Space-flavoured ``README.md`` with the YAML
front-matter, then uploads via ``HfApi.upload_folder``. Finally triggers a
factory reboot to force a clean rebuild.

Authentication
--------------
Run ``hf auth login`` (or ``huggingface-cli login``) first. The script picks
up the cached token automatically.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

SPACE_ID = "ladyFaye1998/OrcaDolittle"
LOCAL_ROOT = Path(__file__).resolve().parent

GRADIO_VERSION = "5.50.0"

REQUIREMENTS = f"""\
gradio[oauth]=={GRADIO_VERSION}
torch>=2.2
torchaudio
transformers>=4.40
huggingface-hub>=0.23
numpy
scipy
scikit-learn
soundfile
librosa
pydantic>=2.0
click
rich
matplotlib
tqdm
"""

SPACE_README = f"""\
---
title: OrcaDolittle
emoji: 🐋
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: {GRADIO_VERSION}
app_file: web/app.py
pinned: true
license: mit
short_description: A Doctor Dolittle stack for killer whales.
---

# OrcaDolittle — A Doctor Dolittle stack for killer whales

Perceive · Generate · Select · Anticipate.

Built on DCLDE 2026 (225 000 annotated orca calls), OrcaSound live
hydrophones, and the published killer-whale playback literature.

**GitHub:** [ladyFaye1998/OrcaDolittle](https://github.com/ladyFaye1998/OrcaDolittle)
"""

DIRS_TO_COPY = ["web", "orcadolittle", "assets"]


def main() -> None:
    api = HfApi()

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "staging"
        staging.mkdir()

        for d in DIRS_TO_COPY:
            src = LOCAL_ROOT / d
            dst = staging / d
            if src.exists():
                shutil.copytree(
                    src, dst,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", ".mypy_cache",
                        ".pytest_cache", ".ruff_cache",
                    ),
                )
                print(f"  Staged {d}/")

        (staging / "requirements.txt").write_text(
            REQUIREMENTS.strip() + "\n", encoding="utf-8",
        )
        print("  Wrote requirements.txt")

        (staging / "README.md").write_text(
            SPACE_README, encoding="utf-8",
        )
        print("  Wrote README.md")

        print(f"Uploading to HuggingFace Space {SPACE_ID} …")
        api.create_repo(
            repo_id=SPACE_ID, repo_type="space",
            space_sdk="gradio", private=True, exist_ok=True,
        )
        api.upload_folder(
            folder_path=str(staging),
            repo_id=SPACE_ID,
            repo_type="space",
            commit_message="OrcaDolittle initial deploy",
        )
        print("Upload complete.")

    print("Requesting factory reboot …")
    api.restart_space(SPACE_ID, factory_reboot=True)
    print(f"Done — https://huggingface.co/spaces/{SPACE_ID}")


if __name__ == "__main__":
    main()
