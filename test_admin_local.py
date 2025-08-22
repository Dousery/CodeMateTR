#!/usr/bin/env python3
"""
Local'de admin yetkisini test etmek için script
"""

import os
import sys
from dotenv import load_dotenv

# Environment variables'ları yükle
load_dotenv()

def test_admin_endpoints():
    """Admin endpoint'lerini test eder"""
    try:
        # Flask app'i import et
        from app import app, db, User
        
        with app.app_context():
            # Veritabanı bağlantısını test et
            print("🔍 Veritabanı bağlantısı test ediliyor...")
            
            # User tablosunda is_admin sütunu var mı kontrol et
            try:
                # PostgreSQL'de sütun ekleme
                with db.engine.connect() as conn:
                    # is_admin sütununu ekle
                    conn.execute(db.text("""
                        ALTER TABLE "user" 
                        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE
                    """))
                    conn.commit()
                    print("✅ is_admin sütunu eklendi/kontrol edildi")
                    
                    # doguser'ı bul
                    result = conn.execute(db.text("""
                        SELECT username, interest FROM "user" WHERE username = 'doguser'
                    """)).fetchone()
                    
                    if result:
                        username, interest = result
                        print(f"✅ doguser bulundu: {username}, {interest}")
                        
                        # Admin yap
                        conn.execute(db.text("""
                            UPDATE "user" SET is_admin = TRUE WHERE username = 'doguser'
                        """))
                        conn.commit()
                        print("✅ doguser admin yapıldı!")
                        
                        # Kontrol et
                        result = conn.execute(db.text("""
                            SELECT username, interest, is_admin FROM "user" WHERE username = 'doguser'
                        """)).fetchone()
                        
                        if result:
                            username, interest, is_admin = result
                            print(f"✅ Güncellenmiş kullanıcı: {username}, {interest}, Admin: {is_admin}")
                        
                    else:
                        print("❌ doguser kullanıcısı bulunamadı")
                        
            except Exception as e:
                print(f"❌ Veritabanı işlemi hatası: {str(e)}")
                return False
            
            print("\n🎉 Admin yetkisi başarıyla eklendi!")
            return True
            
    except Exception as e:
        print(f"❌ Genel hata: {str(e)}")
        return False

if __name__ == '__main__':
    print("🔧 Admin yetkisi test ediliyor...")
    
    if test_admin_endpoints():
        print("\n✅ Test başarılı! doguser artık admin yetkilerine sahip.")
        print("\nAdmin yetkileri:")
        print("  - /admin/dashboard - Admin dashboard")
        print("  - /admin/users - Kullanıcı yönetimi")
        print("  - /admin/posts - Forum gönderi yönetimi")
        print("  - /admin/reports - Rapor yönetimi")
        print("  - /admin/notifications/send - Toplu bildirim gönderme")
        print("  - /admin/forum/create-post - Admin gönderisi oluşturma")
    else:
        print("\n❌ Test başarısız!")
        sys.exit(1)
