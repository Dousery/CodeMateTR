import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Avatar, Stack, Grid, 
  CircularProgress, LinearProgress, Chip, List, ListItem, ListItemText,
  ListItemIcon, Divider, Badge
} from '@mui/material';
import { motion } from 'framer-motion';
import { useAuth } from './App';
import QuizIcon from '@mui/icons-material/Quiz';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ForumIcon from '@mui/icons-material/Forum';
import WorkIcon from '@mui/icons-material/Work';
import StarIcon from '@mui/icons-material/Star';
import CommentIcon from '@mui/icons-material/Comment';
import CodeIcon from '@mui/icons-material/Code';
import axios from 'axios';

const alanlar = {
  'AI': 'AI Developer',
  'Data Science': 'Data Scientist',
  'Web Development': 'Web Developer',
  'Mobile': 'Mobile Developer',
  'Cyber Security': 'Cyber Security Specialist'
};

export default function Profile({ setIsLoggedIn }) {
  const { setIsLoggedIn: setAuthLoggedIn } = useAuth();
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const username = localStorage.getItem('username');
  const interest = localStorage.getItem('interest');

  useEffect(() => {
    fetchUserStats();
  }, []);

  const fetchUserStats = async () => {
    try {
      const response = await axios.get('http://localhost:5000/profile', {
        withCredentials: true
      });
      setUserStats(response.data);
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    setIsLoggedIn(false);
    setAuthLoggedIn(false);
  };

  const getSkillColor = (level) => {
    switch (level) {
      case 'İleri': return '#4caf50';
      case 'Orta': return '#ff9800';
      case 'Gelişen': return '#2196f3';
      default: return '#9e9e9e';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    if (score >= 40) return '#2196f3';
    return '#f44336';
  };

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress sx={{ color: 'white' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', py: 10, px: 2, display: 'flex', justifyContent: 'center', alignItems: 'flex-start' }}>
      <Box sx={{ maxWidth: "700px", width: '70%', ml: 4 }}>
        <Grid container spacing={2}>
          
          {/* Birleşik Profil ve İstatistik Kartı */}
          <Grid item xs={12}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 30 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.6 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 2, borderRadius: 4 }}
            >
              {/* Profil Bölümü */}
              <Box sx={{ textAlign: 'center', mb: 2.5, pb: 1.5, borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <Avatar 
                  sx={{ 
                    width: 60, 
                    height: 60, 
                    mx: 'auto', 
                    mb: 1, 
                    bgcolor: 'rgba(79, 70, 229, 0.8)',
                    border: '3px solid rgba(255,255,255,0.2)',
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    color: 'white',
                    boxShadow: '0 6px 24px rgba(79, 70, 229, 0.3)'
                  }}
                >
                  {username?.charAt(0)?.toUpperCase()}
                </Avatar>
                
                <Typography variant="h6" fontWeight={700} mb={0.5} color="white">
                  {username}
                </Typography>
                
                <Chip 
                  label={interest ? alanlar[interest] : 'Geliştirici'}
                  sx={{ 
                    bgcolor: 'rgba(79, 70, 229, 0.3)',
                    color: 'white',
                    fontWeight: 600,
                    fontSize: '0.8rem',
                    px: 1,
                    py: 0.25
                  }}
                />
              </Box>

              {/* İstatistikler Bölümü */}
              <Box>
                <Typography variant="h5" fontWeight={700} color="white" mb={3}>
                  İstatistikler
                </Typography>
                
                <Grid container spacing={2}>
                  
                  {/* Test İstatistikleri */}
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ 
                      p: 2, 
                      borderRadius: 3, 
                      bgcolor: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      textAlign: 'center'
                    }}>
                      <QuizIcon sx={{ color: '#4caf50', fontSize: 35, mb: 1 }} />
                      <Typography variant="h4" fontWeight={700} color="white" mb={0.5}>
                        {userStats?.stats?.total_tests || 0}
                      </Typography>
                      <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={1}>
                        Tamamlanan Test
                      </Typography>
                      
                      {userStats?.stats?.total_tests > 0 && (
                        <Box>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                            <Typography variant="caption" color="rgba(255,255,255,0.7)">
                              Ortalama
                            </Typography>
                            <Typography variant="caption" fontWeight={600} color={getScoreColor(userStats.stats.average_score)}>
                              {userStats.stats.average_score}%
                            </Typography>
                          </Box>
                          <LinearProgress 
                            variant="determinate" 
                            value={userStats.stats.average_score} 
                            sx={{
                              height: 6,
                              borderRadius: 3,
                              backgroundColor: 'rgba(255,255,255,0.1)',
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: getScoreColor(userStats.stats.average_score),
                                borderRadius: 3
                              }
                            }}
                          />
                        </Box>
                      )}
                    </Box>
                  </Grid>

                  {/* Forum Aktivitesi */}
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ 
                      p: 2, 
                      borderRadius: 3, 
                      bgcolor: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      textAlign: 'center'
                    }}>
                      <ForumIcon sx={{ color: '#ff9800', fontSize: 35, mb: 1 }} />
                      <Typography variant="h4" fontWeight={700} color="white" mb={0.5}>
                        {(userStats?.stats?.forum_posts || 0) + (userStats?.stats?.forum_comments || 0)}
                      </Typography>
                      <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={1}>
                        Forum Aktivitesi
                      </Typography>

                      <Stack direction="row" spacing={1} justifyContent="center">
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="body2" color="#4caf50" fontWeight={600} mr={0.5}>
                            {userStats?.stats?.forum_posts || 0}
                          </Typography>
                          <Typography variant="caption" color="rgba(255,255,255,0.7)">
                            Gönderi
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <CommentIcon sx={{ color: '#2196f3', fontSize: 16, mr: 0.5 }} />
                          <Typography variant="body2" color="#2196f3" fontWeight={600} mr={0.5}>
                            {userStats?.stats?.forum_comments || 0}
                          </Typography>
                          <Typography variant="caption" color="rgba(255,255,255,0.7)">
                            Yorum
                          </Typography>
                        </Box>
                      </Stack>
                    </Box>
                  </Grid>

                  {/* Kodlama Oturumu */}
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ 
                      p: 2, 
                      borderRadius: 3, 
                      bgcolor: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      textAlign: 'center'
                    }}>
                      <CodeIcon sx={{ color: '#00e676', fontSize: 35, mb: 1 }} />
                      <Typography variant="h4" fontWeight={700} color="white" mb={0.5}>
                        {userStats?.stats?.total_code_sessions || 0}
                      </Typography>
                      <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={1}>
                        Kodlama Oturumu
                      </Typography>

                      {userStats?.stats?.code_trend?.length > 0 && (
                        <Chip 
                          label={`+${userStats.stats.code_trend.length} aktivite`}
                          size="small"
                          sx={{ 
                            bgcolor: 'rgba(0, 230, 118, 0.3)',
                            color: '#00e676',
                            fontWeight: 600,
                            fontSize: '0.75rem'
                          }}
                        />
                      )}
                    </Box>
                  </Grid>

                  {/* CV Durumu */}
                  <Grid item xs={12} sm={6} md={4}>
                    <Box sx={{ 
                      p: 2, 
                      borderRadius: 3, 
                      bgcolor: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      textAlign: 'center'
                    }}>
                      <WorkIcon sx={{ color: userStats?.stats?.has_cv ? '#4caf50' : '#f44336', fontSize: 35, mb: 1 }} />
                      <Typography variant="h6" fontWeight={700} color="white" mb={0.5}>
                        CV Analizi
                      </Typography>
                      <Chip 
                        label={userStats?.stats?.has_cv ? 'Yüklenmiş' : 'Yüklenmemiş'}
                        size="small"
                        sx={{ 
                          bgcolor: userStats?.stats?.has_cv ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)',
                          color: userStats?.stats?.has_cv ? '#4caf50' : '#f44336',
                          fontWeight: 600
                        }}
                      />
                    </Box>
                  </Grid>

                </Grid>
              </Box>

              {/* Günlük Aktivite Serisi */}
              <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <Typography variant="h6" fontWeight={700} color="white" mb={2}>
                  Günlük Aktivite Serisi
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: 120, px: 1 }}>
                  {userStats?.stats?.daily_activity ? (
                    userStats.stats.daily_activity.slice().reverse().map((day, index) => {
                      const height = day.total_activity > 0 ? Math.max(20, day.total_activity * 15) : 5;
                      return (
                        <Box key={index} sx={{ textAlign: 'center', flex: 1, mx: 0.5 }}>
                          <Box
                            sx={{
                              height: height,
                              minHeight: 5,
                              bgcolor: day.total_activity > 0 ? 'rgba(79, 70, 229, 0.8)' : 'rgba(255,255,255,0.1)',
                              borderRadius: '4px 4px 0 0',
                              mb: 1,
                              transition: 'all 0.3s ease',
                              cursor: 'pointer',
                              '&:hover': {
                                bgcolor: day.total_activity > 0 ? 'rgba(79, 70, 229, 1)' : 'rgba(255,255,255,0.2)',
                                transform: 'scaleY(1.1)'
                              }
                            }}
                          />
                          <Typography variant="caption" color="rgba(255,255,255,0.7)" sx={{ fontSize: '0.7rem' }}>
                            {day.day_name}
                          </Typography>
                          <Typography variant="caption" color="white" fontWeight={600} sx={{ fontSize: '0.6rem', display: 'block' }}>
                            {day.total_activity}
                          </Typography>
                        </Box>
                      );
                    })
                  ) : (
                    // Placeholder bars when no data
                    Array.from({ length: 7 }, (_, index) => {
                      const days = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'];
                      return (
                        <Box key={index} sx={{ textAlign: 'center', flex: 1, mx: 0.5 }}>
                          <Box
                            sx={{
                              height: 5,
                              bgcolor: 'rgba(255,255,255,0.1)',
                              borderRadius: '4px 4px 0 0',
                              mb: 1
                            }}
                          />
                          <Typography variant="caption" color="rgba(255,255,255,0.5)" sx={{ fontSize: '0.7rem' }}>
                            {days[index]}
                          </Typography>
                          <Typography variant="caption" color="rgba(255,255,255,0.5)" sx={{ fontSize: '0.6rem', display: 'block' }}>
                            0
                          </Typography>
                        </Box>
                      );
                    })
                  )}
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, px: 1 }}>
                  <Typography variant="caption" color="rgba(255,255,255,0.6)">
                    Düşük Aktivite
                  </Typography>
                  <Typography variant="caption" color="rgba(255,255,255,0.6)">
                    Yüksek Aktivite
                  </Typography>
                </Box>
              </Box>
            </Paper>
          </Grid>

        {/* Son Test Sonuçları */}
        {userStats?.stats?.test_trend && userStats.stats.test_trend.length > 0 && (
          <Grid item xs={12}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 30 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.6, delay: 0.5 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 3, borderRadius: 4 }}
            >
              <Typography variant="h5" fontWeight={700} color="white" mb={2}>
                <TrendingUpIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
                Son Test Performansları
              </Typography>
              
              <List sx={{ py: 0 }}>
                {userStats.stats.test_trend.map((test, index) => (
                  <Box key={index}>
                    <ListItem 
                      component={motion.div}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + (index * 0.1) }}
                      sx={{ py: 1 }}
                    >
                      <ListItemIcon>
                        <QuizIcon sx={{ color: getScoreColor(test.score) }} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography color="white" fontWeight={600}>
                              {alanlar[test.interest] || test.interest}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                              <Typography variant="body2" color="rgba(255,255,255,0.7)">
                                {test.date}
                              </Typography>
                              <Chip 
                                label={`${test.score}%`}
                                size="small"
                                sx={{ 
                                  bgcolor: `${getScoreColor(test.score)}20`,
                                  color: getScoreColor(test.score),
                                  fontWeight: 700
                                }}
                              />
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < userStats.stats.test_trend.length - 1 && (
                      <Divider sx={{ bgcolor: 'rgba(255,255,255,0.1)' }} />
                    )}
                  </Box>
                ))}
              </List>
            </Paper>
          </Grid>
        )}

        </Grid>
      </Box>
    </Box>
  );
} 