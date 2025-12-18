#!/usr/bin/env python3
import json
from huggingface_hub import snapshot_download
import os

OUT = "./../dataset/cadllm_raw"   # directory that will be created

# Ensure the output directory exists
os.makedirs(OUT, exist_ok=True)

print("📥 Downloading dataset from HF…")
print("   This may take a while (dataset is ~15GB)...")

snapshot_download(
    repo_id="lanlanguai/CADLLM",
    repo_type="dataset",
    local_dir=OUT,
    # Removed allow_patterns to download all files, then filter locally
)

print("✅ Download complete:", OUT)

# Merge all JSONL files into a single file for uniform processing
combined = "./../dataset/cadllm_raw.jsonl"

# Ensure the parent directory for the combined file exists
os.makedirs(os.path.dirname(combined), exist_ok=True)

print("📦 Merging JSONL files into:", combined)

# Check if the directory exists and has files
if not os.path.exists(OUT):
    print(f"❌ Error: Directory {OUT} does not exist after download")
    exit(1)

# Recursively find all JSONL files in the directory tree
print("🔍 Searching for JSONL files...")
jsonl_files = []
for root, dirs, files in os.walk(OUT):
    for fname in files:
        if fname.endswith(".jsonl"):
            jsonl_files.append(os.path.join(root, fname))

if not jsonl_files:
    print(f"⚠️  Warning: No JSONL files found in {OUT}")
    print("   Listing directory contents for debugging:")
    for root, dirs, files in os.walk(OUT):
        level = root.replace(OUT, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for fname in files[:10]:  # Show first 10 files
            print(f"{subindent}{fname}")
        if len(files) > 10:
            print(f"{subindent}... and {len(files) - 10} more files")
    print("Creating empty combined file...")
    with open(combined, "w") as outfile:
        pass
else:
    print(f"📄 Found {len(jsonl_files)} JSONL file(s)")
    with open(combined, "w") as outfile:
        for path in jsonl_files:
            print(" - adding", path)
            with open(path) as f:
                for line in f:
                    outfile.write(line)

print("🎉 Combined dataset ready at:", combined)
