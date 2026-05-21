# Cross-platform task runner for ai-org-simulation.
# Recipes here are the single source of truth for common dev commands.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]
set shell := ["bash", "-c"]
set dotenv-load := true

# List all available recipes.
default:
    @just --list

# Install Python deps into .venv via uv.
setup:
    uv sync
    @echo "Setup complete. Try: just db-up && just dev"

# Run FastAPI dev server with auto-reload.
dev:
    uv run uvicorn backend.main:app --reload --app-dir .

# Start the local Postgres container in the background.
db-up:
    docker compose up -d postgres

# Stop and remove all docker-compose services.
db-down:
    docker compose down

# Lint check (no changes).
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-format and auto-fix lints.
fmt:
    uv run ruff format .
    uv run ruff check --fix .

# Run the test suite.
test:
    uv run pytest
