import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Button, TextField, CircularProgress, Alert, 
  Card, CardContent, Chip, Tab, Tabs, Grid, IconButton, Switch, FormControlLabel
} from '@mui/material';
import { 
  Mic, MicOff, PlayArrow, VolumeUp, Send, Keyboard, RecordVoiceOver 
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';
import API_ENDPOINTS, { getAudioUrl } from './config.js';

export default function Interview() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [step, setStep] = useState('start'); // start, cv-upload, interview, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [cvFile, setCvFile] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [difficulty, setDifficulty] = useState('orta');
  const [personalizedQuestions, setPersonalizedQuestions] = useState([]);
  
  // Ses ile ilgili state'ler
  const [audioUrl, setAudioUrl] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [isSpeechMode, setIsSpeechMode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Ses fonksiyonları
  const playAudio = (url) => {
    try {
      const audio = new Audio(url);
      audio.play().catch(e => {
        console.log('Ses çalınamadı:', e);
        setError('Ses dosyası çalınamadı. Lütfen tekrar deneyin.');
      });
    } catch (e) {
      console.log('Audio oluşturma hatası:', e);
      setError('Ses oynatma hatası oluştu.');
    }
  };

  const cleanupRecording = () => {
    if (mediaRecorder && mediaRecorder.stream) {
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    setMediaRecorder(null);
    setIsRecording(false);
  };

  const startRecording = async () => {
    if (isRecording) return; // Zaten kayıt yapılıyorsa çık
    
    try {
      setError(''); // Önceki hataları temizle
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // Düşük sample rate (Gemini için yeterli)
          channelCount: 1     // Mono kayıt (daha küçük dosya)
        } 
      });
      
      // Daha iyi sıkıştırma için codec seçimi
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
      }
      
      const recorder = new MediaRecorder(stream, {
        mimeType: mimeType,
        audioBitsPerSecond: 32000 // Düşük bitrate (daha küçük dosya)
      });
      
      setMediaRecorder(recorder);
      setAudioChunks([]);
      setIsRecording(true);
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioChunks(prev => [...prev, event.data]);
        }
      };
      
      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.onerror = (event) => {
        console.error('Kayıt hatası:', event.error);
        setError('Ses kaydı sırasında hata oluştu.');
        cleanupRecording();
      };
      
      recorder.start(1000); // Her 1 saniyede data toplama
    } catch (error) {
      console.error('Mikrofon erişim hatası:', error);
      setError('Mikrofon erişimi başarısız. Lütfen mikrofon izni verin ve tekrar deneyin.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  };

  // Mülakat fonksiyonları
  const fetchQuestion = async () => {
    if (loading) return; // Zaten loading varsa çık
    
    // API key kontrolü
    const apiKey = localStorage.getItem('geminiApiKey');
    if (!apiKey) {
      setError('AI özellikleri için Gemini API key gerekli. Lütfen çıkış yapıp tekrar giriş yaparken API key\'inizi girin.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_SIMULATION, {}, { 
        withCredentials: true,
        timeout: 30000 // 30 saniye timeout
      });
      setQuestion(res.data.question);
      setStep('interview');
    } catch (err) {
      console.error('Soru alma hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Soru alınamadı. Lütfen tekrar deneyin.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchSpeechQuestion = async () => {
    if (loading) return;
    
    setLoading(true);
    setError('');
    setIsSpeechMode(true); // Sesli soru alındığında otomatik olarak sesli moda geç
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_SPEECH_QUESTION, {
        voice_name: 'Kore'
      }, { 
        withCredentials: true,
        timeout: 45000 // Ses işleme daha uzun sürebilir
      });
      
      setQuestion(res.data.question);
      if (res.data.audio_url) {
        setAudioUrl(getAudioUrl(res.data.audio_url));
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(getAudioUrl(res.data.audio_url));
        }, 500);
      }
      setStep('interview');
    } catch (err) {
      console.error('Sesli soru alma hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Sesli soru alınamadı. Lütfen tekrar deneyin.';
      setError(errorMsg);
      setIsSpeechMode(false); // Hata durumunda sesli modu kapat
    } finally {
      setLoading(false);
    }
  };

  const fetchCvBasedQuestion = async () => {
    if (loading) return;
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_CV_QUESTION, {}, { 
        withCredentials: true,
        timeout: 30000
      });
      setQuestion(res.data.question);
      setStep('interview');
    } catch (err) {
      console.error('CV tabanlı soru alma hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'CV tabanlı soru alınamadı. Lütfen tekrar deneyin.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchCvBasedSpeechQuestion = async () => {
    if (loading) return;
    
    setLoading(true);
    setError('');
    setIsSpeechMode(true); // CV tabanlı sesli soru alındığında otomatik olarak sesli moda geç
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_CV_SPEECH_QUESTION, {
        voice_name: 'Kore'
      }, { 
        withCredentials: true,
        timeout: 45000
      });
      
      setQuestion(res.data.question);
      if (res.data.audio_url) {
        setAudioUrl(getAudioUrl(res.data.audio_url));
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(getAudioUrl(res.data.audio_url));
        }, 500);
      }
      setStep('interview');
    } catch (err) {
      console.error('CV tabanlı sesli soru alma hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'CV tabanlı sesli soru alınamadı. Lütfen tekrar deneyin.';
      setError(errorMsg);
      setIsSpeechMode(false);
    } finally {
      setLoading(false);
    }
  };

  const handleCvUpload = async () => {
    if (!cvFile) {
      setError('Lütfen bir CV dosyası seçin.');
      return;
    }
    
    // Dosya boyutu kontrolü (10MB limit)
    if (cvFile.size > 10 * 1024 * 1024) {
      setError('Dosya boyutu 10MB\'dan büyük olamaz.');
      return;
    }
    
    // Dosya tipi kontrolü
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(cvFile.type)) {
      setError('Sadece PDF, DOC ve DOCX dosyaları desteklenir.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    
    try {
      const res = await axios.post(API_ENDPOINTS.UPLOAD_CV, formData, {
        withCredentials: true,
        timeout: 60000, // CV analizi uzun sürebilir
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setCvAnalysis(res.data.analysis);
      setStep('cv-uploaded');
    } catch (err) {
      console.error('CV yükleme hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'CV yükleme başarısız. Lütfen tekrar deneyin.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const fetchPersonalizedQuestions = async () => {
    if (loading) return;
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_PERSONALIZED, {
        difficulty: difficulty
      }, { 
        withCredentials: true,
        timeout: 45000
      });
      setPersonalizedQuestions(res.data.questions);
      setStep('personalized-questions');
    } catch (err) {
      console.error('Kişiselleştirilmiş sorular alma hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Kişiselleştirilmiş sorular alınamadı. Lütfen tekrar deneyin.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (loading) return;
    if (!answer.trim()) {
      setError('Lütfen cevabınızı yazın.');
      return;
    }
    
    // API key kontrolü
    const apiKey = localStorage.getItem('geminiApiKey');
    if (!apiKey) {
      setError('AI özellikleri için Gemini API key gerekli. Lütfen çıkış yapıp tekrar giriş yaparken API key\'inizi girin.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(API_ENDPOINTS.INTERVIEW_EVALUATE, {
        question: question,
        answer: answer.trim() // Backend'de 'answer' olarak bekliyor
      }, { 
        withCredentials: true,
        timeout: 45000
      });
      setResult(res.data);
      setStep('result');
    } catch (err) {
      console.error('Cevap değerlendirme hatası:', err);
      const errorMsg = err.response?.data?.error || err.message || 'Değerlendirme başarısız. Lütfen tekrar deneyin.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const submitSpeechAnswer = async () => {
    if (loading) return;
    
    if (!audioChunks.length && !answer.trim()) {
      setError('Lütfen ses kaydı yapın veya metin cevap yazın.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Eğer ses kaydı varsa, ses dosyasını backend'e gönder
      if (audioChunks.length > 0) {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm;codecs=opus' });
        
        // Dosya boyutu kontrolü
        const fileSizeMB = audioBlob.size / (1024 * 1024);
        console.log(`Ses dosyası boyutu: ${fileSizeMB.toFixed(2)} MB`);
        
        if (fileSizeMB > 25) { // 25MB limit
          setError(`Ses dosyası çok büyük (${fileSizeMB.toFixed(1)}MB). Lütfen daha kısa kayıt yapın.`);
          return;
        }
        
        const audioUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(audioUrl);
        
        // Ses dosyasını FormData ile backend'e gönder
        const formData = new FormData();
        formData.append('audio', audioBlob, 'answer.webm');
        formData.append('question', question);
        formData.append('voice_name', 'Enceladus');
        
        // Eğer ek metin varsa onu da ekle
        if (answer.trim()) {
          formData.append('additional_text', answer.trim());
        }

        console.log('Ses dosyası gönderiliyor, lütfen bekleyin...');
        
        const res = await axios.post(API_ENDPOINTS.INTERVIEW_SPEECH_EVALUATION, formData, {
          withCredentials: true,
          timeout: 120000, // 2 dakika timeout (ses işleme uzun sürebilir)
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            console.log(`Upload progress: ${percentCompleted}%`);
          }
        });
        
        setResult(res.data);
        if (res.data.audio_url) {
          // Geri bildirim sesini otomatik çal
          setTimeout(() => {
            playAudio(getAudioUrl(res.data.audio_url));
          }, 500);
        }
        setStep('result');
      } else {
        // Sadece metin cevap varsa
        const res = await axios.post(API_ENDPOINTS.INTERVIEW_SPEECH_EVALUATION, {
          question: question,
          user_answer: answer.trim(),
          voice_name: 'Enceladus'
        }, { 
          withCredentials: true,
          timeout: 60000 // Metin işleme daha hızlı
        });
        
        setResult(res.data);
        if (res.data.audio_url) {
          setTimeout(() => {
            playAudio(getAudioUrl(res.data.audio_url));
          }, 500);
        }
        setStep('result');
      }
    } catch (err) {
      console.error('Sesli cevap değerlendirme hatası:', err);
      
      if (err.code === 'ECONNABORTED') {
        setError('İşlem çok uzun sürdü. Lütfen daha kısa ses kaydı yapın veya internet bağlantınızı kontrol edin.');
      } else {
        const errorMsg = err.response?.data?.error || err.message || 'Değerlendirme başarısız. Lütfen tekrar deneyin.';
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
      // Cleanup ses kaydı
      cleanupRecording();
    }
  };

  if (step === 'start') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 400, maxWidth: 600, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            Mülakat Simülasyonu
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Mülakat türünüzü seçin ve hazırlanın!
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Card sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                <CardContent>
                  <Typography variant="h6" color="white" mb={1}>🎯 Genel Mülakat</Typography>
                  <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={2}>
                    İlgi alanınıza göre genel teknik sorular
                  </Typography>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Button 
                        variant="contained" 
                        color="primary" 
                        fullWidth
                        startIcon={<Keyboard />}
                        onClick={fetchQuestion} 
                        disabled={loading}
                        endIcon={loading && <CircularProgress size={20} color="inherit" />}
                        size="small"
                      >
                        Metin
                      </Button>
                    </Grid>
                    <Grid item xs={6}>
                      <Button 
                        variant="contained" 
                        color="secondary" 
                        fullWidth
                        startIcon={<RecordVoiceOver />}
                        onClick={fetchSpeechQuestion} 
                        disabled={loading}
                        endIcon={loading && <CircularProgress size={20} color="inherit" />}
                        size="small"
                      >
                        Sesli
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12}>
              <Card sx={{ backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                <CardContent>
                  <Typography variant="h6" color="white" mb={1}>📄 CV Tabanlı Mülakat</Typography>
                  <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={2}>
                    CV'nize özel kişiselleştirilmiş sorular
                  </Typography>
                  <Button 
                    variant="outlined" 
                    fullWidth
                    onClick={() => setStep('cv-upload')}
                    sx={{ 
                      color: 'white', 
                      borderColor: 'rgba(255,255,255,0.3)',
                      '&:hover': { borderColor: 'white' }
                    }}
                  >
                    CV Yükle ve Başla
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    );
  }

  if (step === 'cv-upload') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 400, maxWidth: 600, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            CV Yükle
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            CV'nizi yükleyin ve size özel sorular alın
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Box sx={{ mb: 3 }}>
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => setCvFile(e.target.files[0])}
              style={{ display: 'none' }}
              id="cv-upload"
            />
            <label htmlFor="cv-upload">
              <Button
                variant="outlined"
                component="span"
                fullWidth
                sx={{ 
                  color: 'white', 
                  borderColor: 'rgba(255,255,255,0.3)',
                  py: 2,
                  '&:hover': { borderColor: 'white' }
                }}
              >
                {cvFile ? cvFile.name : 'CV Dosyası Seç (PDF, DOC, DOCX)'}
              </Button>
            </label>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button 
                variant="outlined" 
                fullWidth
                onClick={() => setStep('start')}
                sx={{ 
                  color: 'rgba(255,255,255,0.7)', 
                  borderColor: 'rgba(255,255,255,0.3)',
                  '&:hover': { borderColor: 'rgba(255,255,255,0.7)' }
                }}
              >
                Geri
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button 
                variant="contained" 
                color="primary" 
                fullWidth
                onClick={handleCvUpload} 
                disabled={loading || !cvFile}
                endIcon={loading && <CircularProgress size={20} color="inherit" />}
              >
                CV Yükle
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    );
  }

  if (step === 'cv-uploaded') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 400, maxWidth: 700, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            CV Analizi Tamamlandı! 🎉
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Mülakat türünüzü seçin
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          {cvAnalysis && (
            <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
              <CardContent>
                <Typography variant="h6" color="white" mb={1}>📊 CV Analizi</Typography>
                <Typography variant="body2" color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap', maxHeight: 200, overflow: 'auto' }}>
                  {cvAnalysis}
                </Typography>
              </CardContent>
            </Card>
          )}
          
          <Tabs 
            value={tabValue} 
            onChange={(e, newValue) => setTabValue(newValue)}
            sx={{ 
              mb: 3,
              '& .MuiTab-root': { color: 'rgba(255,255,255,0.7)' },
              '& .Mui-selected': { color: 'white !important' },
              '& .MuiTabs-indicator': { backgroundColor: 'white' }
            }}
          >
            <Tab label="Tek Soru" />
            <Tab label="Kişiselleştirilmiş Sorular" />
          </Tabs>
          
          {tabValue === 0 && (
            <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
              <CardContent>
                <Typography variant="h6" color="white" mb={1}>🎯 CV Tabanlı Tek Soru</Typography>
                <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={2}>
                  CV'nize özel hazırlanmış tek bir mülakat sorusu
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Button 
                      variant="contained" 
                      color="primary" 
                      fullWidth
                      startIcon={<Keyboard />}
                      onClick={fetchCvBasedQuestion} 
                      disabled={loading}
                      endIcon={loading && <CircularProgress size={20} color="inherit" />}
                      size="small"
                    >
                      Metin
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button 
                      variant="contained" 
                      color="secondary" 
                      fullWidth
                      startIcon={<RecordVoiceOver />}
                      onClick={fetchCvBasedSpeechQuestion} 
                      disabled={loading}
                      endIcon={loading && <CircularProgress size={20} color="inherit" />}
                      size="small"
                    >
                      Sesli
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
          
          {tabValue === 1 && (
            <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
              <CardContent>
                <Typography variant="h6" color="white" mb={1}>📋 Kişiselleştirilmiş Sorular</Typography>
                <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={2}>
                  CV'nize göre 5 adet kişiselleştirilmiş soru
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="white" mb={1}>Zorluk Seviyesi:</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    {['kolay', 'orta', 'zor'].map((level) => (
                      <Chip
                        key={level}
                        label={level.charAt(0).toUpperCase() + level.slice(1)}
                        clickable
                        color={difficulty === level ? 'primary' : 'default'}
                        onClick={() => setDifficulty(level)}
                        sx={{ 
                          color: difficulty === level ? 'white' : 'rgba(255,255,255,0.7)',
                          backgroundColor: difficulty === level ? 'primary.main' : 'rgba(255,255,255,0.1)'
                        }}
                      />
                    ))}
                  </Box>
                </Box>
                
                <Button 
                  variant="contained" 
                  color="primary" 
                  fullWidth
                  onClick={fetchPersonalizedQuestions} 
                  disabled={loading}
                  endIcon={loading && <CircularProgress size={20} color="inherit" />}
                >
                  Kişiselleştirilmiş Sorular Al
                </Button>
              </CardContent>
            </Card>
          )}
          
          <Button 
            variant="outlined" 
            fullWidth
            onClick={() => setStep('start')}
            sx={{ 
              color: 'rgba(255,255,255,0.7)', 
              borderColor: 'rgba(255,255,255,0.3)',
              '&:hover': { borderColor: 'rgba(255,255,255,0.7)' }
            }}
          >
            Ana Sayfaya Dön
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'personalized-questions') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, maxWidth: 800, mx: 'auto', borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            Kişiselleştirilmiş Sorular
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            CV'nize özel {difficulty} seviye sorular
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Box sx={{ mb: 3, whiteSpace: 'pre-wrap', color: 'rgba(255,255,255,0.9)', lineHeight: 1.6 }}>
            {personalizedQuestions}
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              variant="outlined" 
              onClick={() => setStep('cv-uploaded')}
              sx={{ 
                color: 'rgba(255,255,255,0.7)', 
                borderColor: 'rgba(255,255,255,0.3)',
                '&:hover': { borderColor: 'rgba(255,255,255,0.7)' }
              }}
            >
              Geri
            </Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={fetchCvBasedQuestion}
              disabled={loading}
              endIcon={loading && <CircularProgress size={20} color="inherit" />}
            >
              Tek Soru ile Başla
            </Button>
          </Box>
        </Paper>
      </Box>
    );
  }

  if (step === 'interview') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 6 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, maxWidth: 800, mx: 'auto', borderRadius: 4 }}
        >
          <Typography variant="h5" fontWeight={700} mb={3} color="white">Mülakat Sorusu</Typography>
          
          {/* Sesli mülakat modunu değiştirme */}
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={isSpeechMode}
                  onChange={(e) => setIsSpeechMode(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography color="white">
                  {isSpeechMode ? 'Sesli Mülakat' : 'Metin Mülakat'}
                </Typography>
              }
            />
            
            {audioUrl && (
              <IconButton 
                onClick={() => playAudio(audioUrl)}
                sx={{ color: 'white' }}
                title="Soruyu Tekrar Dinle"
              >
                <VolumeUp />
              </IconButton>
            )}
          </Box>
          
          <Typography fontWeight={600} mb={2} color="white">Soru:</Typography>
          <Typography mb={3} color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>{question}</Typography>
          
          {isSpeechMode ? (
            <Box>
              <Typography fontWeight={600} mb={2} color="white">Sesli Cevap:</Typography>
              
              {/* Ses kayıt kontrolleri */}
              <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
                <IconButton
                  onClick={isRecording ? stopRecording : startRecording}
                  sx={{ 
                    color: isRecording ? 'error.main' : 'primary.main',
                    backgroundColor: 'rgba(255,255,255,0.1)',
                    '&:hover': { backgroundColor: 'rgba(255,255,255,0.2)' }
                  }}
                  size="large"
                >
                  {isRecording ? <MicOff /> : <Mic />}
                </IconButton>
                
                <Typography color="white">
                  {isRecording ? 'Kayıt durduruluyor...' : audioChunks.length > 0 ? 'Kayıt tamamlandı' : 'Kayıt başlatmak için tıklayın'}
                </Typography>
                
                {recordedAudio && (
                  <IconButton onClick={() => playAudio(recordedAudio)} sx={{ color: 'white' }}>
                    <PlayArrow />
                  </IconButton>
                )}
              </Box>
              
              {/* Yedek metin girişi */}
              <Typography variant="body2" mb={1} color="rgba(255,255,255,0.7)">
                İsteğe bağlı: Metinle destekle
              </Typography>
              <TextField
                multiline
                rows={3}
                fullWidth
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Ek açıklamalar (isteğe bağlı)..."
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    color: 'white',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                    '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.5)', opacity: 1 },
                  },
                }}
              />
            </Box>
          ) : (
            <Box>
              <Typography fontWeight={600} mb={2} color="white">Cevabını Yaz:</Typography>
              <TextField
                multiline
                rows={6}
                fullWidth
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Cevabını buraya yaz..."
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    color: 'white',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                    '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.5)', opacity: 1 },
                  },
                }}
              />
            </Box>
          )}
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={isSpeechMode ? submitSpeechAnswer : handleSubmit} 
            disabled={loading || (!answer.trim() && (!isSpeechMode || audioChunks.length === 0))} 
            endIcon={loading && <CircularProgress size={20} color="inherit" />}
            startIcon={isSpeechMode ? <Send /> : <Keyboard />}
            sx={{
              background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
              borderRadius: '25px',
              py: 1.5,
              textTransform: 'none',
              fontWeight: 600,
              boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
              '&:hover': {
                background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
              },
              '&:disabled': {
                background: 'rgba(255,255,255,0.1)',
                color: 'rgba(255,255,255,0.5)',
                boxShadow: 'none'
              }
            }}
          >
            {loading ? (
              isSpeechMode && audioChunks.length > 0 
                ? 'Ses işleniyor... (2 dakika sürebilir)' 
                : 'Değerlendiriliyor...'
            ) : (
              isSpeechMode ? 'Sesli Cevabı Gönder' : 'Cevabı Gönder'
            )}
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'result') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 340, maxWidth: 600, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            Değerlendirme
          </Typography>
          
          {result && (
            <>
              {result.audio_url && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                  <IconButton 
                    onClick={() => playAudio(getAudioUrl(result.audio_url))}
                    sx={{ 
                      color: 'primary.main',
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      '&:hover': { backgroundColor: 'rgba(255,255,255,0.2)' }
                    }}
                    size="large"
                    title="Sesli Geri Bildirimi Dinle"
                  >
                    <VolumeUp />
                  </IconButton>
                </Box>
              )}
              
              <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.evaluation}
              </Typography>
              
              {result.has_cv_context && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  Bu değerlendirme CV'niz bağlamında yapılmıştır.
                </Alert>
              )}
              
              {result.has_audio && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Sesli geri bildirim mevcut! 🎧
                </Alert>
              )}
            </>
          )}
          
          <Button 
            variant="outlined" 
            color="primary" 
            fullWidth 
            onClick={() => { 
              // Tüm state'leri temizle
              setStep('start'); 
              setAnswer(''); 
              setQuestion('');
              setResult(null); 
              setCvAnalysis(null); 
              setCvFile(null); 
              setPersonalizedQuestions([]);
              setTabValue(0);
              setDifficulty('orta');
              setAudioUrl(null);
              setAudioChunks([]);
              setRecordedAudio(null);
              setIsSpeechMode(false);
              setError('');
              setLoading(false);
              // Ses kaydını temizle
              cleanupRecording();
            }}
            sx={{
              mt: 2,
              borderColor: 'rgba(255,255,255,0.3)',
              color: 'white',
              '&:hover': {
                borderColor: 'rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            Yeni Mülakat
          </Button>
        </Paper>
      </Box>
    );
  }
}
