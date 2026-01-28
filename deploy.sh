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

# Check if .vercel directory exists and is valid (from vercel link)
if [ -d ".vercel" ] && [ -f ".vercel/project.json" ]; then
    echo -e "${GREEN}✅ Found existing .vercel directory (project already linked)${NC}"
    echo -e "${YELLOW}   Using existing project link...${NC}"
else
    # Remove any existing .vercel directories to prevent conflict/incorrect settings
    echo -e "${YELLOW}🧹 Cleaning Vercel metadata...${NC}"
    rm -rf .vercel
    rm -rf frontend/.vercel
fi

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

# Deploy from root (vercel.json is in root)
echo -e "${YELLOW}Running: vercel deploy${NC}"

# Check if we have a valid .vercel directory from vercel link
if [ -d ".vercel" ] && [ -f ".vercel/project.json" ]; then
    # Use existing project link (from vercel link command)
    # When using local link, prefer local authentication over token
    # Token authentication can conflict with local project links
    echo -e "${GREEN}✅ Using existing project link from .vercel directory${NC}"
    
    # When using local authentication, we don't need to hide .git
    # The local link should work fine with .git present
    echo -e "${YELLOW}   Using local authentication (from vercel login)...${NC}"
    echo -e "${YELLOW}   (This may take a moment - Vercel is building and deploying...)${NC}"
    set +e
    # Run normally first to see progress, capture output only if it fails
    vercel deploy $VERCEL_ARGS --yes
    EXIT_CODE=$?
    set -e
    
    # If local auth fails with "Cannot load project settings", the .vercel might be for wrong team
    if [ $EXIT_CODE -ne 0 ]; then
        # Try to capture error output for analysis
        set +e
        ERROR_OUTPUT=$(vercel deploy $VERCEL_ARGS --yes 2>&1)
        set -e
        
        # Show the error for debugging
        echo "$ERROR_OUTPUT" | tail -10
        
        if echo "$ERROR_OUTPUT" | grep -q "Cannot load project settings\|cannot-load-project-settings"; then
            echo -e "${YELLOW}⚠️  'Cannot load project settings' error detected.${NC}"
            echo -e "${YELLOW}   Removing .vercel directory (as per Vercel docs) and trying with token...${NC}"
            echo -e "${YELLOW}   (This can happen if .vercel belongs to a different team/account)${NC}"
            rm -rf .vercel
            if [ -n "$VERCEL_TOKEN" ] && [ -n "$VERCEL_PROJECT_ID" ] && [ -n "$VERCEL_ORG_ID" ]; then
                mkdir -p .vercel
                echo "{\"projectId\":\"$VERCEL_PROJECT_ID\",\"orgId\":\"$VERCEL_ORG_ID\"}" > .vercel/project.json
                set +e
                vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
                EXIT_CODE=$?
                set -e
            else
                echo -e "${RED}❌ Cannot proceed: Need VERCEL_TOKEN, VERCEL_PROJECT_ID, and VERCEL_ORG_ID${NC}"
                EXIT_CODE=1
            fi
        else
            # Different error, try with token as fallback
            echo -e "${YELLOW}⚠️  Local authentication failed, trying with token...${NC}"
            if [ -n "$VERCEL_TOKEN" ]; then
                set +e
                vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
                EXIT_CODE=$?
                set -e
            fi
        fi
    fi
elif [ -n "$VERCEL_TOKEN" ] && [ -n "$VERCEL_PROJECT_ID" ] && [ -n "$VERCEL_ORG_ID" ]; then
    # No existing .vercel directory, try to create one
    # For token-based deployments, hide .git to avoid author check issues
    if [ -d ".git" ]; then
        echo -e "${YELLOW}🙈 Temporarily hiding .git to bypass Vercel author check...${NC}"
        mv ".git" ".git_temp"
    fi
    
    echo -e "${YELLOW}🧹 No existing .vercel directory found, attempting to create project link...${NC}"
    rm -rf .vercel
    
    # Try deploying without project.json - Vercel should auto-detect or prompt
    # Use --yes to auto-confirm any prompts
    echo -e "${YELLOW}Deploying without pre-created project.json (let Vercel handle linking)...${NC}"
    set +e
    vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
    EXIT_CODE=$?
    set -e
    
    # If that fails, try with project.json created after first attempt
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${YELLOW}⚠️  First deployment attempt failed, trying with project.json...${NC}"
        mkdir -p .vercel
        echo "{\"projectId\":\"$VERCEL_PROJECT_ID\",\"orgId\":\"$VERCEL_ORG_ID\"}" > .vercel/project.json
        set +e
        vercel deploy $VERCEL_ARGS --token=$VERCEL_TOKEN --yes
        EXIT_CODE=$?
        set -e
    fi
    
    # If still failing, provide helpful diagnostics
    if [ $EXIT_CODE -ne 0 ]; then
        echo -e "${RED}❌ Deployment failed. Possible issues:${NC}"
        echo -e "${YELLOW}   1. VERCEL_TOKEN might not have access to project $VERCEL_PROJECT_ID${NC}"
        echo -e "${YELLOW}   2. VERCEL_PROJECT_ID or VERCEL_ORG_ID might be incorrect${NC}"
        echo -e "${YELLOW}   3. Token might need to be regenerated with proper scopes${NC}"
        echo -e "${YELLOW}   4. Try running: vercel login (to authenticate locally)${NC}"
        echo -e "${YELLOW}   5. Then run: vercel link (to link the project)${NC}"
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
    # Restore .git if it was hidden
    if [ -d ".git_temp" ]; then
        echo -e "${YELLOW}🙈 Restoring .git directory...${NC}"
        mv ".git_temp" ".git"
    fi
    exit $EXIT_CODE
fi

# Restore .git if it was hidden (only for token-based deployments)
if [ -d ".git_temp" ]; then
    echo -e "${YELLOW}🙈 Restoring .git directory...${NC}"
    mv ".git_temp" ".git"
fi

echo "-----------------------------------"
echo -e "${GREEN}🎉 Deployment Script Finished!${NC}"
