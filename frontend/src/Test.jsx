import React, { useState } from 'react';
import { Box, Typography, Paper, Button, Radio, RadioGroup, FormControlLabel, CircularProgress, Alert, Stack } from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function Test() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState('start'); // start, quiz, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const fetchQuestions = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/test_your_skill', {}, { withCredentials: true });
      setQuestions(res.data.questions);
      setStep('quiz');
    } catch (err) {
      setError(err.response?.data?.error || 'Soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (idx, value) => {
    setAnswers({ ...answers, [idx]: value });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const user_answers = questions.map((q, i) => answers[i] || '');
      const res = await axios.post('http://localhost:5000/test_your_skill/evaluate', {
        user_answers,
        questions
      }, { withCredentials: true });
      setResult(res.data);
      setStep('result');
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
          sx={{ p: 5, minWidth: 340, maxWidth: 500, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Test Çöz</Typography>
          <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)">Bilgini test etmek için başla!</Typography>
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
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 6 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, maxWidth: 700, mx: 'auto', borderRadius: 4 }}
        >
          <Typography variant="h5" fontWeight={700} mb={3} color="white">Sorular</Typography>
          <Stack spacing={3}>
            {questions.map((q, i) => (
              <Box key={i}>
                <Typography fontWeight={600} mb={1} color="white">{i + 1}. {q.question}</Typography>
                <RadioGroup value={answers[i] || ''} onChange={e => handleAnswer(i, e.target.value)}>
                  {q.choices.map((choice, j) => (
                    <FormControlLabel 
                      key={j} 
                      value={choice} 
                      control={<Radio sx={{ color: 'rgba(255,255,255,0.7)', '&.Mui-checked': { color: '#4f46e5' } }} />} 
                      label={<Typography color="rgba(255,255,255,0.8)">{choice}</Typography>} 
                    />
                  ))}
                </RadioGroup>
              </Box>
            ))}
          </Stack>
          {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            sx={{ mt: 4 }}
            onClick={handleSubmit} 
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
            Testi Bitir
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
          sx={{ p: 5, minWidth: 340, maxWidth: 500, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Sonuçlar</Typography>
          {result && (
            <>
              <Typography textAlign="center" mb={2} color="rgba(255,255,255,0.8)">
                {result.results.filter(r => r.is_correct).length} doğru, {result.results.length - result.results.filter(r => r.is_correct).length} yanlış
              </Typography>
              {result.resources && result.resources.length > 0 && (
                <Alert severity="info" sx={{ mb: 2 }}>Eksik olduğun konu için önerilen kaynak: <b>{result.resources[0]}</b></Alert>
              )}
            </>
          )}
          <Button 
            variant="outlined" 
            color="primary" 
            fullWidth 
            sx={{ mt: 2 }}
            onClick={() => { setStep('start'); setAnswers({}); setResult(null); }}
            sx={{
              borderColor: 'rgba(255,255,255,0.3)',
              color: 'white',
              '&:hover': {
                borderColor: 'rgba(255,255,255,0.5)',
                background: 'rgba(255,255,255,0.1)',
              }
            }}
          >
            Tekrar Dene
          </Button>
        </Paper>
      </Box>
    );
  }
} 