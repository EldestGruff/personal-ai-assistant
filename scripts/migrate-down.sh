#!/bin/bash
#
# Rollback last database migration
# Usage: ./scripts/migrate-down.sh [steps]
# Examples:
#   ./scripts/migrate-down.sh     # Rollback 1 migration
#   ./scripts/migrate-down.sh 2   # Rollback 2 migrations

set -e

STEPS=${1:-1}

echo "⚠️  Rolling back $STEPS migration(s)..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rollback migrations
alembic downgrade -$STEPS

echo "✅ Rollback complete"
