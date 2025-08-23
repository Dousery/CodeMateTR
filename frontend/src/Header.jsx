import React, { useState, useEffect } from 'react';
import { AppBar, Toolbar, IconButton, Menu, MenuItem, Avatar, Box, Tooltip, Stack, Button, Badge, Typography, Divider, Chip, keyframes, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Alert } from '@mui/material';
import API_ENDPOINTS from './config.js';
import QuizIcon from '@mui/icons-material/Quiz';

import PsychologyIcon from '@mui/icons-material/Psychology';
import CodeIcon from '@mui/icons-material/Code';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ForumIcon from '@mui/icons-material/Forum';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import NotificationsIcon from '@mui/icons-material/Notifications';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import CommentIcon from '@mui/icons-material/Comment';
import CloseIcon from '@mui/icons-material/Close';
import LockIcon from '@mui/icons-material/Lock';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './App';

const menuItems = [
  { icon: <QuizIcon />, label: 'Test Çöz', route: '/test' },
  { icon: <CodeIcon />, label: 'Kodlama Odası', route: '/code' },
  { icon: <RecordVoiceOverIcon />, label: 'Otomatik Mülakat', route: '/auto-interview' },
  { icon: <ForumIcon />, label: 'Forum', route: '/forum' },
];

// Admin için ek menü öğeleri
const adminMenuItems = [
  { icon: <AdminPanelSettingsIcon />, label: 'Admin Paneli', route: '/admin' },
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
  const [passwordChangeDialogOpen, setPasswordChangeDialogOpen] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordChangeError, setPasswordChangeError] = useState('');
  const [passwordChangeSuccess, setPasswordChangeSuccess] = useState('');
  const [isPasswordChanging, setIsPasswordChanging] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

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
      await fetch(API_ENDPOINTS.LOGOUT, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    // Local storage'ı temizle
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    localStorage.removeItem('geminiApiKey');
    
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

  const handlePasswordChangeDialogOpen = () => {
    setPasswordChangeDialogOpen(true);
    setNewPassword('');
    setConfirmNewPassword('');
    setPasswordChangeError('');
    setPasswordChangeSuccess('');
    setIsPasswordChanging(false);
  };

  const handlePasswordChangeDialogClose = () => {
    setPasswordChangeDialogOpen(false);
  };

  const handlePasswordChange = async () => {
    if (newPassword !== confirmNewPassword) {
      setPasswordChangeError('Şifreler eşleşmiyor.');
      return;
    }

    if (newPassword.length < 6) {
      setPasswordChangeError('Şifre en az 6 karakter olmalıdır.');
      return;
    }

    setIsPasswordChanging(true);
    setPasswordChangeError('');
    setPasswordChangeSuccess('');

    try {
      const response = await fetch(API_ENDPOINTS.CHANGE_PASSWORD, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (response.ok) {
        setPasswordChangeSuccess('Şifreniz başarıyla değiştirildi.');
        // 2 saniye sonra modal'ı kapat
        setTimeout(() => {
          handlePasswordChangeDialogClose();
        }, 2000);
      } else {
        const errorData = await response.json();
        setPasswordChangeError(errorData.error || 'Şifre değiştirme hatası.');
      }
    } catch (error) {
      console.error('Password change error:', error);
      setPasswordChangeError('Şifre değiştirme sırasında bir hata oluştu.');
    } finally {
      setIsPasswordChanging(false);
    }
  };

  // Notification fonksiyonları
  const fetchNotifications = async () => {
    if (!username) return;
    
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_NOTIFICATIONS, {
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

  // Admin kontrolü
  useEffect(() => {
    const checkAdminStatus = async () => {
      if (!username) return;
      
      try {
        const response = await fetch(`${API_ENDPOINTS.BASE_URL}/profile`, {
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          setIsAdmin(data.is_admin || false);
        }
      } catch (error) {
        console.error('Admin status check error:', error);
      }
    };

    checkAdminStatus();
  }, [username]);

  const handleMarkAllRead = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_NOTIFICATIONS_MARK_READ, {
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
      const response = await fetch(`${API_ENDPOINTS.FORUM_NOTIFICATIONS}/${notificationId}`, {
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
              
              {/* Admin menü öğeleri */}
              {isAdmin && adminMenuItems.map((item) => (
                <Tooltip title={item.label} key={item.label} arrow>
                  <IconButton
                    onClick={() => navigate(item.route)}
                    sx={{
                      color: '#FFD700',
                      opacity: 0.9,
                      borderRadius: 2,
                      transition: 'all 0.3s ease',
                      mx: 0.5,
                      background: 'rgba(255, 215, 0, 0.1)',
                      border: '1px solid rgba(255, 215, 0, 0.3)',
                      width: 45,
                      height: 45,
                      p: 1,
                      '&:hover': {
                        bgcolor: 'rgba(255, 215, 0, 0.2)',
                        color: '#FFD700',
                        transform: 'scale(1.1)',
                        border: '1px solid rgba(255, 215, 0, 0.5)',
                        boxShadow: '0 4px 15px rgba(255, 215, 0, 0.2)',
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
                <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)', mx: 1 }} />
                <MenuItem onClick={handlePasswordChangeDialogOpen} sx={{ 
                  '&:hover': {
                    background: 'rgba(255,255,255,0.1)',
                  }
                }}>
                  Şifre Değiştir
                </MenuItem>
                <Divider sx={{ borderColor: 'rgba(255,255,255,0.06)', mx: 1 }} />
                <MenuItem onClick={handleLogout} sx={{ 
                  color: 'rgba(255,255,255,0.8)',
                  '&:hover': {
                    background: 'rgba(255, 71, 87, 0.1)',
                    color: '#ff6b6b'
                  }
                }}>
                  Çıkış Yap
                </MenuItem>
              </Menu>

              {/* Password Change Dialog */}
              <Dialog 
                open={passwordChangeDialogOpen} 
                onClose={handlePasswordChangeDialogClose}
                PaperProps={{
                  sx: {
                    background: 'rgba(255,255,255,0.05)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                    borderRadius: '16px',
                    overflow: 'hidden',
                    minWidth: 400,
                    '& .MuiDialogTitle-root': {
                      background: 'linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.01) 100%)',
                      borderBottom: '1px solid rgba(255,255,255,0.06)',
                      color: 'white',
                      fontWeight: 600,
                      fontSize: '1.2rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      py: 2.5,
                      px: 3
                    },
                    '& .MuiDialogContent-root': {
                      p: 3,
                      color: 'white'
                    },
                    '& .MuiDialogActions-root': {
                      p: 2.5,
                      pt: 0,
                      gap: 1
                    }
                  }
                }}
              >
                <DialogTitle>
                  <LockIcon sx={{ fontSize: '1.4rem', color: 'rgba(255,255,255,0.8)' }} />
                  Şifre Değiştir
                </DialogTitle>
                <DialogContent>
                  {passwordChangeError && (
                    <Alert severity="error" sx={{ 
                      mb: 2,
                      background: 'rgba(244, 67, 54, 0.1)',
                      border: '1px solid rgba(244, 67, 54, 0.3)',
                      color: '#ff6b6b',
                      '& .MuiAlert-icon': {
                        color: '#ff6b6b'
                      }
                    }}>
                      {passwordChangeError}
                    </Alert>
                  )}
                  {passwordChangeSuccess && (
                    <Alert severity="success" sx={{ 
                      mb: 2,
                      background: 'rgba(76, 175, 80, 0.1)',
                      border: '1px solid rgba(76, 175, 80, 0.3)',
                      color: '#4ade80',
                      '& .MuiAlert-icon': {
                        color: '#4ade80'
                      }
                    }}>
                      {passwordChangeSuccess}
                    </Alert>
                  )}
                  <TextField
                    label="Yeni Şifre"
                    type="password"
                    fullWidth
                    margin="normal"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: 'rgba(255,255,255,0.7)',
                        '&.Mui-focused': {
                          color: 'rgba(255,255,255,0.9)'
                        }
                      },
                      '& .MuiInput-root': {
                        color: 'white',
                        '&::before': { borderBottomColor: 'rgba(255,255,255,0.3)' },
                        '&::after': { borderBottomColor: 'rgba(255,255,255,0.7)' },
                        '&:hover::before': { borderBottomColor: 'rgba(255,255,255,0.5)' },
                        '&.Mui-focused::before': { borderBottomColor: 'rgba(255,255,255,0.7)' },
                      },
                      '& .MuiInputBase-input': {
                        '&::placeholder': {
                          color: 'rgba(255,255,255,0.5)',
                          opacity: 1
                        }
                      }
                    }}
                  />
                  <TextField
                    label="Yeni Şifreyi Tekrar Girin"
                    type="password"
                    fullWidth
                    margin="normal"
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handlePasswordChange();
                      }
                    }}
                    sx={{
                      '& .MuiInputLabel-root': {
                        color: 'rgba(255,255,255,0.7)',
                        '&.Mui-focused': {
                          color: 'rgba(255,255,255,0.9)'
                        }
                      },
                      '& .MuiInput-root': {
                        color: 'white',
                        '&::before': { borderBottomColor: 'rgba(255,255,255,0.3)' },
                        '&::after': { borderBottomColor: 'rgba(255,255,255,0.7)' },
                        '&:hover::before': { borderBottomColor: 'rgba(255,255,255,0.5)' },
                        '&.Mui-focused::before': { borderBottomColor: 'rgba(255,255,255,0.7)' },
                      },
                      '& .MuiInputBase-input': {
                        '&::placeholder': {
                          color: 'rgba(255,255,255,0.5)',
                          opacity: 1
                        }
                      }
                    }}
                  />
                </DialogContent>
                <DialogActions>
                  <Button 
                    onClick={handlePasswordChangeDialogClose} 
                    sx={{ 
                      color: 'rgba(255,255,255,0.7)',
                      '&:hover': {
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white'
                      }
                    }}
                  >
                    İptal
                  </Button>
                  <Button 
                    onClick={handlePasswordChange} 
                    variant="contained" 
                    disabled={isPasswordChanging}
                    sx={{ 
                      background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                      color: 'white',
                      fontWeight: 600,
                      px: 3,
                      py: 1,
                      borderRadius: '8px',
                      textTransform: 'none',
                      '&:hover': {
                        background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                        boxShadow: '0 4px 12px rgba(79, 70, 229, 0.4)'
                      },
                      '&:disabled': {
                        background: 'rgba(255,255,255,0.1)',
                        color: 'rgba(255,255,255,0.5)'
                      }
                    }}
                  >
                    {isPasswordChanging ? 'Değiştiriliyor...' : 'Şifre Değiştir'}
                  </Button>
                </DialogActions>
              </Dialog>
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