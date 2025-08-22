#!/usr/bin/env python3
"""
Database migration script to update password_hash column length
"""
import os
from sqlalchemy import text
from app import app, db

def migrate_database():
    """Migrate database to fix password_hash column length"""
    with app.app_context():
        try:
            # PostgreSQL için ALTER TABLE komutu
            with db.engine.connect() as conn:
                # password_hash sütununu VARCHAR(255) olarak değiştir
                conn.execute(text("""
                    ALTER TABLE "user" 
                    ALTER COLUMN password_hash TYPE VARCHAR(255)
                """))
                conn.commit()
                print("✅ Database migration completed successfully!")
                print("✅ password_hash column updated to VARCHAR(255)")
                
        except Exception as e:
            print(f"⚠️ Migration error (this might be expected if column already exists): {e}")
            print("✅ Continuing with application startup...")

if __name__ == "__main__":
    migrate_database() 