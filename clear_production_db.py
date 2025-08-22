#!/usr/bin/env python3
"""
Production PostgreSQL veritabanını temizleme scripti
"""
import os
from sqlalchemy import text
from app import app, db

def clear_production_database():
    """Production PostgreSQL veritabanındaki tüm kayıtları temizle"""
    with app.app_context():
        try:
            print("🔄 Production veritabanı temizleme işlemi başlatılıyor...")
            
            # Tablo isimlerini al
            tables_query = """
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'pg_%' 
                AND tablename NOT LIKE 'sql_%'
            """
            
            with db.engine.connect() as conn:
                # Mevcut tabloları listele
                result = conn.execute(text(tables_query))
                tables = [row[0] for row in result.fetchall()]
                
                print(f"📋 Bulunan tablolar: {', '.join(tables)}")
                
                if not tables:
                    print("ℹ️ Temizlenecek tablo bulunamadı")
                    return True
                
                # Foreign key kısıtlamalarını geçici olarak kaldır
                print("🔓 Foreign key kısıtlamaları geçici olarak devre dışı bırakılıyor...")
                conn.execute(text("SET session_replication_role = replica;"))
                
                # Her tabloyu temizle
                for table in tables:
                    try:
                        print(f"🗑️ {table} tablosu temizleniyor...")
                        conn.execute(text(f"TRUNCATE TABLE \"{table}\" CASCADE"))
                        print(f"✅ {table} tablosu temizlendi")
                    except Exception as e:
                        print(f"⚠️ {table} tablosu temizlenemedi: {e}")
                
                # Foreign key kısıtlamalarını yeniden etkinleştir
                print("🔒 Foreign key kısıtlamaları yeniden etkinleştiriliyor...")
                conn.execute(text("SET session_replication_role = DEFAULT;"))
                
                # Değişiklikleri kaydet
                conn.commit()
                
                print("\n🎉 Production veritabanı başarıyla temizlendi!")
                print("📝 Tüm tablolar boş, sistem temiz durumda!")
                
                # Temizleme sonrası kontrol
                total_records = 0
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
                        count = result.scalar()
                        total_records += count
                        if count > 0:
                            print(f"⚠️ {table}: {count} kayıt kaldı")
                    except:
                        pass
                
                if total_records == 0:
                    print("✅ Tüm tablolar tamamen boş!")
                else:
                    print(f"⚠️ Toplam {total_records} kayıt kaldı")
                
        except Exception as e:
            print(f"❌ Veritabanı temizleme hatası: {e}")
            return False
            
    return True

def main():
    """Ana fonksiyon"""
    print("🚨 PRODUCTION VERİTABANI TEMİZLEME")
    print("=" * 50)
    print("⚠️  DİKKAT: Bu işlem PostgreSQL production veritabanındaki")
    print("           TÜM kayıtları kalıcı olarak silecektir!")
    print("📊 Silinecek veriler:")
    print("   • Tüm kullanıcı hesapları")
    print("   • Test geçmişleri")
    print("   • Mülakat kayıtları") 
    print("   • Forum gönderileri ve yorumları")
    print("   • Kullanıcı istatistikleri")
    print("   • Diğer tüm uygulama verileri")
    print("=" * 50)
    
    # Kullanıcıdan onay al
    while True:
        choice = input("\nProduction veritabanını temizlemek istediğinizden emin misiniz? (EVET/hayır): ").strip()
        if choice == 'EVET':
            break
        elif choice.lower() in ['hayır', 'h', 'no', 'n']:
            print("❌ İşlem iptal edildi.")
            return
        else:
            print("⚠️ Güvenlik için tam olarak 'EVET' yazın veya 'hayır' ile iptal edin.")
    
    print("\n🔄 Production veritabanı temizleme işlemi başlatılıyor...")
    
    # Temizleme işlemini gerçekleştir
    if clear_production_database():
        print("\n✅ İşlem başarıyla tamamlandı!")
    else:
        print("\n❌ İşlem sırasında hata oluştu!")

if __name__ == "__main__":
    main()
