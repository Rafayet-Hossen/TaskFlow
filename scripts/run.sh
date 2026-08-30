#!/usr/bin/env bash
set -e

# Change to project root directory
cd "$(dirname "$0")/.."

echo "⚡ Starting TaskFlow Application..."

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run FastAPI with Uvicorn
echo "🚀 Server launching at: http://localhost:8000"
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

