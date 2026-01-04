#!/bin/bash
# Helper script to add missing GitHub secrets

echo "🔐 Adding Missing GitHub Secrets"
echo "================================"
echo ""

# Check authentication
if ! gh auth status &> /dev/null; then
  echo "❌ Not authenticated. Run: gh auth login"
  exit 1
fi

echo "Current secrets:"
gh secret list
echo ""

echo "Missing secrets to add:"
echo "  1. SUPABASE_SERVICE_ROLE_KEY (⚠️  CRITICAL - for backend DB operations)"
echo "  2. SUPABASE_ANON_KEY (if different from SUPABASE_KEY)"
echo "  3. OPENAI_API_KEY (for AI transcription features)"
echo "  4. SENTRY_DSN (optional - for error tracking)"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
  echo "📄 Found .env file"
  echo ""
  echo "You can set secrets from your .env file:"
  echo ""
  
  # Check for SUPABASE_SERVICE_ROLE_KEY
  if grep -q "^SUPABASE_SERVICE_ROLE_KEY=" .env; then
    VALUE=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" .env | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    if [ -n "$VALUE" ] && [ "$VALUE" != "your_supabase_service_role_key_here" ]; then
      echo "Setting SUPABASE_SERVICE_ROLE_KEY from .env..."
      echo "$VALUE" | gh secret set SUPABASE_SERVICE_ROLE_KEY
      echo "✅ SUPABASE_SERVICE_ROLE_KEY set"
    fi
  else
    echo "⚠️  SUPABASE_SERVICE_ROLE_KEY not found in .env"
    echo "   You can set it manually with:"
    echo "   gh secret set SUPABASE_SERVICE_ROLE_KEY"
  fi
  
  # Check for SUPABASE_ANON_KEY
  if grep -q "^SUPABASE_ANON_KEY=" .env; then
    VALUE=$(grep "^SUPABASE_ANON_KEY=" .env | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    if [ -n "$VALUE" ] && [ "$VALUE" != "your_supabase_anon_key_here" ]; then
      echo "Setting SUPABASE_ANON_KEY from .env..."
      echo "$VALUE" | gh secret set SUPABASE_ANON_KEY
      echo "✅ SUPABASE_ANON_KEY set"
    fi
  fi
  
  # Check for OPENAI_API_KEY
  if grep -q "^OPENAI_API_KEY=" .env; then
    VALUE=$(grep "^OPENAI_API_KEY=" .env | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    if [ -n "$VALUE" ] && [ "$VALUE" != "your_openai_api_key_here" ]; then
      echo "Setting OPENAI_API_KEY from .env..."
      echo "$VALUE" | gh secret set OPENAI_API_KEY
      echo "✅ OPENAI_API_KEY set"
    else
      echo "⚠️  OPENAI_API_KEY not set in .env"
    fi
  else
    echo "⚠️  OPENAI_API_KEY not found in .env"
  fi
  
  # Check for SENTRY_DSN (optional)
  if grep -q "^SENTRY_DSN=" .env; then
    VALUE=$(grep "^SENTRY_DSN=" .env | cut -d'=' -f2- | sed 's/^"//;s/"$//')
    if [ -n "$VALUE" ] && [ "$VALUE" != "your_sentry_dsn_here" ]; then
      echo "Setting SENTRY_DSN from .env..."
      echo "$VALUE" | gh secret set SENTRY_DSN
      echo "✅ SENTRY_DSN set"
    fi
  fi
  
else
  echo "⚠️  .env file not found"
  echo ""
  echo "You can set secrets manually:"
  echo ""
  echo "  # Most critical - required for backend operations"
  echo "  gh secret set SUPABASE_SERVICE_ROLE_KEY"
  echo ""
  echo "  # For AI features"
  echo "  gh secret set OPENAI_API_KEY"
  echo ""
  echo "  # Optional - if you have SUPABASE_ANON_KEY separate from SUPABASE_KEY"
  echo "  gh secret set SUPABASE_ANON_KEY"
  echo ""
  echo "  # Optional - for error tracking"
  echo "  gh secret set SENTRY_DSN"
fi

echo ""
echo "✅ Done! Verify with: gh secret list"
echo ""

