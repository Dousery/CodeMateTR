import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, IconButton, Menu, MenuItem, Avatar, Box, Tooltip, Stack, Button, Badge, Typography, Divider, Chip, keyframes } from '@mui/material';
import QuizIcon from '@mui/icons-material/Quiz';
import WorkIcon from '@mui/icons-material/Work';
import PsychologyIcon from '@mui/icons-material/Psychology';
import CodeIcon from '@mui/icons-material/Code';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ForumIcon from '@mui/icons-material/Forum';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import NotificationsIcon from '@mui/icons-material/Notifications';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import CommentIcon from '@mui/icons-material/Comment';
import CloseIcon from '@mui/icons-material/Close';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './App';

const menuItems = [
  { icon: <QuizIcon />, label: 'Test Çöz', route: '/test' },
  { icon: <CodeIcon />, label: 'Kodlama Odası', route: '/code' },
  { icon: <RecordVoiceOverIcon />, label: 'Otomatik Mülakat', route: '/auto-interview' },
  { icon: <WorkIcon />, label: 'Akıllı İş Bulma', route: '/smart-job-finder' },
  { icon: <ForumIcon />, label: 'Forum', route: '/forum' },
];

function CodeMateLogo({ onClick }) {
  return (
    <Box onClick={onClick} sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer', userSelect: 'none', mr: 2 }}>
      {/* Modern kod bloğu SVG */}
      <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="8" width="24" height="16" rx="4" fill="rgba(255,255,255,0.1)" />
        <rect x="8" y="12" width="16" height="8" rx="2" fill="rgba(255,255,255,0.2)" />
        <path d="M13 16L11 18L13 20" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M19 16L21 18L19 20" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <Box sx={{ fontWeight: 900, fontSize: 22, letterSpacing: 1, color: 'white', ml: 1, opacity: 1, fontFamily: 'monospace' }}>
        CodeMateTR
      </Box>
    </Box>
  );
}

export default function Header() {
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationAnchorEl, setNotificationAnchorEl] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [previousUnreadCount, setPreviousUnreadCount] = useState(0);
  const [showNotificationPulse, setShowNotificationPulse] = useState(false);
  const navigate = useNavigate();
  const { isLoggedIn } = useAuth();
  const username = isLoggedIn ? localStorage.getItem('username') : null;

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
  const handleLogout = async () => {
    try {
      // Backend'e logout isteği gönder
      await fetch('http://localhost:5000/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    // Local storage'ı temizle
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    
    // localStorage değişikliğini tetikle
    window.dispatchEvent(new Event('localStorageChange'));
    
    handleClose();
    
    // Direkt ana sayfaya yönlendir
    navigate('/', { replace: true });
  };
  const handleProfile = () => {
    handleClose();
    navigate('/profile');
  };

  // Notification fonksiyonları
  const fetchNotifications = async () => {
    if (!username) return;
    
    try {
      const response = await fetch('http://localhost:5000/forum/notifications', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        const newUnreadCount = data.notifications?.filter(n => !n.is_read).length || 0;
        
        // Yeni bildirim geldiğinde animasyon tetikle
        if (newUnreadCount > previousUnreadCount) {
          setShowNotificationPulse(true);
          setTimeout(() => setShowNotificationPulse(false), 3000); // 3 saniye sonra durdur
        }
        
        setPreviousUnreadCount(newUnreadCount);
        setNotifications(data.notifications || []);
        setUnreadCount(newUnreadCount);
      }
    } catch (error) {
      console.error('Notification fetch error:', error);
    }
  };

  const handleNotificationMenu = (event) => {
    setNotificationAnchorEl(event.currentTarget);
    // Bildirim menüsü açıldığında pulse animasyonunu durdur
    setShowNotificationPulse(false);
  };

  const handleNotificationClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleMarkAllRead = async () => {
    try {
      const response = await fetch('http://localhost:5000/forum/notifications/mark-read', {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        setUnreadCount(0);
        setPreviousUnreadCount(0);
        setShowNotificationPulse(false);
        // Tüm bildirimleri sil (geçmişi temizle)
        setNotifications([]);
        handleNotificationClose();
      }
    } catch (error) {
      console.error('Mark read error:', error);
    }
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      const response = await fetch(`http://localhost:5000/forum/notifications/${notificationId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (response.ok) {
        // Bildirimi listeden kaldır
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        // Okunmamış sayısını güncelle
        const newUnreadCount = notifications.filter(n => n.id !== notificationId && !n.is_read).length;
        setUnreadCount(newUnreadCount);
        setPreviousUnreadCount(newUnreadCount);
      }
    } catch (error) {
      console.error('Delete notification error:', error);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'solution_accepted':
        return <CheckCircleIcon sx={{ color: '#4ade80', fontSize: '1.1rem' }} />;
      case 'like':
        return <ThumbUpIcon sx={{ color: '#60a5fa', fontSize: '1.1rem' }} />;
      case 'comment':
        return <CommentIcon sx={{ color: '#fbbf24', fontSize: '1.1rem' }} />;
      default:
        return <NotificationsIcon sx={{ color: '#a3a3a3', fontSize: '1.1rem' }} />;
    }
  };

  const formatNotificationTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Az önce';
    if (diffInMinutes < 60) return `${diffInMinutes} dk önce`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} saat önce`;
    return `${Math.floor(diffInMinutes / 1440)} gün önce`;
  };

  // Animasyon keyframes
  const pulseAnimation = keyframes`
    0% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.1);
      opacity: 0.8;
    }
    100% {
      transform: scale(1);
      opacity: 1;
    }
  `;

  const glowAnimation = keyframes`
    0% {
      box-shadow: 0 0 5px rgba(255, 71, 87, 0.5);
    }
    50% {
      box-shadow: 0 0 20px rgba(255, 71, 87, 0.8), 0 0 30px rgba(255, 71, 87, 0.4);
    }
    100% {
      box-shadow: 0 0 5px rgba(255, 71, 87, 0.5);
    }
  `;

  // Notification'ları periyodik olarak güncelle
  useEffect(() => {
    if (username) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 30000); // 30 saniyede bir güncelle
      return () => clearInterval(interval);
    }
  }, [username]);

  return (
    <AppBar position="fixed" color="default" elevation={0} sx={{
      background: 'rgba(255,255,255,0.05)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(255,255,255,0.1)',
      zIndex: 1300,
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      px: { xs: 1, sm: 3 },
    }}>
      <Toolbar sx={{ minHeight: 64, display: 'flex', alignItems: 'center' }}>
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-start' }}>
          <CodeMateLogo onClick={() => navigate(username ? '/dashboard' : '/')} />
        </Box>
        
        {username && (
          <Box sx={{ flex: 2, display: 'flex', justifyContent: 'center' }}>
            <Stack direction="row" spacing={1}>
              {menuItems.map((item) => (
                <Tooltip title={item.label} key={item.label} arrow>
                  <IconButton
                    onClick={() => navigate(item.route)}
                    sx={{
                      color: 'white',
                      opacity: 0.8,
                      borderRadius: 2,
                      transition: 'all 0.3s ease',
                      mx: 0.5,
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      width: 45,
                      height: 45,
                      p: 1,
                      '&:hover': {
                        bgcolor: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        transform: 'scale(1.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                      },
                      '& .MuiSvgIcon-root': {
                        fontSize: '1.3rem'
                      }
                    }}
                    size="medium"
                  >
                    {item.icon}
                  </IconButton>
                </Tooltip>
              ))}
            </Stack>
          </Box>
        )}
        
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 1.5 }}>
          {username ? (
            <>
              {/* Notification Icon - Minimalist Design with Pulse Animation */}
              <Tooltip title={unreadCount > 0 ? `${unreadCount} yeni bildirim` : "Bildirimler"} arrow>
                <Box sx={{ position: 'relative' }}>
                  {/* Pulse Animation Indicator */}
                  {showNotificationPulse && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: '-4px',
                        right: '-6px',
                        width: '16px',
                        height: '16px',
                        borderRadius: '50%',
                        background: 'linear-gradient(45deg, #ff4757 0%, #ff3742 100%)',
                        animation: `${pulseAnimation} 1s ease-in-out infinite, ${glowAnimation} 1.5s ease-in-out infinite`,
                        zIndex: 1,
                        pointerEvents: 'none',
                      }}
                    />
                  )}
                  
                  <IconButton 
                    onClick={handleNotificationMenu} 
                    size="medium" 
                    sx={{
                      transition: 'all 0.2s ease',
                      color: 'white',
                      opacity: 0.85,
                      background: 'transparent',
                      border: 'none',
                      p: 1,
                      minWidth: 'auto',
                      position: 'relative',
                      zIndex: 2,
                      '&:hover': {
                        background: 'rgba(255,255,255,0.08)',
                        transform: 'translateY(-1px)',
                        opacity: 1,
                      },
                      '&:active': {
                        transform: 'translateY(0px)',
                      }
                    }}
                  >
                    <Badge 
                      badgeContent={unreadCount} 
                      color="error" 
                      max={99}
                      sx={{
                        '& .MuiBadge-badge': {
                          fontSize: '0.65rem',
                          height: '18px',
                          minWidth: '18px',
                          borderRadius: '9px',
                          background: 'linear-gradient(45deg, #ff4757 0%, #ff3742 100%)',
                          boxShadow: '0 2px 8px rgba(255, 71, 87, 0.4)',
                          border: '1px solid rgba(255,255,255,0.2)',
                        }
                      }}
                    >
                      <NotificationsIcon sx={{ fontSize: '1.4rem' }} />
                    </Badge>
                  </IconButton>
                </Box>
              </Tooltip>

              {/* Notification Menu - Minimalist Design */}
              <Menu 
                anchorEl={notificationAnchorEl} 
                open={Boolean(notificationAnchorEl)} 
                onClose={handleNotificationClose}
                PaperProps={{
                  sx: {
                    background: 'rgba(255,255,255,0.05)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                    maxHeight: 450,
                    width: 320,
                    mt: 1,
                    borderRadius: '16px',
                    overflow: 'hidden'
                  }
                }}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <Box sx={{ 
                  p: 2.5, 
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.01) 100%)'
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" sx={{ 
                      color: 'white', 
                      fontWeight: 500,
                      fontSize: '1.1rem',
                      letterSpacing: '0.5px'
                    }}>
                      Bildirimler
                    </Typography>
                    {unreadCount > 0 && (
                      <Chip 
                        label={`${unreadCount} yeni`} 
                        size="small" 
                        sx={{ 
                          fontSize: '0.65rem',
                          height: '20px',
                          background: 'linear-gradient(45deg, #ff4757 0%, #ff3742 100%)',
                          color: 'white',
                          fontWeight: 500,
                          '& .MuiChip-label': {
                            px: 1
                          }
                        }}
                      />
                    )}
                  </Box>
                </Box>
                
                {notifications.length === 0 ? (
                  <Box sx={{ p: 4, textAlign: 'center' }}>
                    <NotificationsIcon sx={{ 
                      fontSize: '2.5rem', 
                      color: 'rgba(255,255,255,0.3)', 
                      mb: 1 
                    }} />
                    <Typography sx={{ 
                      color: 'rgba(255,255,255,0.5)',
                      fontSize: '0.9rem',
                      fontWeight: 400
                    }}>
                      Henüz bildiriminiz yok
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ maxHeight: 320, overflow: 'auto' }}>
                    {notifications.slice(0, 8).map((notification, index) => (
                      <MenuItem 
                        key={notification.id} 
                        sx={{ 
                          display: 'flex', 
                          alignItems: 'flex-start', 
                          gap: 2, 
                          p: 2.5,
                          borderBottom: index < notifications.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                          background: notification.is_read ? 'transparent' : 'rgba(255,255,255,0.03)',
                          transition: 'all 0.2s ease',
                          position: 'relative',
                          '&:hover': {
                            background: 'rgba(255,255,255,0.06)',
                            transform: 'translateX(2px)',
                            '& .delete-button': {
                              opacity: 1,
                            }
                          },
                          '&:first-of-type': {
                            borderTop: 'none'
                          }
                        }}
                      >
                        <Box sx={{ 
                          mt: 0.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: 32,
                          height: 32,
                          borderRadius: '8px',
                          background: notification.is_read ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.08)',
                          flexShrink: 0
                        }}>
                          {getNotificationIcon(notification.notification_type)}
                        </Box>
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              color: 'white', 
                              fontWeight: notification.is_read ? 400 : 500,
                              mb: 0.5,
                              lineHeight: 1.4,
                              fontSize: '0.85rem'
                            }}
                          >
                            {notification.title}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              color: 'rgba(255,255,255,0.6)', 
                              display: 'block',
                              lineHeight: 1.3,
                              fontSize: '0.75rem'
                            }}
                          >
                            {notification.message}
                          </Typography>
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              color: 'rgba(255,255,255,0.4)', 
                              display: 'block',
                              mt: 0.5,
                              fontSize: '0.7rem',
                              fontWeight: 400
                            }}
                          >
                            {formatNotificationTime(notification.created_at)}
                          </Typography>
                        </Box>
                        
                        {/* Delete Button */}
                        <IconButton
                          className="delete-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteNotification(notification.id);
                          }}
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: '8px',
                            right: '8px',
                            opacity: 0,
                            transition: 'all 0.2s ease',
                            color: 'rgba(255,255,255,0.5)',
                            background: 'rgba(255,255,255,0.05)',
                            width: '24px',
                            height: '24px',
                            '&:hover': {
                              background: 'rgba(255,255,255,0.1)',
                              color: 'rgba(255,255,255,0.8)',
                              transform: 'scale(1.1)',
                            }
                          }}
                        >
                          <CloseIcon sx={{ fontSize: '0.9rem' }} />
                        </IconButton>
                      </MenuItem>
                    ))}
                  </Box>
                )}
                
                {unreadCount > 0 && (
                  <>
                    <Divider sx={{ 
                      borderColor: 'rgba(255,255,255,0.06)',
                      mx: 2
                    }} />
                    <MenuItem 
                      onClick={handleMarkAllRead}
                      sx={{ 
                        color: 'rgba(255,255,255,0.7)',
                        fontSize: '0.8rem',
                        fontWeight: 500,
                        py: 1.5,
                        px: 2.5,
                        textAlign: 'center',
                        '&:hover': {
                          background: 'rgba(255,255,255,0.04)',
                          color: 'rgba(255,255,255,0.9)',
                        }
                      }}
                    >
                      Tüm bildirimleri temizle
                    </MenuItem>
                  </>
                )}
              </Menu>

              {/* Profile Icon - Minimalist Design */}
              <IconButton onClick={handleMenu} size="medium" sx={{
                transition: 'all 0.2s ease',
                boxShadow: 'none',
                border: 'none',
                outline: 'none',
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                p: 1,
                minWidth: 'auto',
                '&:focus': { outline: 'none', boxShadow: 'none' },
                '&:active': { outline: 'none', boxShadow: 'none' },
                '&:hover': {
                  boxShadow: '0 4px 15px rgba(79, 70, 229, 0.3)',
                  transform: 'translateY(-1px)',
                  background: 'linear-gradient(135deg, #4338ca 0%, #6d28d9 100%)',
                }
              }}>
                <Avatar sx={{ 
                  bgcolor: 'transparent', 
                  color: 'white', 
                  width: 32, 
                  height: 32, 
                  boxShadow: 'none', 
                  border: 'none'
                }}>
                  <AccountCircleIcon sx={{ fontSize: '1.3rem' }} />
                </Avatar>
              </IconButton>
              <Menu 
                anchorEl={anchorEl} 
                open={Boolean(anchorEl)} 
                onClose={handleClose}
                PaperProps={{
                  sx: {
                    background: 'rgba(255,255,255,0.05)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    '& .MuiMenuItem-root': {
                      color: 'white',
                      '&:hover': {
                        background: 'rgba(255,255,255,0.1)',
                      }
                    }
                  }
                }}
              >
                <MenuItem disabled sx={{ color: 'rgba(255,255,255,0.6)' }}>Profil: <b style={{ marginLeft: 8, color: 'white' }}>{username}</b></MenuItem>
                <MenuItem onClick={handleProfile}>Profilimi Gör</MenuItem>
                <MenuItem onClick={handleLogout}>Çıkış Yap</MenuItem>
              </Menu>
            </>
          ) : (
            <Stack direction="row" spacing={2}>
              <Button 
                variant="outlined" 
                size="small"
                onClick={() => navigate('/login')}
                sx={{
                  borderColor: 'rgba(255,255,255,0.3)',
                  color: 'white',
                  borderRadius: '20px',
                  px: 2,
                  py: 0.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.5)',
                    background: 'rgba(255,255,255,0.1)',
                  }
                }}
              >
                Giriş Yap
              </Button>
              <Button 
                variant="contained" 
                size="small"
                onClick={() => navigate('/register')}
                sx={{
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  borderRadius: '20px',
                  px: 2,
                  py: 0.5,
                  textTransform: 'none',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  boxShadow: '0 2px 8px rgba(79, 70, 229, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                    boxShadow: '0 4px 12px rgba(79, 70, 229, 0.5)',
                  }
                }}
              >
                Kayıt Ol
              </Button>
            </Stack>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
} 