#!/usr/bin/env node
// Only run husky when not in CI and .git exists (avoids ".git can't be found" on Vercel)
const fs = require('fs');
const { execSync } = require('child_process');
if (process.env.CI !== 'true' && fs.existsSync('.git')) {
  execSync('npx husky', { stdio: 'inherit' });
}
