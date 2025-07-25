import React from 'react';
import { Box, Typography, Paper, Avatar, Button, Stack } from '@mui/material';
import { motion } from 'framer-motion';
import { useAuth } from './App';

const alanlar = {
  'AI': 'AI Developer',
  'Data Science': 'Data Scientist',
  'Web Development': 'Web Developer',
  'Mobile': 'Mobile Developer',
  'Cyber Security': 'Cyber Security Specialist'
};

export default function Profile({ setIsLoggedIn }) {
  const { setIsLoggedIn: setAuthLoggedIn } = useAuth();
  const username = localStorage.getItem('username');
  const interest = localStorage.getItem('interest');

  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    setIsLoggedIn(false);
    setAuthLoggedIn(false);
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
        <Box sx={{ textAlign: 'center' }}>
          <Avatar 
            sx={{ 
              width: 120, 
              height: 120, 
              mx: 'auto', 
              mb: 3, 
              bgcolor: 'rgba(255,255,255,0.1)',
              border: '3px solid rgba(255,255,255,0.2)',
              fontSize: '3rem',
              fontWeight: 700,
              color: 'white'
            }}
          >
            {username?.charAt(0)?.toUpperCase()}
          </Avatar>
          
          <Typography variant="h4" fontWeight={700} mb={1} color="white">
            {username}
          </Typography>
          
          <Typography variant="h6" mb={3} color="rgba(255,255,255,0.8)">
            {interest ? alanlar[interest] : 'Geliştirici'}
          </Typography>
          
          <Stack spacing={2}>
            <Button 
              variant="outlined" 
              color="primary" 
              fullWidth 
              onClick={handleLogout}
              sx={{
                borderColor: 'rgba(255,255,255,0.3)',
                color: 'white',
                py: 1.5,
                borderRadius: '25px',
                textTransform: 'none',
                fontWeight: 600,
                '&:hover': {
                  borderColor: 'rgba(255,255,255,0.5)',
                  background: 'rgba(255,255,255,0.1)',
                }
              }}
            >
              Çıkış Yap
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Box>
  );
} 