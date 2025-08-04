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

## Güvenlik Ayarları

### Environment Variables (.env)
```env
SECRET_KEY=btk-project-2024-secure-key-change-in-production-8f7d6e5c4b3a2
FLASK_ENV=development
FLASK_DEBUG=False
```

### Session Ayarları
```python
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 saat
app.config['SESSION_COOKIE_SECURE'] = False  # Development için
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_MAX_AGE'] = 3600
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
```

## Production Güvenlik Önerileri

### 1. Secret Key
- [ ] Production'da güçlü, rastgele secret key kullanın
- [ ] Secret key'i environment variable olarak saklayın

### 2. HTTPS
- [ ] `SESSION_COOKIE_SECURE = True` yapın
- [ ] SSL sertifikası kullanın

### 3. Rate Limiting
- [ ] Login denemelerini sınırlayın
- [ ] API isteklerini rate limit ile koruyun

### 4. Input Validation
- [ ] Tüm kullanıcı girdilerini doğrulayın
- [ ] SQL injection koruması ekleyin

### 5. Logging
- [ ] Güvenlik olaylarını loglayın
- [ ] Başarısız login denemelerini takip edin

## Güvenlik Testleri

### Test Edilmesi Gerekenler:
1. ✅ Şifre 5 karakterden az olamaz
2. ✅ Aynı kullanıcı adı ile tekrar kayıt olamaz
3. ✅ Giriş yapmadan özel sayfalara erişilemez
4. ✅ Session 1 saat sonra sona erer
5. ✅ Şifreler hashlenmiş olarak saklanır

### Test Senaryoları:
```bash
# Şifre gücü testi
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123","interest":"Data Science"}'
# Beklenen: "Şifre en az 5 karakter olmalıdır."

# Session kontrolü testi
curl -X GET http://localhost:5000/profile
# Beklenen: "Giriş yapmalısınız."
```

## Güvenlik Güncellemeleri

### Son Güncellemeler:
- ✅ Şifre gücü kontrolü eklendi (minimum 5 karakter)
- ✅ Secret key .env'den alınıyor
- ✅ Login_required dekoratörü eklendi
- ✅ Session güvenlik ayarları iyileştirildi
- ✅ Şifre değiştirme fonksiyonunda güç kontrolü eklendi

### Gelecek Güncellemeler:
- [ ] Rate limiting eklenmesi
- [ ] İki faktörlü doğrulama (2FA)
- [ ] Şifre karmaşıklık kontrolü (büyük harf, sayı, özel karakter)
- [ ] Otomatik şifre sıfırlama
- [ ] Güvenlik logları 