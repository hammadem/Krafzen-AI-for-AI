# Setting Up GitHub Secrets via Command Line

## Method 1: Using GitHub CLI (Recommended)

### Installation

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

**Windows:**
```bash
winget install GitHub.cli
```

### Authentication

1. **Login to GitHub:**
```bash
gh auth login
```

Follow the prompts to authenticate (browser or token).

2. **Verify authentication:**
```bash
gh auth status
```

### Setting Secrets

Once authenticated, you can set secrets using:

```bash
# Set individual secrets
gh secret set SUPABASE_URL --body "https://your-project.supabase.co"
gh secret set SUPABASE_ANON_KEY --body "your-anon-key-here"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "your-service-role-key-here"
gh secret set OPENAI_API_KEY --body "your-openai-key-here"
gh secret set SENTRY_DSN --body "your-sentry-dsn-here"  # Optional

# Set from environment variable
export SUPABASE_URL="https://your-project.supabase.co"
gh secret set SUPABASE_URL --body "$SUPABASE_URL"

# Set from file (useful for long keys)
gh secret set SUPABASE_SERVICE_ROLE_KEY < ~/.supabase/service-role-key.txt
```

### Viewing Secrets

```bash
# List all secrets (names only, not values)
gh secret list

# Check if a specific secret exists
gh secret list | grep SUPABASE_URL
```

### Deleting Secrets

```bash
gh secret delete SUPABASE_URL
```

---

## Method 2: Using GitHub API with curl

If you prefer not to install GitHub CLI, you can use the GitHub API directly:

### Prerequisites

1. **Create a Personal Access Token (PAT):**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Select scopes: `repo` and `admin:repo_hook`
   - Copy the token

2. **Set your token:**
```bash
export GITHUB_TOKEN="your-personal-access-token-here"
export GITHUB_REPO="KRAFZEN/KRAFZEN-AI-"  # Your repo in format: owner/repo
```

### Setting Secrets via API

The GitHub API requires encrypting secrets with the repository's public key. Here's a script to do it:

```bash
#!/bin/bash
# save-secret.sh - Helper script to set GitHub secrets via API

set -e

# Configuration
GITHUB_REPO="${GITHUB_REPO:-KRAFZEN/KRAFZEN-AI-}"
SECRET_NAME="$1"
SECRET_VALUE="$2"

if [ -z "$SECRET_NAME" ] || [ -z "$SECRET_VALUE" ]; then
  echo "Usage: $0 <SECRET_NAME> <SECRET_VALUE>"
  echo "Example: $0 SUPABASE_URL 'https://xxx.supabase.co'"
  exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable not set"
  echo "Get a token from: https://github.com/settings/tokens"
  exit 1
fi

# Get repository public key
echo "Fetching repository public key..."
PUBLIC_KEY_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$GITHUB_REPO/actions/secrets/public-key")

PUBLIC_KEY=$(echo "$PUBLIC_KEY_RESPONSE" | grep -o '"key":"[^"]*' | cut -d'"' -f4)
KEY_ID=$(echo "$PUBLIC_KEY_RESPONSE" | grep -o '"key_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$PUBLIC_KEY" ] || [ -z "$KEY_ID" ]; then
  echo "Error: Failed to get public key. Check your token permissions."
  exit 1
fi

# Encrypt the secret using sodium (requires libsodium)
# For macOS: brew install libsodium
# For Linux: apt-get install libsodium-dev

if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is required for encryption"
  exit 1
fi

ENCRYPTED_VALUE=$(python3 <<EOF
from base64 import b64encode
from nacl import encoding, public

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key_bytes = b64decode(public_key)
    public_key_obj = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key_obj)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

import sys
from base64 import b64decode
try:
    from nacl import encoding, public
    result = encrypt("$PUBLIC_KEY", "$SECRET_VALUE")
    print(result)
except ImportError:
    print("Error: PyNaCl library required. Install with: pip install pynacl", file=sys.stderr)
    sys.exit(1)
EOF
)

if [ $? -ne 0 ]; then
  echo "Error: Encryption failed. Install PyNaCl: pip install pynacl"
  exit 1
fi

# Set the secret
echo "Setting secret: $SECRET_NAME..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$GITHUB_REPO/actions/secrets/$SECRET_NAME" \
  -d "{\"encrypted_value\":\"$ENCRYPTED_VALUE\",\"key_id\":\"$KEY_ID\"}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 204 ] || [ "$HTTP_CODE" -eq 201 ]; then
  echo "✅ Secret '$SECRET_NAME' set successfully"
else
  echo "❌ Failed to set secret. HTTP $HTTP_CODE"
  echo "$BODY"
  exit 1
fi
```

**Make it executable:**
```bash
chmod +x save-secret.sh
```

**Install PyNaCl (required for encryption):**
```bash
pip install pynacl
```

**Usage:**
```bash
export GITHUB_TOKEN="your-token"
export GITHUB_REPO="KRAFZEN/KRAFZEN-AI-"

./save-secret.sh SUPABASE_URL "https://your-project.supabase.co"
./save-secret.sh SUPABASE_ANON_KEY "your-anon-key"
./save-secret.sh SUPABASE_SERVICE_ROLE_KEY "your-service-role-key"
./save-secret.sh OPENAI_API_KEY "your-openai-key"
```

---

## Method 3: Bulk Setup Script

Create a script to set all secrets at once:

```bash
#!/bin/bash
# setup-all-secrets.sh

set -e

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo "Error: GitHub CLI (gh) not installed"
  echo "Install with: brew install gh (macOS) or see https://cli.github.com"
  exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
  echo "Not authenticated. Running: gh auth login"
  gh auth login
fi

echo "Setting up GitHub secrets..."
echo ""

# Read secrets from your .env file (don't commit this!)
if [ -f "backend/.env" ]; then
  echo "Reading from backend/.env..."
  
  # Extract and set each secret
  while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove quotes from value
    value=$(echo "$value" | sed 's/^"//;s/"$//')
    
    # Only set secrets that should be secrets
    case "$key" in
      SUPABASE_URL|SUPABASE_ANON_KEY|SUPABASE_SERVICE_ROLE_KEY|OPENAI_API_KEY|SENTRY_DSN)
        echo "Setting $key..."
        echo "$value" | gh secret set "$key"
        ;;
    esac
  done < backend/.env
  
  echo ""
  echo "✅ All secrets set!"
  echo ""
  echo "Verify with: gh secret list"
else
  echo "Error: backend/.env file not found"
  echo "Create it from backend/env.example first"
  exit 1
fi
```

**Usage:**
```bash
chmod +x setup-all-secrets.sh
./setup-all-secrets.sh
```

---

## Quick Reference

### GitHub CLI Commands:
```bash
# List all secrets
gh secret list

# Set a secret
gh secret set SECRET_NAME --body "value"

# Delete a secret
gh secret delete SECRET_NAME

# View secret (shows if it exists, not the value)
gh secret list | grep SECRET_NAME
```

### Required Secrets for This Project:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `SENTRY_DSN` (optional)

---

## Security Notes

1. **Never commit secrets** to the repository
2. **Use different keys** for staging and production
3. **Rotate keys regularly**
4. **Limit token permissions** (only `repo` scope needed)
5. **Store tokens securely** (use password manager or keychain)

---

## Troubleshooting

**"gh: command not found"**
- Install GitHub CLI: `brew install gh` (macOS) or see installation instructions above

**"Authentication required"**
- Run: `gh auth login`
- Follow the prompts to authenticate

**"Permission denied"**
- Check your token has `repo` and `admin:repo_hook` scopes
- Verify you have admin access to the repository

**"Secret not found"**
- List secrets: `gh secret list`
- Verify the secret name is correct (case-sensitive)

