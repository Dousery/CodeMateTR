import React, { useState } from 'react';
import { AppBar, Toolbar, IconButton, Menu, MenuItem, Avatar, Box, Tooltip, Stack, Button } from '@mui/material';
import QuizIcon from '@mui/icons-material/Quiz';
import WorkIcon from '@mui/icons-material/Work';
import PsychologyIcon from '@mui/icons-material/Psychology';
import CodeIcon from '@mui/icons-material/Code';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import ForumIcon from '@mui/icons-material/Forum';
import HistoryEduIcon from '@mui/icons-material/HistoryEdu';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './App';

const menuItems = [
  { icon: <QuizIcon />, label: 'Test', route: '/test' },
  { icon: <WorkIcon />, label: 'İş Bulma', route: '/job-search' },
  { icon: <PsychologyIcon />, label: 'Gelişmiş CV Analizi', route: '/advanced-job-search' },
  { icon: <CodeIcon />, label: 'Kodlama Odası', route: '/code' },
  { icon: <RecordVoiceOverIcon />, label: 'Otomatik Mülakat', route: '/auto-interview' },
  { icon: <ForumIcon />, label: 'Forum', route: '/forum' },
  { icon: <HistoryEduIcon />, label: 'Geçmiş', route: '/history' },
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
        CodeMate
      </Box>
    </Box>
  );
}

export default function Header() {
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();
  const { isLoggedIn } = useAuth();
  const username = isLoggedIn ? localStorage.getItem('username') : null;

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };
  const handleLogout = () => {
    localStorage.removeItem('username');
    localStorage.removeItem('interest');
    
    // localStorage değişikliğini tetikle
    window.dispatchEvent(new Event('localStorageChange'));
    
    handleClose();
    navigate('/');
    // Sayfayı yenilemek için
    window.location.reload();
  };
  const handleProfile = () => {
    handleClose();
    navigate('/profile');
  };

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
                      '&:hover': {
                        bgcolor: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        transform: 'scale(1.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                      },
                    }}
                    size="large"
                  >
                    {item.icon}
                  </IconButton>
                </Tooltip>
              ))}
            </Stack>
          </Box>
        )}
        
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
          {username ? (
            <>
              <IconButton onClick={handleMenu} size="large" sx={{
                transition: 'all 0.3s ease',
                boxShadow: 'none',
                border: 'none',
                outline: 'none',
                background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                '&:focus': { outline: 'none', boxShadow: 'none' },
                '&:active': { outline: 'none', boxShadow: 'none' },
                '&:hover': {
                  boxShadow: '0 6px 20px rgba(79, 70, 229, 0.4)',
                  transform: 'scale(1.05)',
                  background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                }
              }}>
                <Avatar sx={{ 
                  bgcolor: 'transparent', 
                  color: 'white', 
                  width: 38, 
                  height: 38, 
                  boxShadow: 'none', 
                  border: 'none'
                }}>
                  <AccountCircleIcon fontSize="medium" />
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