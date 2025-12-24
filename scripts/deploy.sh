#!/bin/bash
# Deployment Script for Personal AI Assistant
# Called by webhook receiver when code is pushed to main
# This script handles the complete deployment process

set -e  # Exit on error

# Configuration
APP_DIR="/mnt/data2-pool/andy-ai/app"
DOCKER_DIR="$APP_DIR/docker"
FRONTEND_DIR="$APP_DIR/frontend"
WEB_DIR="$APP_DIR/web"
LOG_DIR="$APP_DIR/logs/deployments"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create timestamp
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="$LOG_DIR/$TIMESTAMP.log"
LATEST_LOG="$LOG_DIR/latest.log"

# Redirect all output to log file AND stdout
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

# Helper functions
log_section() {
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════"
}

log_success() {
    echo "✅ $1"
}

log_error() {
    echo "❌ $1"
}

# Start deployment
log_section "DEPLOYMENT STARTED"
echo "timestamp: $TIMESTAMP"
echo "app_dir: $APP_DIR"
echo "log_file: $LOG_FILE"

# Step 1: Verify environment
log_section "STEP 1: VERIFY ENVIRONMENT"
if [ ! -d "$APP_DIR" ]; then
    log_error "app directory not found: $APP_DIR"
    exit 1
fi
log_success "app directory exists"

if [ ! -d "$APP_DIR/.git" ]; then
    log_error "git repository not found: $APP_DIR/.git"
    exit 1
fi
log_success "git repository exists"

# Step 2: Pull latest code
log_section "STEP 2: PULL LATEST CODE FROM GITHUB"
cd "$APP_DIR"
# Allow git to operate on repository even if owned by different user (Docker container issue)
git config --global --add safe.directory "$APP_DIR"
# Use rebase for automated deployments (keeps history linear, no merge commits)
git config pull.rebase true
git_output=$(git pull origin main 2>&1) || {
    log_error "git pull failed"
    echo "$git_output"
    exit 1
}
echo "$git_output"
log_success "code pulled from github"

# Step 3: Build frontend
log_section "STEP 3: BUILD FRONTEND"
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

if [ ! -f "$FRONTEND_DIR/package.json" ]; then
    log_error "package.json not found in frontend directory"
    exit 1
fi

cd "$FRONTEND_DIR"
npm_output=$(npm install 2>&1) || {
    log_error "npm install failed"
    echo "$npm_output"
    exit 1
}
echo "npm install output (last 20 lines):"
echo "$npm_output" | tail -20
log_success "dependencies installed"

build_output=$(npm run build 2>&1) || {
    log_error "npm build failed"
    echo "$build_output"
    exit 1
}
echo "build output (last 30 lines):"
echo "$build_output" | tail -30
log_success "frontend built successfully"

# Step 4: Copy build to web directory
log_section "STEP 4: COPY BUILD TO WEB DIRECTORY"
if [ ! -d "$FRONTEND_DIR/dist" ]; then
    log_error "build output directory not found: $FRONTEND_DIR/dist"
    exit 1
fi

# Clear web directory and copy new build
rm -rf "$WEB_DIR"/*
cp -r "$FRONTEND_DIR/dist"/* "$WEB_DIR/" || {
    log_error "failed to copy build to web directory"
    exit 1
}
log_success "build copied to web directory"

# Step 5: Run database migrations
log_section "STEP 5: RUN DATABASE MIGRATIONS"
cd "$APP_DIR"
if [ ! -f "alembic.ini" ]; then
    log_error "alembic.ini not found"
    exit 1
fi

# Get database URL from docker compose environment
if [ ! -f "$DOCKER_DIR/.env" ]; then
    log_error "docker .env file not found: $DOCKER_DIR/.env"
    exit 1
fi

# Source the environment to get POSTGRES variables
source "$DOCKER_DIR/.env" || {
    log_error "failed to source docker .env"
    exit 1
}

# Construct DATABASE_URL from individual postgres variables
# docker-compose does this dynamically, so we replicate that here
DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"

if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL could not be constructed from POSTGRES variables"
    exit 1
fi

migration_output=$(alembic upgrade head 2>&1) || {
    log_error "alembic migrations failed"
    echo "$migration_output"
    exit 1
}
echo "$migration_output"
log_success "database migrations completed"

# Step 6: Rebuild Docker images (only API, not webhook to avoid bootstrap issues)
log_section "STEP 6: REBUILD DOCKER IMAGES"
cd "$DOCKER_DIR"
docker_build=$(docker compose build api 2>&1) || {
    log_error "docker compose build failed"
    echo "$docker_build"
    exit 1
}
echo "build output (last 40 lines):"
echo "$docker_build" | tail -40
log_success "docker images built successfully"

# Step 7: Restart containers (only API - webhook must not restart itself!)
# Note: postgres doesn't need restart on code deploys, webhook would kill this script
log_section "STEP 7: RESTART API CONTAINER"
echo "stopping api container..."
docker_stop=$(docker compose stop api 2>&1) || {
    log_error "docker compose stop api failed"
    echo "$docker_stop"
    exit 1
}
echo "$docker_stop"

echo "removing api container..."
docker_rm=$(docker compose rm -f api 2>&1) || {
    log_error "docker compose rm api failed"
    echo "$docker_rm"
    exit 1
}
echo "$docker_rm"

echo "starting api container with new image..."
docker_up=$(docker compose up -d api 2>&1) || {
    log_error "docker compose up api failed"
    echo "$docker_up"
    exit 1
}
echo "$docker_up"
log_success "api container restarted"

# Step 8: Wait for services to be healthy
log_section "STEP 8: WAIT FOR SERVICES"
echo "waiting 15 seconds for services to stabilize..."
sleep 15

# Check if API is healthy
api_health=$(curl -s http://localhost:8000/api/v1/health 2>&1 || echo "failed") 
if echo "$api_health" | grep -q "healthy"; then
    log_success "API health check passed"
else
    log_error "API health check failed: $api_health"
    exit 1
fi

# Final summary
log_section "DEPLOYMENT COMPLETED SUCCESSFULLY"
echo "timestamp: $TIMESTAMP"
echo "log_file: $LOG_FILE"
echo ""
echo "deployment is live ✨"

# Update latest log symlink
rm -f "$LATEST_LOG"
ln -s "$LOG_FILE" "$LATEST_LOG"

exit 0
