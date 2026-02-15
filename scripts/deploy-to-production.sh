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

echo "🔄 Syncing staging with main (so staging is not behind)..."
git checkout staging
git pull origin staging
git merge main -m "chore: sync staging with main after production deploy"
echo "📤 Pushing staging to origin..."
git push origin staging

echo ""
echo "✅ Production deploy triggered and staging synced with main:"
echo "   • Backend: push to main → Render production (deploy-backend.yml)"
echo "   • Frontend: push to main → Vercel production (main-frontend.yaml)"
echo "   • Staging branch updated to match main."
echo "   Check GitHub Actions for status."
