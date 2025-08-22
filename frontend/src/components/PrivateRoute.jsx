import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, Typography, CircularProgress, Alert } from '@mui/material';

const PrivateRoute = ({ children, requireAdmin = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Yükleniyor...</Typography>
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !user.is_admin) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <Alert severity="error" sx={{ maxWidth: 600 }}>
          Bu sayfaya erişim yetkiniz yok. Admin yetkisi gerekli.
        </Alert>
      </Box>
    );
  }

  return children;
};

export default PrivateRoute;
