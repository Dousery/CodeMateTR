# BTK Project - AI-Powered Learning Platform

Bu proje, yapay zeka destekli bir öğrenme platformudur. React frontend ve Flask backend kullanılarak geliştirilmiştir.

## 🚀 Özellikler

- **AI Test Sistemi**: Kişiselleştirilmiş testler ve değerlendirmeler
- **Kodlama Odası**: AI destekli kod yazma ve değerlendirme
- **Mülakat Simülasyonu**: Gerçek zamanlı AI mülakat deneyimi
- **Otomatik Mülakat**: Sesli ve metin tabanlı mülakat sistemi
- **Akıllı İş Bulma**: CV analizi ve kariyer önerileri
- **Forum Sistemi**: Topluluk etkileşimi ve bilgi paylaşımı

## 🛠️ Teknolojiler

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM
- **PostgreSQL**: Veritabanı
- **Gunicorn**: WSGI server
- **Google Gemini AI**: AI servisleri

### Frontend
- **React**: UI framework
- **Vite**: Build tool
- **Material-UI**: UI components
- **Axios**: HTTP client
- **Framer Motion**: Animasyonlar

## 📦 Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Docker (opsiyonel)

### Local Development

1. **Repository'yi klonlayın**
```bash
git clone <repository-url>
cd BTK_Project
```

2. **Backend kurulumu**
```bash
# Virtual environment oluşturun
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Environment değişkenlerini ayarlayın
cp env.example .env
# .env dosyasını düzenleyin
```

3. **Frontend kurulumu**
```bash
cd frontend
npm install
```

4. **Veritabanını ayarlayın**
```bash
# PostgreSQL'de veritabanı oluşturun
createdb btk_project

# Backend'de veritabanı tablolarını oluşturun
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. **Uygulamayı çalıştırın**
```bash
# Backend (bir terminal'de)
python app.py

# Frontend (başka bir terminal'de)
cd frontend
npm run dev
```

### Docker ile Kurulum

1. **Docker Compose ile çalıştırın**
```bash
docker-compose up --build
```

2. **Uygulamaya erişin**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## 🌐 Production Deployment

### Render.com ile Deploy

1. **Repository'yi Render'a bağlayın**
2. **Environment variables'ları ayarlayın:**
   - `FLASK_ENV=production`
   - `SECRET_KEY=<your-secret-key>`
   - `DATABASE_URL=<postgresql-url>`
   - `FRONTEND_URL=<your-frontend-url>`
   - `GEMINI_API_KEY=<your-gemini-api-key>`

3. **Build ve start komutları:**
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn --bind 0.0.0.0:$PORT app:app`

### Manuel Deploy

1. **Backend için:**
```bash
# Production dependencies
pip install -r requirements.txt

# Environment variables
export FLASK_ENV=production
export DATABASE_URL=<your-database-url>
export SECRET_KEY=<your-secret-key>
export FRONTEND_URL=<your-frontend-url>
export GEMINI_API_KEY=<your-gemini-api-key>

# Start with gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 app:app
```

2. **Frontend için:**
```bash
cd frontend
npm install
npm run build
# dist/ klasörünü web server'a deploy edin
```

## 🔧 Environment Variables

### Backend (.env)
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost:5432/btk_project
FRONTEND_URL=http://localhost:5173
GEMINI_API_KEY=your-gemini-api-key-here
```

### Frontend (.env.production)
```env
VITE_API_BASE_URL=https://your-backend-domain.com
```

## 📁 Proje Yapısı

```
BTK_Project/
├── app.py                 # Flask uygulaması
├── requirements.txt       # Python bağımlılıkları
├── Dockerfile            # Backend Docker
├── docker-compose.yml    # Docker Compose
├── render.yaml           # Render.com config
├── build.sh              # Build script
├── start.sh              # Start script
├── agents/               # AI agent'ları
├── models/               # Veritabanı modelleri
├── utils/                # Yardımcı fonksiyonlar
├── frontend/             # React uygulaması
│   ├── src/
│   ├── package.json
│   ├── Dockerfile        # Frontend Docker
│   └── nginx.conf        # Nginx config
└── uploads/              # Yüklenen dosyalar
```

## 🔒 Güvenlik

- CORS ayarları production'da sıkılaştırılmıştır
- Session güvenliği için secure cookies kullanılır
- API key'ler environment variables ile yönetilir
- File upload güvenliği için boyut ve tip kontrolleri

## 🧪 Test

```bash
# Backend testleri
python -m pytest tests/

# Frontend testleri
cd frontend
npm test
```

## 📝 API Documentation

### Authentication
- `POST /register` - Kullanıcı kaydı
- `POST /login` - Kullanıcı girişi
- `POST /logout` - Kullanıcı çıkışı

### Test Sistemi
- `POST /test_your_skill` - Test başlat
- `POST /test_your_skill/evaluate` - Test değerlendir

### Mülakat Sistemi
- `POST /interview_simulation` - Mülakat başlat
- `POST /interview_simulation/evaluate` - Cevap değerlendir
- `POST /auto_interview/start` - Otomatik mülakat başlat

### Kodlama Sistemi
- `POST /code_room` - Kod sorusu al
- `POST /code_room/evaluate` - Kod değerlendir
- `POST /code_room/run` - Kod çalıştır

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🆘 Destek

Herhangi bir sorun yaşarsanız:
1. Issue oluşturun
2. Documentation'ı kontrol edin
3. Environment variables'ları kontrol edin
4. Log dosyalarını inceleyin

## 🔄 Güncellemeler

- **v1.0.0**: İlk production release
- AI test sistemi
- Mülakat simülasyonu
- Kodlama odası
- Forum sistemi
