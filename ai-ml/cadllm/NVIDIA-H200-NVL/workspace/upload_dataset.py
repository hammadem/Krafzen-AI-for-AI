#!/usr/bin/env python3
"""
Upload dataset to Hugging Face Hub.

This script uploads a JSONL dataset file to Hugging Face Hub as a dataset repository.

Usage:
    python upload_dataset.py [--dataset_path PATH] [--dataset_name NAME]
"""

import os
import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login, create_repo
from huggingface_hub.utils import HfHubHTTPError

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload dataset to Hugging Face Hub"
    )
    parser.add_argument(
        "--dataset_path",
        type=str,
        default=None,
        help="Path to dataset JSONL file (required: set DATASET_PATH env var or use --dataset_path)"
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default=None,
        help="Name for the dataset repository (required: set HF_DATASET_NAME env var or use --dataset_name)"
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=None,
        help="Make repository private (default: True, use --public to make public)"
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Make repository public (overrides --private)"
    )
    parser.add_argument(
        "--skip_validation",
        action="store_true",
        help="Skip dataset validation (faster upload)"
    )
    return parser.parse_args()


def validate_jsonl(file_path: Path) -> tuple[int, list]:
    """
    Validate JSONL file and return line count and sample records.
    
    Args:
        file_path: Path to JSONL file
        
    Returns:
        Tuple of (line_count, sample_records)
    """
    print(f"🔍 Validating JSONL file: {file_path}")
    
    line_count = 0
    sample_records = []
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    line_count += 1
                    
                    # Collect first 3 records as samples
                    if len(sample_records) < 3:
                        sample_records.append(record)
                        
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: {str(e)}")
                    if len(errors) >= 10:  # Limit error messages
                        break
    except Exception as e:
        raise ValueError(f"Error reading JSONL file: {str(e)}")
    
    if errors:
        print(f"⚠️  Found {len(errors)} JSON parsing errors:")
        for error in errors[:5]:
            print(f"   {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more errors")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            raise ValueError("Validation failed. Fix errors and try again.")
    
    print(f"✅ Validated {line_count:,} records")
    if sample_records:
        print(f"   Sample record keys: {list(sample_records[0].keys())}")
    
    return line_count, sample_records


def generate_dataset_card(dataset_name: str, repo_id: str, line_count: int, sample_record: dict = None) -> str:
    """
    Generate a dataset card (README.md) for the dataset.
    
    Args:
        dataset_name: Name of the dataset
        repo_id: Hugging Face repository ID
        line_count: Number of records in the dataset
        sample_record: Sample record from the dataset
        
    Returns:
        Dataset card content as string
    """
    current_date = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    
    sample_text = ""
    if sample_record:
        sample_text = f"""
## Sample Record

```json
{json.dumps(sample_record, indent=2)}
```
"""
    
    dataset_card = f"""---
license: apache-2.0
task_categories:
- text-generation
- other
tags:
- cad
- architecture
- floor-plan
- dsl
size_categories:
- 100K<n<1M
---

# Dataset Card for {repo_id}

## Dataset Description

This dataset contains CAD layout descriptions in a structured format for training CAD language models.

- **Repository:** [{repo_id}](https://huggingface.co/datasets/{repo_id})
- **Total Records:** {line_count:,}
- **Format:** JSONL (JSON Lines)
- **Upload Date:** {current_date}

## Dataset Structure

Each record in the dataset contains:
- `instruction`: The task or instruction for the model
- `input`: Optional input context (may be "(none)")
- `output`: The expected DSL format output

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("{repo_id}")
```

## Dataset Statistics

- **Total Examples:** {line_count:,}
- **Format:** JSONL
- **File Size:** See repository files for exact size

{sample_text}

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{{{dataset_name},
  title={{CAD Layout Dataset}},
  author={{Your Name}},
  year={{2024}},
  url={{https://huggingface.co/datasets/{repo_id}}}
}}
```

## License

This dataset is licensed under Apache 2.0.
"""
    
    return dataset_card


def upload_dataset(
    dataset_path: Path,
    repo_id: str,
    private: bool = True,
    skip_validation: bool = False
):
    """
    Upload dataset to Hugging Face Hub.
    
    Args:
        dataset_path: Path to JSONL dataset file
        repo_id: Hugging Face repository ID (username/dataset-name)
        private: Whether to make the repository private
        skip_validation: Skip JSONL validation
    """
    print("=" * 60)
    print("Uploading Dataset to Hugging Face Hub")
    print("=" * 60)
    print(f"Dataset: {dataset_path}")
    print(f"Repository: {repo_id}")
    print(f"Private: {private}")
    print()
    
    # Validate dataset
    if not skip_validation:
        line_count, sample_records = validate_jsonl(dataset_path)
        sample_record = sample_records[0] if sample_records else None
    else:
        print("⏭️  Skipping validation")
        # Quick count for dataset card
        with open(dataset_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for line in f if line.strip())
        sample_record = None
    
    # Get Hugging Face token
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise ValueError(
            "HF_TOKEN not found in .env file.\n"
            "Please add HF_TOKEN=your_token_here to your .env file.\n"
            "Get your token from: https://huggingface.co/settings/tokens"
        )
    
    # Login to Hugging Face
    print("🔐 Logging in to Hugging Face...")
    try:
        login(token=HF_TOKEN)
        print("✅ Logged in successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to login to Hugging Face: {str(e)}")
    
    # Create repository if it doesn't exist
    api = HfApi(token=HF_TOKEN)
    print(f"\n📦 Creating/checking repository: {repo_id}")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            private=private,
            token=HF_TOKEN,
            exist_ok=True
        )
        print(f"✅ Repository ready: https://huggingface.co/datasets/{repo_id}")
    except HfHubHTTPError as e:
        if "already exists" in str(e).lower():
            print(f"✅ Repository already exists: https://huggingface.co/datasets/{repo_id}")
        else:
            raise RuntimeError(f"Failed to create repository: {str(e)}")
    
    # Upload dataset file
    print(f"\n📤 Uploading dataset file...")
    print(f"   File: {dataset_path.name}")
    print(f"   Size: {dataset_path.stat().st_size / (1024*1024):.2f} MB")
    
    try:
        api.upload_file(
            path_or_fileobj=str(dataset_path),
            path_in_repo=dataset_path.name,
            repo_id=repo_id,
            repo_type="dataset",
            token=HF_TOKEN,
        )
        print(f"✅ Dataset file uploaded successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to upload dataset file: {str(e)}")
    
    # Generate and upload dataset card
    print(f"\n📝 Generating dataset card...")
    dataset_name = repo_id.split('/')[-1]
    dataset_card = generate_dataset_card(dataset_name, repo_id, line_count, sample_record)
    
    card_path = Path(__file__).parent / "dataset_card_temp.md"
    try:
        card_path.write_text(dataset_card, encoding='utf-8')
        
        print(f"📤 Uploading dataset card...")
        api.upload_file(
            path_or_fileobj=str(card_path),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            token=HF_TOKEN,
        )
        print(f"✅ Dataset card uploaded")
    finally:
        # Clean up temp file
        if card_path.exists():
            card_path.unlink()
    
    print()
    print("=" * 60)
    print("✅ Dataset Upload Complete!")
    print("=" * 60)
    print(f"Repository: https://huggingface.co/datasets/{repo_id}")
    print(f"Total records: {line_count:,}")
    print()
    print("You can now load this dataset with:")
    print(f"  from datasets import load_dataset")
    print(f"  dataset = load_dataset('{repo_id}')")


def main():
    """Main function."""
    args = parse_args()
    
    # Get dataset path
    dataset_path = args.dataset_path or os.getenv("DATASET_PATH")
    if not dataset_path:
        raise ValueError(
            "Dataset path not specified.\n"
            "Set DATASET_PATH in .env file or use --dataset_path argument.\n"
            "Example: DATASET_PATH=./dataset/jsonl/cadllm.jsonl"
        )
    
    dataset_path = Path(dataset_path).expanduser().resolve()
    if not dataset_path.exists():
        raise ValueError(f"Dataset file does not exist: {dataset_path}")
    
    if not dataset_path.suffix == '.jsonl':
        print(f"⚠️  Warning: File does not have .jsonl extension: {dataset_path}")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Get dataset name
    dataset_name = args.dataset_name or os.getenv("HF_DATASET_NAME")
    if not dataset_name:
        raise ValueError(
            "Dataset name not specified.\n"
            "Set HF_DATASET_NAME in .env file or use --dataset_name argument.\n"
            "Example: HF_DATASET_NAME=cadllm-dataset"
        )
    
    # Get username
    HF_USERNAME = os.getenv("HF_USERNAME")
    if not HF_USERNAME:
        raise ValueError(
            "HF_USERNAME not found in .env file.\n"
            "Please add HF_USERNAME=your_username to your .env file."
        )
    
    repo_id = f"{HF_USERNAME}/{dataset_name}"
    
    # Determine privacy setting
    if args.public:
        private = False
    elif args.private is not None:
        private = args.private
    else:
        # Default from env or True
        private_str = os.getenv("HF_DATASET_PRIVATE", "true").lower()
        private = private_str in ("true", "1", "yes")
    
    # Upload dataset
    upload_dataset(
        dataset_path=dataset_path,
        repo_id=repo_id,
        private=private,
        skip_validation=args.skip_validation
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Upload cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

