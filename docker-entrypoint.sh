#!/bin/bash
# Docker entrypoint script for Personal AI Assistant
# Runs database migrations before starting the API server

set -e  # Exit on error

echo "🔧 Running database migrations..."
alembic upgrade head

echo "🚀 Starting Personal AI Assistant API..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
