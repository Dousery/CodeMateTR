<div align="center">

<h2>🚀 BTK Project — Yapay Zeka Destekli Öğrenme Platformu</h2>

<p>AI ile test, kodlama ve mülakat deneyimleri. React + Flask mimarisi.</p>

<a href="https://codematetr.onrender.com"><img alt="Live" src="https://img.shields.io/badge/Live-codematetr.onrender.com-22c55e?style=for-the-badge&logo=vercel&logoColor=white"></a>
<img alt="Frontend" src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=white">
<img alt="Backend" src="https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white">
<img alt="License" src="https://img.shields.io/badge/License-MIT-0ea5e9?style=for-the-badge">

</div>

### Canlı Yayın
- Site: `https://codematetr.onrender.com`

### Öne Çıkanlar
- 🎯 AI Test: Kişiselleştirilmiş test ve anlık değerlendirme
- 💻 Kodlama Odası: Çalıştır, değerlendir, iyileştir — tek akışta
- 🧠 Mülakat: Gerçek zamanlı ve otomatik (ses/metin) senaryolar

### Teknolojiler
- Backend: Flask, SQLAlchemy, PostgreSQL, Gunicorn
- Frontend: React, Vite, MUI, Axios

---

### ⚡ Hızlı Başlangıç (Yerel)
1) Depoyu klonlayın ve köke geçin.
2) Backend: sanal ortamı kurun ve bağımlılıkları yükleyin.
```bash
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
cp env.example .env
```
3) Frontend: bağımlılıkları yükleyin.
```bash
cd frontend && npm install
```
4) Geliştirme modunda çalıştırın.
```bash
# Backend
python app.py

# Frontend
cd frontend && npm run dev
```

### 🐳 Docker ile Çalıştırma
```bash
docker-compose up --build
```

### 🔧 Ortam Değişkenleri (özet)
- Backend `.env`: `SECRET_KEY`, `DATABASE_URL`, `FRONTEND_URL`, `FLASK_ENV`
- Frontend `.env.production`: `VITE_API_BASE_URL`

### 📁 Proje Yapısı (kısa)
```
BTK_Project/
├── app.py
├── agents/, models/, utils/
├── frontend/ (React)
└── docker-compose.yml, Dockerfile, requirements.txt
```

### 📜 Lisans
MIT
