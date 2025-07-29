import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Button, TextField, CircularProgress, Alert, 
  Card, CardContent, Chip, Grid, IconButton, LinearProgress, Dialog,
  DialogTitle, DialogContent, DialogActions, Divider
} from '@mui/material';
import { 
  Mic, MicOff, PlayArrow, VolumeUp, Send, Keyboard, RecordVoiceOver,
  CheckCircle, Timer, Person, Psychology, Warning, Refresh
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function AutoInterview() {
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [userAnswer, setUserAnswer] = useState('');
  const [step, setStep] = useState('starting'); // starting, session_choice, interviewing, completed
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [audioUrl, setAudioUrl] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [finalEvaluation, setFinalEvaluation] = useState('');
  const [sessionInfo, setSessionInfo] = useState(null);
  const [showFinalDialog, setShowFinalDialog] = useState(false);

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

  // Otomatik mülakat başlatma
  const startAutoInterview = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/auto_interview/start', {}, { 
        withCredentials: true 
      });
      
      setSessionId(res.data.session_id);
      setCurrentQuestion(res.data.question);
      setQuestionIndex(res.data.question_index);
      setTotalQuestions(res.data.total_questions);
      
      if (res.data.audio_url) {
        setAudioUrl(`http://localhost:5000${res.data.audio_url}`);
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(`http://localhost:5000${res.data.audio_url}`);
        }, 500);
      }
      
      setStep('interviewing');
    } catch (err) {
      setError(err.response?.data?.error || 'Otomatik mülakat başlatılamadı.');
      setStep('starting');
    } finally {
      setLoading(false);
    }
  };

  // Cevap gönderme
  const submitAnswer = async () => {
    if (!userAnswer.trim()) {
      setError('Lütfen bir cevap yazın.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/auto_interview/submit_answer', {
        session_id: sessionId,
        answer: userAnswer,
        voice_name: 'Kore'
      }, { withCredentials: true });
      
      setCurrentQuestion(res.data.question);
      setQuestionIndex(res.data.question_index);
      setTotalQuestions(res.data.total_questions);
      setUserAnswer('');
      
      if (res.data.audio_url) {
        setAudioUrl(`http://localhost:5000${res.data.audio_url}`);
        // Ses otomatik çalsın
        setTimeout(() => {
          playAudio(`http://localhost:5000${res.data.audio_url}`);
        }, 500);
      }
      
    } catch (err) {
      setError(err.response?.data?.error || 'Cevap gönderilemedi.');
    } finally {
      setLoading(false);
    }
  };

  // Mülakatı tamamlama
  const completeInterview = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/auto_interview/complete', {
        session_id: sessionId
      }, { withCredentials: true });
      
      setFinalEvaluation(res.data.final_evaluation);
      setSessionInfo({
        total_questions: res.data.total_questions,
        total_answers: res.data.total_answers,
        session_duration: res.data.session_duration
      });
      setStep('completed');
      setShowFinalDialog(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Mülakat tamamlanamadı.');
    } finally {
      setLoading(false);
    }
  };

  // Aktif oturum kontrolü - basitleştirilmiş
  const checkActiveSession = async () => {
    try {
      const res = await axios.get('http://localhost:5000/auto_interview/status', { 
        withCredentials: true 
      });
      
      if (res.data.has_active_session) {
        // Aktif session varsa kullanıcıya seçenek sun
        setStep('session_choice');
      } else {
        setStep('starting');
      }
    } catch (err) {
      // Hata durumunda direkt starting adımına geç
      setStep('starting');
    }
  };



  // Sesli cevap gönderme
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
      const res = await axios.post('http://localhost:5000/auto_interview/submit_answer', formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setCurrentQuestion(res.data.question);
      setQuestionIndex(res.data.question_index);
      setTotalQuestions(res.data.total_questions);
      setUserAnswer('');
      
      if (res.data.audio_url) {
        setAudioUrl(`http://localhost:5000${res.data.audio_url}`);
        setTimeout(() => {
          playAudio(`http://localhost:5000${res.data.audio_url}`);
        }, 500);
      }
      
    } catch (err) {
      setError(err.response?.data?.error || 'Sesli cevap gönderilemedi.');
    } finally {
      setLoading(false);
    }
  };

  // Ses kaydı tamamlandığında
  useEffect(() => {
    if (audioChunks.length > 0 && !isRecording) {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      setRecordedAudio(audioBlob);
    }
  }, [audioChunks, isRecording]);



  if (step === 'starting') {
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
            Otomatik Mülakat Sistemi
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Yapay zeka destekli otomatik mülakat sistemi ile kendinizi test edin. 
            Sistem, cevaplarınıza göre dinamik olarak sorular üretecek.
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={startAutoInterview} 
            disabled={loading} 
            endIcon={loading && <CircularProgress size={20} color="inherit" />}
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
            {loading ? 'Başlatılıyor...' : 'Mülakatı Başlat'}
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'session_choice') {
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
            Aktif Mülakat Bulundu
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Sistemde aktif bir mülakat oturumu bulunuyor. Ne yapmak istiyorsunuz?
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Box display="flex" gap={2} justifyContent="center">
            <Button
              variant="contained"
              color="primary"
              onClick={startAutoInterview}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <Refresh />}
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
              {loading ? 'Başlatılıyor...' : 'Yeni Mülakat Başlat'}
            </Button>
            
            <Button
              variant="outlined"
              color="secondary"
              onClick={() => setStep('starting')}
              disabled={loading}
              sx={{
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'rgba(255,255,255,0.7)',
                borderRadius: '25px',
                py: 1.5,
                textTransform: 'none',
                fontWeight: 600,
                '&:hover': {
                  borderColor: 'rgba(255,255,255,0.5)',
                  background: 'rgba(255,255,255,0.1)',
                }
              }}
            >
              Geri Dön
            </Button>
          </Box>
        </Paper>
      </Box>
    );
  }

  if (step === 'interviewing') {
    return (
      <Box 
        width="100%"
        maxWidth="1200px" 
        mx="auto" 
        p={3} 
        minHeight="calc(100vh - 140px)"
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        mt={6}
        gap={3}
        sx={{ marginLeft: 'auto', marginRight: '500px' }}
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}
        >
          {/* Progress Bar */}
          <Paper elevation={2} sx={{ p: 2, mb: 3, width: '100%', maxWidth: '1000px' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2" color="text.secondary">
                Mülakat İlerlemesi
              </Typography>
              <Chip 
                icon={<Timer />} 
                label={`${Math.round((questionIndex / 10) * 100)}%`} 
                color="primary" 
              />
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={(questionIndex / 10) * 100} 
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Paper>

          {/* Current Question */}
          <Paper elevation={3} sx={{ p: 4, mb: 3, width: '100%', maxWidth: '1000px' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Person sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" color="primary">
                Mülakat Sorusu
              </Typography>
            </Box>
            
            <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.6 }}>
              {currentQuestion}
            </Typography>
            
            {audioUrl && (
              <Box mt={2}>
                <Button
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={() => playAudio(audioUrl)}
                >
                  Soruyu Dinle
                </Button>
              </Box>
            )}
          </Paper>

          {/* Answer Input */}
          <Paper elevation={3} sx={{ p: 4, mb: 3, width: '100%', maxWidth: '1000px' }}>
            <Typography variant="h6" gutterBottom>
              Cevabınız
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  variant="outlined"
                  placeholder="Cevabınızı buraya yazın..."
                  value={userAnswer}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  disabled={loading}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Box display="flex" flexDirection="column" gap={2}>
                  <Button
                    variant="contained"
                    onClick={submitAnswer}
                    disabled={loading || !userAnswer.trim()}
                    startIcon={loading ? <CircularProgress size={20} /> : <Send />}
                    fullWidth
                  >
                    {loading ? 'Gönderiliyor...' : 'Cevabı Gönder'}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={isRecording ? stopRecording : startRecording}
                    startIcon={isRecording ? <MicOff /> : <Mic />}
                    color={isRecording ? 'error' : 'primary'}
                    fullWidth
                  >
                    {isRecording ? 'Kaydı Durdur' : 'Sesli Cevap'}
                  </Button>
                  

                  
                  {recordedAudio && (
                    <Button
                      variant="outlined"
                      onClick={submitVoiceAnswer}
                      disabled={loading}
                      startIcon={<VolumeUp />}
                      fullWidth
                      sx={{ bgcolor: 'success.light', color: 'white' }}
                    >
                      Sesli Cevabı Gönder
                    </Button>
                  )}
                  

                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Complete Interview Button */}
          <Box display="flex" justifyContent="center" mt={3}>
            <Button
              variant="outlined"
              color="secondary"
              onClick={completeInterview}
              disabled={loading}
              startIcon={<CheckCircle />}
            >
              Mülakatı Tamamla
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </motion.div>
      </Box>
    );
  }

  if (step === 'completed') {
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
            Mülakat Tamamlandı!
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Otomatik mülakatınız başarıyla tamamlandı. Sonuçlarınızı görüntüleyebilirsiniz.
          </Typography>
          
          <Button
            variant="contained"
            onClick={() => setShowFinalDialog(true)}
            startIcon={<Psychology />}
            fullWidth
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
            Sonuçları Görüntüle
          </Button>
        </Paper>

        {/* Final Evaluation Dialog */}
        <Dialog 
          open={showFinalDialog} 
          onClose={() => setShowFinalDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Typography variant="h5">Mülakat Sonuçları</Typography>
          </DialogTitle>
          <DialogContent>
            <Box mb={3}>
              <Typography variant="h6" gutterBottom color="primary">
                Genel Değerlendirme
              </Typography>
              <Typography variant="body1" paragraph sx={{ whiteSpace: 'pre-line' }}>
                {finalEvaluation}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary">
                      Toplam Soru
                    </Typography>
                    <Typography variant="h4">
                      {sessionInfo?.total_questions || 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary">
                      Süre (Dakika)
                    </Typography>
                    <Typography variant="h4">
                      {sessionInfo ? Math.round(sessionInfo.session_duration / 60) : 0}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowFinalDialog(false)}>
              Kapat
            </Button>
            <Button 
              variant="contained" 
              onClick={() => {
                setShowFinalDialog(false);
                setStep('starting');
                setSessionId(null);
                setCurrentQuestion('');
                setUserAnswer('');
                setQuestionIndex(0);
                setTotalQuestions(0);
                setFinalEvaluation('');
                setSessionInfo(null);
              }}
            >
              Yeni Mülakat Başlat
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    );
  }

  return null;
} 