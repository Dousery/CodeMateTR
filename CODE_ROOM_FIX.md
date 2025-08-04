# Kodlama Odası Debug ve Session Kontrol Düzeltmeleri

## Yapılan Düzeltmeler

### 1. Backend Debug Logging Eklendi
```python
@app.route('/code_room', methods=['POST'])
@login_required
def code_room():
    print(f"DEBUG: code_room called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
```

### 2. Kodlama Odası Endpoint'i Eklendi
```python
@app.route('/code', methods=['GET'])
def code_page():
    """Kodlama odası sayfası için basit endpoint"""
    return jsonify({
        'message': 'Kodlama odası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })
```

### 3. Frontend Session Kontrolü
```javascript
// Component mount olduğunda state'leri sıfırla ve session kontrolü yap
useEffect(() => {
  resetAllStates();
  
  // Session durumunu kontrol et
  const checkSession = async () => {
    try {
      console.log('Checking session status for code room...');
      const sessionRes = await axios.get(API_ENDPOINTS.SESSION_STATUS, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Session status:', sessionRes.data);
      
      // Code endpoint'ini de kontrol et
      const codeRes = await axios.get(API_ENDPOINTS.CODE_PAGE, { 
        withCredentials: true,
        timeout: 5000
      });
      console.log('Code page status:', codeRes.data);
    } catch (err) {
      console.error('Session check failed for code room:', err);
    }
  };
  
  checkSession();
}, []);
```

### 4. Gelişmiş Error Handling

#### fetchQuestion Fonksiyonu
```javascript
const fetchQuestion = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Fetching coding question from:', API_ENDPOINTS.CODE_ROOM);
    console.log('Request data:', { difficulty: difficulty, language: selectedLanguage });
    
    const res = await axios.post(API_ENDPOINTS.CODE_ROOM, {
      difficulty: difficulty,
      language: selectedLanguage
    }, { 
      withCredentials: true,
      timeout: 15000
    });
    
    console.log('Coding question response:', res.data);
    setQuestion(res.data.coding_question);
    setStep('coding');
  } catch (err) {
    console.error('Error fetching coding question:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Kodlama sorusu alınamadı. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### handleRunCode Fonksiyonu
```javascript
const handleRunCode = async () => {
  if (!userCode.trim()) {
    setError('Lütfen kodunuzu yazın.');
    return;
  }
  
  setLoading(true);
  setError('');
  try {
    console.log('Running code with:', API_ENDPOINTS.CODE_RUN_SIMPLE);
    console.log('Code data:', { language: selectedLanguage, code_length: userCode.length });
    
    const res = await axios.post(API_ENDPOINTS.CODE_RUN_SIMPLE, {
      user_code: userCode,
      language: selectedLanguage
    }, { 
      withCredentials: true,
      timeout: 20000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error running code:', err);
    console.error('Error response:', err.response);
    
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      // Fallback: Eski API'yi dene
      try {
        console.log('🔄 Yeni API başarısız, eski API deneniyor...');
        const fallbackRes = await axios.post(API_ENDPOINTS.CODE_RUN, {
          user_code: userCode,
          language: selectedLanguage
        }, { 
          withCredentials: true,
          timeout: 20000
        });
        setExecutionOutput(fallbackRes.data.result);
      } catch (fallbackErr) {
        console.error('Fallback API also failed:', fallbackErr);
        setError(err.response?.data?.error || fallbackErr.response?.data?.error || 'Kod çalıştırma başarısız. Lütfen tekrar deneyin.');
      }
    }
  } finally {
    setLoading(false);
  }
};
```

#### handleEvaluateCode Fonksiyonu
```javascript
const handleEvaluateCode = async () => {
  if (!userCode.trim()) {
    setError('Lütfen kodunuzu yazın.');
    return;
  }
  
  setLoading(true);
  setError('');
  try {
    console.log('Evaluating code with:', API_ENDPOINTS.CODE_EVALUATE);
    console.log('Evaluation data:', { 
      question_length: question.length, 
      code_length: userCode.length, 
      language: selectedLanguage 
    });
    
    const res = await axios.post(API_ENDPOINTS.CODE_EVALUATE, {
      question: question,
      user_code: userCode,
      use_execution: true,
      language: selectedLanguage
    }, { 
      withCredentials: true,
      timeout: 30000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error evaluating code:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Değerlendirme başarısız. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### generateSolution Fonksiyonu
```javascript
const generateSolution = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Generating solution with:', API_ENDPOINTS.CODE_GENERATE);
    console.log('Solution data:', { question_length: question.length, language: selectedLanguage });
    
    const res = await axios.post(API_ENDPOINTS.CODE_GENERATE, {
      question: question,
      language: selectedLanguage
    }, { 
      withCredentials: true,
      timeout: 25000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error generating solution:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Çözüm üretilemedi. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### getResources Fonksiyonu
```javascript
const getResources = async () => {
  setLoading(true);
  setError('');
  try {
    console.log('Getting resources with:', API_ENDPOINTS.CODE_SUGGEST);
    
    const config = languageConfigs[selectedLanguage];
    const searchTopic = question 
      ? `${config.name} programlama ${question.slice(0, 100)}` 
      : `${config.name} programlama başlangıç orta seviye`;
    
    console.log('Search topic:', searchTopic);
      
    const res = await axios.post(API_ENDPOINTS.CODE_SUGGEST, {
      topic: searchTopic,
      num_resources: 5
    }, { 
      withCredentials: true,
      timeout: 15000
    });
    
    console.log('Resources response:', res.data);
    setResources(res.data);
  } catch (err) {
    console.error('Error getting resources:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError(err.response?.data?.error || 'Kaynaklar alınamadı. Lütfen tekrar deneyin.');
    }
  } finally {
    setLoading(false);
  }
};
```

#### formatCode Fonksiyonu
```javascript
const formatCode = async () => {
  if (!userCode.trim()) return;
  
  setLoading(true);
  setError('');
  try {
    console.log('Formatting code with:', API_ENDPOINTS.CODE_FORMAT);
    console.log('Format data:', { language: selectedLanguage, code_length: userCode.length });
    
    const res = await axios.post(API_ENDPOINTS.CODE_FORMAT, {
      code: userCode,
      language: selectedLanguage
    }, { 
      withCredentials: true,
      timeout: 10000
    });
    
    // ... rest of the code
  } catch (err) {
    console.error('Error formatting code:', err);
    console.error('Error response:', err.response);
    if (err.response?.status === 401) {
      setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
    } else if (err.code === 'ECONNABORTED') {
      setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
    } else {
      setError('❌ Kod formatlanamadı: ' + (err.response?.data?.error || err.message));
    }
  } finally {
    setLoading(false);
  }
};
```

## Test Endpoint'leri
- `/code`: Kodlama odası durumunu kontrol etmek için
- `/session-status`: Session durumunu kontrol etmek için
- `/code_room`: Kodlama sorusu almak için (POST)
- `/code_room/evaluate`: Kod değerlendirmesi için (POST)
- `/code_room/run`: Kod çalıştırma için (POST)
- `/code_room/run_simple`: Basit kod çalıştırma için (POST)
- `/code_room/generate_solution`: AI çözüm üretimi için (POST)
- `/code_room/suggest_resources`: Kaynak önerileri için (POST)
- `/code_room/format_code`: Kod formatlama için (POST)

## Debug Kontrolleri
1. Browser console'da session durumu kontrol edilir
2. Backend loglarında session bilgileri görüntülenir
3. API çağrıları detaylı olarak loglanır
4. Hata durumları kategorize edilir
5. Timeout ayarları eklendi

## Deployment Sonrası Kontrol
1. Kodlama odasına gidin: `https://codematetr.onrender.com/code`
2. Browser console'u açın ve logları kontrol edin
3. Backend loglarını kontrol edin
4. Session durumunu kontrol edin: `https://btk-project-backend.onrender.com/session-status`

## Notlar
- Kodlama odası artık session kontrolü yapıyor
- Debug bilgileri console'da görüntüleniyor
- Timeout ayarları eklendi (10-30 saniye)
- Error handling geliştirildi
- Fallback API'ler eklendi
- Tüm API çağrıları detaylı loglanıyor 