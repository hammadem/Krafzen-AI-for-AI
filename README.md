## 🧭 Contributing Guidelines – Krafzen AI Frontend (Next.js)

---

### 🚀 Tech Stack
| Category      | Technology                  |
|----------------|-----------------------------|
| **Framework**  | Next.js 14+                 |
| **Auth**       | Supabase (JWT sessions)     |
| **Monitoring** | Sentry                      |
| **Analytics**  | PostHog                     |
| **Deployment** | Vercel                      |

---

### 🌿 Branch Strategy

| Branch Name | Purpose |
|--------------|----------|
| `main`       | Production-ready code |
| `staging`    | Integration testing & pre-demo before merging into main |
| `feature/*`   | Active branch on to add new feature |

---

### ✍️ Commit Message Format

We follow **[Conventional Commits]
(https://www.conventionalcommits.org/)**.

**Format:**

**Types:**
- `feat`: new feature (e.g. `feat: add voice recording UI`)
- `fix`: bug fix (e.g. `fix: handle Supabase auth refresh`)
- `chore`: setup or minor update (e.g. `chore: setup Sentry + PostHog`)
- `refactor`: code improvement
- `style`: UI or CSS updates
- `docs`: documentation updates

```
# check for staging branch locally 
git checkout staging

# fetch the fresh changes from staging branch
git pull upstream staging

# create branch feature/details to make a meaningfull commit
git checkout -b feature/setup

# Go to github.com from your forked repo merge the changes to the branch

```

---

### 🤝 PR Review Checklist

Before submitting a Pull Request, ensure that:

- ✅ Runs locally without errors  
- ✅ Passes lint (`npm run lint`)  
- ✅ UI tested on **mobile** + **desktop**  
- ✅ Includes clear commit messages  
- ✅ Sentry & PostHog initialized correctly  
- ✅ No sensitive data in code  

---

💡 *Following these practices helps maintain clean, stable, and production-ready code across all environments.*

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
git clone https://github.com/Sonudhukia143/krafzen-ai.git

cd krafzen-ai

git remote add upstream https://github.com/khadijazain46-hub/krafzen-ai.git

npm install

npm run dev

```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
