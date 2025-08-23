#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Initialize database (if needed)
python -c "
from app import app, db
with app.app_context():
    try:
        # Check if admin columns exist
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Check if is_admin column exists
            result = conn.execute(text(\"\"\"
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'is_admin'
            \"\"\"))
            is_admin_exists = result.fetchone() is not None
            
            # Check if created_at column exists
            result = conn.execute(text(\"\"\"
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'created_at'
            \"\"\"))
            created_at_exists = result.fetchone() is not None
            
            if not is_admin_exists or not created_at_exists:
                print('Adding missing columns to user table...')
                
                # Add is_admin column if it doesn't exist
                if not is_admin_exists:
                    conn.execute(text('ALTER TABLE \"user\" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE'))
                    print('Added is_admin column')
                
                # Add created_at column if it doesn't exist
                if not created_at_exists:
                    conn.execute(text('ALTER TABLE \"user\" ADD COLUMN created_at TIMESTAMP DEFAULT NOW()'))
                    print('Added created_at column')
                
                # Add admin post columns to forum_post table
                result = conn.execute(text(\"\"\"
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'forum_post' AND column_name = 'is_admin_post'
                \"\"\"))
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE forum_post ADD COLUMN is_admin_post BOOLEAN DEFAULT FALSE'))
                    conn.execute(text('ALTER TABLE forum_post ADD COLUMN is_removed BOOLEAN DEFAULT FALSE'))
                    conn.execute(text('ALTER TABLE forum_post ADD COLUMN removed_by VARCHAR(80)'))
                    conn.execute(text('ALTER TABLE forum_post ADD COLUMN removed_at TIMESTAMP'))
                    print('Added admin post columns to forum_post table')
                
                # Add admin notification columns to forum_notification table
                result = conn.execute(text(\"\"\"
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'forum_notification' AND column_name = 'is_admin_message'
                \"\"\"))
                if not result.fetchone():
                    conn.execute(text('ALTER TABLE forum_notification ADD COLUMN is_admin_message BOOLEAN DEFAULT FALSE'))
                    conn.execute(text('ALTER TABLE forum_notification ADD COLUMN admin_username VARCHAR(80)'))
                    print('Added admin notification columns to forum_notification table')
                
                conn.commit()
                print('Database schema updated successfully')
            else:
                print('All required columns already exist')
        
        # Create tables if they don't exist
        db.create_all()
        print('Database initialized successfully')
        
        # Create admin user if it doesn't exist
        from app import User
        admin_user = User.query.filter_by(username='doguser').first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                username='doguser',
                interest='admin',
                is_admin=True
            )
            admin_user.set_password('Admin123!')
            db.session.add(admin_user)
            db.session.commit()
            print('Admin user created: doguser / Admin123!')
        else:
            if not admin_user.is_admin:
                admin_user.is_admin = True
                db.session.commit()
                print('Admin privileges activated for existing user: doguser')
            else:
                print('Admin user already exists with privileges')
                
    except Exception as e:
        print(f'Database initialization error: {e}')
        # Continue with build even if there's a DB error
        pass
"

echo "Build completed successfully" 