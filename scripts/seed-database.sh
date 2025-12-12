#!/bin/bash
# seed-database.sh - Create initial user in production database

set -e

echo "🌱 Seeding database with initial user..."

ssh andy@moria "sudo docker exec personal-ai-api python3 -c \"
from src.database.session import SessionLocal
from src.models.user import UserDB
from datetime import datetime

db = SessionLocal()

try:
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.id == '550e8400-e29b-41d4-a716-446655440000').first()
    
    if existing_user:
        print('✅ User already exists')
    else:
        # Create initial user
        user = UserDB(
            id='550e8400-e29b-41d4-a716-446655440000',
            name='Andy',
            email='andy@fennerfam.com',
            preferences={
                'timezone': 'America/New_York',
                'max_thoughts_goal': 20,
                'reminder_frequency_minutes': 30
            },
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        print('✅ Initial user created: Andy (andy@fennerfam.com)')
        
finally:
    db.close()
\""

echo "✅ Database seeding complete!"
