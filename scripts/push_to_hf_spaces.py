"""
Push code to HuggingFace Spaces.
Pushes Gateway (Space 1), ML (Space 2), and Data (Space 3) code.

Usage:
    set HF_TOKEN=hf_xxxx
    python scripts/push_to_hf_spaces.py
"""
import os
import sys
import json

HF_TOKEN = os.getenv("HF_TOKEN", "")
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")

SPACES = {
    "gateway": {
        "repo_id": "Qrmanual/AUMOv3",
        "source_dir": os.path.join(PROJECT_ROOT, "ai-service"),
        "files": [
            "main.py", "config.py", "Dockerfile", "requirements.txt",
            "algorithms/__init__.py", "algorithms/astar.py",
            "algorithms/emissions.py", "algorithms/graph_builder.py",
            "algorithms/maharashtra_poi.py", "algorithms/matching.py",
            "models/__init__.py", "models/data_generator.py",
            "models/lstm_model.py", "models/trainer.py",
            "utils/__init__.py", "utils/haversine.py",
            "utils/live_traffic.py", "utils/osrm_client.py",
        ],
    },
    "ml": {
        "repo_id": "Qrmanual/AUMOV3.1",
        "source_dir": os.path.join(PROJECT_ROOT, "ai-service-ml"),
        "files": [
            "main.py", "config.py", "Dockerfile", "requirements.txt",
        ],
    },
    "data": {
        "repo_id": "Qrmanual/AUMOv3.2",
        "source_dir": os.path.join(PROJECT_ROOT, "ai-service-data"),
        "files": [
            "main.py", "config.py", "Dockerfile", "requirements.txt",
        ],
    },
}


def push_space(space_name: str, space_config: dict):
    """Push files to a HuggingFace Space."""
    from huggingface_hub import HfApi
    api = HfApi(token=HF_TOKEN)

    repo_id = space_config["repo_id"]
    source_dir = space_config["source_dir"]
    files = space_config["files"]

    print(f"\n{'='*50}")
    print(f"  Pushing to: {repo_id}")
    print(f"  Source: {source_dir}")
    print(f"{'='*50}")

    for filepath in files:
        full_path = os.path.join(source_dir, filepath)
        if not os.path.exists(full_path):
            print(f"  ⚠️  SKIP (not found): {filepath}")
            continue

        try:
            with open(full_path, "rb") as f:
                content = f.read()
            api.upload_file(
                path_or_fileobj=content,
                path_in_repo=filepath,
                repo_id=repo_id,
                repo_type="space",
            )
            print(f"  ✅ {filepath}")
        except Exception as e:
            print(f"  ❌ {filepath}: {e}")

    print(f"  Done: {repo_id}")


def main():
    if not HF_TOKEN:
        print("ERROR: Set HF_TOKEN environment variable first.")
        print("  Windows:  set HF_TOKEN=hf_xxxx")
        print("  Linux:    export HF_TOKEN=hf_xxxx")
        sys.exit(1)

    args = sys.argv[1:]

    if args:
        # Push specific spaces
        for name in args:
            if name in SPACES:
                push_space(name, SPACES[name])
            else:
                print(f"Unknown space: {name}. Available: {', '.join(SPACES.keys())}")
    else:
        # Push all spaces
        for name, config in SPACES.items():
            push_space(name, config)

    print("\n✅ All spaces pushed! They will rebuild automatically on HuggingFace.")


if __name__ == "__main__":
    main()
