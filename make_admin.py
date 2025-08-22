#!/usr/bin/env python3
"""
doguser kullanıcısını admin yapmak için script
"""

import os
import sys
from dotenv import load_dotenv

# Environment variables'ları yükle
load_dotenv()

# Flask app'i import et
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def make_doguser_admin():
    """doguser kullanıcısını admin yapar"""
    with app.app_context():
        try:
            # doguser kullanıcısını bul
            user = User.query.filter_by(username='doguser').first()
            
            if not user:
                print("❌ 'doguser' kullanıcısı bulunamadı!")
                return False
            
            # Admin yap
            user.is_admin = True
            db.session.commit()
            
            print(f"✅ '{user.username}' kullanıcısı başarıyla admin yapıldı!")
            print(f"   - Username: {user.username}")
            print(f"   - Interest: {user.interest}")
            print(f"   - Admin: {user.is_admin}")
            
            return True
            
        except Exception as e:
            print(f"❌ Hata oluştu: {str(e)}")
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
        sys.exit(1)
