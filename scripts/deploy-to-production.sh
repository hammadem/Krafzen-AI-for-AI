#!/usr/bin/env bash
# Sync staging into main and push. GitHub Actions will deploy:
#   - main → Render (production backend) + Vercel (production frontend)
# Run from repo root. Requires clean working tree on current branch.

set -e
cd "$(git rev-parse --show-toplevel)"

if [[ -n $(git status --porcelain) ]]; then
  echo "❌ Working tree has uncommitted changes. Commit or stash them first."
  git status --short
  exit 1
fi

echo "📥 Fetching latest from origin..."
git fetch origin

echo "🔄 Syncing main with staging..."
git checkout main
git pull origin main
git merge origin/staging -m "chore: deploy to production — sync staging into main"
echo "📤 Pushing main to origin (this triggers production deploys)..."
git push origin main

echo "↩️  Switching back to staging..."
git checkout staging

echo ""
echo "✅ Production deploy triggered:"
echo "   • Backend: push to main → Render production (deploy-backend.yml)"
echo "   • Frontend: push to main → Vercel production (main-frontend.yaml)"
echo "   Check GitHub Actions for status."
