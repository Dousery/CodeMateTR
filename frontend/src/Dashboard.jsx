import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent, CardActions, Button, Avatar, Dialog, DialogTitle, DialogContent, DialogActions, MenuItem, Select, FormControl, InputLabel, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import CodeIcon from '@mui/icons-material/Code';
import QuizIcon from '@mui/icons-material/Quiz';
import PsychologyIcon from '@mui/icons-material/Psychology';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import WorkIcon from '@mui/icons-material/Work';
import ForumIcon from '@mui/icons-material/Forum';
import axios from 'axios';
import API_ENDPOINTS from './config.js';

const modules = [
  {
    title: 'Test Çöz',
    desc: 'Bilgini test et, eksiklerini gör.',
    icon: <QuizIcon fontSize="large" color="primary" />, 
    path: '/test',
    tags: ['AI Test Sistemi', 'Kişiselleştirilmiş Öneriler']
  },
  {
    title: 'Kodlama Odası',
    desc: 'Kodlama becerilerini geliştir.',
    icon: <CodeIcon fontSize="large" color="success" />, 
    path: '/code',
    tags: ['AI Kod Asistanı', 'Kod Değerlendirme']
  },
  {
    title: 'Mülakat',
    desc: 'Yapay zeka ile dinamik mülakat.',
    icon: <RecordVoiceOverIcon fontSize="large" color="info" />, 
    path: '/auto-interview',
    tags: ['AI Recruiter', 'Sesli Mülakat']
  },
  {
    title: 'Akıllı İş Bulma',
    desc: 'CV\'ni analiz et, ideal işleri keşfet.',
    icon: <WorkIcon fontSize="large" color="secondary" />, 
    path: '/smart-job-finder',
    tags: ['AI CV Analizi', 'Kariyer Önerileri']
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
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Geliştirici';
  const [open, setOpen] = useState(false);
  const [alan, setAlan] = useState(localStorage.getItem('interest') || '');
  const [saving, setSaving] = useState(false);

  // Add CSS for pulse animation
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.2);
          opacity: 0.7;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);


  useEffect(() => {
    // Eğer ilgi alanı yoksa önce backend'den çek
    if (!alan) {
      axios.get(API_ENDPOINTS.PROFILE, { withCredentials: true })
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
      await axios.post(API_ENDPOINTS.SET_INTEREST, { interest: alan }, { withCredentials: true });
      localStorage.setItem('interest', alan);
      setOpen(false);
    } catch (err) {
      alert('Alan kaydedilemedi!');
    } finally {
      setSaving(false);
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
        <>
          <Grid container spacing={4} justifyContent="center" sx={{ mt: 2, maxWidth: '1200px', mx: 'auto' }}>
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
                    maxWidth: 280,
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
                    <Typography color="rgba(255,255,255,0.8)" mb={2}>{mod.desc}</Typography>
                    
                    {/* AI Tags */}
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, justifyContent: 'center', mb: 1 }}>
                      {mod.tags.map((tag, index) => (
                        <Chip
                          key={index}
                          label={tag}
                          size="small"
                          sx={{
                            background: 'rgba(255, 255, 255, 0.2)',
                            backdropFilter: 'blur(10px)',
                            color: 'white',
                            fontSize: '0.7rem',
                            fontWeight: 500,
                            border: '1px solid rgba(255, 255, 255, 0.3)',
                            '& .MuiChip-label': {
                              px: 1,
                            }
                          }}
                        />
                      ))}
                    </Box>
                  </CardContent>
                  <CardActions sx={{ justifyContent: 'center', pb: 1.5 }}>
                    <Button 
                      variant="contained" 
                      color="primary" 
                      size="large" 
                      onClick={() => navigate(mod.path)}
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

          {/* Floating Forum Button */}
          <Box
            component={motion.div}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            sx={{
              position: 'fixed',
              bottom: 20,
              right: 20,
              zIndex: 1000,
            }}
          >
            <Button
              variant="contained"
              onClick={() => {
                // Smooth transition to forum
                const button = event.target;
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                  navigate('/forum');
                }, 150);
              }}
              sx={{
                background: 'linear-gradient(135deg, #4c63d2 0%, #5a3d7a 100%)',
                backdropFilter: 'blur(15px)',
                borderRadius: '50px',
                px: 3,
                py: 1.5,
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.9rem',
                boxShadow: '0 4px 15px rgba(76, 99, 210, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white',
                minWidth: 'auto',
                position: 'relative',
                '&:hover': {
                  background: 'linear-gradient(135deg, #3f52b5 0%, #4a3368 100%)',
                  boxShadow: '0 6px 20px rgba(76, 99, 210, 0.4)',
                  transform: 'translateY(-2px) scale(1.05)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                },
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: -2,
                  right: -2,
                  width: 8,
                  height: 8,
                  background: '#4ade80',
                  borderRadius: '50%',
                  border: '2px solid rgba(255, 255, 255, 0.9)',
                  animation: 'pulse 2s infinite',
                }
              }}
            >
              <ForumIcon sx={{ mr: 0.5, fontSize: 20 }} />
              Forum
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
} 