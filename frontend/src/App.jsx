import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './Home';
import Register from './Register';
import Login from './Login';
import Dashboard from './Dashboard';
import Test from './Test';
import JobSearch from './JobSearch';
import AdvancedJobSearch from './AdvancedJobSearch';
import Code from './Code';
import AutoInterview from './AutoInterview';
import Forum from './Forum';
import History from './History';
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
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? children : <Navigate to="/login" replace />;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(Boolean(localStorage.getItem('username')));
  const [mode, setMode] = useState('light');

  const toggleTheme = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  // localStorage değişirse state'i güncelle (başka sekmeden logout vs için)
  useEffect(() => {
    const syncLogin = () => setIsLoggedIn(Boolean(localStorage.getItem('username')));
    
    // Sayfa yüklendiğinde kontrol et
    syncLogin();
    
    // localStorage değişikliklerini dinle
    window.addEventListener('storage', syncLogin);
    
    // Custom event listener ekle (aynı sekmede localStorage değişiklikleri için)
    const handleStorageChange = () => {
      syncLogin();
    };
    
    window.addEventListener('localStorageChange', handleStorageChange);
    
    return () => {
      window.removeEventListener('storage', syncLogin);
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
              <Route path="/job-search" element={<ProtectedRoute><JobSearch /></ProtectedRoute>} />
              <Route path="/advanced-job-search" element={<ProtectedRoute><AdvancedJobSearch /></ProtectedRoute>} />
              <Route path="/code" element={<ProtectedRoute><Code /></ProtectedRoute>} />
              <Route path="/auto-interview" element={<ProtectedRoute><AutoInterview /></ProtectedRoute>} />
              <Route path="/forum" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
              <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
              <Route path="/profile" element={<ProtectedRoute><Profile setIsLoggedIn={setIsLoggedIn} /></ProtectedRoute>} />
            </Routes>
          </Box>
        </Router>
      </AuthContext.Provider>
    </ThemeProvider>
  );
}

export default App;
