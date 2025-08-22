#!/usr/bin/env python3
"""
Database migration script to update password_hash column length
"""
import os
from sqlalchemy import text
from app import app, db

def migrate_database():
    """Migrate database to add admin and report system columns"""
    with app.app_context():
        try:
            # Veritabanı bağlantısını test et
            db.engine.connect().close()
            print("✅ Database connection successful")
            
            with db.engine.connect() as conn:
                # 1. User tablosuna is_admin kolonu ekle
                try:
                    conn.execute(text("""
                        ALTER TABLE "user" 
                        ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
                    """))
                    print("✅ Added is_admin column to user table")
                except Exception as e:
                    print(f"⚠️ is_admin column might already exist: {e}")

                # 2. Forum_post tablosuna admin kolonları ekle
                try:
                    conn.execute(text("""
                        ALTER TABLE forum_post 
                        ADD COLUMN is_removed BOOLEAN DEFAULT FALSE
                    """))
                    print("✅ Added is_removed column to forum_post table")
                except Exception as e:
                    print(f"⚠️ is_removed column might already exist: {e}")

                try:
                    conn.execute(text("""
                        ALTER TABLE forum_post 
                        ADD COLUMN removed_by VARCHAR(80)
                    """))
                    print("✅ Added removed_by column to forum_post table")
                except Exception as e:
                    print(f"⚠️ removed_by column might already exist: {e}")

                try:
                    conn.execute(text("""
                        ALTER TABLE forum_post 
                        ADD COLUMN removed_at TIMESTAMP
                    """))
                    print("✅ Added removed_at column to forum_post table")
                except Exception as e:
                    print(f"⚠️ removed_at column might already exist: {e}")

                try:
                    conn.execute(text("""
                        ALTER TABLE forum_post 
                        ADD COLUMN removal_reason TEXT
                    """))
                    print("✅ Added removal_reason column to forum_post table")
                except Exception as e:
                    print(f"⚠️ removal_reason column might already exist: {e}")

                # 3. Forum_report tablosunu oluştur (eğer yoksa)
                try:
                    # Önce tablo var mı kontrol et
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'forum_report'
                        )
                    """))
                    table_exists = result.scalar()
                    
                    if not table_exists:
                        conn.execute(text("""
                            CREATE TABLE forum_report (
                                id SERIAL PRIMARY KEY,
                                post_id INTEGER NOT NULL REFERENCES forum_post(id),
                                comment_id INTEGER REFERENCES forum_comment(id),
                                reporter_username VARCHAR(80) NOT NULL,
                                report_reason VARCHAR(100) NOT NULL,
                                report_details TEXT,
                                status VARCHAR(20) DEFAULT 'pending',
                                reviewed_by VARCHAR(80),
                                reviewed_at TIMESTAMP,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """))
                        print("✅ Created forum_report table")
                    else:
                        print("ℹ️ forum_report table already exists")
                except Exception as e:
                    print(f"⚠️ forum_report table creation error: {e}")

                # 4. Admin kullanıcısı oluştur (username: doguser, password: admin123)
                try:
                    from werkzeug.security import generate_password_hash
                    admin_password_hash = generate_password_hash('admin123', method='pbkdf2:sha256')
                    
                    # Önce kullanıcı var mı kontrol et
                    result = conn.execute(text("""
                        SELECT username FROM "user" WHERE username = 'doguser'
                    """))
                    user_exists = result.fetchone()
                    
                    if user_exists:
                        # Kullanıcı varsa admin yetkisi ver
                        conn.execute(text("""
                            UPDATE "user" SET is_admin = TRUE WHERE username = 'doguser'
                        """))
                        print("✅ Admin user updated (username: doguser)")
                    else:
                        # Kullanıcı yoksa oluştur
                        conn.execute(text("""
                            INSERT INTO "user" (username, password_hash, is_admin) 
                            VALUES ('doguser', :password_hash, TRUE)
                        """), {"password_hash": admin_password_hash})
                        print("✅ Admin user created (username: doguser, password: admin123)")
                        
                except Exception as e:
                    print(f"⚠️ Admin user creation error: {e}")

                conn.commit()
                print("✅ Database migration completed successfully!")
                
        except Exception as e:
            print(f"⚠️ Migration error: {e}")
            print("✅ Continuing with application startup...")

if __name__ == "__main__":
    migrate_database() 