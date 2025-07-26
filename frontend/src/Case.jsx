import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Paper, Button, TextField, CircularProgress, Alert, Chip, Avatar, Stack, IconButton, Divider } from '@mui/material';
import { Mic, MicOff, Send, VolumeUp } from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function Case() {
  const [caseStudy, setCaseStudy] = useState('');
  const [solution, setSolution] = useState('');
  const [step, setStep] = useState('start'); // start, waiting, case, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [partner, setPartner] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30 * 60); // 30 dakika
  const [partnerSolution, setPartnerSolution] = useState('');
  const [isPartnerSubmitted, setIsPartnerSubmitted] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioText, setAudioText] = useState('');
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  
  const intervalRef = useRef(null);
  const checkMatchIntervalRef = useRef(null);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  // Kullanıcı bilgisini al
  useEffect(() => {
    const getUserInfo = async () => {
      try {
        const res = await axios.get('http://localhost:5000/profile', { withCredentials: true });
        setCurrentUser(res.data.username);
      } catch (err) {
        console.error('Kullanıcı bilgisi alınamadı:', err);
      }
    };
    getUserInfo();
  }, []);

  // Timer efekti
  useEffect(() => {
    if (step === 'case' && timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            // Süre bitti, otomatik submit
            handleSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [step, timeLeft]);

  // Eşleşme kontrolü
  useEffect(() => {
    if (step === 'waiting') {
      checkMatchIntervalRef.current = setInterval(checkMatch, 2000);
    }

    return () => {
      if (checkMatchIntervalRef.current) clearInterval(checkMatchIntervalRef.current);
    };
  }, [step]);

  // Mesajları otomatik scroll - KALDIRILDI (kullanıcı kendisi scroll yapacak)
  // useEffect(() => {
  //   messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  // }, [messages]);

  // Speech recognition setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'tr-TR';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Ses tanıma sonucu:', transcript);
        setAudioText(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        alert(`Ses tanıma hatası: ${event.error}`);
      };

      recognitionRef.current.onend = () => {
        console.log('Ses tanıma sonlandı');
        setIsListening(false);
      };

      recognitionRef.current.onstart = () => {
        console.log('Ses tanıma başladı');
        setIsListening(true);
      };
    } else {
      console.error('Web Speech API desteklenmiyor');
      alert('Tarayıcınız ses tanıma özelliğini desteklemiyor. Chrome kullanmayı deneyin.');
    }
  }, []);

  // Mesajları periyodik olarak güncelle
  useEffect(() => {
    if (step === 'case' && sessionId) {
      const fetchMessages = async () => {
        try {
          const res = await axios.get(`http://localhost:5000/case_study_room/get_messages?session_id=${sessionId}`, { withCredentials: true });
          console.log('Gelen mesajlar:', res.data.messages);
          setMessages(res.data.messages);
        } catch (err) {
          console.error('Mesaj getirme hatası:', err);
        }
      };

      fetchMessages();
      const messageInterval = setInterval(fetchMessages, 3000);
      return () => clearInterval(messageInterval);
    }
  }, [step, sessionId]);

  const checkMatch = async () => {
    try {
      console.log('Eşleşme kontrolü yapılıyor...');
      const res = await axios.get('http://localhost:5000/case_study_room/check_match', { withCredentials: true });
      console.log('Check match response:', res.data);
      
      if (res.data.status === 'matched') {
        console.log('Eşleşme bulundu!');
        setSessionId(res.data.session_id);
        setCaseStudy(res.data.case);
        setPartner(res.data.partner);
        setStep('case');
        setTimeLeft(res.data.duration * 60);
      } else if (res.data.status === 'waiting') {
        console.log('Hala bekleniyor...');
      } else {
        console.log('Eşleşme bulunamadı:', res.data.status);
      }
    } catch (err) {
      console.error('Eşleşme kontrolü hatası:', err);
      console.error('Hata detayı:', err.response?.data);
    }
  };

  const fetchCaseStudy = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Case study başlatılıyor...');
      const res = await axios.post('http://localhost:5000/case_study_room', {}, { withCredentials: true });
      console.log('Backend response:', res.data);
      
      if (res.data.status === 'matched') {
        console.log('Eşleşme bulundu!', res.data);
        setSessionId(res.data.session_id);
        setCaseStudy(res.data.case);
        setPartner(res.data.partner);
      setStep('case');
        setTimeLeft(res.data.duration * 60);
      } else {
        console.log('Eşleşme bekleniyor...');
        setStep('waiting');
      }
    } catch (err) {
      console.error('Case study hatası:', err);
      setError(err.response?.data?.error || 'Case study alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (isSubmitted) return;
    
    setLoading(true);
    setError('');
    setIsSubmitted(true);
    
    try {
      console.log('Oturum tamamlanıyor...', { sessionId, currentUser, partner });
      
      // Session ID kontrolü
      if (!sessionId) {
        throw new Error('Session ID bulunamadı');
      }
      
      // Oturumu tamamla (mesajlaşma zaten çözüm olarak kabul edilecek)
      const response = await axios.post('http://localhost:5000/case_study_room/complete_session', {
        session_id: sessionId
      }, { withCredentials: true });
      
      console.log('Oturum tamamlandı, sonuçlar kontrol ediliyor...', response.data);
      
      // Partner'ın tamamlamasını kontrol et
      checkPartnerSolution();
      
    } catch (err) {
      console.error('Oturum tamamlama hatası:', err);
      console.error('Hata detayları:', {
        sessionId,
        currentUser,
        partner,
        error: err.response?.data,
        status: err.response?.status
      });
      setError(err.response?.data?.error || 'Oturum tamamlanamadı. Lütfen tekrar deneyin.');
      setIsSubmitted(false);
    } finally {
      setLoading(false);
    }
  };

  const checkPartnerSolution = async () => {
    try {
      console.log('Sonuçlar kontrol ediliyor...', { sessionId, currentUser });
      
      const res = await axios.get(`http://localhost:5000/case_study_room/get_result?session_id=${sessionId}`, { withCredentials: true });
      
      console.log('Sonuç yanıtı:', res.data);
      
      if (res.data.status === 'completed') {
        console.log('Sonuçlar bulundu, result sayfasına yönlendiriliyor...');
        
        // Kullanıcı atama düzeltmesi
        const resultData = {
          ...res.data,
          currentUser: currentUser, // Mevcut kullanıcıyı ekle
          userEvaluation: res.data.evaluation, // Mevcut kullanıcının değerlendirmesi
          partnerEvaluation: res.data.partner_evaluation, // Partner'ın değerlendirmesi
          partner: res.data.partner // Partner adı
        };
        
        console.log('Düzeltilmiş sonuç verisi:', resultData);
        setResult(resultData);
        setStep('result');
      } else {
        console.log('Sonuçlar henüz hazır değil, tekrar kontrol ediliyor...', res.data.status);
        // Hemen tekrar kontrol et (polling yerine)
        setTimeout(checkPartnerSolution, 1000);
      }
    } catch (err) {
      console.error('Sonuç kontrolü hatası:', err);
      console.error('Sonuç kontrolü hata detayları:', {
        sessionId,
        currentUser,
        error: err.response?.data,
        status: err.response?.status
      });
      // Hata durumunda da tekrar dene
      setTimeout(checkPartnerSolution, 2000);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    
    try {
      await axios.post('http://localhost:5000/case_study_room/send_message', {
        session_id: sessionId,
        message: newMessage
      }, { withCredentials: true });
      setNewMessage('');
    } catch (err) {
      console.error('Mesaj gönderme hatası:', err);
    }
  };

  const startRecording = async () => {
    try {
      // Hem ses tanıma hem de ses kaydı başlat
      if (recognitionRef.current) {
        console.log('Ses tanıma başlatılıyor...');
        recognitionRef.current.start();
      }
      
      // MediaRecorder ile ses dosyası kaydet
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks = [];
      mediaRecorderRef.current.ondataavailable = (event) => {
        chunks.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      console.log('Ses kaydı başlatıldı');
      
    } catch (error) {
      console.error('Ses kaydı başlatma hatası:', error);
      alert('Ses kaydı başlatılamadı. Mikrofon izni verdiğinizden emin olun.');
    }
  };

  const stopRecording = () => {
    try {
      // Ses tanımayı durdur
      if (recognitionRef.current && isListening) {
        console.log('Ses tanıma durduruluyor...');
        recognitionRef.current.stop();
      }
      
      // MediaRecorder'ı durdur
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        console.log('Ses kaydı durduruluyor...');
        mediaRecorderRef.current.stop();
      }
    } catch (error) {
      console.error('Ses kaydı durdurma hatası:', error);
    }
  };

  const sendAudioMessage = async () => {
    if (!audioText.trim()) return;
    
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('audio_text', audioText);
      
      if (audioBlob) {
        formData.append('audio_file', audioBlob, 'audio_message.webm');
      }
      
      await axios.post('http://localhost:5000/case_study_room/send_audio', formData, { 
        withCredentials: true,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setAudioText('');
      setAudioBlob(null);
      setAudioUrl('');
    } catch (err) {
      console.error('Ses mesajı gönderme hatası:', err);
    }
  };

  const formatMessageTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('tr-TR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
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
          sx={{ p: 5, minWidth: 340, maxWidth: 500, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Çoklu Case Study</Typography>
          <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)">
            Aynı ilgi alanına sahip bir partner ile birlikte case study çözün!
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={fetchCaseStudy} 
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
            Partner Ara
          </Button>
          
          <Button 
            variant="outlined" 
            color="secondary" 
            size="small" 
            fullWidth 
            onClick={async () => {
              try {
                const res = await axios.post('http://localhost:5000/debug/force_match', {
                  interest: 'Data Science'
                });
                console.log('Manuel eşleştirme:', res.data);
                if (res.data.status === 'success') {
                  alert('Eşleştirme başarılı! Sayfayı yenileyin.');
                }
              } catch (err) {
                console.error('Manuel eşleştirme hatası:', err);
              }
            }}
            sx={{ mt: 1 }}
          >
            Manuel Eşleştirme (Test)
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'waiting') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 340, maxWidth: 500, borderRadius: 4, textAlign: 'center' }}
        >
          <CircularProgress size={60} sx={{ color: '#4f46e5', mb: 3 }} />
          <Typography variant="h5" fontWeight={700} mb={2} color="white">Partner Aranıyor...</Typography>
          <Typography color="rgba(255,255,255,0.8)" mb={3}>
            Aynı ilgi alanına sahip bir partner bulunduğunda otomatik olarak eşleşeceksiniz.
          </Typography>
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={() => { setStep('start'); setError(''); }}
            sx={{
              borderColor: 'rgba(255,255,255,0.3)',
              color: 'white',
              '&:hover': {
                borderColor: 'rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            İptal Et
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'case') {
    console.log('Case step render ediliyor...', { caseStudy, partner, sessionId });
    
    // Hata kontrolü
    if (!caseStudy) {
      return (
        <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Paper elevation={8} className="glass-card" sx={{ p: 5, borderRadius: 4 }}>
            <Typography variant="h5" color="white" textAlign="center">Case Study Yükleniyor...</Typography>
            <Typography color="rgba(255,255,255,0.8)" textAlign="center" mt={2}>
              Case study verisi bulunamadı. Lütfen sayfayı yenileyin.
            </Typography>
            <Button 
              variant="contained" 
              onClick={() => window.location.reload()} 
              sx={{ mt: 2, display: 'block', mx: 'auto' }}
            >
              Sayfayı Yenile
            </Button>
          </Paper>
        </Box>
      );
    }
    
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 11 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, maxWidth: 1000, mx: 'auto', borderRadius: 4 }}
        >
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" fontWeight={700} color="white">Çoklu Case Study</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label={`Partner: ${partner}`} 
                avatar={<Avatar sx={{ bgcolor: '#4f46e5' }}>{partner?.charAt(0)}</Avatar>}
                sx={{ color: 'white', bgcolor: 'rgba(79, 70, 229, 0.2)' }}
              />
              <Chip 
                label={`Kalan Süre: ${formatTime(timeLeft)}`} 
                color={timeLeft < 300 ? 'error' : 'primary'}
                sx={{ color: 'white' }}
              />
            </Box>
          </Box>

          {/* Case Study Metni */}
          <Box sx={{ mb: 3, p: 2, borderRadius: 2, bgcolor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.15)' }}>
            <Typography variant="h6" fontWeight={600} color="#4f46e5" mb={1}>{caseStudy?.title || 'Case Study'}</Typography>
            <Typography color="rgba(255,255,255,0.9)" mb={1}>{caseStudy?.description}</Typography>
            {caseStudy?.requirements && (
              <Typography color="rgba(255,255,255,0.8)" mb={0.5}>
                <strong>Gereksinimler:</strong> {caseStudy.requirements.join(', ')}
              </Typography>
            )}
            {caseStudy?.constraints && (
              <Typography color="rgba(255,255,255,0.8)" mb={0.5}>
                <strong>Kısıtlar:</strong> {caseStudy.constraints.join(', ')}
              </Typography>
            )}
            {caseStudy?.evaluation_criteria && (
              <Typography color="rgba(255,255,255,0.8)">
                <strong>Değerlendirme Kriterleri:</strong> {caseStudy.evaluation_criteria.join(', ')}
              </Typography>
            )}
          </Box>

          {/* Mesajlaşma Alanı */}
          <Box sx={{ mb: 3, height: 400, border: '1px solid rgba(255,255,255,0.2)', borderRadius: 2, p: 2, display: 'flex', flexDirection: 'column' }}>
            <Typography fontWeight={600} mb={2} color="white">Partner ile Mesajlaş:</Typography>
            {/* Mesajlar */}
            <Box sx={{ flex: '1 1 auto', overflow: 'auto', mb: 2 }}>
              {messages.map((msg, index) => (
                <Box key={index} sx={{ mb: 1, textAlign: msg.username === currentUser ? 'right' : 'left' }}>
                  <Box sx={{ 
                    display: 'inline-block', 
                    maxWidth: '70%', 
                    p: 1, 
                    borderRadius: 2,
                    bgcolor: msg.username === currentUser ? 'rgba(79, 70, 229, 0.3)' : 'rgba(255,255,255,0.1)',
                    color: 'white'
                  }}>
                    <Typography variant="caption" display="block" color="rgba(255,255,255,0.6)">
                      {msg.username} • {formatMessageTime(msg.timestamp)}
                    </Typography>
                    <Typography>
                      {msg.type === 'audio' ? (
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <VolumeUp fontSize="small" />
                            <Typography variant="body2">{msg.audio_text}</Typography>
                          </Box>
                          {msg.audio_url && (
                            <audio controls style={{ width: '100%', height: '32px' }}>
                              <source src={msg.audio_url} type="audio/webm" />
                              Tarayıcınız ses dosyasını desteklemiyor.
                            </audio>
                          )}
                        </Box>
                      ) : (
                        msg.message
                      )}
                    </Typography>
                  </Box>
                </Box>
              ))}
              <div ref={messagesEndRef} />
            </Box>
            {/* Mesaj Gönderme */}
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexShrink: 0 }}>
              <TextField
                size="small"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Mesaj yaz..."
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                sx={{
                  flex: 1,
                  '& .MuiOutlinedInput-root': {
                    color: 'white',
                    '& fieldset': {
                      borderColor: 'rgba(255,255,255,0.3)',
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: 'rgba(255,255,255,0.5)',
                    },
                  },
                }}
              />
              <IconButton 
                onClick={sendMessage} 
                disabled={!newMessage.trim()}
                sx={{ color: 'white' }}
              >
                <Send />
              </IconButton>
              <IconButton 
                onClick={isListening ? stopRecording : startRecording}
                sx={{ 
                  color: isListening ? '#ff4444' : 'white',
                  bgcolor: isListening ? 'rgba(255,68,68,0.2)' : 'transparent',
                  border: isListening ? '2px solid #ff4444' : '2px solid rgba(255,255,255,0.3)',
                  '&:hover': {
                    bgcolor: isListening ? 'rgba(255,68,68,0.3)' : 'rgba(255,255,255,0.1)'
                  }
                }}
                title={isListening ? 'Ses kaydını durdur' : 'Ses kaydı başlat'}
              >
                {isListening ? <MicOff /> : <Mic />}
              </IconButton>
            </Box>
          {/* Ses Kaydı Önizleme */}
            {audioText && (
              <Box sx={{ mt: 1, p: 2, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 2, border: '1px solid rgba(255,255,255,0.2)' }}>
                <Typography variant="body2" color="rgba(255,255,255,0.9)" sx={{ mb: 1 }}>
                  <strong>Ses tanıma sonucu:</strong>
                </Typography>
          <TextField
            multiline
                  rows={2}
            fullWidth
                  value={audioText}
                  onChange={(e) => setAudioText(e.target.value)}
                  placeholder="Metni düzenleyebilirsiniz..."
            sx={{
                    mb: 2,
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': {
                  borderColor: 'rgba(255,255,255,0.3)',
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(255,255,255,0.5)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#4f46e5',
                },
                '& .MuiInputBase-input::placeholder': {
                  color: 'rgba(255,255,255,0.5)',
                  opacity: 1,
                },
              },
            }}
          />
                
                {audioUrl && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="rgba(255,255,255,0.8)" sx={{ mb: 1 }}>
                      <strong>Ses dosyası:</strong>
                    </Typography>
                    <audio controls style={{ width: '100%' }}>
                      <source src={audioUrl} type="audio/webm" />
                      Tarayıcınız ses dosyasını desteklemiyor.
                    </audio>
                  </Box>
                )}
                
                <Stack direction="row" spacing={1}>
                  <Button 
                    size="small" 
                    variant="contained"
                    onClick={sendAudioMessage}
                    disabled={!audioText.trim()}
                    sx={{ 
                      color: 'white',
                      bgcolor: '#4f46e5',
                      '&:hover': { bgcolor: '#4338ca' }
                    }}
                  >
                    Gönder
                  </Button>
                  <Button 
                    size="small" 
                    variant="outlined"
                    onClick={() => {
                      setAudioText('');
                      setAudioBlob(null);
                      setAudioUrl('');
                    }}
                    sx={{ 
                      color: 'white',
                      borderColor: 'rgba(255,255,255,0.3)',
                      '&:hover': { borderColor: 'rgba(255,255,255,0.5)' }
                    }}
                  >
                    İptal
                  </Button>
                </Stack>
              </Box>
            )}
          </Box>
          

          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Stack direction="row" spacing={2} justifyContent="space-between">
            <Button 
              variant="outlined" 
              color="primary" 
              onClick={() => { setStep('start'); setError(''); }}
              sx={{
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white',
                '&:hover': {
                  borderColor: 'rgba(255,255,255,0.5)',
                  background: 'rgba(255,255,255,0.1)',
                }
              }}
            >
              Çık
            </Button>
            
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            onClick={handleSubmit} 
              disabled={loading || isSubmitted} 
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
              {isSubmitted ? 'Oturum Tamamlandı' : 'Oturumu Tamamla'}
          </Button>
          </Stack>
        </Paper>
      </Box>
    );
  }

  if (step === 'result') {
    // Unified evaluation fallback logic
    const evalObj = result.userEvaluation?.unified_evaluation || result.userEvaluation || {};
    const partnerEvalObj = result.partnerEvaluation?.unified_evaluation || result.partnerEvaluation || {};
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, minWidth: 340, maxWidth: 900, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Case Study Değerlendirmesi</Typography>
          {result && (
            <Stack spacing={3}>
              {/* Birleşik Performans Değerlendirmesi */}
              <Box>
                <Typography variant="h6" fontWeight={600} mb={1} color="white">
                  {result.currentUser} Performans Değerlendirmesi:
                </Typography>
                <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                  {evalObj.feedback || evalObj.error || 'Performans değerlendirmesi bulunamadı.'}
                </Typography>
                
                {/* Detailed Analysis */}
                {evalObj.detailed_analysis && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>Detaylı Analiz:</Typography>
                    <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                      {evalObj.detailed_analysis}
                    </Typography>
                  </Box>
                )}
                
                {/* Strengths */}
                {evalObj.strengths && evalObj.strengths.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>Güçlü Yanlar:</Typography>
                    <Box sx={{ pl: 2 }}>
                      {evalObj.strengths.map((strength, index) => (
                        <Typography key={index} color="rgba(255,255,255,0.8)" sx={{ mb: 0.5 }}>
                          • {strength}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {/* Improvements */}
                {evalObj.improvements && evalObj.improvements.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>İyileştirme Önerileri:</Typography>
                    <Box sx={{ pl: 2 }}>
                      {evalObj.improvements.map((improvement, index) => (
                        <Typography key={index} color="rgba(255,255,255,0.8)" sx={{ mb: 0.5 }}>
                          • {improvement}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {evalObj.total_score && (
                  <Box sx={{ mt: 2 }}>
                    <Chip 
                      label={`Toplam Puan: ${evalObj.total_score}/100`} 
                      color="primary" 
                      sx={{ mr: 1, color: 'white' }}
                    />
                    {evalObj.problem_analysis_score && (
                      <Chip 
                        label={`Problem Analizi: ${evalObj.problem_analysis_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {evalObj.solution_approach_score && (
                      <Chip 
                        label={`Çözüm Yaklaşımı: ${evalObj.solution_approach_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {evalObj.communication_score && (
                      <Chip 
                        label={`İletişim: ${evalObj.communication_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {evalObj.technical_score && (
                      <Chip 
                        label={`Teknik Bilgi: ${evalObj.technical_score}/25`} 
                        color="secondary" 
                        sx={{ color: 'white' }}
                      />
                    )}
                  </Box>
                )}
              </Box>
              {/* Partner'ın Performans Değerlendirmesi */}
              <Box>
                <Typography variant="h6" fontWeight={600} mb={1} color="white">
                  {result.partner} Performans Değerlendirmesi:
              </Typography>
                <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                  {partnerEvalObj.feedback || partnerEvalObj.error || 'Partner performans değerlendirmesi bulunamadı.'}
                </Typography>
                
                {/* Detailed Analysis */}
                {partnerEvalObj.detailed_analysis && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>Detaylı Analiz:</Typography>
                    <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                      {partnerEvalObj.detailed_analysis}
                    </Typography>
                  </Box>
                )}
                
                {/* Strengths */}
                {partnerEvalObj.strengths && partnerEvalObj.strengths.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>Güçlü Yanlar:</Typography>
                    <Box sx={{ pl: 2 }}>
                      {partnerEvalObj.strengths.map((strength, index) => (
                        <Typography key={index} color="rgba(255,255,255,0.8)" sx={{ mb: 0.5 }}>
                          • {strength}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {/* Improvements */}
                {partnerEvalObj.improvements && partnerEvalObj.improvements.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight={600} color="white" mb={1}>İyileştirme Önerileri:</Typography>
                    <Box sx={{ pl: 2 }}>
                      {partnerEvalObj.improvements.map((improvement, index) => (
                        <Typography key={index} color="rgba(255,255,255,0.8)" sx={{ mb: 0.5 }}>
                          • {improvement}
                        </Typography>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {partnerEvalObj.total_score && (
                  <Box sx={{ mt: 2 }}>
                    <Chip 
                      label={`Toplam Puan: ${partnerEvalObj.total_score}/100`} 
                      color="primary" 
                      sx={{ mr: 1, color: 'white' }}
                    />
                    {partnerEvalObj.problem_analysis_score && (
                      <Chip 
                        label={`Problem Analizi: ${partnerEvalObj.problem_analysis_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {partnerEvalObj.solution_approach_score && (
                      <Chip 
                        label={`Çözüm Yaklaşımı: ${partnerEvalObj.solution_approach_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {partnerEvalObj.communication_score && (
                      <Chip 
                        label={`İletişim: ${partnerEvalObj.communication_score}/25`} 
                        color="secondary" 
                        sx={{ mr: 1, color: 'white' }}
                      />
                    )}
                    {partnerEvalObj.technical_score && (
                      <Chip 
                        label={`Teknik Bilgi: ${partnerEvalObj.technical_score}/25`} 
                        color="secondary" 
                        sx={{ color: 'white' }}
                      />
                    )}
                  </Box>
                )}
              </Box>


              

              
              {/* Mesajlaşma Geçmişi */}
              {(result.messages?.length > 0 || result.audio_messages?.length > 0) && (
                <Box>
                  <Typography variant="h6" fontWeight={600} mb={1} color="white">Mesajlaşma Geçmişi:</Typography>
                  <Box sx={{ maxHeight: 200, overflow: 'auto', p: 1, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 1 }}>
                    {[...(result.messages || []), ...(result.audio_messages || [])]
                      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
                      .map((msg, index) => (
                        <Box key={index} sx={{ mb: 1, fontSize: '0.9rem' }}>
                          <Typography variant="caption" color="rgba(255,255,255,0.6)">
                            {msg.username} • {formatMessageTime(msg.timestamp)}
                          </Typography>
                          <Typography color="rgba(255,255,255,0.8)">
                            {msg.type === 'audio' ? (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <VolumeUp fontSize="small" />
                                {msg.audio_text}
                              </Box>
                            ) : (
                              msg.message
                            )}
                          </Typography>
                        </Box>
                      ))}
                  </Box>
                </Box>
              )}
            </Stack>
          )}
          <Button 
            variant="outlined" 
            color="primary" 
            fullWidth 
              onClick={() => { 
                setStep('start'); 
                setSolution(''); 
                setResult(null); 
                setSessionId(null);
                setPartner(null);
                setTimeLeft(30 * 60);
                setIsSubmitted(false);
              }}
            sx={{
                mt: 3,
              borderColor: 'rgba(255,255,255,0.3)',
              color: 'white',
              '&:hover': {
                borderColor: 'rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            Yeni Case Study
          </Button>
        </Paper>
      </Box>
    );
  }
} 