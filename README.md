<div align="center">

<h2>🚀 CodeMateTR — Yapay Zeka Destekli Öğrenme Platformu</h2>

<p>AI ile test, kodlama ve mülakat deneyimleri. React + Flask mimarisi.</p>

### SİTE ŞUAN BAKIMDA

</div>

<img width="1817" height="977" alt="image" src="https://github.com/user-attachments/assets/ca759938-4e3c-4dfd-9bfe-956c6f4ed460" />


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
