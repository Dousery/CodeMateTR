import React, { useState, useEffect } from 'react';
import { Button, Box, Typography, Stack, Card, CardContent, Grid, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import QuizIcon from '@mui/icons-material/Quiz';
import CodeIcon from '@mui/icons-material/Code';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import WorkIcon from '@mui/icons-material/Work';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

// Typing animation component for CodeMateTR
const TypingAnimation = () => {
  const [text, setText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  const fullText = 'CodeMateTR';
  
  useEffect(() => {
    let currentIndex = 0;
    const interval = setInterval(() => {
      if (currentIndex <= fullText.length) {
        setText(fullText.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(interval);
      }
    }, 150);
    
    return () => clearInterval(interval);
  }, []);
  
  useEffect(() => {
    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);
    
    return () => clearInterval(cursorInterval);
  }, []);

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Typography 
        variant="h1" 
        fontWeight={900} 
        sx={{ 
          fontSize: { xs: '2.5rem', md: '4rem', lg: '5rem' },
          fontFamily: 'monospace',
          background: 'linear-gradient(45deg, #fff 0%, #e0e0e0 50%, #fff 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textShadow: '0 4px 20px rgba(0,0,0,0.3)',
          letterSpacing: '0.1em',
          position: 'relative',
        }}
      >
        {text}
        <motion.span
          animate={{ opacity: showCursor ? 1 : 0 }}
          transition={{ duration: 0.1 }}
          style={{
            display: 'inline-block',
            width: '3px',
            height: '1em',
            background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
            marginLeft: '2px',
            borderRadius: '2px',
            boxShadow: '0 0 10px rgba(79, 70, 229, 0.8)',
          }}
        />
      </Typography>
    </Box>
  );
};

// Feature cards component
const FeatureCards = () => {
  const features = [
    {
      icon: <QuizIcon sx={{ fontSize: 40, color: '#4f46e5' }} />,
      title: 'AI Test Sistemi',
      description: 'Kişiselleştirilmiş testler ve akıllı değerlendirmeler ile bilgini ölç',
      tags: ['Adaptif Öğrenme', 'Anlık Geri Bildirim']
    },
    {
      icon: <CodeIcon sx={{ fontSize: 40, color: '#10b981' }} />,
      title: 'Kodlama Odası',
      description: 'AI destekli kod yazma ve gerçek zamanlı kod değerlendirme',
      tags: ['AI Asistan', 'Kod Analizi']
    },
    {
      icon: <RecordVoiceOverIcon sx={{ fontSize: 40, color: '#f59e0b' }} />,
      title: 'Otomatik Mülakat',
      description: 'Sesli ve metin tabanlı AI mülakat simülasyonu',
      tags: ['Sesli Mülakat', 'Gerçek Zamanlı']
    },
    {
      icon: <WorkIcon sx={{ fontSize: 40, color: '#ef4444' }} />,
      title: 'Akıllı İş Bulma',
      description: 'CV analizi ve kariyer önerileri ile ideal işini bul',
      tags: ['CV Analizi', 'Kariyer Önerileri']
    },
    {
      icon: <PsychologyIcon sx={{ fontSize: 40, color: '#8b5cf6' }} />,
      title: 'Mülakat Simülasyonu',
      description: 'Gerçek mülakat deneyimi ile kendini hazırla',
      tags: ['Simülasyon', 'Pratik']
    },
    {
      icon: <AutoAwesomeIcon sx={{ fontSize: 40, color: '#06b6d4' }} />,
      title: 'AI Destekli Öğrenme',
      description: 'Yapay zeka ile kişiselleştirilmiş öğrenme deneyimi',
      tags: ['Kişiselleştirme', 'AI']
    }
  ];

  return (
    <Grid container spacing={3} sx={{ maxWidth: 1200, mx: 'auto', px: 2 }}>
      {features.map((feature, index) => (
        <Grid item xs={12} sm={6} md={4} key={index}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: index * 0.1 }}
            whileHover={{ y: -8 }}
          >
            <Card
              sx={{
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: 3,
                height: '100%',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.15)',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                }
              }}
            >
              <CardContent sx={{ p: 3, textAlign: 'center' }}>
                <Box sx={{ mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography
                  variant="h6"
                  sx={{
                    color: 'white',
                    fontWeight: 600,
                    mb: 1,
                    fontSize: { xs: '1.1rem', md: '1.2rem' }
                  }}
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.8)',
                    mb: 2,
                    lineHeight: 1.5,
                    fontSize: { xs: '0.9rem', md: '1rem' }
                  }}
                >
                  {feature.description}
                </Typography>
                <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap">
                  {feature.tags.map((tag, tagIndex) => (
                    <Chip
                      key={tagIndex}
                      label={tag}
                      size="small"
                      sx={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        color: 'rgba(255, 255, 255, 0.9)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        fontSize: '0.75rem',
                        '&:hover': {
                          background: 'rgba(255, 255, 255, 0.2)',
                        }
                      }}
                    />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      ))}
    </Grid>
  );
};

// Floating particles component
const FloatingParticles = () => (
  <Box sx={{ position: 'absolute', width: '100%', height: '100%', overflow: 'hidden', zIndex: 1 }}>
    {[...Array(20)].map((_, i) => (
      <motion.div
        key={i}
        style={{
          position: 'absolute',
          width: Math.random() * 4 + 2,
          height: Math.random() * 4 + 2,
          background: `rgba(255, 255, 255, ${Math.random() * 0.3 + 0.1})`,
          borderRadius: '50%',
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
        }}
        animate={{
          y: [0, -100, 0],
          x: [0, Math.random() * 50 - 25, 0],
          opacity: [0, 1, 0],
        }}
        transition={{
          duration: Math.random() * 10 + 10,
          repeat: Infinity,
          ease: "linear",
          delay: Math.random() * 5,
        }}
      />
    ))}
  </Box>
);

// Animated gradient background
const AnimatedGradient = () => (
  <motion.div
    style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      background: 'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)',
      zIndex: 0,
    }}
    animate={{
      background: [
        'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)',
        'linear-gradient(135deg, #1a1b3d 0%, #2d1b69 25%, #4a148c 50%, #6a1b9a 75%, #0a0e27 100%)',
        'linear-gradient(135deg, #2d1b69 0%, #4a148c 25%, #6a1b9a 50%, #0a0e27 75%, #1a1b3d 100%)',
        'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)',
      ],
    }}
    transition={{
      duration: 8,
      repeat: Infinity,
      ease: "easeInOut",
    }}
  />
);

export default function Home() {
  const navigate = useNavigate();
  
  return (
    <Box sx={{ 
      position: 'relative',
      minHeight: '100vh',
      overflow: 'auto',
    }}>
      <AnimatedGradient />
      <FloatingParticles />
      
      {/* Hero Section */}
      <Box sx={{ 
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        zIndex: 2,
      }}>
        <Stack
          component={motion.div}
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          spacing={6}
          alignItems="center"
          justifyContent="center"
          sx={{
            width: '100%',
            color: 'white',
            px: 2,
          }}
        >
        {/* CodeMateTR Typing Animation */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <TypingAnimation />
        </motion.div>
        
        {/* Developer Eğitim Platformu - Moved down */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 1.5 }}
        >
          <Typography 
            variant="h2" 
            fontWeight={700} 
            textAlign="center" 
            gutterBottom 
            sx={{ 
              fontSize: { xs: '1.4rem', md: '2.2rem' },
              textShadow: '0 4px 20px rgba(0,0,0,0.3)',
              background: 'linear-gradient(45deg, #fff, #e0e0e0)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              opacity: 0.9,
            }}
          >
            Developer Eğitim Platformu
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2.2 }}
        >
          <Typography 
            variant="h5" 
            textAlign="center" 
            maxWidth={700}
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              textShadow: '0 2px 10px rgba(0,0,0,0.2)',
              lineHeight: 1.6
            }}
          >
            AI destekli testler, kodlama ve mülakat simülasyonları ile kendini geliştir. Akıllı iş bulma sistemi ile hayalindeki kariyere adım at. Modern, şık ve interaktif bir deneyim seni bekliyor!
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 2.8 }}
        >
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3}>
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                variant="contained" 
                color="primary" 
                size="large" 
                onClick={() => navigate('/register')}
                sx={{
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  borderRadius: '25px',
                  px: 4,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                    boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
                    transform: 'translateY(-2px)'
                  }
                }}
              >
                Kayıt Ol
              </Button>
            </motion.div>
            
            <motion.div
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button 
                variant="outlined" 
                color="secondary" 
                size="large" 
                onClick={() => navigate('/login')}
                sx={{
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white',
                  borderRadius: '25px',
                  px: 4,
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '1.1rem',
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.5)',
                    background: 'rgba(255,255,255,0.1)',
                    transform: 'translateY(-2px)'
                  }
                }}
              >
                Giriş Yap
              </Button>
            </motion.div>
          </Stack>
        </motion.div>
      </Stack>
      </Box>
      
      {/* Features Section */}
      <Box sx={{ 
        py: 8,
        position: 'relative',
        zIndex: 2,
        background: 'rgba(0, 0, 0, 0.1)',
      }}>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <Typography
            variant="h3"
            textAlign="center"
            sx={{
              color: 'white',
              fontWeight: 700,
              mb: 6,
              fontSize: { xs: '2rem', md: '2.5rem' },
              textShadow: '0 4px 20px rgba(0,0,0,0.3)',
            }}
          >
            Platform Özellikleri
          </Typography>
        </motion.div>
        
        <FeatureCards />
      </Box>
    </Box>
  );
} 