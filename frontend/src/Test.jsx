import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, Typography, Paper, Button, Radio, RadioGroup, FormControlLabel, 
  CircularProgress, Alert, Stack, LinearProgress, Chip, Grid, Card,
  CardContent, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import { motion } from 'framer-motion';
import { AccessTime, ExpandMore, CheckCircle, Cancel, School, TrendingUp } from '@mui/icons-material';
import axios from 'axios';

export default function Test() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState('start'); // start, quiz, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [testSessionId, setTestSessionId] = useState('');
  const [timeLeft, setTimeLeft] = useState(0); // saniye cinsinden
  const [totalTime, setTotalTime] = useState(0);
  const [difficulty, setDifficulty] = useState('mixed');
  const [numQuestions, setNumQuestions] = useState(10);
  const [showTimer, setShowTimer] = useState(false);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswer = (idx, value) => {
    setAnswers({ ...answers, [idx]: value });
  };

  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setError('');
    console.log('Submitting with testSessionId:', testSessionId);
    try {
      const user_answers = questions.map((q, i) => answers[i] || '');
      const res = await axios.post('http://localhost:5000/test_your_skill/evaluate', {
        user_answers,
        test_session_id: testSessionId
      }, { withCredentials: true });
      
      setResult(res.data);
      setStep('result');
    } catch (err) {
      setError(err.response?.data?.error || 'Değerlendirme başarısız.');
    } finally {
      setLoading(false);
    }
  }, [questions, answers, testSessionId]);

  // Geri sayım timer - handleSubmit tanımlandıktan sonra
  useEffect(() => {
    let timer;
    if (step === 'quiz' && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft, handleSubmit]);

  // Son 5 dakikada otomatik olarak timer'ı göster
  useEffect(() => {
    if (timeLeft <= 300 && timeLeft > 0) { // Son 5 dakika
      setShowTimer(true);
    }
  }, [timeLeft]);

  const fetchQuestions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/test_your_skill', {
        num_questions: numQuestions,
        difficulty: difficulty
      }, { withCredentials: true });
      
      console.log('New test session created:', res.data.test_session_id);
      setQuestions(res.data.questions);
      setTestSessionId(res.data.test_session_id);
      setTimeLeft(res.data.duration);
      setTotalTime(res.data.duration);
      setStep('quiz');
      
      // İlk sınava girdiğinde 5 saniye timer'ı göster
      setShowTimer(true);
      setTimeout(() => {
        setShowTimer(false);
      }, 5000);
    } catch (err) {
      setError(err.response?.data?.error || 'Soru alınamadı.');
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
            Seviye Tespit Sınavı
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Bilgi seviyenizi ölçmek için sorulara cevap verin. Test süreli olacak!
          </Typography>
          
          {/* Test ayarları */}
          <Stack spacing={3} mb={4}>
            <Box>
              <Typography color="white" mb={1} fontWeight={600}>Soru Sayısı:</Typography>
              <Stack direction="row" spacing={1}>
                {[5, 10, 15, 20].map(num => (
                  <Button 
                    key={num}
                    variant={numQuestions === num ? "contained" : "outlined"}
                    size="small"
                    onClick={() => setNumQuestions(num)}
                    sx={{ 
                      color: numQuestions === num ? 'white' : 'rgba(255,255,255,0.7)',
                      borderColor: 'rgba(255,255,255,0.3)'
                    }}
                  >
                    {num}
                  </Button>
                ))}
              </Stack>
            </Box>
            
            <Box>
              <Typography color="white" mb={1} fontWeight={600}>Zorluk Seviyesi:</Typography>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {[
                  { value: 'beginner', label: 'Başlangıç' },
                  { value: 'intermediate', label: 'Orta' },
                  { value: 'advanced', label: 'İleri' },
                  { value: 'mixed', label: 'Karışık' }
                ].map(diff => (
                  <Button 
                    key={diff.value}
                    variant={difficulty === diff.value ? "contained" : "outlined"}
                    size="small"
                    onClick={() => setDifficulty(diff.value)}
                    sx={{ 
                      color: difficulty === diff.value ? 'white' : 'rgba(255,255,255,0.7)',
                      borderColor: 'rgba(255,255,255,0.3)',
                      mb: 1
                    }}
                  >
                    {diff.label}
                  </Button>
                ))}
              </Stack>
            </Box>
          </Stack>
          
          <Alert severity="info" sx={{ mb: 3, backgroundColor: 'rgba(33, 150, 243, 0.1)' }}>
            <Typography color="rgba(255,255,255,0.9)">
              ⏱️ Test süresi: 30 dakika<br/>
              📝 {numQuestions} soru<br/>
              📊 Zorluk: {difficulty === 'mixed' ? 'Karışık' : difficulty === 'beginner' ? 'Başlangıç' : difficulty === 'intermediate' ? 'Orta' : 'İleri'}
            </Typography>
          </Alert>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={fetchQuestions} 
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
            Teste Başla
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'quiz') {
    const progressPercentage = ((totalTime - timeLeft) / totalTime) * 100;
    const isTimeRunningOut = timeLeft < 300; // Son 5 dakika
    
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        {/* Timer Bar */}
        <Box
          sx={{
            position: 'fixed',
            top: 80,
            left: 20,
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}
        >
          {/* Progress Ring - Clickable */}
          <Box 
            sx={{ 
              position: 'relative', 
              display: 'inline-flex',
              cursor: 'pointer',
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'scale(1.05)'
              }
            }}
            onClick={() => setShowTimer(!showTimer)}
          >
            <CircularProgress
              variant="determinate"
              value={progressPercentage}
              size={60}
              thickness={4}
              sx={{
                color: isTimeRunningOut 
                  ? 'rgba(255, 107, 107, 0.2)'
                  : 'rgba(255, 255, 255, 0.2)',
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                }
              }}
            />
            <CircularProgress
              variant="determinate"
              value={progressPercentage}
              size={60}
              thickness={4}
              sx={{
                position: 'absolute',
                color: isTimeRunningOut 
                  ? '#ff6b6b'
                  : '#ffffff',
                '& .MuiCircularProgress-circle': {
                  strokeLinecap: 'round',
                },
                filter: 'drop-shadow(0 0 6px rgba(255,255,255,0.4))'
              }}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AccessTime sx={{ 
                color: isTimeRunningOut ? '#ff6b6b' : '#ffffff',
                fontSize: 22,
                filter: 'drop-shadow(0 0 4px rgba(255,255,255,0.3))'
              }} />
            </Box>
          </Box>

          {/* Timer Display - Conditional */}
          {showTimer && (
            <Paper
              component={motion.div}
              initial={{ opacity: 0, scale: 0.8, x: -20 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.8, x: -20 }}
              transition={{ duration: 0.3 }}
              elevation={8}
              sx={{
                background: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(15px)',
                border: `2px solid ${isTimeRunningOut ? 'rgba(255, 107, 107, 0.3)' : 'rgba(255, 255, 255, 0.3)'}`,
                borderRadius: '20px',
                px: 3,
                py: 1.5,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                minWidth: 120,
                justifyContent: 'center'
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 700,
                  color: isTimeRunningOut ? '#ff6b6b' : '#ffffff',
                  fontFamily: 'monospace',
                  fontSize: '1.2rem'
                }}
              >
                {formatTime(timeLeft)}
              </Typography>
            </Paper>
          )}
        </Box>

        {/* Sorular */}
        <Box sx={{ mt: 20 }}>
          <Paper 
            component={motion.div} 
            initial={{ opacity: 0, y: 40 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.7 }} 
            elevation={8} 
            className="glass-card"
            sx={{ p: 5, maxWidth: 900, mx: 'auto', borderRadius: 4 }}
          >
            <Typography variant="h5" fontWeight={700} mb={4} color="white" textAlign="center">
              Seviye Tespit Sınavı
            </Typography>
            
            <Stack spacing={4}>
              {questions.map((q, i) => (
                <Card 
                  key={i}
                  component={motion.div}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  sx={{ 
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    border: answers[i] ? '2px solid #4f46e5' : '2px solid transparent',
                    borderRadius: 3
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Stack direction="row" alignItems="flex-start" spacing={2} mb={2}>
                      <Chip 
                        label={i + 1} 
                        size="small" 
                        sx={{ 
                          backgroundColor: '#4f46e5',
                          color: 'white',
                          fontWeight: 600
                        }}
                      />
                      <Typography 
                        fontWeight={600} 
                        color="white" 
                        sx={{ flexGrow: 1, lineHeight: 1.6 }}
                      >
                        {q.question}
                      </Typography>
                      {q.difficulty && (
                        <Chip 
                          label={q.difficulty} 
                          size="small"
                          color={
                            q.difficulty === 'beginner' ? 'success' : 
                            q.difficulty === 'intermediate' ? 'warning' : 'error'
                          }
                        />
                      )}
                    </Stack>
                    
                    <RadioGroup 
                      value={answers[i] || ''} 
                      onChange={e => handleAnswer(i, e.target.value)}
                      sx={{ ml: 2 }}
                    >
                      {q.options && q.options.map((option, j) => {
                        const letter = option.charAt(0); // A, B, C, D
                        return (
                          <FormControlLabel 
                            key={j} 
                            value={letter} 
                            control={
                              <Radio 
                                sx={{ 
                                  color: 'rgba(255,255,255,0.7)', 
                                  '&.Mui-checked': { color: '#4f46e5' } 
                                }} 
                              />
                            } 
                            label={
                              <Typography 
                                color="rgba(255,255,255,0.9)"
                                sx={{ 
                                  fontSize: '0.95rem',
                                  fontWeight: answers[i] === letter ? 600 : 400
                                }}
                              >
                                {option}
                              </Typography>
                            } 
                          />
                        );
                      })}
                    </RadioGroup>
                  </CardContent>
                </Card>
              ))}
            </Stack>
            
            {error && <Alert severity="error" sx={{ mt: 3 }}>{error}</Alert>}
            
            <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
              <Button 
                variant="contained" 
                color="primary" 
                size="large" 
                onClick={handleSubmit} 
                disabled={loading} 
                endIcon={loading && <CircularProgress size={20} color="inherit" />}
                sx={{
                  minWidth: 200,
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  borderRadius: '25px',
                  py: 1.5,
                  px: 4,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                    boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
                  }
                }}
              >
                Testi Bitir ve Değerlendir
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>
    );
  }

  if (step === 'result') {
    const evaluation = result?.evaluation;
    const summary = evaluation?.summary;
    
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        <Grid container spacing={4} sx={{ maxWidth: 1200, mx: 'auto', px: 2 }}>
          {/* Ana Sonuç Kartı */}
          <Grid item xs={12} md={6}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 40 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.7 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 4, borderRadius: 4, textAlign: 'center' }}
            >
              <Typography variant="h4" fontWeight={700} mb={2} color="white">
                Test Sonucu
              </Typography>
              
              {summary && (
                <>
                  <Box sx={{ position: 'relative', display: 'inline-flex', mb: 3 }}>
                    <CircularProgress
                      variant="determinate"
                      value={summary.success_rate}
                      size={120}
                      thickness={4}
                      sx={{
                        color: summary.success_rate >= 80 ? '#4caf50' : 
                               summary.success_rate >= 60 ? '#ff9800' : '#f44336',
                      }}
                    />
                    <Box
                      sx={{
                        top: 0,
                        left: 0,
                        bottom: 0,
                        right: 0,
                        position: 'absolute',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Typography variant="h6" component="div" color="white" fontWeight={700}>
                        %{summary.success_rate}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Typography variant="h5" color="white" fontWeight={600} mb={1}>
                    Seviye: {summary.skill_level}
                  </Typography>
                  
                  <Typography color="rgba(255,255,255,0.8)" mb={3}>
                    {summary.correct_answers} / {summary.total_questions} doğru cevap
                  </Typography>
                  
                  {result.time_taken && (
                    <Typography color="rgba(255,255,255,0.7)" mb={2}>
                      ⏱️ Süre: {result.time_taken.minutes}dk {result.time_taken.seconds}sn
                    </Typography>
                  )}
                  
                  {summary.time_performance && (
                    <Chip 
                      label={summary.time_performance}
                      color={
                        summary.time_performance.includes('Optimal') ? 'success' :
                        summary.time_performance.includes('Hızlı') ? 'warning' : 'default'
                      }
                      sx={{ mb: 2 }}
                    />
                  )}
                </>
              )}
            </Paper>
          </Grid>

          {/* Öneriler ve Kaynaklar */}
          <Grid item xs={12}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 40 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.9 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 4, borderRadius: 4 }}
            >
              <Typography variant="h6" fontWeight={700} mb={3} color="white">
                <School sx={{ mr: 1, verticalAlign: 'middle' }} />
                Öneriler ve Gelişim Tavsiyeleri
              </Typography>
              
              {evaluation?.recommendations && (
                <Stack spacing={2} mb={3}>
                  <Typography variant="subtitle2" color="rgba(255,255,255,0.9)" fontWeight={600}>
                    📈 Gelişim Önerileri:
                  </Typography>
                  {evaluation.recommendations.map((rec, i) => (
                    <Alert key={i} severity="info" sx={{ backgroundColor: 'rgba(33, 150, 243, 0.1)' }}>
                      <Typography color="rgba(255,255,255,0.9)">{rec}</Typography>
                    </Alert>
                  ))}
                </Stack>
              )}
            </Paper>
          </Grid>

          {/* Tüm Kaynaklar - Birleştirilmiş Bölüm */}
          {((result.resources && result.resources.length > 0) || 
            (result.web_resources && (result.web_resources.youtube_videos || result.web_resources.websites))) && (
            <Grid item xs={12}>
                <Paper 
                  component={motion.div} 
                  initial={{ opacity: 0, y: 40 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  transition={{ duration: 1.0 }} 
                  elevation={8} 
                  className="glass-card"
                  sx={{ p: 4, borderRadius: 4, mt: 3 }}
                >
                  <Typography variant="h6" fontWeight={700} mb={3} color="white">
                    🌐 Önerilen Öğrenme Kaynakları
                  </Typography>
                  
                  <Grid container spacing={3}>
                    {/* Direkt URL Kaynakları */}
                    {result.resources && result.resources.length > 0 && (
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="#4f46e5" fontWeight={600} mb={2}>
                          🎯 Doğrudan Erişim Kaynakları:
                        </Typography>
                        <Grid container spacing={2}>
                          {result.resources.slice(0, 6).map((resource, i) => (
                            <Grid item xs={12} sm={6} md={4} key={i}>
                              <Card sx={{ 
                                backgroundColor: 'rgba(79,70,229,0.1)', 
                                border: '1px solid rgba(79,70,229,0.2)',
                                height: '100%',
                                display: 'flex',
                                flexDirection: 'column'
                              }}>
                                <CardContent sx={{ py: 2, flexGrow: 1 }}>
                                  <Stack spacing={1}>
                                    <Typography color="white" fontWeight={600} variant="body2">
                                      {resource.title || resource}
                                    </Typography>
                                    
                                    <Stack direction="row" spacing={1} flexWrap="wrap">
                                      {resource.type && (
                                        <Chip 
                                          label={resource.type} 
                                          size="small" 
                                          sx={{ backgroundColor: '#4f46e5', color: 'white', fontSize: '0.7rem' }}
                                        />
                                      )}
                                      {resource.level && (
                                        <Chip 
                                          label={resource.level} 
                                          size="small" 
                                          variant="outlined"
                                          sx={{ borderColor: 'rgba(255,255,255,0.3)', color: 'rgba(255,255,255,0.8)', fontSize: '0.7rem' }}
                                        />
                                      )}
                                    </Stack>
                                    
                                    {resource.description && (
                                      <Typography color="rgba(255,255,255,0.7)" variant="caption" display="block">
                                        {resource.description}
                                      </Typography>
                                    )}
                                    
                                    {resource.url && (
                                      <Button
                                        variant="outlined"
                                        size="small"
                                        onClick={() => window.open(resource.url, '_blank')}
                                        sx={{
                                          borderColor: '#4f46e5',
                                          color: '#4f46e5',
                                          textTransform: 'none',
                                          fontSize: '0.75rem',
                                          mt: 'auto',
                                          '&:hover': {
                                            borderColor: '#7c3aed',
                                            backgroundColor: 'rgba(79,70,229,0.1)'
                                          }
                                        }}
                                      >
                                        🔗 Kaynağa Git
                                      </Button>
                                    )}
                                  </Stack>
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                      </Grid>
                    )}
                    
                    {/* YouTube Videoları */}
                    {result.web_resources && result.web_resources.youtube_videos && result.web_resources.youtube_videos.length > 0 && (
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="#ff4444" fontWeight={600} mb={2}>
                          📺 YouTube Videoları:
                        </Typography>
                        <Stack spacing={2}>
                          {result.web_resources.youtube_videos.slice(0, 3).map((video, i) => (
                            <Card key={i} sx={{ backgroundColor: 'rgba(255,68,68,0.1)', border: '1px solid rgba(255,68,68,0.2)' }}>
                              <CardContent sx={{ py: 2 }}>
                                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                                  <Typography color="white" fontWeight={600} variant="body2" sx={{ flexGrow: 1 }}>
                                    {video.title}
                                  </Typography>
                                  {video.level && (
                                    <Chip 
                                      label={video.level} 
                                      size="small" 
                                      sx={{ backgroundColor: '#ff4444', color: 'white' }}
                                    />
                                  )}
                                </Stack>
                                {video.description && (
                                  <Typography color="rgba(255,255,255,0.7)" variant="caption" display="block" sx={{ mb: 1 }}>
                                    {video.description}
                                  </Typography>
                                )}
                                {video.duration_estimate && (
                                  <Typography color="rgba(255,255,255,0.6)" variant="caption" display="block" sx={{ mb: 2 }}>
                                    ⏱️ Süre: {video.duration_estimate}
                                  </Typography>
                                )}
                                <Button
                                  variant="outlined"
                                  size="small"
                                  onClick={() => window.open(video.url, '_blank')}
                                  sx={{
                                    borderColor: '#ff4444',
                                    color: '#ff4444',
                                    textTransform: 'none',
                                    fontSize: '0.75rem',
                                    '&:hover': {
                                      borderColor: '#ff6666',
                                      backgroundColor: 'rgba(255,68,68,0.1)'
                                    }
                                  }}
                                >
                                  📺 YouTube'da Ara
                                </Button>
                              </CardContent>
                            </Card>
                          ))}
                        </Stack>
                      </Grid>
                    )}
                    
                    {/* Web Siteleri */}
                    {result.web_resources && result.web_resources.websites && result.web_resources.websites.length > 0 && (
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" color="#4fc3f7" fontWeight={600} mb={2}>
                          🌐 Web Kaynakları ve Makaleler:
                        </Typography>
                        <Stack spacing={2}>
                          {result.web_resources.websites.slice(0, 3).map((website, i) => (
                            <Card key={i} sx={{ backgroundColor: 'rgba(79,195,247,0.1)', border: '1px solid rgba(79,195,247,0.2)' }}>
                              <CardContent sx={{ py: 2 }}>
                                <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                                  <Typography color="white" fontWeight={600} variant="body2" sx={{ flexGrow: 1 }}>
                                    {website.title}
                                  </Typography>
                                  {website.type && (
                                    <Chip 
                                      label={website.type} 
                                      size="small" 
                                      sx={{ backgroundColor: '#4fc3f7', color: 'white' }}
                                    />
                                  )}
                                </Stack>
                                {website.description && (
                                  <Typography color="rgba(255,255,255,0.7)" variant="caption" display="block" sx={{ mb: 1 }}>
                                    {website.description}
                                  </Typography>
                                )}
                                {website.level && (
                                  <Typography color="rgba(255,255,255,0.6)" variant="caption" display="block" sx={{ mb: 2 }}>
                                    📚 Seviye: {website.level}
                                  </Typography>
                                )}
                                <Button
                                  variant="outlined"
                                  size="small"
                                  onClick={() => window.open(website.url, '_blank')}
                                  sx={{
                                    borderColor: '#4fc3f7',
                                    color: '#4fc3f7',
                                    textTransform: 'none',
                                    fontSize: '0.75rem',
                                    '&:hover': {
                                      borderColor: '#81d4fa',
                                      backgroundColor: 'rgba(79,195,247,0.1)'
                                    }
                                  }}
                                >
                                  🔗 Siteye Git
                                </Button>
                              </CardContent>
                            </Card>
                          ))}
                        </Stack>
                      </Grid>
                    )}
                  </Grid>
                </Paper>
            </Grid>
          )}

          {/* Dinamik Öğrenme Kaynakları */}
          {evaluation?.suggested_resources && evaluation.suggested_resources.length > 0 && (
            <Grid item xs={12}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 40 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 1.0 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 4, borderRadius: 4 }}
              >
                <Typography variant="h6" fontWeight={700} mb={3} color="white">
                  <School sx={{ mr: 1, verticalAlign: 'middle' }} />
                  🌐 Zayıf Alanlarınız İçin Öğrenme Kaynakları
                </Typography>
                
                <Grid container spacing={3}>
                  {evaluation.suggested_resources.map((resource, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Card
                        component={motion.div}
                        whileHover={{ scale: 1.02 }}
                        sx={{
                          background: 'linear-gradient(135deg, rgba(79,70,229,0.2) 0%, rgba(124,58,237,0.2) 100%)',
                          backdropFilter: 'blur(10px)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: 3,
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column'
                        }}
                      >
                        <CardContent sx={{ flexGrow: 1, p: 3 }}>
                          <Stack spacing={2}>
                            {/* Kaynak Türü Chip */}
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <Chip 
                                label={resource.type || 'Kaynak'} 
                                size="small" 
                                sx={{ 
                                  background: 'linear-gradient(45deg, #4f46e5, #7c3aed)',
                                  color: 'white',
                                  fontWeight: 600,
                                  fontSize: '0.7rem'
                                }} 
                              />
                              {resource.level && (
                                <Chip 
                                  label={resource.level} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ 
                                    borderColor: 'rgba(255,255,255,0.3)',
                                    color: 'rgba(255,255,255,0.8)',
                                    fontSize: '0.65rem'
                                  }} 
                                />
                              )}
                            </Box>
                            
                            {/* Başlık */}
                            <Typography 
                              variant="subtitle2" 
                              fontWeight={700} 
                              color="white"
                              sx={{ 
                                fontSize: '0.9rem',
                                lineHeight: 1.3,
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden'
                              }}
                            >
                              {resource.title}
                            </Typography>
                            
                            {/* Açıklama */}
                            <Typography 
                              color="rgba(255,255,255,0.7)" 
                              variant="caption" 
                              sx={{ 
                                fontSize: '0.75rem',
                                lineHeight: 1.4,
                                display: '-webkit-box',
                                WebkitLineClamp: 3,
                                WebkitBoxOrient: 'vertical',
                                overflow: 'hidden'
                              }}
                            >
                              {resource.description}
                            </Typography>
                            
                            {/* İlgili Konu */}
                            {resource.related_topic && (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography 
                                  color="rgba(255,255,255,0.6)" 
                                  variant="caption"
                                  sx={{ fontSize: '0.7rem' }}
                                >
                                  📚 Konu:
                                </Typography>
                                <Typography 
                                  color="#4fc3f7" 
                                  variant="caption" 
                                  fontWeight={600}
                                  sx={{ fontSize: '0.7rem' }}
                                >
                                  {resource.related_topic}
                                </Typography>
                              </Box>
                            )}
                            
                            {/* Süre Bilgisi */}
                            {resource.estimated_duration && (
                              <Typography 
                                color="rgba(255,255,255,0.6)" 
                                variant="caption"
                                sx={{ fontSize: '0.7rem' }}
                              >
                                ⏱️ {resource.estimated_duration}
                              </Typography>
                            )}
                          </Stack>
                          
                          {/* Kaynak Erişim Butonu */}
                          <Button
                            variant="contained"
                            size="small"
                            fullWidth
                            onClick={() => window.open(resource.url, '_blank')}
                            sx={{
                              mt: 2,
                              background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                              borderRadius: '20px',
                              textTransform: 'none',
                              fontWeight: 600,
                              fontSize: '0.75rem',
                              py: 1,
                              boxShadow: '0 2px 10px rgba(79, 70, 229, 0.3)',
                              '&:hover': {
                                background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                                boxShadow: '0 4px 15px rgba(79, 70, 229, 0.5)',
                                transform: 'translateY(-1px)'
                              }
                            }}
                          >
                            {resource.type === 'YouTube Video' || resource.type === 'Video' || resource.type === 'YouTube Kanal' ? '📹' : 
                             resource.type === 'Kurs' ? '🎓' :
                             resource.type === 'Doküman' ? '📖' :
                             resource.type === 'Tutorial' ? '📝' :
                             resource.type === 'Oyun' ? '🎮' :
                             resource.type === 'Challenge' ? '🏆' : '🌐'} 
                            {' '}{resource.type === 'YouTube Video' || resource.type === 'Video' ? 'İzle' : 
                                 resource.type === 'YouTube Kanal' ? 'Kanala Git' :
                                 resource.type === 'Kurs' ? 'Kursa Başla' : 
                                 'Kaynaşa Git'}
                          </Button>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
                
                {/* Kaynak İstatistikleri */}
                <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
                  <Typography variant="body2" color="rgba(255,255,255,0.8)" textAlign="center">
                    💡 Bu kaynaklar yanlış cevapladığınız konulara göre özelleştirilmiştir
                  </Typography>
                  <Typography variant="caption" color="rgba(255,255,255,0.6)" textAlign="center" display="block" sx={{ mt: 1 }}>
                    Toplam {evaluation.suggested_resources.length} kişiselleştirilmiş kaynak • 
                    {evaluation.suggested_resources.filter(r => r.type?.includes('Video')).length} Video • 
                    {evaluation.suggested_resources.filter(r => r.type === 'Kurs').length} Kurs • 
                    {evaluation.suggested_resources.filter(r => r.type === 'Doküman').length} Doküman
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          )}

          {/* Detaylı Analiz */}
          <Grid item xs={12}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 40 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 1.1 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 4, borderRadius: 4 }}
            >
              <Typography variant="h6" fontWeight={700} mb={3} color="white">
                <TrendingUp sx={{ mr: 1, verticalAlign: 'middle' }} />
                Detaylı Analiz
              </Typography>
              
              <Grid container spacing={3}>
                {/* Güçlü Alanlar */}
                {evaluation?.strong_areas && evaluation.strong_areas.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="#4caf50" fontWeight={600} mb={2}>
                      ✅ Güçlü Alanlarınız:
                    </Typography>
                    <Stack spacing={1}>
                      {evaluation.strong_areas.map((area, i) => (
                        <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 1 }}>
                          <Typography color="white" variant="body2">{area.category}</Typography>
                          <Chip label={`%${area.success_rate}`} size="small" color="success" />
                        </Box>
                      ))}
                    </Stack>
                  </Grid>
                )}
                
                {/* Zayıf Alanlar */}
                {evaluation?.weak_areas && evaluation.weak_areas.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="#f44336" fontWeight={600} mb={2}>
                      📚 Gelişim Alanlarınız:
                    </Typography>
                    <Stack spacing={1}>
                      {evaluation.weak_areas.map((area, i) => (
                        <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1, backgroundColor: 'rgba(244, 67, 54, 0.1)', borderRadius: 1 }}>
                          <Typography color="white" variant="body2">{area.category}</Typography>
                          <Chip label={`%${area.success_rate}`} size="small" color="error" />
                        </Box>
                      ))}
                    </Stack>
                  </Grid>
                )}
              </Grid>
              
              {/* Soru Detayları */}
              <Accordion sx={{ mt: 3, backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                  <Typography color="white" fontWeight={600}>Soru Detaylarını Görüntüle</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    {evaluation?.results && evaluation.results.map((result, i) => (
                      <Box key={i} sx={{ p: 2, border: '1px solid rgba(255,255,255,0.1)', borderRadius: 1 }}>
                        <Stack direction="row" alignItems="center" spacing={2} mb={1}>
                          {result.is_correct ? 
                            <CheckCircle sx={{ color: '#4caf50' }} /> : 
                            <Cancel sx={{ color: '#f44336' }} />
                          }
                          <Typography color="white" variant="body2" sx={{ flexGrow: 1 }}>
                            {result.question}
                          </Typography>
                        </Stack>
                        <Typography color="rgba(255,255,255,0.7)" variant="caption">
                          Cevabınız: {result.user_answer} | Doğru: {result.correct_answer}
                        </Typography>
                        {result.explanation && (
                          <Typography color="rgba(255,255,255,0.6)" variant="caption" display="block" sx={{ mt: 1 }}>
                            💡 {result.explanation}
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </AccordionDetails>
              </Accordion>
            </Paper>
          </Grid>

          {/* Aksiyonlar */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
              <Button 
                variant="contained" 
                color="primary" 
                size="large"
                onClick={() => { 
                  setStep('start'); 
                  setAnswers({}); 
                  setResult(null); 
                  setTimeLeft(0);
                  setTestSessionId('');
                }}
                sx={{
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  borderRadius: '25px',
                  py: 1.5,
                  px: 4,
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                    boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
                  }
                }}
              >
                Yeni Test Başlat
              </Button>
              
              <Button 
                variant="outlined" 
                color="primary" 
                size="large"
                onClick={() => window.location.href = '/dashboard'}
                sx={{
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white',
                  borderRadius: '25px',
                  py: 1.5,
                  px: 4,
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.5)',
                    background: 'rgba(255,255,255,0.1)',
                  }
                }}
              >
                Dashboard'a Dön
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    );
  }
} 