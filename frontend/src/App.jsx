import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './Home';
import Register from './Register';
import Login from './Login';
import Dashboard from './Dashboard';
import Test from './Test';
import Code from './Code';
import AutoInterview from './AutoInterview';
import Forum from './Forum';
import Header from './Header';
import Profile from './Profile';

import { Box, CssBaseline, ThemeProvider, createTheme } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#4f46e5' },
    background: {
      default: '#0a0e27',
      paper: 'rgba(255,255,255,0.05)',
    },
    text: {
      primary: '#fff',
      secondary: 'rgba(255,255,255,0.8)',
    },
  },
  shape: { borderRadius: 12 },
  typography: { fontFamily: 'Inter, Roboto, Arial, sans-serif' },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#0a0e27',
          background: 'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)',
        },
      },
    },
  },
});

// Context ile login durumunu paylaş
const AuthContext = createContext();
export function useAuth() { return useContext(AuthContext); }

function ProtectedRoute({ children }) {
  const { isLoggedIn, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: 'calc(100vh - 64px)',
        background: 'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)'
      }}>
        <Box sx={{ 
          width: 40, 
          height: 40, 
          border: '2px solid rgba(255,255,255,0.3)', 
          borderTop: '2px solid #4f46e5', 
          borderRadius: '50%', 
          animation: 'spin 1s linear infinite' 
        }} />
      </Box>
    );
  }
  
  return isLoggedIn ? children : <Navigate to="/login" replace />;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [mode, setMode] = useState('light');

  const toggleTheme = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  // Session kontrolü ve localStorage senkronizasyonu
  useEffect(() => {
    const checkSession = async () => {
      try {
        const username = localStorage.getItem('username');
        if (!username) {
          setIsLoggedIn(false);
          setIsLoading(false);
          return;
        }

        // Backend'de session'ı kontrol et
        const response = await fetch('https://btk-project-backend.onrender.com/profile', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          // Timeout süresini artır
          signal: AbortSignal.timeout(30000) // 30 saniye
        });

        if (response.ok) {
          const data = await response.json();
          setIsLoggedIn(true);
          // localStorage'ı güncelle
          localStorage.setItem('username', data.username || username);
          if (data.interest) {
            localStorage.setItem('interest', data.interest);
          }
        } else {
          // Session geçersiz, localStorage'ı temizle
          localStorage.removeItem('username');
          localStorage.removeItem('interest');
          setIsLoggedIn(false);
        }
      } catch (error) {
        console.error('Session check error:', error);
        // Hata durumunda localStorage'ı temizle
        localStorage.removeItem('username');
        localStorage.removeItem('interest');
        setIsLoggedIn(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkSession();

    // localStorage değişikliklerini dinle
    const handleStorageChange = () => {
      setIsLoggedIn(Boolean(localStorage.getItem('username')));
    };
    
    window.addEventListener('localStorageChange', handleStorageChange);
    
    return () => {
      window.removeEventListener('localStorageChange', handleStorageChange);
    };
  }, []);



  // Loading durumunda loading spinner göster
  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #0a0e27 0%, #1a1b3d 25%, #2d1b69 50%, #4a148c 75%, #6a1b9a 100%)'
        }}>
          <Box sx={{ 
            width: 50, 
            height: 50, 
            border: '3px solid rgba(255,255,255,0.3)', 
            borderTop: '3px solid #4f46e5', 
            borderRadius: '50%', 
            animation: 'spin 1s linear infinite' 
          }} />
        </Box>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthContext.Provider value={{ isLoggedIn, setIsLoggedIn, isLoading }}>
        <Router>
          <Header mode={mode} toggleTheme={toggleTheme} />
          <Box className="main-content" sx={{ 
                        pt: '64px', 
                        width: '100%', 
                        minHeight: '100vh', 
                        maxWidth: '100%', 
                        overflowX: 'hidden',
                        padding: 0,
                        margin: 0
                      }}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/register" element={<Register setIsLoggedIn={setIsLoggedIn} />} />
              <Route path="/login" element={<Login setIsLoggedIn={setIsLoggedIn} />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/test" element={<ProtectedRoute><Test /></ProtectedRoute>} />
              <Route path="/code" element={<ProtectedRoute><Code /></ProtectedRoute>} />
              <Route path="/auto-interview" element={<ProtectedRoute><AutoInterview /></ProtectedRoute>} />

              <Route path="/forum" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile setIsLoggedIn={setIsLoggedIn} /></ProtectedRoute>} />
              {/* Catch-all route for 404 handling */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Box>
        </Router>
      </AuthContext.Provider>
    </ThemeProvider>
  );
}

export default App;
