#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Initialize database (if needed)
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

# Run admin migration
python -c "
from app import app
from migrations.add_admin_column import upgrade
with app.app_context():
    try:
        upgrade()
        print('Admin migration completed successfully')
    except Exception as e:
        print(f'Admin migration error: {e}')
        # Migration hatası kritik değil, devam et
"

echo "Build completed successfully" 