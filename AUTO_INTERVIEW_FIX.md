# Otomatik Mülakat Odası Debug ve Session Kontrol Düzeltmeleri

## Yapılan Düzeltmeler

### 1. Backend Debug Logging Eklendi
```python
@app.route('/auto_interview/start', methods=['POST'])
@login_required
def start_auto_interview():
    """Otomatik mülakat başlatır"""
    print(f"DEBUG: start_auto_interview called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
```

### 2. Otomatik Mülakat Odası Endpoint'i Eklendi
```python
@app.route('/auto-interview', methods=['GET'])
def auto_interview_page():
    """Otomatik mülakat odası sayfası için basit endpoint"""
    return jsonify({
        'message': 'Otomatik mülakat odası erişilebilir',
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
      console.log('Checking session status for auto interview...');
      const sessionRes = await axios.get(API_ENDPOINTS.SESSION_STATUS, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Session status:', sessionRes.data);
      
      // Auto interview endpoint'ini de kontrol et
      const autoInterviewRes = await axios.get(API_ENDPOINTS.AUTO_INTERVIEW_PAGE, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Auto interview page status:', autoInterviewRes.data);
    } catch (err) {
      console.error('Session check failed for auto interview:', err);
    }
  };
  
  checkSession();
}, []);
```

### 4. Gelişmiş Error Handling

#### startAutoInterview Fonksiyonu
```javascript
const startAutoInterview = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Starting auto interview with:', API_ENDPOINTS.AUTO_INTERVIEW_START);
    
    const res = await axios.post(API_ENDPOINTS.AUTO_INTERVIEW_START, {}, { 
      withCredentials: true,
      timeout: 20000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error starting auto interview:', err);
    console.error('Error response:', err.response);
    
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
      setStep('starting');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
      setStep('starting');
    } else if (err.response?.data?.error === 'Aktif bir mülakat oturumunuz zaten var.') {
      // Aktif oturum varsa kullanıcıya seçenek sun
      setStep('session_choice');
    } else {
      setError(err.response?.data?.error || 'Otomatik mülakat başlatılamadı. Lütfen tekrar deneyin.');
      setStep('starting');
    }
  } finally {
    setLoading(false);
  }
};
```

#### clearActiveSession Fonksiyonu
```javascript
const clearActiveSession = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Clearing active session with:', API_ENDPOINTS.DEBUG_CLEAR_SESSIONS);
    
    await axios.post(API_ENDPOINTS.DEBUG_CLEAR_SESSIONS, {}, { 
      withCredentials: true,
      timeout: 10000
    });
    
    // Temizleme başarılı olduktan sonra yeni mülakat başlat
    await startAutoInterview();
  } catch (err) {
    console.error('Error clearing active session:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError('Oturum temizlenemedi. Lütfen tekrar deneyin.');
    }
    setStep('starting');
  } finally {
    setLoading(false);
  }
};
```

#### submitAnswer Fonksiyonu
```javascript
const submitAnswer = async () => {
  if (!userAnswer.trim()) {
    setError('Lütfen bir cevap yazın.');
    return;
  }

  setLoading(true);
  setError('');
  try {
    console.log('Submitting answer with:', API_ENDPOINTS.AUTO_INTERVIEW_SUBMIT);
    console.log('Answer data:', { 
      session_id: sessionId, 
      answer_length: userAnswer.length,
      voice_name: 'Kore'
    });
    
    const res = await axios.post(API_ENDPOINTS.AUTO_INTERVIEW_SUBMIT, {
      session_id: sessionId,
      answer: userAnswer,
      voice_name: 'Kore'
    }, { 
      withCredentials: true,
      timeout: 25000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error submitting answer:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Cevap gönderilemedi. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### completeInterview Fonksiyonu
```javascript
const completeInterview = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Completing interview with:', API_ENDPOINTS.AUTO_INTERVIEW_COMPLETE);
    console.log('Complete data:', { session_id: sessionId });
    
    const res = await axios.post(API_ENDPOINTS.AUTO_INTERVIEW_COMPLETE, {
      session_id: sessionId
    }, { 
      withCredentials: true,
      timeout: 30000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error completing interview:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Mülakat tamamlanamadı. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### checkActiveSession Fonksiyonu
```javascript
const checkActiveSession = async () => {
  try {
    console.log('Checking active session with:', API_ENDPOINTS.AUTO_INTERVIEW_STATUS);
    
    const res = await axios.get(API_ENDPOINTS.AUTO_INTERVIEW_STATUS, { 
      withCredentials: true,
      timeout: 10000
    });
    
    console.log('Active session response:', res.data);
    
    if (res.data.has_active_session) {
      // Aktif session varsa kullanıcıya seçenek sun
      setStep('session_choice');
    } else {
      setStep('starting');
    }
  } catch (err) {
    console.error('Error checking active session:', err);
    console.error('Error response:', err.response);
    // Hata durumunda direkt starting adımına geç
    setStep('starting');
  }
};
```

#### submitVoiceAnswer Fonksiyonu
```javascript
const submitVoiceAnswer = async () => {
  if (!recordedAudio) {
    setError('Lütfen önce ses kaydı yapın.');
    return;
  }

  setLoading(true);
  setError('');
  
  const formData = new FormData();
  formData.append('audio', recordedAudio);
  formData.append('session_id', sessionId);
  formData.append('voice_name', 'Kore');
  
  try {
    console.log('Submitting voice answer with:', API_ENDPOINTS.AUTO_INTERVIEW_SUBMIT);
    console.log('Voice answer data:', { 
      session_id: sessionId, 
      audio_size: recordedAudio.size,
      voice_name: 'Kore'
    });
    
    const res = await axios.post(API_ENDPOINTS.AUTO_INTERVIEW_SUBMIT, formData, {
      withCredentials: true,
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error submitting voice answer:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Sesli cevap gönderilemedi. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

## Test Endpoint'leri
- `/auto-interview`: Otomatik mülakat odası durumunu kontrol etmek için
- `/session-status`: Session durumunu kontrol etmek için
- `/auto_interview/start`: Otomatik mülakat başlatmak için (POST)
- `/auto_interview/submit_answer`: Mülakat cevabı göndermek için (POST)
- `/auto_interview/complete`: Mülakatı tamamlamak için (POST)
- `/auto_interview/status`: Mülakat durumunu kontrol etmek için (GET)

## Debug Kontrolleri
1. Browser console'da session durumu kontrol edilir
2. Backend loglarında session bilgileri görüntülenir
3. API çağrıları detaylı olarak loglanır
4. Hata durumları kategorize edilir
5. Timeout ayarları eklendi (10-30 saniye)
6. Ses dosyası boyutu loglanır

## Deployment Sonrası Kontrol
1. Otomatik mülakat odasına gidin: `https://codematetr.onrender.com/auto-interview`
2. Browser console'u açın ve logları kontrol edin
3. Backend loglarını kontrol edin
4. Session durumunu kontrol edin: `https://btk-project-backend.onrender.com/session-status`

## Notlar
- Otomatik mülakat odası artık session kontrolü yapıyor
- Debug bilgileri console'da görüntüleniyor
- Timeout ayarları eklendi (10-30 saniye)
- Error handling geliştirildi
- Ses dosyası işlemleri detaylı loglanıyor
- Tüm API çağrıları detaylı loglanıyor
- Session durumu her adımda kontrol ediliyor 