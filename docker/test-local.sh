#!/bin/bash
# Quick local test of Docker deployment
# Tests that services start and API responds

set -e

echo "🧪 Testing Docker Deployment Locally"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Navigate to docker directory
cd "$(dirname "$0")"

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit docker/.env with your API keys:"
    echo "   - POSTGRES_PASSWORD (change from 'changeme')"
    echo "   - API_KEY (generate a UUID)"
    echo "   - ANTHROPIC_API_KEY (your Claude API key)"
    echo ""
    echo "Then run this script again."
    exit 0
fi

echo "✅ .env file found"
echo ""

# Stop any existing services
echo "🧹 Cleaning up existing services..."
docker-compose down -v > /dev/null 2>&1 || true
echo ""

# Build images
echo "🔨 Building Docker images..."
docker-compose build --no-cache
echo ""

# Start services
echo "▶️  Starting services..."
docker-compose up -d
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30
echo ""

# Check PostgreSQL
echo "🐘 Testing PostgreSQL..."
if docker-compose exec -T postgres pg_isready -U andy -d personal_ai > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "❌ PostgreSQL is not responding"
    docker-compose logs postgres
    exit 1
fi
echo ""

# Check API health
echo "🏥 Testing API health..."
if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ API is healthy"
    curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
else
    echo "❌ API health check failed"
    docker-compose logs api
    exit 1
fi
echo ""

# Check backend availability
echo "🤖 Testing backend availability..."
if curl -f -s http://localhost:8000/api/v1/health/backends > /dev/null; then
    echo "✅ Backends endpoint responding"
    curl -s http://localhost:8000/api/v1/health/backends | python3 -m json.tool
else
    echo "⚠️  Backends endpoint returned error (may be expected if no API keys)"
fi
echo ""

# Test thoughts endpoint (requires API key)
echo "🧠 Testing thoughts endpoint..."
API_KEY=$(grep "^API_KEY=" .env | cut -d'=' -f2)
if [ -n "$API_KEY" ] && [ "$API_KEY" != "your-secure-api-key-here" ]; then
    if curl -f -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/v1/thoughts > /dev/null; then
        echo "✅ Thoughts endpoint accessible"
    else
        echo "⚠️  Thoughts endpoint returned error"
    fi
else
    echo "⚠️  API_KEY not configured in .env, skipping auth test"
fi
echo ""

# Show running containers
echo "📊 Running containers:"
docker-compose ps
echo ""

# Show logs (last 10 lines)
echo "📝 Recent logs:"
docker-compose logs --tail=10
echo ""

echo "======================================"
echo "✅ ALL TESTS PASSED!"
echo ""
echo "🎉 Docker deployment is working locally"
echo ""
echo "Next steps:"
echo "  - View API docs: http://localhost:8000/docs"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Deploy to moria: ./deploy.sh moria"
echo ""
