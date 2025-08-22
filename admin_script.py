#!/usr/bin/env python3
"""
doguser kullanıcısını admin yapmak için basit script
"""

import sqlite3
import os

def make_doguser_admin():
    """doguser kullanıcısını admin yapar"""
    try:
        # Veritabanı bağlantısı
        db_path = os.path.join(os.path.dirname(__file__), 'btk_project.db')
        
        if not os.path.exists(db_path):
            print(f"❌ Veritabanı bulunamadı: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Önce user tablosunda is_admin sütunu var mı kontrol et
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_admin' not in columns:
            print("🔧 is_admin sütunu ekleniyor...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ is_admin sütunu eklendi")
        
        # doguser kullanıcısını bul
        cursor.execute("SELECT username, interest FROM user WHERE username = ?", ('doguser',))
        user = cursor.fetchone()
        
        if not user:
            print("❌ 'doguser' kullanıcısı bulunamadı!")
            return False
        
        # Admin yap
        cursor.execute("UPDATE user SET is_admin = 1 WHERE username = ?", ('doguser',))
        conn.commit()
        
        print(f"✅ '{user[0]}' kullanıcısı başarıyla admin yapıldı!")
        print(f"   - Username: {user[0]}")
        print(f"   - Interest: {user[1]}")
        print(f"   - Admin: True")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Hata oluştu: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == '__main__':
    print("🔧 doguser kullanıcısını admin yapılıyor...")
    
    if make_doguser_admin():
        print("\n🎉 İşlem başarılı! doguser artık admin yetkilerine sahip.")
        print("\nAdmin yetkileri:")
        print("  - Tüm forum içeriklerini görme ve silme")
        print("  - Rapor edilmiş gönderileri çözme")
        print("  - Tüm kullanıcılara bildirim gönderme")
        print("  - Admin olarak forum gönderisi oluşturma")
        print("  - Admin gönderileri farklı görünüm")
    else:
        print("\n❌ İşlem başarısız!")
        exit(1)
