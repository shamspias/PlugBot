# PlugBot ⚡

_Easily bridge any number of Dify apps to Telegram bots_

[![Docker ready](https://img.shields.io/badge/docker-ready-2496ed?logo=docker&logoColor=white)](https://hub.docker.com/)
[![GitHub stars](https://img.shields.io/github/stars/shamspias/plugbot?style=social)](https://github.com/shamspias/plugbot/stargazers)
[![Build status](https://img.shields.io/github/actions/workflow/status/shamspias/plugbot/ci.yml)](../../actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


> **PlugBot** lets you manage unlimited **Dify** applications  
> (chat, agent, chat-flow, workflow) and expose each one through a Telegram bot—  
> no extra glue code, all in a polished Next.js dashboard.

---

## Table of Contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Architecture](#architecture)
4. [Quick start (Docker)](#quick-start-docker)
5. [Manual installation](#manual-installation-without-docker)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Development workflow](#development-workflow)
9. [Testing](#testing)
10. [Security policy](#security-policy)
11. [Contributing](#contributing)
12. [License](#license)
13. [Acknowledgements](#acknowledgements)

---

## Features

| &nbsp;                      | Capability                                                                   |
|-----------------------------|------------------------------------------------------------------------------|
| 🔗 **Multi-endpoint**       | Point to any number of Dify servers—just paste *endpoint* + *API key*.       |
| 🤖 **Multi-bot**            | Each Dify app can be paired with its own Telegram bot token.                 |
| 🖥 **Dashboard**            | Start / stop / restart, live health-check, conversation counters.            |
| 🔄 **Streaming & blocking** | Toggle real-time streaming or batch responses per bot.                       |
| 🔐 **Secrets at rest**      | API keys & bot tokens encrypted with Fernet AES-128 (configurable).          |
| 🐳 **One-command deploy**   | `docker compose up -d --build` brings up Postgres, Redis, backend, frontend. |
| 🚀 **Hot-reload dev**       | Works equally well outside Docker for fast local hacking.                    |
| ✅ **CI-ready**              | Unit tests + pre-commit hooks + conventional commits.                        |

---

## Tech stack

* **Backend** – FastAPI × SQLAlchemy × Alembic × Pydantic v2
* **Realtime** – python-telegram-bot v20 (long-polling or web-hooks)
* **Frontend** – Next.js 14, React 18, Tailwind CSS, Lucide icons
* **Data** – PostgreSQL 16, Redis 7
* **Packaging** – Docker multistage images, docker-compose v3.9

---

## Architecture

```

┌────────────┐     (REST)     ┌──────────────┐
│  Frontend  │ ─────────────► │   FastAPI    │ ─┐
│  Next.js   │                │  PlugBot API │  │          ┌──────────────┐
└────────────┘                └──────────────┘  │ (HTTPS)  │   Dify API   │
│◄────────►│ (one or many)│
(WebSocket / HTTP)            ▲              │          └──────────────┘
│              │
│  (async I/O) │
│              ▼
┌────────────────────┐
│ python-telegram-bot │  (long-poll / web-hook)
└────────────────────┘

````

---

## Quick start (Docker)

```bash
# 1 — clone & enter the repo
git clone https://github.com/shamspias/plugbot.git
cd plugbot

# 2 — create env files
cp .env.example .env

# 3 — edit the new .env files (SECRET_KEY, ENCRYPTION_KEY, etc.)

# 4 — build & run everything
docker compose up -d --build
```


| Service     | Host URL                                                 | Inside-container URL    |
| ----------- | -------------------------------------------------------- | ----------------------- |
| Frontend UI | [http://localhost:3514](http://localhost:3514)           | `http://localhost:3000` |
| FastAPI API | [http://localhost:8531/docs](http://localhost:8531/docs) | `http://localhost:8000` |
| PostgreSQL  | `localhost:5432` *(optional)*                            | `postgres://db:5429`    |
| Redis       | n/a *(internal only)*                                    | `redis://redis:6387`    |

*Back-end migrations run automatically on first boot.*

---

## Manual installation (without Docker)

### Prerequisites

| Stack      | Version |
|------------|---------|
| Python     | 3.11    |
| Node       | 18      |
| PostgreSQL | ≥ 14    |
| Redis      | ≥ 6     |

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit secrets & DB URL

alembic upgrade head   # create tables
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ../frontend
npm install
cp .env.example .env           # adjust NEXT_PUBLIC_API_URL if needed
npm run dev                    # http://localhost:3514
```

---

## Configuration

All settings are environment variables.
The most important ones are:

| Variable              | Where    | Default                                          | Purpose                                   |
|-----------------------|----------|--------------------------------------------------|-------------------------------------------|
| `SECRET_KEY`          | backend  | *(none)*                                         | JWT signing & CSRF                        |
| `ENCRYPTION_KEY`      | backend  | *(none)*                                         | 32-char Fernet key for encrypting secrets |
| `DATABASE_URL`        | backend  | `postgresql://postgres:postgres@db:5432/plugbot` | SQLAlchemy DSN                            |
| `REDIS_URL`           | backend  | `redis://redis:6387/0`                           | Caching / queues                          |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:8531/api/v1`                   | Point UI to the API                       |

---

## Usage

1. **Open the dashboard** → click **“Add Bot”**.
2. Paste your **Dify endpoint** and **API key**.
3. *(Optional)* paste a Telegram **bot token** from **@BotFather**.
4. Hit **Create** – PlugBot verifies the Dify server, starts the Telegram bot,
   and you’re good to go! 🎉

---

## Development workflow

| Task                       | Command                                          |
|----------------------------|--------------------------------------------------|
| Lint / format (pre-commit) | `pre-commit run --all-files`                     |
| Python hot-reload          | `uvicorn app.main:app --reload`                  |
| Next.js hot-reload         | `npm run dev`                                    |
| Generate Alembic revision  | `alembic revision --autogenerate -m "my change"` |

> **Tip**: `pre-commit install` will auto-run *black*, *ruff*, *isort*, Prettier, ESLint, etc. on every commit.

---

## Testing

```bash
# Docker
docker compose exec backend pytest -q
# or local venv
pytest
```

Front-end tests live under `frontend/src/__tests__/` (React Testing Library).

---

## Security policy

Please report vulnerabilities privately by opening a “Security advisory” on
GitHub or emailing *[info@shamspias.com](mailto:info@shamspias.com)*.
We follow [responsible disclosure](https://en.wikipedia.org/wiki/Responsible_disclosure) and aim to patch within **30
days**.

---

## Contributing

Pull requests are welcome!
Read the [**CONTRIBUTING.md**](CONTRIBUTING.md) guide for branching, coding style,
commit messages, and CI checklist.

---

## License

PlugBot is released under the [MIT license](LICENSE).

---

## Acknowledgements

* [Dify](https://github.com/langgenius/dify) – powerful LLM app platform
* [FastAPI](https://fastapi.tiangolo.com/) – modern, fast web framework
* [Next.js](https://nextjs.org/) – React framework for the web
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) – Telegram API wrapper
* All [contributors](../../graphs/contributors) – thank you! 🙏