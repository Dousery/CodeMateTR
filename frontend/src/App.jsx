import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
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
import SmartJobFinder from './SmartJobFinder';
import { Box, CssBaseline, ThemeProvider, createTheme, CircularProgress, Typography } from '@mui/material';
import API_ENDPOINTS from './config.js';

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
  const location = useLocation();
  
  // Loading durumunda loading göster
  if (isLoading) {
    return (
      <Box 
        display="flex" 
        flexDirection="column"
        justifyContent="center" 
        alignItems="center" 
        minHeight="100vh"
        sx={{ pt: '64px' }}
      >
        <CircularProgress 
          size={60}
          thickness={4}
          sx={{
            color: '#4f46e5',
            mb: 2
          }}
        />
        <Typography 
          variant="h6" 
          color="rgba(255,255,255,0.8)"
          sx={{ mt: 2 }}
        >
          Oturum kontrol ediliyor...
        </Typography>
      </Box>
    );
  }
  
  // Giriş yapmamışsa login sayfasına yönlendir, ama mevcut URL'yi state olarak geç
  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
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

        // Backend'de session'ı kontrol et - timeout ile
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 saniye timeout

        const response = await fetch(API_ENDPOINTS.PROFILE, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: controller.signal
        });

        clearTimeout(timeoutId);

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
        
        // Network hatası durumunda localStorage'ı temizleme, sadece loading'i kapat
        if (error.name === 'AbortError') {
          console.warn('Session check timeout - keeping existing session');
          // Timeout durumunda mevcut session'ı koru
          setIsLoggedIn(Boolean(localStorage.getItem('username')));
        } else {
          // Diğer hatalarda localStorage'ı temizle
          localStorage.removeItem('username');
          localStorage.removeItem('interest');
          setIsLoggedIn(false);
        }
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
              <Route path="/smart-job-finder" element={<ProtectedRoute><SmartJobFinder /></ProtectedRoute>} />
              <Route path="/forum" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile setIsLoggedIn={setIsLoggedIn} /></ProtectedRoute>} />
            </Routes>
          </Box>
        </Router>
      </AuthContext.Provider>
    </ThemeProvider>
  );
}

export default App;
