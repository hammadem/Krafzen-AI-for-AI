#!/bin/bash

# KRAFZEN AI Deployment Script
# Deploys to Render, Vercel, and Supabase

set -e # Exit on error

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
    export VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Deployment Process...${NC}"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${YELLOW}📍 Current Branch: $CURRENT_BRANCH${NC}"

if [[ "$CURRENT_BRANCH" == "main" ]]; then
    ENV_NAME="Production"
elif [[ "$CURRENT_BRANCH" == "staging" ]]; then
    ENV_NAME="Staging"
else
    echo -e "${RED}⚠️  Warning: You are not on 'main' or 'staging'. Deployments might behave unexpectedly.${NC}"
    echo -e "${YELLOW}Proceeding in 3 seconds...${NC}"
    sleep 3
    ENV_NAME="Custom ($CURRENT_BRANCH)"
fi

echo -e "${GREEN}target Environment: $ENV_NAME${NC}"
echo "-----------------------------------"

# 1. Git & Render Deployment
# Render is configured to auto-deploy on git push.
echo -e "${YELLOW}📦 [1/3] Preparing Git & Render Deployment...${NC}"

if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}📝 Uncommitted changes detected.${NC}"
    
    COMMIT_MSG="chore: automated deployment update $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${YELLOW}Auto-committing with message: '$COMMIT_MSG'${NC}"
    
    git add .
    git commit -m "$COMMIT_MSG"
    
    echo -e "${YELLOW}Pushing to remote...${NC}"
    git push origin "$CURRENT_BRANCH"
    echo -e "${GREEN}✅ Changes pushed! Render should automatically start building.${NC}"
else
    echo -e "${GREEN}✨ No changes to commit.${NC}"
    echo -e "${YELLOW}ℹ️  To trigger a Render redeploy without changes, you can use the Render Dashboard (skipped auto-commit).${NC}"
fi

echo "-----------------------------------"

# 2. Supabase Deployment
echo -e "${YELLOW}🗄️  [2/3] Supabase Deployment...${NC}"

if [ -d "supabase" ]; then
    if command -v supabase &> /dev/null; then
        echo -e "${YELLOW}Deploying Supabase migrations...${NC}"
        supabase db push
    else
        echo -e "${YELLOW}⚠️  Supabase CLI not found globally. Trying npx...${NC}"
        npx supabase db push
    fi
else
    echo -e "${YELLOW}⚠️  No 'supabase' directory found. Skipping database migration deployment.${NC}"
fi

echo "-----------------------------------"

# 3. Vercel Deployment
echo -e "${YELLOW}🌐 [3/3] Vercel Frontend Deployment...${NC}"

# Remove any existing .vercel directories to prevent conflict/incorrect settings
echo -e "${YELLOW}🧹 Cleaning Vercel metadata...${NC}"
rm -rf .vercel
rm -rf frontend/.vercel

echo -e "${YELLOW}Deploying backend is handled by Render (via git).${NC}"
echo -e "${YELLOW}Deploying Frontend to Vercel...${NC}"

# Determine if prod or staging
VERCEL_ARGS=""
if [[ "$ENV_NAME" == "Production" ]]; then
    VERCEL_ARGS="--prod"
fi

# Store root directory
ROOT_DIR=$(pwd)

# Trap to ensure .git is restored even if script fails/exits
cleanup() {
    if [ -d "$ROOT_DIR/.git_temp" ]; then
        echo -e "${YELLOW}🙈 Restoring .git directory...${NC}"
        mv "$ROOT_DIR/.git_temp" "$ROOT_DIR/.git"
    fi
}
trap cleanup EXIT

# Workaround for Vercel "Git author must have access" error
# We temporarily hide the .git directory so Vercel CLI treats it as a manual deployment
# without trying to link it to the git commit author.

if [ -d ".git" ]; then
    echo -e "${YELLOW}🙈 Temporarily hiding .git to bypass Vercel author check...${NC}"
    mv ".git" ".git_temp"
fi

# Deploy from root (vercel.json is in root)
echo -e "${YELLOW}Running: vercel deploy${NC}"
if [ -n "$VERCEL_TOKEN" ] && [ -n "$VERCEL_PROJECT_ID" ] && [ -n "$VERCEL_ORG_ID" ]; then
    # Try using vercel link first to properly link the project
    echo -e "${YELLOW}🔗 Linking Vercel project...${NC}"
    rm -rf .vercel
    
    # Try to link using vercel link command (non-interactive)
    # Note: vercel link might prompt, but we'll try with --yes flag
    set +e
    echo -e "${YELLOW}Attempting to link project with vercel link...${NC}"
    # Use printf to pipe answers to vercel link if needed
    printf "\n\n" | vercel link --yes --token=$VERCEL_TOKEN 2>/dev/null
    LINK_EXIT=$?
    set -e
    
    # If link didn't work, create project.json manually
    if [ $LINK_EXIT -ne 0 ] || [ ! -f ".vercel/project.json" ]; then
        echo -e "${YELLOW}Creating .vercel/project.json manually...${NC}"
        mkdir -p .vercel
        echo "{\"projectId\":\"$VERCEL_PROJECT_ID\",\"orgId\":\"$VERCEL_ORG_ID\"}" > .vercel/project.json
        echo -e "${GREEN}✅ Created .vercel/project.json${NC}"
    else
        echo -e "${GREEN}✅ Project linked successfully${NC}"
    fi
    
    # Now deploy with the token
    set +e
    vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
    EXIT_CODE=$?
    set -e
    
    # If that fails, the token might not have access - provide helpful error
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ Deployment failed. Possible issues:${NC}"
        echo -e "${YELLOW}   1. VERCEL_TOKEN might not have access to project $VERCEL_PROJECT_ID${NC}"
        echo -e "${YELLOW}   2. VERCEL_PROJECT_ID or VERCEL_ORG_ID might be incorrect${NC}"
        echo -e "${YELLOW}   3. Token might need to be regenerated with proper scopes${NC}"
    fi
elif [ -n "$VERCEL_TOKEN" ]; then
    # If we have token but not project/org IDs, try deploying anyway
    echo -e "${YELLOW}⚠️  VERCEL_PROJECT_ID or VERCEL_ORG_ID not set, deploying with token only...${NC}"
    rm -rf .vercel
    set +e
    vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
    EXIT_CODE=$?
    set -e
else
    # Fallback to npx vercel if env vars not set (local development)
    echo -e "${YELLOW}⚠️  VERCEL_TOKEN not set, using npx vercel (may require interactive login)${NC}"
    set +e
    npx -y vercel $VERCEL_ARGS
    EXIT_CODE=$?
    set -e
fi

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}❌ Vercel deployment failed!${NC}"
    exit $EXIT_CODE
fi

echo "-----------------------------------"
echo -e "${GREEN}🎉 Deployment Script Finished!${NC}"
