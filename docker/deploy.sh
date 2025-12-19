#!/bin/bash
# Quick deployment script for Personal AI Assistant
# Usage: ./deploy.sh [local|moria]

set -e

TARGET=${1:-local}

echo "🚀 Personal AI Assistant - Deployment Script"
echo "Target: $TARGET"
echo ""

if [ "$TARGET" = "local" ]; then
    echo "📦 Deploying locally for testing..."
    
    # Check if .env exists
    if [ ! -f .env ]; then
        echo "⚠️  No .env file found. Creating from template..."
        cp .env.example .env
        echo "✏️  Please edit .env with your configuration"
        exit 1
    fi
    
    # Build and start
    echo "🔨 Building Docker images..."
    docker compose build
    
    echo "▶️  Starting services..."
    docker compose up -d
    
    echo "⏳ Waiting for services to be healthy..."
    sleep 10
    
    echo "🏥 Checking health..."
    curl -f http://localhost:8000/api/v1/health || {
        echo "❌ Health check failed"
        docker compose logs
        exit 1
    }
    
    echo ""
    echo "✅ Deployment successful!"
    echo "📝 API Documentation: http://localhost:8000/docs"
    echo "❤️  Health Check: http://localhost:8000/api/v1/health"
    echo "📊 View logs: docker compose logs -f"
    
elif [ "$TARGET" = "moria" ]; then
    echo "📦 Deploying to TrueNAS SCALE (moria)..."
    
    # Check SSH connectivity
    echo "🔐 Checking SSH connection to moria..."
    ssh -q andy@moria exit || {
        echo "❌ Cannot connect to moria via SSH"
        exit 1
    }
    
    # Create deployment package
    echo "📦 Creating deployment package..."
    cd ..
    tar --exclude='venv' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='tests' \
        --exclude='htmlcov' \
        --exclude='.pytest_cache' \
        --exclude='*.db' \
        -czf personal-ai-assistant.tar.gz .
    
    # Transfer to moria
    echo "📤 Transferring to moria..."
    scp personal-ai-assistant.tar.gz andy@moria:/tmp/
    
    # Deploy on moria
    echo "🚀 Deploying on moria..."
    ssh andy@moria << 'EOF'
        set -e
        cd /mnt/data2-pool/andy-ai/app

        # Backup current version
        if [ -d "src" ]; then
            echo "💾 Backing up current version..."
            cd ..
            tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz app/
        fi

        # Extract new version
        echo "📦 Extracting new version..."
        cd /mnt/data2-pool/andy-ai/app
        tar -xzf /tmp/personal-ai-assistant.tar.gz
        rm /tmp/personal-ai-assistant.tar.gz

        # Ensure .env exists
        echo "📝 Checking environment configuration..."
        cd docker
        if [ ! -f .env ]; then
            echo "⚙️  Creating .env from template..."
            cp .env.production .env
            # Set matching API key from web config
            sed -i 's/^API_KEY=.*/API_KEY=ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03/' .env
        fi

        # Stop services
        echo "⏹️  Stopping services..."
        docker compose down || true

        # Build new images
        echo "🔨 Building Docker images..."
        docker compose build --no-cache

        # Start services
        echo "▶️  Starting services..."
        docker compose up -d

        echo "⏳ Waiting for services..."
        sleep 15

        # Fix web directory permissions (workaround for UID mismatch)
        echo "🔧 Fixing web directory permissions..."
        docker exec -u root personal-ai-api chmod -R 755 /app/web

        echo "✅ Deployment complete!"
EOF
    
    echo ""
    echo "✅ Deployment to moria successful!"
    echo "🔍 Check status: ssh andy@moria 'cd /mnt/data2-pool/andy-ai/app/docker && docker compose ps'"
    echo "📝 View logs: ssh andy@moria 'cd /mnt/data2-pool/andy-ai/app/docker && docker compose logs -f'"
    echo "🏥 Health check: curl http://moria:8000/api/v1/health"
    echo "🌐 Dashboard: http://moria:8000/dashboard/"
    
    # Cleanup local package
    rm personal-ai-assistant.tar.gz
    
else
    echo "❌ Unknown target: $TARGET"
    echo "Usage: $0 [local|moria]"
    exit 1
fi
