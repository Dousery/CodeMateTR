import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Stepper, Step, StepLabel, StepContent, Chip } from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('http://localhost:5000/user_history', { withCredentials: true });
      setHistory(res.data.history || []);
    } catch (err) {
      console.error('History alınamadı:', err);
    } finally {
      setLoading(false);
    }
  };

  const getModuleColor = (module) => {
    const colors = {
      'Test': '#1976d2',
      'Case Study': '#dc004e',
      'Code': '#2e7d32',
      'Interview': '#ed6c02'
    };
    return colors[module] || '#666';
  };

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="white">Yükleniyor...</Typography>
      </Box>
    );
  }

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
        <Typography variant="h4" fontWeight={700} mb={4} color="white" textAlign="center">Geçmiş Aktiviteler</Typography>
        
        {history.length === 0 ? (
          <Typography textAlign="center" color="rgba(255,255,255,0.8)">
            Henüz aktivite bulunmuyor. Modülleri kullanmaya başlayın!
          </Typography>
        ) : (
          <Stepper orientation="vertical">
            {history.map((item, index) => (
              <Step key={index} active={true}>
                <StepLabel 
                  sx={{ 
                    '& .MuiStepLabel-label': { 
                      color: 'white',
                      fontWeight: 600
                    },
                    '& .MuiStepLabel-iconContainer': {
                      color: getModuleColor(item.module)
                    }
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography color="white" variant="h6">
                      {item.module}
                    </Typography>
                    <Chip 
                      label={item.score ? `${item.score}/100` : 'Tamamlandı'} 
                      size="small" 
                      sx={{ 
                        bgcolor: getModuleColor(item.module),
                        color: 'white',
                        fontWeight: 600
                      }} 
                    />
                  </Box>
                </StepLabel>
                <StepContent>
                  <Typography color="rgba(255,255,255,0.8)" mb={1}>
                    {new Date(item.timestamp).toLocaleString('tr-TR')}
                  </Typography>
                  {item.feedback && (
                    <Typography color="rgba(255,255,255,0.7)" variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {item.feedback}
                    </Typography>
                  )}
                </StepContent>
              </Step>
            ))}
          </Stepper>
        )}
      </Paper>
    </Box>
  );
} 