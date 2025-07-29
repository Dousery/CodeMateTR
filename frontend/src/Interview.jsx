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

  // Ses fonksiyonları
  const playAudio = (url) => {
    const audio = new Audio(url);
    audio.play().catch(e => console.log('Ses çalınamadı:', e));
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      setMediaRecorder(recorder);
      setAudioChunks([]);
      setIsRecording(true);
      
      recorder.ondataavailable = (event) => {
        setAudioChunks(prev => [...prev, event.data]);
      };
      
      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start();
    } catch {
      setError('Mikrofon erişimi başarısız. Lütfen mikrofon izni verin.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    }
  };

  // Mülakat fonksiyonları
  const fetchQuestion = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/interview_simulation', {}, { withCredentials: true });
      setQuestion(res.data.question);
      setStep('interview');
    } catch (err) {
      setError(err.response?.data?.error || 'Soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSpeechQuestion = async () => {
    setLoading(true);
    setError('');
    setIsSpeechMode(true); // Sesli soru alındığında otomatik olarak sesli moda geç
    try {
      const res = await axios.post('http://localhost:5000/interview_speech_question', {
        voice_name: 'Kore'
      }, { withCredentials: true });
      
      setQuestion(res.data.question);
      if (res.data.audio_url) {
        setAudioUrl(`http://localhost:5000${res.data.audio_url}`);
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(`http://localhost:5000${res.data.audio_url}`);
        }, 500);
      }
      setStep('interview');
    } catch (err) {
      setError(err.response?.data?.error || 'Sesli soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCvBasedQuestion = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/interview_cv_based_question', {}, { withCredentials: true });
      setQuestion(res.data.question);
      setStep('interview');
    } catch (err) {
      setError(err.response?.data?.error || 'CV tabanlı soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCvBasedSpeechQuestion = async () => {
    setLoading(true);
    setError('');
    setIsSpeechMode(true); // CV tabanlı sesli soru alındığında otomatik olarak sesli moda geç
    try {
      const res = await axios.post('http://localhost:5000/interview_cv_speech_question', {
        voice_name: 'Kore'
      }, { withCredentials: true });
      
      setQuestion(res.data.question);
      if (res.data.audio_url) {
        setAudioUrl(`http://localhost:5000${res.data.audio_url}`);
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(`http://localhost:5000${res.data.audio_url}`);
        }, 500);
      }
      setStep('interview');
    } catch (err) {
      setError(err.response?.data?.error || 'CV tabanlı sesli soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleCvUpload = async () => {
    if (!cvFile) {
      setError('Lütfen bir CV dosyası seçin.');
      return;
    }
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    
    try {
      const res = await axios.post('http://localhost:5000/upload_cv', formData, {
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setCvAnalysis(res.data.analysis);
      setStep('cv-uploaded');
    } catch (err) {
      setError(err.response?.data?.error || 'CV yükleme başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const fetchPersonalizedQuestions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/interview_personalized_questions', {
        difficulty: difficulty
      }, { withCredentials: true });
      setPersonalizedQuestions(res.data.questions);
      setStep('personalized-questions');
    } catch (err) {
      setError(err.response?.data?.error || 'Kişiselleştirilmiş sorular alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/interview_simulation/evaluate', {
        question: question,
        answer: answer
      }, { withCredentials: true });
      setResult(res.data);
      setStep('result');
    } catch (err) {
      setError(err.response?.data?.error || 'Değerlendirme başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const submitSpeechAnswer = async () => {
    if (!audioChunks.length && !answer.trim()) {
      setError('Lütfen ses kaydı yapın veya metin cevap yazın.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      let finalAnswer = answer;
      
      // Eğer ses kaydı varsa, ses dosyasını backend'e gönder
      if (audioChunks.length > 0) {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio(audioUrl);
        
        // Ses dosyasını FormData ile backend'e gönder
        const formData = new FormData();
        formData.append('audio', audioBlob, 'answer.webm');
        formData.append('question', question);
        formData.append('voice_name', 'Enceladus');
        
        // Eğer ek metin varsa onu da ekle
        if (answer.trim()) {
          formData.append('additional_text', answer);
        }

        const res = await axios.post('http://localhost:5000/interview_speech_evaluation', formData, {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        setResult(res.data);
        if (res.data.audio_url) {
          // Geri bildirim sesini otomatik çal
          setTimeout(() => {
            playAudio(`http://localhost:5000${res.data.audio_url}`);
          }, 500);
        }
        setStep('result');
      } else {
        // Sadece metin cevap varsa
        const res = await axios.post('http://localhost:5000/interview_speech_evaluation', {
          question: question,
          user_answer: finalAnswer,
          voice_name: 'Enceladus'
        }, { withCredentials: true });
        
        setResult(res.data);
        if (res.data.audio_url) {
          setTimeout(() => {
            playAudio(`http://localhost:5000${res.data.audio_url}`);
          }, 500);
        }
        setStep('result');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Değerlendirme başarısız.');
    } finally {
      setLoading(false);
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
            disabled={loading || (!answer.trim() && audioChunks.length === 0)} 
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
              }
            }}
          >
            {isSpeechMode ? 'Sesli Cevabı Gönder' : 'Cevabı Gönder'}
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
                    onClick={() => playAudio(`http://localhost:5000${result.audio_url}`)}
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
              setStep('start'); 
              setAnswer(''); 
              setResult(null); 
              setCvAnalysis(null); 
              setCvFile(null); 
              setPersonalizedQuestions([]);
              setTabValue(0);
              setAudioUrl(null);
              setAudioChunks([]);
              setRecordedAudio(null);
              setIsSpeechMode(false);
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
