#!/usr/bin/env python3
"""
Database reset script - Veritabanını sıfırdan başlatır
Tüm tabloları siler ve yeniden oluşturur
"""
import os
import sys
from sqlalchemy import text
from app import app, db, User, TestSession, AutoInterviewSession, UserHistory, ForumPost, ForumComment

def reset_database():
    """Veritabanını tamamen sıfırla"""
    with app.app_context():
        try:
            print("🔄 Veritabanı sıfırlama işlemi başlatılıyor...")
            
            # Tüm tabloları sil
            print("🗑️ Mevcut tablolar siliniyor...")
            db.drop_all()
            print("✅ Tüm tablolar silindi!")
            
            # Tabloları yeniden oluştur
            print("🔨 Tablolar yeniden oluşturuluyor...")
            db.create_all()
            print("✅ Tüm tablolar yeniden oluşturuldu!")
            
            # Veritabanı bağlantısını test et
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = result.fetchall()
                print("\n📋 Oluşturulan tablolar:")
                for table in tables:
                    print(f"  ✓ {table[0]}")
            
            print("\n🎉 Veritabanı başarıyla sıfırlandı!")
            print("📝 Artık yeni kullanıcılar kaydolabilir ve sistem temiz bir durumda!")
            
        except Exception as e:
            print(f"❌ Veritabanı sıfırlama hatası: {e}")
            return False
            
    return True

def delete_database_files():
    """Veritabanı dosyalarını fiziksel olarak sil"""
    try:
        print("🗂️ Veritabanı dosyaları kontrol ediliyor...")
        
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        db_files = ['app.db', 'btk_project.db']
        
        deleted_files = []
        for db_file in db_files:
            file_path = os.path.join(instance_path, db_file)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(db_file)
                print(f"🗑️ {db_file} silindi")
        
        if deleted_files:
            print(f"✅ {len(deleted_files)} veritabanı dosyası silindi: {', '.join(deleted_files)}")
        else:
            print("ℹ️ Silinecek veritabanı dosyası bulunamadı")
            
        return True
        
    except Exception as e:
        print(f"❌ Dosya silme hatası: {e}")
        return False

def main():
    """Ana fonksiyon"""
    print("🚨 VERİTABANI SIFIRLAMA İŞLEMİ")
    print("=" * 50)
    print("⚠️  DİKKAT: Bu işlem TÜM verileri kalıcı olarak silecektir!")
    print("📊 Silinecek veriler:")
    print("   • Tüm kullanıcı hesapları")
    print("   • Test geçmişleri")
    print("   • Mülakat kayıtları") 
    print("   • Forum gönderileri ve yorumları")
    print("   • Kullanıcı istatistikleri")
    print("=" * 50)
    
    # Kullanıcıdan onay al
    while True:
        choice = input("\nDevam etmek istediğinizden emin misiniz? (evet/hayır): ").lower().strip()
        if choice in ['evet', 'e', 'yes', 'y']:
            break
        elif choice in ['hayır', 'h', 'no', 'n']:
            print("❌ İşlem iptal edildi.")
            return
        else:
            print("⚠️ Lütfen 'evet' veya 'hayır' yazın.")
    
    print("\n🔄 İşlem başlatılıyor...")
    
    # Seçenek 1: Fiziksel dosyaları sil (daha temiz)
    print("\n📋 Seçenekler:")
    print("1. Veritabanı dosyalarını tamamen sil (önerilen)")
    print("2. Sadece tabloları temizle")
    
    while True:
        method = input("\nHangi yöntemi tercih edersiniz? (1/2): ").strip()
        if method == "1":
            if delete_database_files():
                print("✅ Veritabanı dosyaları silindi. Uygulama restart edildiğinde temiz tablolar oluşturulacak.")
            break
        elif method == "2":
            reset_database()
            break
        else:
            print("⚠️ Lütfen 1 veya 2 seçin.")

if __name__ == "__main__":
    main()
