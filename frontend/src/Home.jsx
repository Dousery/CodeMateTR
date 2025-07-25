import React from 'react';
import { Button, Box, Typography, Stack } from '@mui/material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

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
      position: 'fixed', 
      top: '64px', 
      left: 0, 
      width: '100vw', 
      height: 'calc(100vh - 64px)', 
      overflow: 'hidden',
    }}>
      <AnimatedGradient />
      <FloatingParticles />
      
      <Stack
        component={motion.div}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
        spacing={4}
        alignItems="center"
        justifyContent="center"
        sx={{
          position: 'relative',
          zIndex: 2,
          minHeight: 'calc(100vh - 64px)',
          width: '100vw',
          color: 'white',
        }}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          <Typography 
            variant="h2" 
            fontWeight={700} 
            textAlign="center" 
            gutterBottom 
            sx={{ 
              fontSize: { xs: '2.2rem', md: '3.5rem' },
              textShadow: '0 4px 20px rgba(0,0,0,0.3)',
              background: 'linear-gradient(45deg, #fff, #e0e0e0)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Developer Eğitim Platformu
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
        >
          <Typography 
            variant="h5" 
            textAlign="center" 
            maxWidth={600}
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              textShadow: '0 2px 10px rgba(0,0,0,0.2)'
            }}
          >
            Testler, case study'ler, kodlama ve mülakat simülasyonları ile kendini geliştir. Modern, şık ve interaktif bir deneyim seni bekliyor!
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
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
  );
} 