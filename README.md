# Ghost Typing

An AI conversation-style tool for **reflective closure**, built on a person's own saved messages.

Ghost Typing lets a user import a real message history with someone they can no longer (or won't) talk to, learn the texting style of that conversation, and complete structured guided sessions to say what was never said — framed as a reflective writing exercise, not as talking to the real person.

> **What this is not:** This product does not recreate or channel real people. It simulates *message patterns* learned from text the user already has, and it is designed — deliberately — against rumination, impersonation, harassment, and unhealthy fixation. Safety, consent, and wellbeing requirements are P0, equal in priority to features. See [PRD Section 7](docs/PRD.md#7-safety-ethics--wellbeing-requirements).

---

## Core Principles

These are enforced in code and architecture, not just copy:

| Principle | How it's enforced |
|---|---|
| Always visibly a simulation | Non-dismissible banner + dashed amber bubbles on every simulated-response screen (`5.5`) |
| Defined endings, no infinite chat | Server-enforced time-boxing on all modes (`7.2`) |
| Say Goodbye happens once | One-shot final message, idempotence-guarded server-side, non-repeatable per thread |
| No dark-pattern re-engagement | No push notifications, streaks, or return prompts for ghost threads (`7.2`) — explicitly disallowed |
| Crisis handling is non-negotiable | Two-layer detection middleware on every model call, break-character instruction in the system prompt, non-dismissible resource overlay (`7.5`) |
| Grief simulation out of scope for MVP | Conservative detector at import → hard block + redirect (`7.4`) |
| Someone else's words get the highest data bar | Encrypted-at-rest raw blobs, no ad targeting/resale/model training without opt-in, verified cascading delete with receipt (`7.7`) |
| High engagement is a warning sign | Analytics treat same-thread fixation rate as an alertable risk signal, not a success metric (`3.2`) |

## Tech Stack

- **Backend:** Python / FastAPI
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Database:** PostgreSQL (managed)
- **Object storage:** S3-compatible, encrypted at rest (raw imports)
- **LLM:** Claude via Anthropic API (prompt-based style modeling — no fine-tuning in MVP)
- **Auth:** Supabase Auth (JWT) with 18+ attestation gate
- **Analytics:** Self-hosted PostHog, aggregate-only events, salted-HMAC user IDs
- **Infra:** Docker Compose locally; Vercel or AWS ECS/Fargate in production

## Project Structure

```
ghost-typing/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py            # env-driven settings incl. safety thresholds
│       ├── models.py            # User, Thread, Session, DeletionToken
│       ├── dependencies.py      # JWT auth + age/onboarding gates
│       ├── routers/
│       │   ├── imports.py       # thread import: parse, PII strip, profile, grief flag
│       │   ├── sessions.py      # start/send/final; timebox + mode gating
│       │   └── privacy.py       # cascading delete w/ receipt, GDPR-style export
│       ├── services/
│       │   ├── parser.py        # speaker parsing + PII stripping
│       │   ├── style_profile.py # NLP stats profile (no LLM call)
│       │   ├── llm.py           # generation behind safety middleware
│       │   ├── goodbye.py       # phased Say Goodbye logic + one-shot final
│       │   ├── summary.py       # journal-shaped post-session summary
│       │   ├── storage.py       # encrypted raw-blob store
│       │   ├── analytics.py     # aggregate-only event taxonomy
│       │   └── risk_alerts.py   # inverted-metric thresholds + responses
│       └── safety/
│           ├── middleware.py    # system prompt contract (8.3 structural requirements)
│           ├── crisis.py        # two-layer crisis detection
│           └── grief_detector.py
├── frontend/
│   └── src/
│       ├── pages/               # Onboarding, AgeGate, AppShell
│       └── components/
│           ├── SimulationBanner.tsx    # always-on label (no dismiss exists)
│           ├── ChatView.tsx
│           ├── GoodbyeChat.tsx         # writing → final_ready → closed phases
│           ├── CrisisOverlay.tsx       # non-dismissible resource surface
│           ├── RepeatUseCheckinModal.tsx
│           └── SessionEnd.tsx          # reflection + mood + editable summary
├── docker-compose.yml
├── docs/PRD.md
└── README.md
```

## Getting Started (Local Dev)

### Prerequisites

- Python 3.11+, Node 18+
- Docker (for Postgres)

### Setup

```bash
# 1. Clone & start the database
git clone <repo-url> && cd ghost-typing
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then fill in:
#   ANTHROPIC_API_KEY=sk-...
#   DATABASE_URL=postgresql://gt:gt@localhost:5432/ghosttyping
#   JWT_SECRET=<random>
#   ANALYTICS_SALT=<random>

uvicorn app.main:app --reload   # http://localhost:8000

# 3. Frontend
cd ../frontend
npm install
echo 'VITE_API_URL=http://localhost:8000' > .env.local
npm run dev                     # http://localhost:5173

# 4. Or everything at once:
docker compose up
```

### Running Tests

```bash
cd backend
pytest                          # safety-critical paths first
pytest tests/test_safety.py -v  # crisis + grief detection
```

**Note:** `tests/test_crisis_recall.py` gates external beta — it requires a labeled eval set (~200 messages) meeting **≥95% crisis recall / ≤5% false-positive rate** before any release outside internal use. The regex layer is scaffolding only.

## Key Flows

### Import → Session lifecycle

1. **Import** — paste a conversation; parser separates speakers, strips PII, builds a style profile via NLP stats, flags grief context.
2. **Grief redirect** — if flagged, standard flow is blocked at session start with resources instead (`409 grief_redirect`).
3. **Guided sessions** — five modes: `unsaid`, `replay`, `question`, `goodbye`, `free` (free gated behind ≥1 completed guided session).
4. **Every send** passes through: timebox check → crisis pre-screen → LLM (with fixed-structure safety system prompt) → crisis post-screen → transcript.
5. **Session end** — reflection prompt, editable journal-shaped summary (user's words only), mood check-in, plain-text private export.
6. **Delete** — blob deletion *before* DB commit; failure aborts deletion honestly; tombstone receipt issued only on full success.

### Say Goodbye (the most delicate feature)

Up to 6 turns of writing → explicit "Receive the goodbye" consent step → one final closing message → server force-closes session. Re-running goodbye on the same thread returns a gentle redirect naming the pattern, not a punishment:

> *"You've already completed a goodbye for this conversation. If you're not ready to let it stay finished, that's worth noticing."*

## Safety Architecture

```
User input ──► [crisis pre-screen] ──► [timebox/mode gates] ──► LLM call
                                                                      │
Display ◄──── [crisis post-screen] ◄──────────────────────────────────┘
                    │
                    ▼ (if CRISIS)
             Break character → non-dismissible resource overlay →
             session ends with reason=crisis_redirect → review queue
```

The LLM system prompt carries hard-coded structural rules (never claim to be the real person; never invent opinions/confessions not evidenced in source material; never encourage contact/reconciliation; break character on distress). These are part of the prompt contract in `safety/middleware.py` and are never mode-dependent.

## Metrics Philosophy (deliberately inverted)

Success looks like **resolution, not engagement**:

- Session completion rate **>60%**
- Median **1–3 sessions** per thread, then stop
- 7-day same-thread return rate **<25%** — high numbers here trigger review, not celebration
- Mood check-in **>70% neutral-to-better**
- **100%** correct handling of crisis escalations

Risk alerts live in `services/risk_alerts.py` with defined owners and responses — e.g., >10% of threads reaching ≥5 sessions in 14 days triggers a product review of that cohort's journey.

## Known Limitations (pre-beta)

- ⚠️ Crisis detection uses regex + LLM classifier scaffold — requires trained classifier + eval set before external beta
- Paste-based import only (file exports/screenshots planned)
- Style modeling fidelity unvalidated against the 40-message minimum threshold
- Age assurance is attestation-only pending regional requirements
- Legal review outstanding: right of publicity, GDPR treatment of the simulated person as a data subject, ToS language
- Clinical review of all wellbeing-facing copy outstanding

## Contributing

Any PR touching these areas requires explicit reviewer sign-off from the safety owner:

- `app/safety/**`
- System prompt contract in `middleware.py`
- Crisis/grief detection patterns or thresholds
- Anything affecting the always-on simulation labeling
- Analytics event taxonomy

When in doubt, the PRD's rule applies: **a build that hits every feature but skips Section 7 is not shippable.**

## License & Status

Draft/internal — not for public release until legal, clinical, and safety reviews complete. See `docs/PRD.md` §9 for open risks.
