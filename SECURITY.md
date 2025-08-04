# 🔒 BTK Project Güvenlik Dokümantasyonu

## Güvenlik Önlemleri

### 1. Kullanıcı Doğrulama (Authentication)
- ✅ **Zorunlu Giriş**: Tüm özel sayfalar için giriş zorunlu
- ✅ **Session Kontrolü**: `@login_required` dekoratörü ile otomatik kontrol
- ✅ **Güvenli Çıkış**: Session verileri temizleniyor

### 2. Şifre Güvenliği
- ✅ **Hashleme**: Şifreler `werkzeug.security.generate_password_hash()` ile hashlenmiş
- ✅ **Minimum Uzunluk**: Şifreler en az 5 karakter olmalı
- ✅ **Güçlü Şifre**: Frontend ve backend'de kontrol ediliyor
- ✅ **Şifre Değiştirme**: Güvenli şifre değiştirme fonksiyonu

### 3. Session Yönetimi
- ✅ **Oturum Süresi**: 1 saat (3600 saniye)
- ✅ **Otomatik Yenileme**: Her istekte session yenileniyor
- ✅ **Güvenli Cookie**: HttpOnly ve SameSite ayarları
- ✅ **Session Temizleme**: Login sırasında eski session'lar temizleniyor

### 4. Kullanıcı Adı Benzersizliği
- ✅ **Tekrar Kayıt Engeli**: Aynı kullanıcı adı ile kayıt engellenmiş
- ✅ **Database Constraint**: Unique constraint ile güvence

### 5. Erişim Kontrolü
- ✅ **Özel Sayfa Koruması**: Giriş yapmadan özel sayfalara erişim engellenmiş
- ✅ **API Koruması**: Tüm API endpoint'leri korunmuş
- ✅ **Dekoratör Sistemi**: Temiz ve tutarlı güvenlik kontrolü