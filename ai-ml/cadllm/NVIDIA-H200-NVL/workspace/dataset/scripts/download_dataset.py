#!/usr/bin/env python3
import json
from huggingface_hub import snapshot_download
import os
import zipfile

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

# Check for ZIP files and extract them
print("🔍 Checking for ZIP archives to extract...")
zip_files = []
for root, dirs, files in os.walk(OUT):
    for fname in files:
        if fname.endswith(".zip"):
            zip_path = os.path.join(root, fname)
            zip_files.append(zip_path)

if zip_files:
    print(f"📦 Found {len(zip_files)} ZIP file(s), extracting...")
    for zip_path in zip_files:
        print(f"   Extracting: {zip_path}")
        extract_dir = os.path.join(os.path.dirname(zip_path), os.path.splitext(os.path.basename(zip_path))[0])
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"   ✅ Extracted to: {extract_dir}")
        except zipfile.BadZipFile:
            print(f"   ⚠️  Warning: {zip_path} is not a valid ZIP file, skipping")
        except Exception as e:
            print(f"   ⚠️  Warning: Error extracting {zip_path}: {e}")

# Recursively find all JSONL files in the directory tree
print("🔍 Searching for JSONL files...")
jsonl_files = []
for root, dirs, files in os.walk(OUT):
    # Skip .cache directory
    if '.cache' in root:
        continue
    for fname in files:
        if fname.endswith(".jsonl"):
            jsonl_files.append(os.path.join(root, fname))

if not jsonl_files:
    print(f"⚠️  No JSONL files found. Looking for JSON/TXT pairs to convert...")
    
    # Find all JSON files and their corresponding TXT files
    json_txt_pairs = []
    for root, dirs, files in os.walk(OUT):
        # Skip .cache directory
        if '.cache' in root:
            continue
        for fname in files:
            if fname.endswith(".json"):
                json_path = os.path.join(root, fname)
                base_name = os.path.splitext(fname)[0]
                txt_path = os.path.join(root, base_name + ".txt")
                if os.path.exists(txt_path):
                    json_txt_pairs.append((json_path, txt_path))
    
    if json_txt_pairs:
        print(f"📄 Found {len(json_txt_pairs)} JSON/TXT pairs, converting to JSONL format...")
        with open(combined, "w") as outfile:
            for i, (json_path, txt_path) in enumerate(json_txt_pairs):
                if (i + 1) % 1000 == 0:
                    print(f"   Processed {i + 1}/{len(json_txt_pairs)} pairs...")
                
                try:
                    # Read CCS from TXT file
                    with open(txt_path, 'r') as f:
                        ccs_output = f.read().strip()
                    
                    # Read JSON metadata (optional, for future use)
                    with open(json_path, 'r') as f:
                        json_data = json.load(f)
                    
                    # Create JSONL entry
                    entry = {
                        "instruction": "",  # Empty for now, can be filled from Excel files later
                        "input": "",  # Empty for now
                        "output": ccs_output  # CCS commands from TXT file
                    }
                    
                    outfile.write(json.dumps(entry) + "\n")
                except Exception as e:
                    print(f"   ⚠️  Warning: Error processing {json_path}: {e}")
                    continue
        
        print(f"✅ Converted {len(json_txt_pairs)} pairs to JSONL format")
    else:
        print(f"❌ No JSONL files or JSON/TXT pairs found in {OUT}")
        print("   Listing directory contents for debugging:")
        for root, dirs, files in os.walk(OUT):
            if '.cache' in root:
                continue
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
