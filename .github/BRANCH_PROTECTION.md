# GitHub Branch Protection Configuration

## Required Settings for Main and Staging Branches

### 1. Main Branch Protection
- **Require a pull request before merging**: ✅
- **Required number of reviewers**: 1
- **Dismiss stale reviews when new commits are pushed**: ✅
- **Require review from code owners**: ✅
- **Restrict pushes that create files**: ✅
- **Require status checks to pass before merging**: ✅
- **Require branches to be up to date before merging**: ✅
- **Require conversation resolution before merging**: ✅
- **Require signed commits**: ❌ (Optional for MVP)
- **Require linear history**: ❌ (Optional for MVP)
- **Include administrators**: ✅
- **Allow force pushes**: ❌
- **Allow deletions**: ❌

### 2. Staging Branch Protection
- **Require a pull request before merging**: ✅
- **Required number of reviewers**: 1
- **Dismiss stale reviews when new commits are pushed**: ✅
- **Require review from code owners**: ✅
- **Restrict pushes that create files**: ✅
- **Require status checks to pass before merging**: ✅
- **Require branches to be up to date before merging**: ✅
- **Require conversation resolution before merging**: ✅
- **Include administrators**: ✅
- **Allow force pushes**: ❌
- **Allow deletions**: ❌

### 3. Required Status Checks
- **CI/CD Pipeline**: `test` job must pass
- **Code Quality**: Linting checks must pass
- **Health Checks**: Deployment health checks must pass

### 4. Code Owners
Create `.github/CODEOWNERS` file:
```
# Global code owners
* @kiruthika

# Backend specific
/backend/ @kiruthika

# Frontend specific (when added)
/frontend/ @frontend-team

# Documentation
*.md @kiruthika
```

## Setup Instructions

1. Go to repository Settings → Branches
2. Add rule for `main` branch with above settings
3. Add rule for `staging` branch with above settings
4. Create `.github/CODEOWNERS` file
5. Test by creating a PR to staging branch

## Benefits
- Prevents direct pushes to protected branches
- Ensures code review process
- Maintains code quality standards
- Prevents broken deployments
- Enforces CI/CD pipeline completion
