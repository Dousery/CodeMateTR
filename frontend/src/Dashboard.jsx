import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, CardActions, Button, Avatar, Dialog, DialogTitle, DialogContent, DialogActions, MenuItem, Select, FormControl, InputLabel } from '@mui/material';
import { motion } from 'framer-motion';
import CodeIcon from '@mui/icons-material/Code';
import QuizIcon from '@mui/icons-material/Quiz';
import PsychologyIcon from '@mui/icons-material/Psychology';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import WorkIcon from '@mui/icons-material/Work';
import axios from 'axios';

const modules = [
  {
    title: 'Test Çöz',
    desc: 'Bilgini test et, eksiklerini gör.',
    icon: <QuizIcon fontSize="large" color="primary" />, 
    path: '/test',
  },
  {
    title: 'Case Study',
    desc: 'Gerçek senaryolarla pratik yap.',
    icon: <WorkIcon fontSize="large" color="secondary" />, 
    path: '/case',
  },
  {
    title: 'Kodlama Odası',
    desc: 'Kodlama becerilerini geliştir.',
    icon: <CodeIcon fontSize="large" color="success" />, 
    path: '/code',
  },
  {
    title: 'Mülakat',
    desc: 'Yapay zeka ile dinamik mülakat.',
    icon: <RecordVoiceOverIcon fontSize="large" color="info" />, 
    path: '/auto-interview',
  },
];

const alanlar = [
  { value: 'AI', label: 'AI Developer' },
  { value: 'Data Science', label: 'Data Scientist' },
  { value: 'Web Development', label: 'Web Developer' },
  { value: 'Mobile', label: 'Mobile Developer' },
  { value: 'Cyber Security', label: 'Cyber Security Specialist' },
];

export default function Dashboard() {
  const username = localStorage.getItem('username') || 'Geliştirici';
  const [open, setOpen] = useState(false);
  const [alan, setAlan] = useState(localStorage.getItem('interest') || '');
  const [saving, setSaving] = useState(false);
  const [clearingSessions, setClearingSessions] = useState(false);

  useEffect(() => {
    // Eğer ilgi alanı yoksa önce backend'den çek
    if (!alan) {
      axios.get('http://localhost:5000/profile', { withCredentials: true })
        .then(res => {
          if (res.data.interest) {
            localStorage.setItem('interest', res.data.interest);
            setAlan(res.data.interest);
            setOpen(false);
          } else {
            setOpen(true);
          }
        })
        .catch(() => setOpen(true));
    }
  }, [alan]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.post('http://localhost:5000/set_interest', { interest: alan }, { withCredentials: true });
      localStorage.setItem('interest', alan);
      setOpen(false);
    } catch (err) {
      alert('Alan kaydedilemedi!');
    } finally {
      setSaving(false);
    }
  };

  const handleClearSessions = async () => {
    setClearingSessions(true);
    try {
      await axios.post('http://localhost:5000/debug/clear_user_sessions', {}, { withCredentials: true });
      alert('Session\'lar temizlendi!');
    } catch (err) {
      alert('Session temizleme hatası: ' + (err.response?.data?.error || err.message));
    } finally {
      setClearingSessions(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', py: 18 }}>
      <Dialog 
        open={open} 
        disableEscapeKeyDown 
        disableBackdropClick
        PaperProps={{
          sx: {
            background: 'rgba(20, 20, 40, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            '& .MuiMenu-paper': {
              background: 'rgba(20, 20, 40, 0.98)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255,255,255,0.2)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            }
          }
        }}
      >
        <DialogTitle sx={{ 
          color: 'white', 
          bgcolor: 'rgba(30, 30, 50, 0.9)', 
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          fontWeight: 600
        }}>
          İlgi Alanı Seç
        </DialogTitle>
        <DialogContent sx={{ 
          bgcolor: 'rgba(20, 20, 40, 0.9)', 
          backdropFilter: 'blur(20px)',
          pt: 3
        }}>
          <FormControl fullWidth>
            <InputLabel sx={{ color: 'white', fontWeight: 500 }}>Alan</InputLabel>
            <Select 
              value={alan} 
              label="Alan" 
              onChange={e => setAlan(e.target.value)}
              MenuProps={{
                PaperProps: {
                  sx: {
                    background: 'rgba(20, 20, 40, 0.98)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
                    '& .MuiMenuItem-root': {
                      color: 'white',
                      fontWeight: 500,
                      '&:hover': {
                        background: 'rgba(255,255,255,0.1)',
                      }
                    }
                  }
                }
              }}
              sx={{ 
                color: 'white',
                fontWeight: 500,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.4)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255,255,255,0.6)',
                },
                '& .MuiSvgIcon-root': {
                  color: 'white',
                },
                '& .MuiSelect-select': {
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: 1,
                }
              }}
            >
              {alanlar.map(a => (
                <MenuItem key={a.value} value={a.value} sx={{ 
                  color: 'white', 
                  fontWeight: 500,
                  background: 'rgba(20, 20, 40, 0.98)',
                  '&:hover': {
                    background: 'rgba(255,255,255,0.1)',
                  }
                }}>
                  {a.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions sx={{ 
          bgcolor: 'rgba(30, 30, 50, 0.9)', 
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          p: 2
        }}>
          <Button 
            onClick={handleSave} 
            variant="contained" 
            disabled={!alan || saving}
            sx={{
              background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
              borderRadius: '20px',
              px: 3,
              py: 1,
              textTransform: 'none',
              fontWeight: 600,
              boxShadow: '0 4px 15px rgba(79, 70, 229, 0.3)',
              '&:hover': {
                background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                boxShadow: '0 6px 20px rgba(79, 70, 229, 0.4)',
              }
            }}
          >
            Kaydet
          </Button>
        </DialogActions>
      </Dialog>
      <Typography
        component={motion.h2}
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        variant="h3"
        fontWeight={700}
        textAlign="center"
        mb={4}
        color="white"
      >
        Hoş Geldin, {username}!
      </Typography>
      <Typography textAlign="center" mb={8} color="rgba(255,255,255,0.8)">
        Aşağıdaki modüllerden birini seçerek kendini geliştir!
      </Typography>
      {!alan ? null : (
        <Grid container spacing={4} justifyContent="center" sx={{ mt: 2 }}>
          {modules.map((mod, i) => (
            <Grid item xs={12} sm={6} md={3} key={mod.title}>
              <Card
                component={motion.div}
                whileHover={{ scale: 1.02, y: -8 }}
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.6 }}
                elevation={6}
                className="glass-card"
                sx={{ 
                  borderRadius: 4, 
                  minHeight: 260, 
                  display: 'flex', 
                  flexDirection: 'column', 
                  justifyContent: 'space-between',
                  cursor: 'pointer'
                }}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Avatar sx={{ 
                    bgcolor: 'rgba(255,255,255,0.1)', 
                    mx: 'auto', 
                    mb: 2, 
                    width: 64, 
                    height: 64, 
                    boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
                    border: '1px solid rgba(255,255,255,0.2)'
                  }}>
                    {mod.icon}
                  </Avatar>
                  <Typography variant="h5" fontWeight={600} mb={1} color="white">
                    {mod.title}
                  </Typography>
                  <Typography color="rgba(255,255,255,0.8)">{mod.desc}</Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    size="large" 
                    href={mod.path}
                    sx={{
                      background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                      borderRadius: '25px',
                      px: 4,
                      py: 1.5,
                      textTransform: 'none',
                      fontWeight: 600,
                      boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
                      '&:hover': {
                        background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                        boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
                        transform: 'translateY(-2px)'
                      }
                    }}
                  >
                    Başla
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
} 