import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';

// Components
import Navigation from './components/Navigation';
import PrivateRoute from './components/PrivateRoute';

// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import TestPage from './pages/TestPage';
import CodePage from './pages/CodePage';
import InterviewPage from './pages/InterviewPage';
import ForumPage from './pages/ForumPage';
import ForumPostDetail from './pages/ForumPostDetail';
import CreatePost from './pages/CreatePost';

// Admin Pages
import AdminDashboard from './pages/AdminDashboard';
import AdminCreatePost from './pages/AdminCreatePost';

// Theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <div className="App">
            <Navigation />
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected Routes */}
              <Route path="/profile" element={
                <PrivateRoute>
                  <Profile />
                </PrivateRoute>
              } />
              
              <Route path="/test" element={
                <PrivateRoute>
                  <TestPage />
                </PrivateRoute>
              } />
              
              <Route path="/code" element={
                <PrivateRoute>
                  <CodePage />
                </PrivateRoute>
              } />
              
              <Route path="/interview" element={
                <PrivateRoute>
                  <InterviewPage />
                </PrivateRoute>
              } />
              
              <Route path="/forum" element={
                <PrivateRoute>
                  <ForumPage />
                </PrivateRoute>
              } />
              
              <Route path="/forum/post/:id" element={
                <PrivateRoute>
                  <ForumPostDetail />
                </PrivateRoute>
              } />
              
              <Route path="/forum/create" element={
                <PrivateRoute>
                  <CreatePost />
                </PrivateRoute>
              } />
              
              {/* Admin Routes */}
              <Route path="/admin" element={
                <PrivateRoute requireAdmin>
                  <AdminDashboard />
                </PrivateRoute>
              } />
              
              <Route path="/admin/create-post" element={
                <PrivateRoute requireAdmin>
                  <AdminCreatePost />
                </PrivateRoute>
              } />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
