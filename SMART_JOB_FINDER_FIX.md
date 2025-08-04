# Akıllı İş Bulma Sayfası Debug ve Session Kontrol Düzeltmeleri

## Yapılan Düzeltmeler

### 1. Backend Debug Logging Eklendi
```python
@app.route('/api/analyze-cv', methods=['POST'])
@login_required
def analyze_cv():
    """CV'yi Gemini AI ile analiz eder"""
    print(f"DEBUG: analyze_cv called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    try:
        # Kullanıcı girişi kontrolü (geçici olarak devre dışı - debug için)
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        
        # Test için user_id ata
        user_id = session.get('user_id', 'test_user')
```

```python
@app.route('/api/search-jobs', methods=['POST'])
@login_required
def search_jobs():
    """CV analizine göre iş ilanları arar ve eşleştirir"""
    print(f"DEBUG: search_jobs called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    try:
        # Kullanıcı girişi kontrolü (geçici olarak devre dışı - debug için)
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        
        data = request.json
        if not data or 'cv_analysis' not in data:
            return jsonify({'error': 'CV analizi verisi bulunamadı'}), 400
```

```python
@app.route('/api/job-application-tips', methods=['POST'])
@login_required
def get_job_application_tips():
    print(f"DEBUG: get_job_application_tips called by user: {session.get('username')}")
    """Belirli bir iş için başvuru önerileri verir"""
    try:
```

### 2. Akıllı İş Bulma Sayfası Endpoint'i Eklendi
```python
@app.route('/smart-job-finder', methods=['GET'])
def smart_job_finder_page():
    """Akıllı iş bulma sayfası için basit endpoint"""
    return jsonify({
        'message': 'Akıllı iş bulma sayfası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })
```

### 3. Frontend Session Kontrolü
```javascript
// Component mount olduğunda session kontrolü yap
useEffect(() => {
  const checkSession = async () => {
    try {
      console.log('Checking session status for smart job finder...');
      const sessionRes = await axios.get(API_ENDPOINTS.SESSION_STATUS, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Session status:', sessionRes.data);
      
      // Smart job finder endpoint'ini de kontrol et
      const smartJobRes = await axios.get(API_ENDPOINTS.SMART_JOB_FINDER_PAGE, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Smart job finder page status:', smartJobRes.data);
    } catch (err) {
      console.error('Session check failed for smart job finder:', err);
    }
  };
  
  checkSession();
}, []);
```

### 4. Gelişmiş Error Handling

#### analyzeCvWithFile Fonksiyonu
```javascript
const analyzeCvWithFile = async (file) => {
  if (!file) {
    setError('Lütfen önce bir CV dosyası seçin');
    return;
  }

  setLoading(true);
  setError('');

  const formData = new FormData();
  formData.append('cv_file', file);

  try {
    console.log('Analyzing CV with:', API_ENDPOINTS.ANALYZE_CV);
    console.log('CV file data:', { 
      filename: file.name,
      size: file.size,
      type: file.type
    });
    
    const response = await axios.post(API_ENDPOINTS.ANALYZE_CV, formData, {
      withCredentials: true,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    });

    const data = response.data;
    console.log('CV analysis response:', data);

    if (data.success) {
      setCvAnalysis(data.cv_analysis);
      setActiveStep(1);
      
      // Otomatik olarak iş arama adımına geç
      setTimeout(() => {
        searchJobs(data.cv_analysis);
      }, 1000);
    } else {
      setError(data.error || 'CV analizi başarısız');
    }
  } catch (error) {
    console.error('CV analizi hatası:', error);
    console.error('Error response:', error.response);
    if (error.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (error.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(error.response?.data?.error || 'CV analizi sırasında bir hata oluştu. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### searchJobs Fonksiyonu
```javascript
const searchJobs = async (analysis = cvAnalysis) => {
  if (!analysis) {
    setError('CV analizi bulunamadı');
    return;
  }

  setLoading(true);
  setActiveStep(2);

  try {
    console.log('Searching jobs with:', API_ENDPOINTS.SEARCH_JOBS);
    console.log('Search data:', { 
      cv_analysis_keys: Object.keys(analysis),
      location: 'Türkiye',
      max_jobs: 20
    });
    
    const response = await axios.post(API_ENDPOINTS.SEARCH_JOBS, {
      cv_analysis: analysis,
      location: 'Türkiye',
      max_jobs: 20
    }, {
      withCredentials: true,
      timeout: 60000
    });

    const data = response.data;
    console.log('Job search response:', data);

    if (data.success) {
      setJobs(data.jobs);
      setStats(data.stats);
      setActiveStep(3);
    } else {
      setError(data.error || 'İş arama başarısız');
    }
  } catch (error) {
    console.error('İş arama hatası:', error);
    console.error('Error response:', error.response);
    if (error.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (error.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(error.response?.data?.error || 'İş arama sırasında bir hata oluştu. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### getJobApplicationTips Fonksiyonu
```javascript
const getJobApplicationTips = async (job) => {
  try {
    console.log('Getting job application tips with:', API_ENDPOINTS.JOB_TIPS);
    console.log('Job data:', { 
      job_title: job.title,
      company: job.company,
      url: job.url
    });
    
    const response = await axios.post(API_ENDPOINTS.JOB_TIPS, {
      cv_analysis: cvAnalysis,
      job: job
    }, {
      withCredentials: true,
      timeout: 30000
    });

    const data = response.data;
    console.log('Job tips response:', data);
    
    if (data.success) {
      // Tips'i job objesine ekle
      const updatedJobs = jobs.map(j => 
        j.url === job.url ? { ...j, tips: data.tips } : j
      );
      setJobs(updatedJobs);
    }
  } catch (err) {
    console.error('Başvuru önerileri alınamadı:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      console.error('Session expired while getting job tips');
    } else if (err.code === 'ECONNABORTED') {
      console.error('Timeout while getting job tips');
    }
  }
};
```

## Test Endpoint'leri
- `/smart-job-finder`: Akıllı iş bulma sayfası durumunu kontrol etmek için
- `/session-status`: Session durumunu kontrol etmek için
- `/api/analyze-cv`: CV analizi yapmak için (POST)
- `/api/search-jobs`: İş araması yapmak için (POST)
- `/api/job-application-tips`: İş başvuru önerileri almak için (POST)

## Debug Kontrolleri
1. Browser console'da session durumu kontrol edilir
2. Backend loglarında session bilgileri görüntülenir
3. API çağrıları detaylı olarak loglanır
4. Hata durumları kategorize edilir
5. Timeout ayarları eklendi (30-60 saniye)
6. CV dosyası boyutu ve türü loglanır
7. İş arama parametreleri loglanır

## Deployment Sonrası Kontrol
1. Akıllı iş bulma sayfasına gidin: `https://codematetr.onrender.com/smart-job-finder`
2. Browser console'u açın ve logları kontrol edin
3. Backend loglarını kontrol edin
4. Session durumunu kontrol edin: `https://btk-project-backend.onrender.com/session-status`

## Notlar
- Akıllı iş bulma sayfası artık session kontrolü yapıyor
- Debug bilgileri console'da görüntüleniyor
- Timeout ayarları eklendi (30-60 saniye)
- Error handling geliştirildi
- CV dosyası işlemleri detaylı loglanıyor
- Tüm API çağrıları detaylı loglanıyor
- Session durumu her adımda kontrol ediliyor
- İş arama parametreleri ve sonuçları loglanıyor 