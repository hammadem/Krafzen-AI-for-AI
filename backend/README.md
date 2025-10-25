# KRAFZEN AI Backend

FastAPI backend for voice/text to DXF MVP (60-Day Roadmap).

## Setup (Week 1)
1. `pip install -r requirements.txt`
2. `cp .env.example .env` → Fill Supabase/OpenAI keys
3. `./scripts/setup_supabase.sh` (pushes schema.sql)
4. `make run` → http://localhost:8000/docs

## Milestones
- Weeks 1-2: Supabase schema + API connects (Krish V)
- Tests: `make test` (100% coverage target)
- Deploy: Render via render.yaml (Kiruthika)

Team: Kiruthika (Lead), Sonu (Frontend), Laxmi (Data), Ashwani (QA).
