#!/usr/bin/env python3
"""
Deploy merged model to Ollama.

This script converts a merged Hugging Face model to GGUF format and creates
an Ollama Modelfile for deployment.

Usage:
    python deploy_ollama.py [--model_path PATH] [--ollama_model_name NAME] [--gguf_output_dir DIR]
"""

import os
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# System prompt (matches training format)
SYSTEM_PROMPT = """You are a CAD code assistant. Given a simple CAD description, 
output ONLY the strict DSL format shown below. Do not use natural language.

Required DSL Format (STRICT - must match exactly):
UNITS: mm
ORIGIN_POLICY: room_center_at_(0,0)
ROOM: rect w=WIDTH h=HEIGHT center=(0,0)
WALLS: rect_perimeter closed=true layer=WALLS
OBJECT_NAME: rect w=WIDTH h=HEIGHT center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL
OBJECT_NAME: circle r=RADIUS center=(X,Y) layer=OBJECTS closed=true anchor_wall=WALL

Rules:
- Always start with UNITS, ORIGIN_POLICY, ROOM, WALLS (in that order)
- Use rect or circle primitives only
- Entity names must use underscores (e.g., COFFEE_TABLE not COFFEE TABLE)
- anchor_wall must be: north, south, east, west, or none (for free placement)
- All coordinates in mm, room centered at (0,0)
- All objects must be within room bounds
- Use circle for round objects (burners, round tables, columns)
- Use rect for rectangular objects (tables, desks, appliances)

Default dimensions if not specified:
- Rooms: 3000x3000 (bedroom), 4000x3000 (kitchen), 2000x2000 (bathroom)
- Simple shapes: r=100 (circles), 200x200 (squares), 300x200 (rectangles)
"""


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy merged model to Ollama"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to merged model directory (required: set MODEL_PATH env var or use --model_path)"
    )
    parser.add_argument(
        "--ollama_model_name",
        type=str,
        default=None,
        help="Name for Ollama model (default: cadllm, can be set via OLLAMA_MODEL_NAME env var)"
    )
    parser.add_argument(
        "--gguf_output_dir",
        type=str,
        default=None,
        help="Output directory for GGUF file (default: ./ollama-models, can be set via GGUF_OUTPUT_DIR env var)"
    )
    parser.add_argument(
        "--skip_conversion",
        action="store_true",
        help="Skip GGUF conversion (use existing GGUF file)"
    )
    parser.add_argument(
        "--llama_cpp_path",
        type=str,
        default=None,
        help="Path to llama.cpp directory (default: auto-detects, can be set via LLAMA_CPP_PATH env var)"
    )
    return parser.parse_args()


def find_llama_cpp():
    """Find llama.cpp installation."""
    # Check Homebrew installation first (common on macOS)
    try:
        result = subprocess.run(
            ["brew", "--prefix", "llama.cpp"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            brew_prefix = Path(result.stdout.strip())
            # Homebrew installs to Cellar, but the prefix is a symlink
            # Find the actual Cellar directory
            if brew_prefix.exists():
                # Follow symlink to find actual installation
                actual_path = brew_prefix.resolve()
                if actual_path.exists():
                    # Check if conversion script exists
                    conversion_scripts = [
                        actual_path / "bin" / "convert_hf_to_gguf.py",
                        actual_path / "libexec" / "convert_hf_to_gguf.py",
                    ]
                    for script in conversion_scripts:
                        if script.exists():
                            print(f"   ✅ Found llama.cpp via Homebrew: {actual_path}")
                            return actual_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Homebrew not available, continue with other checks
    
    # Check common locations
    common_paths = [
        Path.home() / "llama.cpp",
        Path.home() / "code" / "llama.cpp",
        Path.home() / "projects" / "llama.cpp",
        Path.home() / "Documents" / "llama.cpp",
        Path("/opt/llama.cpp"),
        Path("/usr/local/llama.cpp"),
        Path.cwd() / "llama.cpp",
        Path.cwd().parent / "llama.cpp",
        Path.cwd().parent.parent / "llama.cpp",
    ]
    
    found_paths = []
    for path in common_paths:
        if path.exists():
            # Check for conversion script (could be different names or locations)
            conversion_scripts = [
                path / "convert-hf-to-gguf.py",
                path / "convert.py",
                path / "convert_hf_to_gguf.py",
                path / "bin" / "convert_hf_to_gguf.py",
                path / "libexec" / "convert_hf_to_gguf.py",
            ]
            for script in conversion_scripts:
                if script.exists():
                    return path
            found_paths.append(path)
    
    # If we found llama.cpp directories but no conversion script, report them
    if found_paths:
        print("⚠️  Found llama.cpp directories but no conversion script:")
        for p in found_paths:
            print(f"   - {p}")
        print("\n   Make sure llama.cpp is fully built and includes conversion scripts.")
    
    return None


def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Note: We don't check for gguf module here because:
# 1. The PyPI 'gguf' package is incompatible with llama.cpp conversion scripts
# 2. The conversion script needs the gguf module from llama.cpp source
# 3. For Homebrew installations, the gguf module may not be included
# The script will add llama.cpp to PYTHONPATH so it can find its own gguf module


def convert_to_gguf(model_path: Path, output_dir: Path, llama_cpp_path: Path):
    """Convert Hugging Face model to GGUF format."""
    print("=" * 60)
    print("Converting Model to GGUF Format")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Output: {output_dir}")
    print(f"llama.cpp: {llama_cpp_path}")
    print()
    
    # Check if model exists
    if not model_path.exists():
        raise ValueError(f"Model path does not exist: {model_path}")
    
    # Check for config.json to verify it's a valid model
    config_file = model_path / "config.json"
    if not config_file.exists():
        raise ValueError(
            f"Model path does not appear to be a valid Hugging Face model: {model_path}\n"
            f"Expected 'config.json' file not found."
        )
    
    # Check for numpy (required for conversion)
    print("🔍 Checking for required dependencies...")
    try:
        import numpy
        print("✅ numpy found")
    except ImportError:
        print("❌ Missing 'numpy' module")
        print("\n📦 Attempting to install numpy...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "numpy"],
                check=True,
                capture_output=True
            )
            print("✅ Successfully installed numpy")
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Missing 'numpy' Python module required for conversion.\n\n"
                "Please install it manually:\n"
                "  pip install numpy"
            )
    
    # Note: The gguf module should come from llama.cpp source, not PyPI
    # The conversion script will use gguf from llama.cpp's directory structure
    # We'll add llama.cpp to PYTHONPATH so it can find its own gguf module
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find conversion script (check multiple locations including Homebrew structure)
    conversion_scripts = [
        llama_cpp_path / "convert-hf-to-gguf.py",
        llama_cpp_path / "convert.py",
        llama_cpp_path / "convert_hf_to_gguf.py",
        llama_cpp_path / "bin" / "convert_hf_to_gguf.py",
        llama_cpp_path / "libexec" / "convert_hf_to_gguf.py",
    ]
    convert_script = None
    for script in conversion_scripts:
        if script.exists():
            convert_script = script
            break
    
    if not convert_script:
        raise ValueError(
            f"Conversion script not found in {llama_cpp_path}\n"
            f"Checked: convert-hf-to-gguf.py, convert.py, convert_hf_to_gguf.py\n"
            f"         bin/convert_hf_to_gguf.py, libexec/convert_hf_to_gguf.py"
        )
    
    print(f"📥 Using conversion script: {convert_script}")
    
    # The conversion script needs the gguf module from llama.cpp source
    # Check if llama.cpp has its own gguf module directory
    # For Homebrew installations, the gguf module should be in the same directory as the script
    # or we need to add the llama.cpp source directory to PYTHONPATH
    env = os.environ.copy()
    
    # Try to find gguf module in llama.cpp directory structure
    possible_gguf_paths = [
        llama_cpp_path.parent.parent / "share" / "llama.cpp",  # Homebrew share location
        llama_cpp_path / "gguf",
        llama_cpp_path.parent / "gguf",
    ]
    
    # Also check if we're in a source installation
    if (llama_cpp_path / "convert-hf-to-gguf.py").exists():
        # Source installation - gguf should be in the same directory
        possible_gguf_paths.insert(0, llama_cpp_path)
    
    # The conversion script needs the gguf module from llama.cpp source
    # Check for gguf module in common locations
    gguf_locations = [
        llama_cpp_path / "gguf",  # Root directory
        llama_cpp_path / "gguf-py" / "gguf",  # gguf-py subdirectory (common in newer versions)
        llama_cpp_path.parent / "gguf-py" / "gguf",  # Parent directory
    ]
    
    gguf_found = False
    for gguf_path in gguf_locations:
        if gguf_path.exists() and (gguf_path / "__init__.py").exists():
            print(f"✅ Found gguf module: {gguf_path}")
            gguf_found = True
            # Add the parent directory to PYTHONPATH so 'import gguf' works
            gguf_parent = gguf_path.parent
            break
    
    if not gguf_found:
        print(f"⚠️  Warning: gguf module not found in expected locations")
        print(f"   Checked: {[str(p) for p in gguf_locations]}")
        print(f"   The conversion script needs the gguf module from llama.cpp source")
        print(f"   If PyPI gguf is installed, uninstall it: pip uninstall gguf")
        gguf_parent = llama_cpp_path  # Fallback to root
    
    # Add llama.cpp directories to PYTHONPATH FIRST so they take precedence over PyPI package
    # This ensures llama.cpp's gguf module is found before the PyPI one
    existing_pythonpath = env.get("PYTHONPATH", "")
    pythonpath_parts = [
        str(gguf_parent),  # Parent of gguf module (so 'import gguf' works)
        str(llama_cpp_path),  # Root directory
    ]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = ":".join(pythonpath_parts)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename based on model name
    # Try to get model name from config.json, otherwise use directory name
    model_name = model_path.name
    try:
        import json
        config_file = model_path / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Try to get a meaningful name from config
                if "model_type" in config:
                    model_name = f"{config.get('model_type', 'model')}-{model_path.name}"
    except Exception:
        pass  # Use directory name as fallback
    
    output_file = output_dir / f"{model_name}.gguf"
    
    # Run conversion
    # Note: Qwen models may need specific parameters
    # Check llama.cpp documentation for Qwen-specific conversion
    cmd = [
        sys.executable,
        str(convert_script),
        str(model_path),
        "--outfile", str(output_file),
        "--outtype", "f16",  # Use float16 for smaller file size
    ]
    
    print(f"🔄 Running conversion command...")
    print(f"   {' '.join(cmd)}")
    print(f"   PYTHONPATH: {env['PYTHONPATH']}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(llama_cpp_path),
            env=env,
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Conversion failed with exit code {e.returncode}\n"
            f"Make sure llama.cpp is properly set up and the conversion script supports Qwen models.\n\n"
            f"Common issues:\n"
            f"  1. gguf module version mismatch: The conversion script needs gguf from llama.cpp source,\n"
            f"     not the PyPI package. If using Homebrew llama.cpp, this should be handled automatically.\n"
            f"  2. Missing 'numpy': pip install numpy\n"
            f"  3. Model architecture not supported by conversion script\n"
            f"  4. Insufficient disk space for GGUF file\n\n"
            f"Note: If the error mentions 'MistralTokenizerType' or similar imports, the gguf module\n"
            f"      from llama.cpp source is required. Try cloning llama.cpp from source:\n"
            f"      git clone https://github.com/ggerganov/llama.cpp.git\n"
            f"      cd llama.cpp\n"
            f"      mkdir build && cd build\n"
            f"      cmake ..\n"
            f"      cmake --build ."
        )
        raise RuntimeError(error_msg)
    
    # Check if the output file was created
    if not output_file.exists():
        # Sometimes the script outputs to a different location, try to find it
        gguf_files = list(output_dir.glob("*.gguf"))
        if not gguf_files:
            raise ValueError(
                f"No GGUF file generated at {output_file}\n"
                f"Conversion may have failed or output to a different location.\n"
                f"Checked directory: {output_dir}"
            )
        # Use the largest file (usually the main model file)
        gguf_file = max(gguf_files, key=lambda f: f.stat().st_size)
        print(f"✅ GGUF file generated (found at different location): {gguf_file}")
    else:
        gguf_file = output_file
        print(f"✅ GGUF file generated: {gguf_file}")
    
    return gguf_file


def create_modelfile(gguf_path: Path, modelfile_path: Path, model_name: str):
    """Create Ollama Modelfile."""
    print("=" * 60)
    print("Creating Ollama Modelfile")
    print("=" * 60)
    print(f"GGUF: {gguf_path}")
    print(f"Modelfile: {modelfile_path}")
    print()
    
    modelfile_content = f"""FROM {gguf_path.absolute()}

SYSTEM \"\"\"{SYSTEM_PROMPT}\"\"\"

# Qwen chat template format (matches training format)
# This ensures the system prompt is included in the chat format
TEMPLATE \"\"\"<|im_start|>system
{{{{ .System }}}}<|im_end|>
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 400
"""
    
    modelfile_path.write_text(modelfile_content)
    print(f"✅ Modelfile created: {modelfile_path}")
    return modelfile_path


def create_ollama_model(modelfile_path: Path, model_name: str):
    """Create Ollama model from Modelfile."""
    print("=" * 60)
    print("Creating Ollama Model")
    print("=" * 60)
    print(f"Model name: {model_name}")
    print(f"Modelfile: {modelfile_path}")
    print()
    
    if not check_ollama_installed():
        raise RuntimeError(
            "Ollama is not installed or not in PATH.\n"
            "Install Ollama from: https://ollama.ai"
        )
    
    cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
    
    print(f"🔄 Creating Ollama model...")
    print(f"   {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False
        )
        print(f"✅ Ollama model '{model_name}' created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to create Ollama model (exit code {e.returncode})\n"
            f"Check Ollama logs for details."
        )


def main():
    """Main deployment function."""
    args = parse_args()
    
    # Get model path from args or env
    # Check MODEL_PATH first (preferred), then MODEL_OUTPUT_DIR for backward compatibility
    model_path = args.model_path or os.getenv("MODEL_PATH") or os.getenv("MODEL_OUTPUT_DIR")
    if not model_path:
        raise ValueError(
            "Model path not specified.\n"
            "Set MODEL_PATH in .env file or use --model_path argument."
        )
    # Expand environment variables and user home directory
    model_path = os.path.expandvars(model_path)  # Expands $HOME, $VAR, etc.
    model_path = Path(model_path).expanduser().resolve()  # Expands ~
    
    # Get Ollama model name
    ollama_model_name = args.ollama_model_name or os.getenv("OLLAMA_MODEL_NAME", "cadllm")
    
    # Get GGUF output directory
    gguf_output_dir = args.gguf_output_dir or os.getenv("GGUF_OUTPUT_DIR")
    if not gguf_output_dir:
        gguf_output_dir = Path(__file__).parent / "ollama-models"
    else:
        # Expand environment variables and user home directory
        gguf_output_dir = os.path.expandvars(gguf_output_dir)  # Expands $HOME, $VAR, etc.
        gguf_output_dir = Path(gguf_output_dir).expanduser().resolve()  # Expands ~
    
    # Find llama.cpp
    # Priority: 1) Command-line arg, 2) Environment variable, 3) Auto-detect
    llama_cpp_path = args.llama_cpp_path or os.getenv("LLAMA_CPP_PATH")
    if llama_cpp_path:
        # Expand environment variables and user home directory
        llama_cpp_path = os.path.expandvars(llama_cpp_path)  # Expands $HOME, $VAR, etc.
        llama_cpp_path = Path(llama_cpp_path).expanduser().resolve()  # Expands ~
        if not llama_cpp_path.exists():
            raise ValueError(f"Specified llama.cpp path does not exist: {llama_cpp_path}")
        source = "command-line arg" if args.llama_cpp_path else "LLAMA_CPP_PATH env var"
        print(f"✅ Using llama.cpp from {source}: {llama_cpp_path}")
    else:
        print("🔍 Searching for llama.cpp...")
        llama_cpp_path = find_llama_cpp()
        if not llama_cpp_path:
            print("\n" + "=" * 60)
            print("❌ llama.cpp not found")
            print("=" * 60)
            print("\nTo install llama.cpp:")
            print("  Option 1 (Homebrew - recommended):")
            print("    brew install llama.cpp")
            print("  Option 2 (From source):")
            print("    1. Clone the repository:")
            print("       git clone https://github.com/ggerganov/llama.cpp.git")
            print("       cd llama.cpp")
            print("    2. Build it (uses CMake):")
            print("       mkdir build && cd build")
            print("       cmake ..")
            print("       cmake --build .")
            print("  3. Install Python dependencies (for conversion):")
            print("     pip install numpy")
            print("\nAfter installation, you can:")
            print("  - Set LLAMA_CPP_PATH in your .env file")
            print("  - Or use --llama_cpp_path argument")
            print("  - Or install it in one of these locations:")
            print("    - ~/llama.cpp")
            print("    - ~/code/llama.cpp")
            print("    - ~/projects/llama.cpp")
            print("    - ./llama.cpp (current directory)")
            print("\nNote: For Qwen models, you may need the latest version of llama.cpp")
            print("      that supports Qwen model conversion.")
            raise ValueError("llama.cpp not found. See instructions above.")
    
    # Verify conversion script exists (check multiple locations)
    conversion_scripts = [
        llama_cpp_path / "convert-hf-to-gguf.py",
        llama_cpp_path / "convert.py",
        llama_cpp_path / "convert_hf_to_gguf.py",
        llama_cpp_path / "bin" / "convert_hf_to_gguf.py",
        llama_cpp_path / "libexec" / "convert_hf_to_gguf.py",
    ]
    convert_script = None
    for script in conversion_scripts:
        if script.exists():
            convert_script = script
            break
    
    if not convert_script:
        raise ValueError(
            f"llama.cpp found at {llama_cpp_path} but conversion script not found.\n"
            f"Checked locations:\n"
            f"  - {llama_cpp_path / 'convert-hf-to-gguf.py'}\n"
            f"  - {llama_cpp_path / 'convert.py'}\n"
            f"  - {llama_cpp_path / 'convert_hf_to_gguf.py'}\n"
            f"  - {llama_cpp_path / 'bin' / 'convert_hf_to_gguf.py'}\n"
            f"  - {llama_cpp_path / 'libexec' / 'convert_hf_to_gguf.py'}\n"
            f"Make sure llama.cpp is fully installed and includes Python conversion scripts."
        )
    
    # Step 1: Convert to GGUF (unless skipped)
    if args.skip_conversion:
        print("⏭️  Skipping GGUF conversion (using existing GGUF file)")
        gguf_files = list(gguf_output_dir.glob("*.gguf"))
        if not gguf_files:
            raise ValueError(f"No GGUF files found in {gguf_output_dir}")
        gguf_path = max(gguf_files, key=lambda f: f.stat().st_size)
        print(f"   Using existing GGUF file: {gguf_path}")
    else:
        gguf_path = convert_to_gguf(model_path, gguf_output_dir, llama_cpp_path)
    
    # Step 2: Create Modelfile
    modelfile_path = gguf_output_dir / "Modelfile"
    create_modelfile(gguf_path, modelfile_path, ollama_model_name)
    
    # Step 3: Create Ollama model
    create_ollama_model(modelfile_path, ollama_model_name)
    
    print()
    print("=" * 60)
    print("✅ Deployment Complete!")
    print("=" * 60)
    print(f"Model name: {ollama_model_name}")
    print(f"GGUF file: {gguf_path}")
    print(f"Modelfile: {modelfile_path}")
    print()
    print("🚀 Test your model:")
    print(f"   ollama run {ollama_model_name} 'Create a circle with radius 10mm'")
    print()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user", file=sys.stderr)
        sys.exit(1)

