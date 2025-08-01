import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Avatar, Button, Stack, Grid, Card, CardContent, 
  CircularProgress, LinearProgress, Chip, List, ListItem, ListItemText,
  ListItemIcon, Divider, Badge, Tooltip
} from '@mui/material';
import { motion } from 'framer-motion';
import { useAuth } from './App';
import QuizIcon from '@mui/icons-material/Quiz';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ForumIcon from '@mui/icons-material/Forum';
import WorkIcon from '@mui/icons-material/Work';
import StarIcon from '@mui/icons-material/Star';
import CommentIcon from '@mui/icons-material/Comment';
import PsychologyIcon from '@mui/icons-material/Psychology';
import CodeIcon from '@mui/icons-material/Code';
import TrophyIcon from '@mui/icons-material/EmojiEvents';
import FlagIcon from '@mui/icons-material/Flag';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
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

  const getAchievementIcon = (iconName) => {
    const icons = {
      'quiz': <QuizIcon />,
      'star': <StarIcon />,
      'flag': <FlagIcon />,
      'forum': <ForumIcon />,
      'trophy': <TrophyIcon />,
      'work': <WorkIcon />,
      'code': <CodeIcon />,
      'psychology': <PsychologyIcon />
    };
    return icons[iconName] || <StarIcon />;
  };

  const getActivityIntensity = (count) => {
    if (count === 0) return 'rgba(255,255,255,0.1)';
    if (count <= 2) return 'rgba(79, 70, 229, 0.3)';
    if (count <= 4) return 'rgba(79, 70, 229, 0.6)';
    return 'rgba(79, 70, 229, 0.9)';
  };

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress sx={{ color: 'white' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', py: 4, px: 2 }}>
      <Grid container spacing={3} maxWidth="1400px" mx="auto">
        
        {/* Profil Kartı */}
        <Grid item xs={12} md={4}>
          <Paper 
            component={motion.div} 
            initial={{ opacity: 0, x: -50 }} 
            animate={{ opacity: 1, x: 0 }} 
            transition={{ duration: 0.6 }} 
            elevation={8} 
            className="glass-card"
            sx={{ p: 4, borderRadius: 4, height: 'fit-content' }}
          >
            <Box sx={{ textAlign: 'center' }}>
              <Avatar 
                sx={{ 
                  width: 120, 
                  height: 120, 
                  mx: 'auto', 
                  mb: 3, 
                  bgcolor: 'rgba(79, 70, 229, 0.8)',
                  border: '4px solid rgba(255,255,255,0.2)',
                  fontSize: '3rem',
                  fontWeight: 700,
                  color: 'white',
                  boxShadow: '0 8px 32px rgba(79, 70, 229, 0.3)'
                }}
              >
                {username?.charAt(0)?.toUpperCase()}
              </Avatar>
              
              <Typography variant="h4" fontWeight={700} mb={1} color="white">
                {username}
              </Typography>
              
              <Chip 
                label={interest ? alanlar[interest] : 'Geliştirici'}
                sx={{ 
                  mb: 3,
                  bgcolor: 'rgba(79, 70, 229, 0.3)',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '1rem',
                  px: 2,
                  py: 0.5
                }}
              />

              {userStats?.stats && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="h6" color="white" mb={1}>
                    Beceri Seviyesi
                  </Typography>
                  <Chip 
                    icon={<StarIcon />}
                    label={userStats.stats.skill_level}
                    sx={{ 
                      bgcolor: getSkillColor(userStats.stats.skill_level),
                      color: 'white',
                      fontWeight: 600,
                      fontSize: '1rem'
                    }}
                  />
                </Box>
              )}
              
              <Button 
                variant="outlined" 
                color="error" 
                fullWidth 
                onClick={handleLogout}
                sx={{
                  borderColor: 'rgba(244, 67, 54, 0.5)',
                  color: '#f44336',
                  py: 1.5,
                  borderRadius: '25px',
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#f44336',
                    background: 'rgba(244, 67, 54, 0.1)',
                  }
                }}
              >
                Çıkış Yap
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* İstatistik Kartları */}
        <Grid item xs={12} md={8}>
          <Grid container spacing={3}>
            
            {/* Test İstatistikleri */}
            <Grid item xs={12} sm={6}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.6, delay: 0.1 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <QuizIcon sx={{ color: '#4caf50', fontSize: 40, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="white">
                      {userStats?.stats?.total_tests || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Tamamlanan Test
                    </Typography>
                  </Box>
                </Box>
                
                {userStats?.stats?.total_tests > 0 && (
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="rgba(255,255,255,0.7)">
                        Ortalama Score
                      </Typography>
                      <Typography variant="body2" fontWeight={600} color={getScoreColor(userStats.stats.average_score)}>
                        {userStats.stats.average_score}%
                      </Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={userStats.stats.average_score} 
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: 'rgba(255,255,255,0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: getScoreColor(userStats.stats.average_score),
                          borderRadius: 4
                        }
                      }}
                    />
                  </Box>
                )}
              </Paper>
            </Grid>

            {/* Forum Aktivitesi */}
            <Grid item xs={12} sm={6}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.6, delay: 0.2 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ForumIcon sx={{ color: '#ff9800', fontSize: 40, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="white">
                      {(userStats?.stats?.forum_posts || 0) + (userStats?.stats?.forum_comments || 0)}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Forum Aktivitesi
                    </Typography>
                  </Box>
                </Box>

                <Stack direction="row" spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="h6" color="#4caf50" mr={1}>
                      {userStats?.stats?.forum_posts || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Gönderi
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <CommentIcon sx={{ color: '#2196f3', fontSize: 20, mr: 1 }} />
                    <Typography variant="h6" color="#2196f3" mr={1}>
                      {userStats?.stats?.forum_comments || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Yorum
                    </Typography>
                  </Box>
                </Stack>
              </Paper>
            </Grid>

            {/* Kodlama Odası */}
            <Grid item xs={12} sm={6}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.6, delay: 0.25 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CodeIcon sx={{ color: '#00e676', fontSize: 40, mr: 2 }} />
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="white">
                      {userStats?.stats?.total_code_sessions || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Kodlama Oturumu
                    </Typography>
                  </Box>
                </Box>

                <Stack direction="row" spacing={2} alignItems="center">
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PsychologyIcon sx={{ color: '#ff9800', fontSize: 20, mr: 1 }} />
                    <Typography variant="h6" color="#ff9800" mr={1}>
                      {userStats?.stats?.total_code_points || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Puan
                    </Typography>
                  </Box>
                  {userStats?.stats?.code_trend?.length > 0 && (
                    <Chip 
                      label={`+${userStats.stats.code_trend.length} aktivite`}
                      size="small"
                      sx={{ 
                        bgcolor: 'rgba(0, 230, 118, 0.3)',
                        color: '#00e676',
                        fontWeight: 600
                      }}
                    />
                  )}
                </Stack>
              </Paper>
            </Grid>

            {/* CV Durumu */}
            <Grid item xs={12} sm={6}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.6, delay: 0.3 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <WorkIcon sx={{ color: userStats?.stats?.has_cv ? '#4caf50' : '#f44336', fontSize: 40, mr: 2 }} />
                  <Box>
                    <Typography variant="h6" fontWeight={700} color="white">
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
                </Box>
              </Paper>
            </Grid>

            {/* Forum Puanları */}
            <Grid item xs={12} sm={6}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.6, delay: 0.4 }} 
                elevation={8} 
                className="glass-card"
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Badge 
                    badgeContent={userStats?.stats?.forum_points || 0} 
                    color="primary"
                    sx={{ 
                      '& .MuiBadge-badge': { 
                        bgcolor: '#ff9800',
                        color: 'white',
                        fontWeight: 700
                      }
                    }}
                  >
                    <TrendingUpIcon sx={{ color: '#ff9800', fontSize: 40, mr: 2 }} />
                  </Badge>
                  <Box>
                    <Typography variant="h4" fontWeight={700} color="white">
                      {userStats?.stats?.forum_points || 0}
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.7)">
                      Forum Puanı
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>

          </Grid>
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
              sx={{ p: 4, borderRadius: 4 }}
            >
              <Typography variant="h5" fontWeight={700} color="white" mb={3}>
                <TrendingUpIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
                Son Test Performansları
              </Typography>
              
              <List>
                {userStats.stats.test_trend.map((test, index) => (
                  <Box key={index}>
                    <ListItem 
                      component={motion.div}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + (index * 0.1) }}
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

        {/* Başarı Rozetleri */}
        {userStats?.stats?.achievements && userStats.stats.achievements.length > 0 && (
          <Grid item xs={12} md={6}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 30 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.6, delay: 0.6 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 4, borderRadius: 4 }}
            >
              <Typography variant="h5" fontWeight={700} color="white" mb={3}>
                <TrophyIcon sx={{ mr: 2, verticalAlign: 'middle', color: '#ffd700' }} />
                Başarı Rozetleri
              </Typography>
              
              <Grid container spacing={2}>
                {userStats.stats.achievements.map((achievement, index) => (
                  <Grid item xs={6} sm={4} key={index}>
                    <Tooltip title={achievement.description} arrow>
                      <Paper
                        component={motion.div}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.7 + (index * 0.1) }}
                        sx={{
                          p: 2,
                          textAlign: 'center',
                          bgcolor: 'rgba(79, 70, 229, 0.2)',
                          border: '1px solid rgba(79, 70, 229, 0.3)',
                          borderRadius: 3,
                          cursor: 'pointer',
                          '&:hover': {
                            bgcolor: 'rgba(79, 70, 229, 0.3)',
                            transform: 'scale(1.05)'
                          },
                          transition: 'all 0.3s ease'
                        }}
                      >
                        <Box sx={{ color: '#ffd700', mb: 1 }}>
                          {getAchievementIcon(achievement.icon)}
                        </Box>
                        <Typography variant="caption" color="white" fontWeight={600}>
                          {achievement.name}
                        </Typography>
                      </Paper>
                    </Tooltip>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
        )}

        {/* Günlük Aktivite */}
        {userStats?.stats?.daily_activity && (
          <Grid item xs={12} md={6}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 30 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.6, delay: 0.7 }} 
              elevation={8} 
              className="glass-card"
              sx={{ p: 4, borderRadius: 4 }}
            >
              <Typography variant="h5" fontWeight={700} color="white" mb={3}>
                <CalendarTodayIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
                Son 7 Günün Aktivitesi
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                {userStats.stats.daily_activity.slice().reverse().map((day, index) => (
                  <Tooltip 
                    key={index}
                    title={`${day.date}: ${day.total_activity} aktivite (${day.tests} test, ${day.forum_activity} forum, ${day.code_activity || 0} kod)`}
                    arrow
                  >
                    <Box sx={{ textAlign: 'center' }}>
                      <Box
                        sx={{
                          width: 40,
                          height: 40,
                          bgcolor: getActivityIntensity(day.total_activity),
                          borderRadius: 2,
                          mb: 1,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          border: '1px solid rgba(255,255,255,0.2)',
                          cursor: 'pointer',
                          '&:hover': {
                            transform: 'scale(1.1)',
                            boxShadow: '0 4px 12px rgba(79, 70, 229, 0.4)'
                          },
                          transition: 'all 0.3s ease'
                        }}
                      >
                        <Typography variant="caption" color="white" fontWeight={700}>
                          {day.total_activity}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="rgba(255,255,255,0.7)">
                        {day.day_name}
                      </Typography>
                    </Box>
                  </Tooltip>
                ))}
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 3 }}>
                <Typography variant="caption" color="rgba(255,255,255,0.6)">
                  Az
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {[0, 1, 3, 5].map((level, idx) => (
                    <Box
                      key={idx}
                      sx={{
                        width: 12,
                        height: 12,
                        bgcolor: getActivityIntensity(level),
                        borderRadius: 1,
                        border: '1px solid rgba(255,255,255,0.2)'
                      }}
                    />
                  ))}
                </Box>
                <Typography variant="caption" color="rgba(255,255,255,0.6)">
                  Çok
                </Typography>
              </Box>
            </Paper>
          </Grid>
        )}

      </Grid>
    </Box>
  );
} 