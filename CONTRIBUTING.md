# Contributing to PlugBot

:+1: **Thanks for helping make PlugBot better!**

We follow the *fork → branch → pull-request* workflow on GitHub.

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| Docker (optional) | Simplest way to run the full stack locally |
| Python 3.11 | Backend development & tests |
| Node 18 | Front-end development & tests |
| `pre-commit` | Auto-format & lint on commit |

Install hooks once:

```bash
pip install pre-commit
pre-commit install
````

---

## Branch naming

* `feat/<short-description>`  → new functionality
* `fix/<short-description>`   → bug fixes
* `docs/<short-description>` → documentation only

---

## Code style

| Language       | Formatter / Linter             |
| -------------- | ------------------------------ |
| Python         | **black**, **isort**, **ruff** |
| TypeScript/JSX | **prettier**, **eslint**       |
| Tailwind CSS   | prettier-plugin-tailwindcss    |

Hooks run these automatically—commits that fail lint/format will be rejected.

---

## Tests

```bash
# Backend (pytest)
docker compose exec backend pytest -q
# or, outside Docker
pytest

# Front-end (Jest + RTL)
cd frontend && npm test
```

Pull requests should keep the entire suite green.

---

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
feat: add webhook support
fix(db): nullable telegram_username
docs: update readme quick-start
```

---

## Pull-request checklist

* [ ] Code lints & is formatted
* [ ] Unit / integration tests added or updated
* [ ] Documentation updated (README, Storybook, OpenAPI, etc.)
* [ ] `docker compose up --build` still works end-to-end
* [ ] CI passes on GitHub Actions

Happy hacking! 🚀