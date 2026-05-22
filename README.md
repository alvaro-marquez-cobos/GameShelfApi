# GameShelf API

Backend API for GameShelf — a multi-platform video game library management app. Aggregates data from Steam, Epic Games, GOG, and PlayStation into a single unified layer, enriched with completion times, Linux compatibility ratings, and deal tracking.

## Stack

| Component | Technology |
|---|---|
| Framework | FastAPI 0.115+ · Python 3.12+ |
| Database | Firestore (Firebase Admin SDK) |
| Cache | Upstash Redis (serverless) |
| Auth | Firebase ID tokens (server-side verification) |
| HTTP Client | httpx (async) |
| Scheduler | APScheduler (deal notifications) |
| Deploy | Docker + Render |

## Architecture

Vertical Slice + Clean Architecture. Each module is fully independent with its own `domain/`, `application/`, and `infrastructure/` layers.

```
GameShelfApi/
├── main.py                  # App factory, lifespan, middleware
├── composition/
│   ├── dependencies.py      # Dependency injection (FastAPI Depends)
│   ├── router_registry.py   # Module router registration
│   └── security.py          # Auth guards
├── modules/
│   ├── auth/                # User sync, profile, logout, account deletion
│   ├── games/               # Game detail, DLCs, Steam/ProtonDB/HLTB/ITAD data
│   ├── home/                # Aggregated home feed
│   ├── library/             # User game library (multi-platform sync)
│   ├── notifications/       # Deal alerts via FCM + APScheduler
│   ├── platforms/           # Platform connection (Steam, Epic, GOG, PSN)
│   ├── search/              # Game search
│   ├── settings/            # User settings
│   └── wishlist/            # Wishlist management
├── shared/
│   ├── domain/interfaces/   # Cross-module contracts
│   ├── infrastructure/
│   │   ├── cache/           # Redis client + @cached decorator + key patterns
│   │   ├── database/        # Firestore base repository
│   │   ├── http/            # Rate limiter, security headers middleware
│   │   └── security/        # Firebase auth provider, token blacklist
│   └── exceptions.py        # AppException base + global handlers
└── tests/                   # Mirrors modules/ structure
```

### Key Rules

- **Dependency direction:** `infrastructure` → `application` → `domain`. Never reversed.
- **No cross-module imports.** Modules only import from `shared/`.
- **Cross-module communication** via interfaces in `shared/domain/interfaces/`.
- **Wiring** exclusively in `composition/dependencies.py`.

## External Services

| Service | Purpose |
|---|---|
| Steam | Library sync, game metadata |
| Epic Games | Library sync |
| GOG | Library sync |
| PlayStation Network | Library sync (psnawp) |
| ProtonDB | Linux compatibility ratings |
| HowLongToBeat | Completion time estimates |
| IsThereAnyDeal (ITAD) | Price tracking and deal alerts |
| Firebase / FCM | Auth + push notifications |

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)
- A Firebase project with Firestore enabled
- An Upstash Redis instance (or local Redis for dev)

### Installation

```bash
cd GameShelfApi
poetry install
```

### Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `FIREBASE_PRIVATE_KEY` | Firebase Admin SDK private key |
| `FIREBASE_CLIENT_EMAIL` | Firebase Admin SDK client email |
| `REDIS_URL` | Redis connection URL |
| `STEAM_API_KEY` | Steam Web API key |
| `ITAD_API_KEY` | IsThereAnyDeal API key |

See `.env.example` for the full list.

### Running

```bash
# Development server (hot reload)
uvicorn main:app --reload --port 8000

# API docs available at:
# http://localhost:8000/docs  (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Docker

```bash
docker-compose up --build
```

## Testing

Tests require `API_ENV=testing` to skip Redis and Firebase initialization.

```bash
# Full suite
API_ENV=testing poetry run pytest

# Single module
API_ENV=testing poetry run pytest tests/games/

# Stop on first failure
API_ENV=testing poetry run pytest -x
```

Tests use `pytest-asyncio` for async use cases and `respx` to mock external HTTP clients.

## Linting & Type Checking

CI must pass in this order:

```bash
poetry run ruff check .          # lint
poetry run ruff format --check . # format check
poetry run mypy .                # type check (strict mode)
API_ENV=testing poetry run pytest
```

## Caching

Results are cached in Redis via the `@cached(ttl=N)` decorator defined in `shared/infrastructure/cache/decorators.py`. TTL strategy:

| Data type | TTL |
|---|---|
| Global data (ProtonDB, HLTB) | 1 hour |
| Per-user data | 2–5 minutes |

Cache key patterns are centralized in `shared/infrastructure/cache/keys.py`.

## Deployment

The project includes a `render.yaml` for one-click deployment to [Render](https://render.com). The `Dockerfile` uses a multi-stage build suitable for the free tier.

## Contributing

- Work on the `development` branch. Never push directly to `main`.
- Follow the naming conventions: `snake_case` for files/functions/variables, `PascalCase` for classes, `I` prefix for interfaces.
- All code, comments, and documentation must be written in English.
