#!/bin/bash
# Quick start script for web dashboard

echo "🧠 Personal AI Assistant - Web Dashboard"
echo "========================================"
echo ""
echo "Starting local web server on http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""

# Check if python3 is available
if command -v python3 &> /dev/null; then
    python3 -m http.server 8080
elif command -v python &> /dev/null; then
    python -m http.server 8080
else
    echo "❌ Python not found. Please install Python 3 or use another web server."
    exit 1
fi
