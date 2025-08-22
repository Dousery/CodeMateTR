"""
Migration: Admin sütunu ekleme ve doguser'ı admin yapma
"""

from sqlalchemy import text
from app import db

def upgrade():
    """Migration'ı uygula"""
    try:
        with db.engine.connect() as conn:
            # is_admin sütununu ekle (eğer yoksa)
            conn.execute(text("""
                ALTER TABLE "user" 
                ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE
            """))
            
            # doguser'ı admin yap
            conn.execute(text("""
                UPDATE "user" 
                SET is_admin = TRUE 
                WHERE username = 'doguser'
            """))
            
            conn.commit()
            print("✅ Admin migration başarıyla uygulandı")
            
    except Exception as e:
        print(f"❌ Migration hatası: {str(e)}")
        raise

def downgrade():
    """Migration'ı geri al"""
    try:
        with db.engine.connect() as conn:
            # doguser'ın admin yetkisini kaldır
            conn.execute(text("""
                UPDATE "user" 
                SET is_admin = FALSE 
                WHERE username = 'doguser'
            """))
            
            # is_admin sütununu kaldır (PostgreSQL'de sütun kaldırma desteklenir)
            # conn.execute(text("ALTER TABLE \"user\" DROP COLUMN is_admin"))
            
            conn.commit()
            print("✅ Admin migration geri alındı")
            
    except Exception as e:
        print(f"❌ Downgrade hatası: {str(e)}")
        raise

if __name__ == '__main__':
    from app import app
    with app.app_context():
        upgrade()
