# Test Soru Çeşitliliği ve Adaptif Test Sistemi

Bu dokümantasyon, BTK Project'te uygulanan test soru çeşitliliği ve adaptif test sistemini açıklar.

## 🎯 Problem

Önceki sistemde kullanıcılar farklı seanslarda aynı test sorularını görüyordu. Bu durum:
- Öğrenme deneyimini azaltıyordu
- Test sonuçlarının güvenilirliğini düşürüyordu
- Kullanıcı motivasyonunu azaltıyordu

## 🚀 Çözüm

### 1. Soru Havuzu Sistemi
- Her ilgi alanı için ayrı soru havuzu
- Otomatik soru çeşitlendirme
- Duplicate soru kontrolü
- Dinamik havuz yenileme

### 2. Kullanıcı Geçmişi Takibi
- Her kullanıcı için benzersiz soru geçmişi
- Son 30 günde kullanılan soruları takip
- Session bazlı soru kullanımı
- Otomatik geçmiş temizleme (90 gün)

### 3. Adaptif Test Sistemi
- Önceki test sonuçlarına göre soru üretimi
- Zayıf alanlara odaklanma
- Performans bazlı zorluk seviyesi ayarlama
- Kişiselleştirilmiş öğrenme deneyimi

## 🔧 Teknik Detaylar

### TestAIAgent Güncellemeleri

#### Yeni Metodlar:
```python
# Soru havuzu yönetimi
def _get_diverse_questions_from_pool(self, num_questions, difficulty, user_id, session_id)
def _select_diverse_questions(self, questions, num_questions)
def _generate_new_questions_for_pool(self, num_questions, difficulty)

# Kullanıcı geçmişi takibi
def _is_question_used_recently(self, user_id, question_hash, days_limit=30)
def _add_question_to_history(self, user_id, question_hash, session_id)

# Adaptif test üretimi
def generate_adaptive_questions(self, user_id, session_id, previous_performance, num_questions)
def _generate_questions_for_weak_areas(self, weak_areas, num_questions, user_id, session_id)

# İstatistik ve yönetim
def get_question_statistics(self, user_id=None)
def refresh_question_pool(self, force_refresh=False)
```

#### Yeni Özellikler:
- **Soru Hash Sistemi**: Her soru için benzersiz MD5 hash
- **Otomatik Kategori Dengeleme**: Her kategoriden eşit soru seçimi
- **Zaman Bazlı Filtreleme**: Son kullanım tarihine göre soru filtreleme
- **Dinamik Soru Üretimi**: Havuzda yeterli soru yoksa otomatik üretim

### Backend API Güncellemeleri

#### Yeni Endpoint'ler:
```python
# Test istatistikleri
GET /test_your_skill/statistics

# Soru havuzu yenileme
POST /test_your_skill/refresh_pool

# Adaptif test önerisi
GET /test_your_skill/recommend_adaptive
```

#### Güncellenen Endpoint:
```python
# Test başlatma (adaptif test desteği eklendi)
POST /test_your_skill
{
  "num_questions": 10,
  "difficulty": "mixed",
  "use_adaptive": true  # Yeni parametre
}
```

### Frontend Güncellemeleri

#### Yeni UI Bileşenleri:
- **Adaptif Test Seçeneği**: Normal/Adaptif test türü seçimi
- **İstatistik Butonları**: Adaptif öneri ve istatistik görüntüleme
- **Modal'lar**: Detaylı bilgi görüntüleme
- **Havuz Yönetimi**: Soru havuzu yenileme

#### Yeni State'ler:
```javascript
const [useAdaptive, setUseAdaptive] = useState(false);
const [showAdaptiveRecommendation, setShowAdaptiveRecommendation] = useState(false);
const [adaptiveRecommendation, setAdaptiveRecommendation] = useState(null);
const [showStatistics, setShowStatistics] = useState(false);
const [statistics, setStatistics] = useState(null);
```

## 📊 Kullanım Senaryoları

### 1. Normal Test
```javascript
// Kullanıcı normal test seçer
setUseAdaptive(false);
setDifficulty('mixed');
setNumQuestions(10);

// Backend'e gönderilen istek
{
  "num_questions": 10,
  "difficulty": "mixed",
  "use_adaptive": false
}
```

### 2. Adaptif Test
```javascript
// Kullanıcı adaptif test seçer
setUseAdaptive(true);

// Backend otomatik olarak:
// - Önceki test sonuçlarını analiz eder
// - Zayıf alanları belirler
// - Uygun zorluk seviyesini seçer
// - Zayıf alanlara odaklı sorular üretir
```

### 3. Soru Havuzu Yönetimi
```javascript
// Kullanıcı istatistikleri görüntüler
getTestStatistics();

// Soru havuzunu yeniler
refreshQuestionPool();
```

## 🎨 Özellik Detayları

### Soru Çeşitlendirme Algoritması
1. **Kategori Gruplandırma**: Sorular kategorilerine göre gruplanır
2. **Eşit Dağılım**: Her kategoriden eşit sayıda soru seçilir
3. **Rastgele Seçim**: Her kategori içinde rastgele soru seçimi
4. **Kullanıcı Geçmişi Kontrolü**: Son kullanılan sorular filtrelenir
5. **Otomatik Tamamlama**: Yeterli soru yoksa yeni sorular üretilir

### Adaptif Test Mantığı
1. **Performans Analizi**: Son 3 testin ortalaması alınır
2. **Zorluk Belirleme**: Başarı oranına göre zorluk seviyesi
3. **Zayıf Alan Tespiti**: %60'ın altında başarı olan kategoriler
4. **Özel Soru Üretimi**: Zayıf alanlar için başlangıç seviyesi sorular
5. **Dengeli Dağılım**: Zayıf alan + genel soru karışımı

### Soru Havuzu Yönetimi
1. **Otomatik Genişleme**: Yeterli soru yoksa otomatik üretim
2. **Zorluk Seviyesi Dengeleme**: Her seviyeden eşit soru
3. **Kategori Çeşitliliği**: Farklı konulardan soru üretimi
4. **Kalite Kontrolü**: Duplicate ve kalitesiz soru filtreleme
5. **Periyodik Yenileme**: Eski soruları temizleme ve yenileme

## 🔍 Test ve Doğrulama

### Demo Dosyası
```bash
python test_question_diversity_example.py
```

### Test Senaryoları
1. **Aynı Kullanıcı, Farklı Seanslar**: Aynı soruların tekrarlanmadığını doğrula
2. **Farklı Kullanıcılar**: Her kullanıcının farklı sorular aldığını doğrula
3. **Adaptif Test**: Zayıf alanlara odaklanan soruların üretildiğini doğrula
4. **Havuz Yenileme**: Soru havuzunun başarıyla yenilendiğini doğrula

### Performans Metrikleri
- **Soru Tekrar Oranı**: %0 (hedef)
- **Havuz Genişleme Hızı**: Otomatik
- **Kullanıcı Deneyimi**: Gelişmiş
- **Sistem Performansı**: Optimize edilmiş

## 🚀 Gelecek Geliştirmeler

### Planlanan Özellikler:
1. **Makine Öğrenmesi Entegrasyonu**: Daha akıllı adaptif test
2. **Soru Kalite Skorlama**: Otomatik kalite değerlendirmesi
3. **Kullanıcı Davranış Analizi**: Test çözme paternleri
4. **Gelişmiş İstatistikler**: Detaylı performans analizi
5. **A/B Test Desteği**: Farklı algoritma karşılaştırması

### Teknik İyileştirmeler:
1. **Redis Cache**: Daha hızlı soru erişimi
2. **Asenkron Soru Üretimi**: Arka planda sürekli soru üretimi
3. **Mikroservis Mimarisi**: Test servisi ayrımı
4. **API Rate Limiting**: Güvenlik ve performans
5. **Monitoring ve Logging**: Detaylı sistem takibi

## 📝 Kullanım Örnekleri

### Frontend'de Adaptif Test
```javascript
// Test başlatma
const startAdaptiveTest = async () => {
  try {
    const response = await axios.post('/test_your_skill', {
      num_questions: 10,
      difficulty: 'mixed',
      use_adaptive: true
    });
    
    if (response.data.is_adaptive) {
      alert('🎯 Adaptif test başlatıldı!');
    }
    
    setQuestions(response.data.questions);
  } catch (error) {
    console.error('Test başlatma hatası:', error);
  }
};
```

### Backend'de Soru Üretimi
```python
# Adaptif soru üretimi
if use_adaptive and previous_performance:
    questions = agent.generate_adaptive_questions(
        user_id=user.username,
        session_id=session_id,
        previous_performance=previous_performance,
        num_questions=num_questions
    )
else:
    questions = agent.generate_questions(
        num_questions=num_questions,
        difficulty=difficulty,
        user_id=user.username,
        session_id=session_id
    )
```

### Soru Havuzu İstatistikleri
```python
# İstatistik alma
stats = agent.get_question_statistics(user_id=user.username)

# Havuz yenileme
refresh_result = agent.refresh_question_pool(force_refresh=True)
```

## 🎉 Sonuç

Bu güncelleme ile:
- ✅ Kullanıcılar artık farklı seanslarda aynı soruları görmeyecek
- ✅ Adaptif test sistemi ile kişiselleştirilmiş öğrenme
- ✅ Otomatik soru havuzu yönetimi
- ✅ Gelişmiş kullanıcı deneyimi
- ✅ Performans odaklı sistem tasarımı

Sistem artık daha akıllı, çeşitli ve kullanıcı dostu bir test deneyimi sunuyor.
