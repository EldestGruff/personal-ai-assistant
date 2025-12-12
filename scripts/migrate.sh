#!/bin/bash
#
# Apply database migrations
# Usage: ./scripts/migrate.sh

set -e

echo "🔄 Applying database migrations..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
alembic upgrade head

echo "âœ… Migrations applied successfully"
