# BTK Project - Bellek Optimizasyonu Rehberi

## Sorun Tespiti

Render.com'da `btk-project-backend` servisi bellek limitini aştı ve otomatik yeniden başlatıldı. Bu sorunun ana nedenleri:

1. **Geçici Dosya Sızıntısı**: `tempfile.NamedTemporaryFile` ile oluşturulan dosyalar `delete=False` parametresi ile oluşturuluyor ve hiçbir yerde silinmiyor
2. **Bellek Temizliği Eksikliği**: Garbage collection ve bellek temizliği yapılmıyor
3. **Ses Dosyaları**: Audio processing sırasında oluşturulan geçici dosyalar birikiyor

## Yapılan Optimizasyonlar

### 1. Geçici Dosya Yönetimi

**Sorun**: `interview_agent.py` dosyasında geçici ses dosyaları düzgün kapatılmıyor ve silinmiyor.

**Çözüm**:
```python
# Önceki kod (sorunlu)
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
self._save_wave_file(temp_file.name, audio_data)

# Yeni kod (düzeltilmiş)
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
temp_file_path = temp_file.name
temp_file.close()  # Dosyayı kapat
self._save_wave_file(temp_file_path, audio_data)
self.temp_files.append(temp_file_path)  # Takip listesine ekle
```

### 2. Otomatik Temizlik Sistemi

**Eklenen Özellikler**:
- `cleanup_temp_files()`: Geçici dosyaları otomatik temizler
- `cleanup_memory()`: Garbage collection yapar
- `get_memory_usage()`: Bellek kullanımını izler

```python
def cleanup_temp_files(self):
    """Geçici dosyaları temizler"""
    for temp_file in self.temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except Exception as e:
            print(f"Error cleaning up temp file {temp_file}: {e}")
    self.temp_files.clear()
```

### 3. Endpoint Bazlı Bellek Temizliği

Kritik endpoint'lere bellek temizliği eklendi:
- `/interview_speech_evaluation`
- `/auto_interview/submit_answer`

```python
# Her kritik işlem sonrası
cleanup_memory()
cleanup_temp_files()
```

### 4. Debug Endpoint'leri

Admin paneli için bellek izleme endpoint'leri:
- `GET /debug/memory_status`: Bellek durumunu gösterir
- `POST /debug/clear_auto_interview_sessions`: Aktif session'ları temizler

## Yeni Bağımlılıklar

`requirements.txt` dosyasına eklendi:
```
psutil>=5.9.0
```

## Performans İyileştirmeleri

### 1. Session Yönetimi
- Production'da session'lar filesystem'de saklanıyor
- Session refresh her istekte yapılmıyor (performans için)
- Session dosya eşiği 500 olarak ayarlandı

### 2. Database Connection Pooling
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_timeout': 20,
    'pool_recycle': 300,
    'max_overflow': 20,
    'pool_pre_ping': True
}
```

### 3. Dosya Boyutu Limitleri
- Maksimum dosya boyutu: 16MB
- Geçici dosyalar 1 saat sonra otomatik silinir

## Monitoring ve İzleme

### Bellek Kullanımı İzleme
```python
def get_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }
```

### Logging
- Bellek temizliği işlemleri loglanıyor
- Geçici dosya silme işlemleri izleniyor
- Hata durumları kaydediliyor

## Öneriler

### 1. Render.com Ayarları
- **Instance Type**: Daha büyük instance kullanın (512MB yerine 1GB)
- **Auto-scaling**: Yüksek trafik için auto-scaling aktif edin
- **Health Checks**: Düzenli health check endpoint'i ekleyin

### 2. Kod İyileştirmeleri
- Audio processing için streaming kullanın
- Büyük dosyalar için chunked processing
- Redis cache ekleyin (session ve geçici veriler için)

### 3. Monitoring
- Prometheus/Grafana ile detaylı monitoring
- Alert sistemi kurun (bellek %80'i geçince)
- Log aggregation (ELK stack)

## Test Senaryoları

### 1. Bellek Sızıntısı Testi
```bash
# 100 ses değerlendirme isteği gönder
for i in {1..100}; do
  curl -X POST /interview_speech_evaluation \
    -F "audio=@test_audio.webm" \
    -F "question=Test question"
done
```

### 2. Geçici Dosya Temizliği Testi
```bash
# Temp dizinindeki dosya sayısını kontrol et
ls -la /tmp/*.wav | wc -l
```

### 3. Bellek Kullanımı Testi
```bash
# Bellek durumunu kontrol et
curl -X GET /debug/memory_status
```

## Deployment Kontrol Listesi

- [ ] `psutil` paketi eklendi
- [ ] Geçici dosya temizliği aktif
- [ ] Bellek izleme endpoint'leri çalışıyor
- [ ] Session yönetimi optimize edildi
- [ ] Database connection pooling aktif
- [ ] Logging seviyesi ayarlandı
- [ ] Health check endpoint'i eklendi

## Sonuç

Bu optimizasyonlar ile:
- Geçici dosya sızıntısı çözüldü
- Bellek kullanımı optimize edildi
- Monitoring sistemi eklendi
- Production performansı iyileştirildi

Render.com'da bellek limiti aşma sorunu çözülmüş olmalı. Düzenli monitoring ile sistem performansını takip edin.
