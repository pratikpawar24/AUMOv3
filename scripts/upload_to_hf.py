"""
Upload existing dataset files to HuggingFace.
Run after build_maharashtra_dataset.py has generated the files.

Usage:
    set HF_TOKEN=hf_xxxx
    python scripts/upload_to_hf.py
"""
import os
import json
import sys

HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "Qrmanual/AUMO")
HF_TOKEN = os.getenv("HF_TOKEN", "")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset_output")

def main():
    if not HF_TOKEN:
        print("ERROR: Set HF_TOKEN environment variable first.")
        print("  Windows:  set HF_TOKEN=hf_xxxx")
        print("  Linux:    export HF_TOKEN=hf_xxxx")
        sys.exit(1)

    combined_file = os.path.join(OUTPUT_DIR, "maharashtra_pois.json")
    stats_file = os.path.join(OUTPUT_DIR, "dataset_stats.json")

    if not os.path.exists(combined_file):
        print(f"ERROR: {combined_file} not found. Run build_maharashtra_dataset.py first.")
        sys.exit(1)

    from huggingface_hub import HfApi
    api = HfApi(token=HF_TOKEN)

    # Upload main dataset
    print(f"Uploading {combined_file}...")
    api.upload_file(
        path_or_fileobj=combined_file,
        path_in_repo="maharashtra_pois.json",
        repo_id=HF_DATASET_REPO,
        repo_type="dataset",
    )
    with open(combined_file, "r") as f:
        count = len(json.load(f))
    print(f"✅ Uploaded maharashtra_pois.json ({count} places)")

    # Upload stats
    if os.path.exists(stats_file):
        print(f"Uploading {stats_file}...")
        api.upload_file(
            path_or_fileobj=stats_file,
            path_in_repo="dataset_stats.json",
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
        )
        print(f"✅ Uploaded dataset_stats.json")

    print(f"\nDone! Dataset available at: https://huggingface.co/datasets/{HF_DATASET_REPO}")


if __name__ == "__main__":
    main()
