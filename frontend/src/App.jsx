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
import SmartJobFinder from './SmartJobFinder';
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
  const { isLoggedIn } = useAuth();
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
        console.log('🔍 Session kontrolü başlatılıyor...');
        
        // Önce session-status endpoint'ini kontrol et
        const sessionResponse = await fetch('https://btk-project-backend.onrender.com/session-status', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        const sessionData = await sessionResponse.json();
        console.log('📊 Session Status Response:', sessionData);
        
        if (sessionData.has_username) {
          console.log('✅ Backend\'de session var, kullanıcı giriş yapmış');
          setIsLoggedIn(true);
          localStorage.setItem('username', sessionData.session_data.username);
          if (sessionData.user_interest) {
            localStorage.setItem('interest', sessionData.user_interest);
          }
          setIsLoading(false);
          return;
        }
        
        console.log('❌ Backend\'de session yok, profile endpoint\'ini kontrol ediyorum...');
        
        // Backend'de session'ı kontrol et (localStorage'a bakmadan)
        const response = await fetch('https://btk-project-backend.onrender.com/profile', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        console.log('📡 Profile Response Status:', response.status);
        console.log('📡 Profile Response Headers:', response.headers);

        if (response.ok) {
          const data = await response.json();
          console.log('✅ Profile endpoint başarılı, kullanıcı giriş yapmış');
          setIsLoggedIn(true);
          // localStorage'ı güncelle
          localStorage.setItem('username', data.username);
          if (data.interest) {
            localStorage.setItem('interest', data.interest);
          }
        } else {
          console.log('❌ Profile endpoint başarısız, session geçersiz');
          // Session geçersiz, localStorage'ı temizle
          localStorage.removeItem('username');
          localStorage.removeItem('interest');
          setIsLoggedIn(false);
        }
      } catch (error) {
        console.error('💥 Session check error:', error);
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



  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthContext.Provider value={{ isLoggedIn, setIsLoggedIn }}>
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
