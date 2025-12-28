#!/usr/bin/env python3
"""
Deploy Space app to Hugging Face Space.

This script pushes the Space app directory to a Hugging Face Space repository
without requiring it to be a separate git repository. It uses a temporary
git repository to push the Space directory.

Features:
- Automatically creates the Space repository if it doesn't exist (requires HF_TOKEN)
- Uses temporary git repository (no git subtree required)
- Clean error messages without tracebacks

Usage:
    python deploy_space.py [--space_dir DIR] [--space_repo REPO] [--commit_message MSG]
    
Requirements:
    - HF_TOKEN in .env file for automatic repository creation
    - huggingface_hub package (already in requirements.txt)
"""

import os
import sys
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Try to import huggingface_hub for repository creation
try:
    from huggingface_hub import HfApi
    # Try to import create_repo (available in newer versions)
    try:
        from huggingface_hub import create_repo
    except ImportError:
        # Fallback: create_repo might be a method of HfApi in older versions
        create_repo = None
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    create_repo = None

# Load .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Default Space repository (can be overridden via env or args)
DEFAULT_SPACE_REPO = os.getenv("HF_SPACE_REPO", "mkmad7/cad-llm-api")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy Space app to Hugging Face Space"
    )
    parser.add_argument(
        "--space_dir",
        type=str,
        default=None,
        help="Path to Space app directory (default: scripts/deployment/space/cad-llm-api)"
    )
    parser.add_argument(
        "--space_repo",
        type=str,
        default=None,
        help=f"Hugging Face Space repository (default: {DEFAULT_SPACE_REPO})"
    )
    parser.add_argument(
        "--commit_message",
        type=str,
        default="Update Space app",
        help="Commit message for Space deployment"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force push even if no changes detected"
    )
    return parser.parse_args()


def get_space_repo_url(repo_id: str) -> str:
    """Get the Hugging Face Space repository URL."""
    # Hugging Face Spaces use https://huggingface.co/spaces/username/repo-name
    return f"https://huggingface.co/spaces/{repo_id}"


def detect_space_sdk(space_dir: Path) -> str:
    """
    Detect the Space SDK type by examining files in the Space directory.
    
    Returns:
        One of: 'gradio', 'streamlit', 'docker', 'static'
        Defaults to 'gradio' if cannot be determined
    """
    # Check for Dockerfile (docker SDK)
    if (space_dir / "Dockerfile").exists():
        return "docker"
    
    # Check app.py for SDK imports
    app_py = space_dir / "app.py"
    if app_py.exists():
        try:
            content = app_py.read_text()
            if "import gradio" in content or "from gradio" in content:
                return "gradio"
            elif "import streamlit" in content or "from streamlit" in content:
                return "streamlit"
        except:
            pass
    
    # Check for static files (index.html, etc.)
    if (space_dir / "index.html").exists() or (space_dir / "static").exists():
        return "static"
    
    # Default to gradio (most common)
    return "gradio"


def check_and_create_space_repo(repo_id: str, space_dir: Path, token: str = None) -> bool:
    """
    Check if Space repository exists, create it if it doesn't.
    
    Returns:
        True if repository exists or was created successfully, False otherwise
    """
    if not HF_HUB_AVAILABLE:
        print("   ⚠️  huggingface_hub not available, cannot auto-create repository")
        print("   Install it with: pip install huggingface_hub")
        return False
    
    try:
        api = HfApi(token=token)
        
        # Check if repository exists
        try:
            api.repo_info(repo_id=repo_id, repo_type="space")
            print(f"   ✅ Space repository exists: {repo_id}")
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                # Repository doesn't exist, create it
                print(f"   📦 Space repository not found, creating: {repo_id}")
                
                # Detect Space SDK type
                space_sdk = detect_space_sdk(space_dir)
                print(f"   🔍 Detected Space SDK: {space_sdk}")
                
                try:
                    if create_repo:
                        # Use standalone create_repo function (newer versions)
                        create_repo(
                            repo_id=repo_id,
                            repo_type="space",
                            space_sdk=space_sdk,
                            token=token,
                            exist_ok=False,
                            private=False,  # Spaces are typically public
                        )
                    else:
                        # Use HfApi method (older versions)
                        api.create_repo(
                            repo_id=repo_id,
                            repo_type="space",
                            space_sdk=space_sdk,
                            token=token,
                            exist_ok=False,
                            private=False,
                        )
                    print(f"   ✅ Space repository created successfully!")
                    return True
                except Exception as create_error:
                    print(f"   ❌ Failed to create repository: {create_error}")
                    print(f"   Please create it manually at: https://huggingface.co/new-space")
                    return False
            else:
                # Other error (permissions, etc.)
                print(f"   ⚠️  Error checking repository: {e}")
                return False
                
    except Exception as e:
        print(f"   ⚠️  Error with Hugging Face API: {e}")
        return False


def check_git_repo():
    """Check if we're in a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            check=True,
            capture_output=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def deploy_space_app(space_dir: Path, space_repo: str, commit_message: str, force: bool = False):
    """
    Deploy Space app to Hugging Face using a temporary git repository.
    
    This method:
    1. Creates a temporary directory
    2. Copies Space files to temp directory
    3. Initializes git repo and pushes to Hugging Face Space
    4. Cleans up temporary directory
    
    This approach doesn't require git subtree and works with any git setup.
    """
    if not space_dir.exists():
        raise ValueError(f"Space directory does not exist: {space_dir}")
    
    space_repo_url = get_space_repo_url(space_repo)
    
    print(f"📦 Space directory: {space_dir.resolve()}")
    print(f"🌐 Space repository: {space_repo}")
    print(f"🌐 Space URL: {space_repo_url}")
    print()
    
    # Check if repository exists, create if it doesn't
    hf_token = os.getenv("HF_TOKEN")
    if not check_and_create_space_repo(space_repo, space_dir=space_dir, token=hf_token):
        print("\n⚠️  Continuing with deployment attempt anyway...")
        print("   If repository doesn't exist, deployment will fail.")
        print()
    
    # Create temporary directory for deployment
    temp_dir = None
    try:
        print("🔄 Setting up deployment...")
        temp_dir = Path(tempfile.mkdtemp(prefix="space-deploy-"))
        print(f"   Temporary directory: {temp_dir}")
        
        # Copy Space files to temporary directory
        print("   Copying Space files...")
        for item in space_dir.iterdir():
            # Skip hidden files that shouldn't be in Space (like .git, .env, etc.)
            if item.name.startswith('.') and item.name not in ['.dockerignore', '.gitattributes']:
                continue
            if item.is_dir():
                shutil.copytree(item, temp_dir / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, temp_dir / item.name)
        
        # Initialize git repository in temp directory
        print("   Initializing git repository...")
        subprocess.run(
            ["git", "init"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        
        # Configure git user (required for commit)
        try:
            subprocess.run(
                ["git", "config", "user.name", "Space Deploy"],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "space-deploy@noreply"],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
        except:
            pass  # Use system defaults if config fails
        
        # Add all files
        print("   Staging files...")
        subprocess.run(
            ["git", "add", "-A"],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=temp_dir,
            capture_output=True
        )
        
        if result.returncode != 0 or force:
            # Commit changes
            print(f"   Committing changes: {commit_message}")
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=temp_dir,
                check=True,
                capture_output=True
            )
        else:
            print("   No changes to commit")
            if not force:
                print("   Use --force to push anyway.")
                return
        
        # Add remote
        print("   Adding remote...")
        subprocess.run(
            ["git", "remote", "add", "origin", space_repo_url],
            cwd=temp_dir,
            check=True,
            capture_output=True
        )
        
        # Push to Hugging Face Space
        print("   Pushing to Hugging Face Space...")
        push_success = False
        last_error = None
        for branch in ["main", "master"]:
            try:
                result = subprocess.run(
                    ["git", "push", "-f", "origin", f"HEAD:{branch}"],
                    cwd=temp_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                push_success = True
                break
            except subprocess.CalledProcessError as e:
                error_msg = (e.stderr or e.stdout or "").lower()
                last_error = e
                if "repository not found" in error_msg or "not found" in error_msg:
                    print(f"\n❌ Repository not found: {space_repo_url}")
                    print(f"\nThe repository may not exist or you may not have access.")
                    print(f"Please ensure:")
                    print(f"  1. The Space repository exists at https://huggingface.co/spaces/{space_repo}")
                    print(f"  2. You have write access to the repository")
                    print(f"  3. You're authenticated with Hugging Face:")
                    print(f"     huggingface-cli login")
                    print(f"\nIf the repository doesn't exist, create it at:")
                    print(f"  https://huggingface.co/new-space")
                    print(f"\nOr ensure HF_TOKEN is set in your .env file for automatic creation.")
                    raise SystemExit(1)  # Exit cleanly with error code
                elif branch == "master":
                    # If both branches fail, show the error
                    error_output = (e.stderr or e.stdout or "Unknown error")
                    print(f"\n❌ Failed to push to Hugging Face Space:")
                    print(f"{error_output}")
                    raise SystemExit(1)  # Exit cleanly with error code
                else:
                    print(f"   Branch '{branch}' failed, trying 'master'...")
                    continue
        
        if not push_success:
            if last_error:
                error_output = (last_error.stderr or last_error.stdout or "Unknown error")
                print(f"\n❌ Failed to push to any branch:")
                print(f"{error_output}")
                raise SystemExit(1)  # Exit cleanly with error code
            else:
                print(f"\n❌ Failed to push to any branch (main/master)")
                raise SystemExit(1)  # Exit cleanly with error code
        
        print()
        print("✅ Space app deployed successfully!")
        print(f"   🌐 Space URL: https://huggingface.co/spaces/{space_repo}")
        print("   The Space will rebuild automatically.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during deployment: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"   stdout: {e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"   stderr: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        raise
    
    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            print(f"   Cleaning up temporary directory...")
            shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Main function."""
    args = parse_args()
    
    # Determine Space directory
    if args.space_dir:
        space_dir = Path(args.space_dir).expanduser().resolve()
    else:
        # Default: scripts/deployment/space/cad-llm-api
        # Get the project root (cadllm directory) by going up from script location
        script_dir = Path(__file__).parent  # scripts/deployment
        # Go up to cadllm root: scripts/deployment -> scripts -> cadllm
        cadllm_root = script_dir.parent.parent
        space_dir = cadllm_root / "scripts" / "deployment" / "space" / "cad-llm-api"
    
    # Determine Space repository
    space_repo = args.space_repo or os.getenv("HF_SPACE_REPO") or DEFAULT_SPACE_REPO
    
    # Validate Space directory
    if not space_dir.exists():
        raise ValueError(
            f"Space directory not found: {space_dir}\n"
            f"Please specify --space_dir or ensure the default path exists."
        )
    
    if not space_dir.is_dir():
        raise ValueError(f"Space path is not a directory: {space_dir}")
    
    try:
        deploy_space_app(
            space_dir=space_dir,
            space_repo=space_repo,
            commit_message=args.commit_message,
            force=args.force
        )
    except Exception as e:
        # Only show traceback for unexpected errors
        # Expected errors (like repository not found) are handled inside deploy_space_app
        print(f"\n❌ Deployment failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

