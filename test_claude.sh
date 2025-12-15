#!/bin/bash
# Test Claude integration endpoints

API_URL="https://ai.gruff.icu/api/v1"
API_KEY="ad8c1f1e-bad4-4f6b-a4ac-a7674bf1ce03"

echo "🧠 Testing Claude Integration"
echo "=============================="
echo ""

# Test 1: Consciousness Check
echo "1. Testing Consciousness Check..."
curl -s -X POST "$API_URL/claude/consciousness-check" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limit_recent": 10}' | jq '.'

echo ""
echo "=============================="
echo ""

# Test 2: Extract Tasks
echo "2. Testing Task Extraction..."
curl -s -X POST "$API_URL/claude/extract-tasks" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limit_recent": 20}' | jq '.'

echo ""
echo "=============================="
echo "Tests complete!"
