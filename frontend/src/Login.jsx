import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Alert, Link } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Login({ setIsLoggedIn }) {
  const [form, setForm] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const res = await axios.post('http://localhost:5000/login', form, { withCredentials: true });
      localStorage.setItem('username', form.username);
      
      // Kullanıcının interest'ini al
      const profileRes = await axios.get('http://localhost:5000/profile', { withCredentials: true });
      if (profileRes.data.interest) {
        localStorage.setItem('interest', profileRes.data.interest);
      }
      
      setIsLoggedIn(true);
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      setError(err.response?.data?.error || 'Giriş başarısız.');
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
        <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">Giriş Yap</Typography>
        <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">Hesabına giriş yap ve eğitime başla!</Typography>
        
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
            {loading ? 'Giriş Yapılıyor...' : 'Giriş Yap'}
          </Button>
          
          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography color="rgba(255,255,255,0.8)">
              Hesabın yok mu?{' '}
              <Link href="/register" sx={{ color: '#4f46e5', textDecoration: 'none', fontWeight: 600 }}>
                Kayıt Ol
              </Link>
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
} 