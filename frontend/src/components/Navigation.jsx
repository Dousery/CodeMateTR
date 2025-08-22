import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Chip,
  Divider
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Forum as ForumIcon,
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Navigation = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState(null);

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMobileMenuOpen = (event) => {
    setMobileMenuAnchor(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMobileMenuAnchor(null);
  };

  const handleLogout = () => {
    logout();
    handleMenuClose();
    navigate('/');
  };

  const handleNavigate = (path) => {
    navigate(path);
    handleMenuClose();
  };

  const isMenuOpen = Boolean(anchorEl);
  const isMobileMenuOpen = Boolean(mobileMenuAnchor);

  const renderProfileMenu = (
    <Menu
      anchorEl={anchorEl}
      open={isMenuOpen}
      onClose={handleMenuClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
    >
      <MenuItem onClick={() => handleNavigate('/profile')}>
        <PersonIcon sx={{ mr: 1 }} />
        Profil
      </MenuItem>
      
      {user?.is_admin && (
        <>
          <Divider />
          <MenuItem onClick={() => handleNavigate('/admin')}>
            <DashboardIcon sx={{ mr: 1 }} />
            Admin Dashboard
          </MenuItem>
          <MenuItem onClick={() => handleNavigate('/admin/create-post')}>
            <AddIcon sx={{ mr: 1 }} />
            Admin Gönderisi Oluştur
          </MenuItem>
        </>
      )}
      
      <Divider />
      <MenuItem onClick={handleLogout}>
        <LogoutIcon sx={{ mr: 1 }} />
        Çıkış Yap
      </MenuItem>
    </Menu>
  );

  const renderMobileMenu = (
    <Menu
      anchorEl={mobileMenuAnchor}
      open={isMobileMenuOpen}
      onClose={handleMenuClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'left',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'left',
      }}
    >
      <MenuItem onClick={() => handleNavigate('/')}>
        Ana Sayfa
      </MenuItem>
      
      <MenuItem onClick={() => handleNavigate('/test')}>
        Test Yap
      </MenuItem>
      
      <MenuItem onClick={() => handleNavigate('/code')}>
        Kodlama Odası
      </MenuItem>
      
      <MenuItem onClick={() => handleNavigate('/interview')}>
        Mülakat Odası
      </MenuItem>
      
      <MenuItem onClick={() => handleNavigate('/forum')}>
        Forum
      </MenuItem>
      
      {user?.is_admin && (
        <>
          <Divider />
          <MenuItem onClick={() => handleNavigate('/admin')}>
            <AdminIcon sx={{ mr: 1 }} />
            Admin Dashboard
          </MenuItem>
          <MenuItem onClick={() => handleNavigate('/admin/create-post')}>
            <AddIcon sx={{ mr: 1 }} />
            Admin Gönderisi Oluştur
          </MenuItem>
        </>
      )}
    </Menu>
  );

  return (
    <AppBar position="static">
      <Toolbar>
        {/* Mobile Menu Button */}
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          sx={{ mr: 2, display: { sm: 'none' } }}
          onClick={handleMobileMenuOpen}
        >
          <MenuIcon />
        </IconButton>

        {/* Logo/Brand */}
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, cursor: 'pointer' }} onClick={() => navigate('/')}>
          CodeMateTR
        </Typography>

        {/* Desktop Navigation */}
        <Box sx={{ display: { xs: 'none', sm: 'flex' }, gap: 1 }}>
          <Button color="inherit" onClick={() => navigate('/test')}>
            Test Yap
          </Button>
          <Button color="inherit" onClick={() => navigate('/code')}>
            Kodlama Odası
          </Button>
          <Button color="inherit" onClick={() => navigate('/interview')}>
            Mülakat Odası
          </Button>
          <Button color="inherit" onClick={() => navigate('/forum')}>
            Forum
          </Button>
        </Box>

        {/* User Menu */}
        {user ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {user.is_admin && (
              <Chip
                icon={<AdminIcon />}
                label="Admin"
                color="primary" // Mavi renk (admin için)
                size="small"
                variant="filled"
                sx={{ color: 'white' }}
              />
            )}
            
            <Button
              color="inherit"
              onClick={handleProfileMenuOpen}
              startIcon={
                <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                  {user.username.charAt(0).toUpperCase()}
                </Avatar>
              }
            >
              {user.username}
            </Button>
          </Box>
        ) : (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button color="inherit" onClick={() => navigate('/login')}>
              Giriş Yap
            </Button>
            <Button color="inherit" onClick={() => navigate('/register')}>
              Kayıt Ol
            </Button>
          </Box>
        )}

        {renderProfileMenu}
        {renderMobileMenu}
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
