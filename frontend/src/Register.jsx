import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Alert, Link, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import API_ENDPOINTS from './config.js';

export default function Register({ setIsLoggedIn }) {
  const [form, setForm] = useState({ username: '', password: '', confirmPassword: '', interest: '', geminiApiKey: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    if (form.password !== form.confirmPassword) {
      setError('Şifreler eşleşmiyor.');
      setLoading(false);
      return;
    }
    
    // Şifre gücü kontrolü
    if (form.password.length < 5) {
      setError('Şifre en az 5 karakter olmalıdır.');
      setLoading(false);
      return;
    }
    
    if (!form.interest) {
      setError('Lütfen bir ilgi alanı seçin.');
      setLoading(false);
      return;
    }
    
    // Eski kullanıcı bilgilerini temizle
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    
    try {
      const res = await axios.post(API_ENDPOINTS.REGISTER, {
        username: form.username,
        password: form.password,
        interest: form.interest,
        geminiApiKey: form.geminiApiKey
      }, { withCredentials: true });
      
      localStorage.setItem('username', form.username);
      localStorage.setItem('interest', form.interest);
      if (form.geminiApiKey) {
        localStorage.setItem('geminiApiKey', form.geminiApiKey);
      }
      
      // localStorage değişikliğini tetikle
      window.dispatchEvent(new Event('localStorageChange'));
      
      setIsLoggedIn(true);
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      setError(err.response?.data?.error || 'Kayıt başarısız.');
    } finally {
      setLoading(false);
    }
  };

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
        <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Kayıt Ol</Typography>
        <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">Hemen üye ol ve eğitime başla!</Typography>
        
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Kullanıcı Adı"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
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
                '& .MuiInputLabel-root': {
                  color: 'rgba(255,255,255,0.7)',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#4f46e5',
                },
              },
            }}
          />
          
          <TextField
            fullWidth
            label="Şifre"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
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
                '& .MuiInputLabel-root': {
                  color: 'rgba(255,255,255,0.7)',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#4f46e5',
                },
              },
            }}
          />
          
          <TextField
            fullWidth
            label="Şifre Tekrar"
            type="password"
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            required
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
                '& .MuiInputLabel-root': {
                  color: 'rgba(255,255,255,0.7)',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#4f46e5',
                },
              },
            }}
          />
          
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>İlgi Alanı</InputLabel>
            <Select
              value={form.interest}
              onChange={(e) => setForm({ ...form, interest: e.target.value })}
              required
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#4f46e5',
                },
                '& .MuiSvgIcon-root': {
                  color: 'rgba(255,255,255,0.7)',
                },
                '& .MuiPaper-root': {
                  backgroundColor: 'rgba(0, 0, 0, 0.9)',
                  backdropFilter: 'blur(10px)',
                },
                '& .MuiMenu-paper': {
                  backgroundColor: 'rgba(0, 0, 0, 0.9)',
                  backdropFilter: 'blur(10px)',
                },
              }}
              MenuProps={{
                PaperProps: {
                  sx: {
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    backdropFilter: 'blur(10px)',
                    '& .MuiMenuItem-root': {
                      color: 'white',
                      '&:hover': {
                        backgroundColor: 'rgba(79, 70, 229, 0.3)',
                      },
                      '&.Mui-selected': {
                        backgroundColor: 'rgba(79, 70, 229, 0.5)',
                        '&:hover': {
                          backgroundColor: 'rgba(79, 70, 229, 0.6)',
                        },
                      },
                    },
                  },
                },
              }}
            >
              <MenuItem value="AI">AI Developer</MenuItem>
              <MenuItem value="Data Science">Data Scientist</MenuItem>
              <MenuItem value="Web Development">Web Developer</MenuItem>
              <MenuItem value="Mobile">Mobile Developer</MenuItem>
              <MenuItem value="Cyber Security">Cyber Security Specialist</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            label="Gemini API Key"
            type="password"
            value={form.geminiApiKey}
            onChange={(e) => setForm({ ...form, geminiApiKey: e.target.value })}
            placeholder="https://aistudio.google.com/app/apikey adresinden alın"
            helperText="Kendi Gemini API key'inizi girin (ücretsiz) - https://aistudio.google.com/app/apikey adresinden alabilirsiniz."
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
                '& .MuiInputLabel-root': {
                  color: 'rgba(255,255,255,0.7)',
                },
                '& .MuiInputLabel-root.Mui-focused': {
                  color: '#4f46e5',
                },
                '& .MuiFormHelperText-root': {
                  color: 'rgba(255,255,255,0.6)',
                },
              },
            }}
          />
          
          {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
          
          <Button 
            type="submit" 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            disabled={loading}
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
            {loading ? 'Kayıt Yapılıyor...' : 'Kayıt Ol'}
          </Button>
          
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography color="rgba(255,255,255,0.8)">
              Zaten hesabın var mı?{' '}
              <Link href="/login" sx={{ color: '#4f46e5', textDecoration: 'none', fontWeight: 600 }}>
                Giriş Yap
              </Link>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
} 