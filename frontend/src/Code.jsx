import React, { useState } from 'react';
import { Box, Typography, Paper, Button, TextField, CircularProgress, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function Code() {
  const [problem, setProblem] = useState('');
  const [solution, setSolution] = useState('');
  const [step, setStep] = useState('start'); // start, code, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const fetchProblem = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room', {}, { withCredentials: true });
      setProblem(res.data.problem);
      setStep('code');
    } catch (err) {
      setError(err.response?.data?.error || 'Problem alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room/evaluate', {
        problem: problem,
        solution: solution
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
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Kodlama Odası</Typography>
          <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)">Kodlama becerilerini geliştir!</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={fetchProblem} 
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
            Problem Al
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'code') {
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
          <Typography variant="h5" fontWeight={700} mb={3} color="white">Kodlama Problemi</Typography>
          <Typography fontWeight={600} mb={2} color="white">Problem:</Typography>
          <Typography mb={3} color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>{problem}</Typography>
          <Typography fontWeight={600} mb={2} color="white">Çözümünü Yaz:</Typography>
          <TextField
            multiline
            rows={8}
            fullWidth
            value={solution}
            onChange={(e) => setSolution(e.target.value)}
            placeholder="Kodunu buraya yaz..."
            sx={{
              mb: 3,
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
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={handleSubmit} 
            disabled={loading || !solution.trim()} 
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
            Kodu Gönder
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
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Değerlendirme</Typography>
          {result && (
            <>
              <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                {result.feedback}
              </Typography>
              {result.score && (
                <Typography textAlign="center" mb={2} color="white" variant="h6">
                  Puan: {result.score}/100
                </Typography>
              )}
            </>
          )}
          <Button 
            variant="outlined" 
            color="primary" 
            fullWidth 
            onClick={() => { setStep('start'); setSolution(''); setResult(null); }}
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
            Yeni Problem
          </Button>
        </Paper>
      </Box>
    );
  }
} 