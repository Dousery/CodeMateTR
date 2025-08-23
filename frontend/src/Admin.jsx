import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import API_ENDPOINTS from './config.js';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Grid,
  Avatar,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar
} from '@mui/material';
import {
  AdminPanelSettings as AdminIcon,
  Send as SendIcon,
  Delete as DeleteIcon,
  RestoreFromTrash as RestoreIcon,
  Visibility as ViewIcon,
  People as PeopleIcon,
  Analytics as AnalyticsIcon,
  Notifications as NotificationsIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Clear as ClearIcon
} from '@mui/icons-material';

const Admin = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  
  // Notification state
  const [notificationDialog, setNotificationDialog] = useState(false);
  const [notificationData, setNotificationData] = useState({
    title: '',
    message: '',
    target_username: ''
  });
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [perPage] = useState(20);

  useEffect(() => {
    if (activeTab === 'dashboard') {
      fetchStats();
    } else if (activeTab === 'users') {
      fetchUsers();
    } else if (activeTab === 'posts') {
      fetchPosts();
    }
  }, [activeTab, currentPage]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/stats`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Admin istatistikleri alınamadı');
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/users?page=${currentPage}&per_page=${perPage}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Kullanıcı listesi alınamadı');
      }
      
      const data = await response.json();
      setUsers(data.users);
      setTotalPages(data.pagination.pages);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/forum/posts?page=${currentPage}&per_page=${perPage}`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Forum gönderileri alınamadı');
      }
      
      const data = await response.json();
      setPosts(data.posts);
      setTotalPages(data.pagination.pages);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const sendNotification = async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/send-notification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(notificationData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Bildirim gönderilemedi');
      }

      const data = await response.json();
      setSnackbar({
        open: true,
        message: `Bildirim başarıyla gönderildi! ${data.target_count} kullanıcıya ulaştı.`,
        severity: 'success'
      });

      setNotificationDialog(false);
      setNotificationData({ title: '', message: '', target_username: '' });
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const removePost = async (postId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/forum/posts/${postId}/remove`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Gönderi kaldırılamadı');
      }

      setSnackbar({
        open: true,
        message: 'Gönderi başarıyla kaldırıldı',
        severity: 'success'
      });

      // Posts listesini güncelle
      fetchPosts();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const restorePost = async (postId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/admin/forum/posts/${postId}/restore`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Gönderi geri yüklenemedi');
      }

      setSnackbar({
        open: true,
        message: 'Gönderi başarıyla geri yüklendi',
        severity: 'success'
      });

      // Posts listesini güncelle
      fetchPosts();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const permanentDeletePost = async (postId) => {
    // Kullanıcıdan onay al
    if (!window.confirm('Bu gönderiyi kalıcı olarak silmek istediğinizden emin misiniz? Bu işlem geri alınamaz!')) {
      return;
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.ADMIN_FORUM_PERMANENT_DELETE}/${postId}/permanent_delete`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Gönderi kalıcı olarak silinemedi');
      }

      setSnackbar({
        open: true,
        message: 'Gönderi kalıcı olarak silindi',
        severity: 'success'
      });

      // Posts listesini güncelle
      fetchPosts();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <AnalyticsIcon /> },
    { id: 'users', label: 'Kullanıcılar', icon: <PeopleIcon /> },
    { id: 'posts', label: 'Forum Gönderileri', icon: <ViewIcon /> },
    { id: 'notifications', label: 'Bildirimler', icon: <NotificationsIcon /> }
  ];

  const renderDashboard = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
          <CardContent>
            <Typography variant="h4" sx={{ color: 'white', mb: 1 }}>
              {stats?.users?.total || 0}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              Toplam Kullanıcı
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
          <CardContent>
            <Typography variant="h4" sx={{ color: '#4CAF50', mb: 1 }}>
              {stats?.users?.admins || 0}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              Admin Kullanıcı
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
          <CardContent>
            <Typography variant="h4" sx={{ color: '#2196F3', mb: 1 }}>
              {stats?.forum?.total_posts || 0}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              Toplam Gönderi
            </Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6} lg={3}>
        <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
          <CardContent>
            <Typography variant="h4" sx={{ color: '#FF9800', mb: 1 }}>
              {stats?.forum?.removed_posts || 0}
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              Kaldırılan Gönderi
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderUsers = () => (
    <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
      <CardContent>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: 'white' }}>Kullanıcı</TableCell>
                <TableCell sx={{ color: 'white' }}>İlgi Alanı</TableCell>
                <TableCell sx={{ color: 'white' }}>Yetki</TableCell>
                <TableCell sx={{ color: 'white' }}>Kayıt Tarihi</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar sx={{ 
                        width: 32, 
                        height: 32,
                        background: user.is_admin 
                          ? 'linear-gradient(45deg, #FFD700 0%, #FFA500 100%)' 
                          : 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)'
                      }}>
                        {user.username.charAt(0).toUpperCase()}
                      </Avatar>
                      <Typography sx={{ color: 'white' }}>
                        {user.username}
                        {user.is_admin && ' 👑'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {user.interest || 'Belirtilmemiş'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.is_admin ? 'Admin' : 'Kullanıcı'}
                      color={user.is_admin ? 'warning' : 'primary'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {formatDate(user.created_at)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(e, page) => setCurrentPage(page)}
            sx={{
              '& .MuiPaginationItem-root': {
                color: 'white'
              }
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );

  const renderPosts = () => (
    <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
      <CardContent>
        <List>
          {posts.map((post) => (
            <ListItem key={post.id} sx={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <ListItemAvatar>
                <Avatar sx={{ 
                  background: post.author_is_admin 
                    ? 'linear-gradient(45deg, #FFD700 0%, #FFA500 100%)' 
                    : 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)'
                }}>
                  {post.author_username.charAt(0).toUpperCase()}
                </Avatar>
              </ListItemAvatar>
              
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography sx={{ color: 'white', fontWeight: 'bold' }}>
                      {post.title}
                    </Typography>
                    {post.is_admin_post && (
                      <Chip label="👑 ADMIN" size="small" sx={{ background: '#FFD700', color: 'black' }} />
                    )}
                    {post.is_removed && (
                      <Chip label="🗑️ KALDIRILDI" size="small" sx={{ background: '#f44336', color: 'white' }} />
                    )}
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      {post.author_username} • {post.interest} • {formatDate(post.created_at)}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                      {post.content.substring(0, 100)}...
                    </Typography>
                  </Box>
                }
              />
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                {post.is_removed ? (
                  <>
                    <Tooltip title="Gönderiyi Geri Yükle">
                      <IconButton
                        onClick={() => restorePost(post.id)}
                        sx={{ color: '#4CAF50' }}
                      >
                        <RestoreIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Gönderiyi Kalıcı Olarak Sil">
                      <IconButton
                        onClick={() => permanentDeletePost(post.id)}
                        sx={{ 
                          color: '#d32f2f',
                          '&:hover': { 
                            bgcolor: 'rgba(211, 47, 47, 0.1)',
                            transform: 'scale(1.1)' 
                          }
                        }}
                      >
                        <ClearIcon sx={{ fontSize: '1.3rem' }} />
                      </IconButton>
                    </Tooltip>
                  </>
                ) : (
                  <Tooltip title="Gönderiyi Kaldır">
                    <IconButton
                      onClick={() => removePost(post.id)}
                      sx={{ color: '#f44336' }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </ListItem>
          ))}
        </List>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(e, page) => setCurrentPage(page)}
            sx={{
              '& .MuiPaginationItem-root': {
                color: 'white'
              }
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );

  const renderNotifications = () => (
    <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
      <CardContent>
        <Box sx={{ mb: 3 }}>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => setNotificationDialog(true)}
            sx={{
              background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #66BB6A 0%, #4CAF50 100%)'
              }
            }}
          >
            Toplu Bildirim Gönder
          </Button>
        </Box>
        
        <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
          Bildirim Gönderme
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 2 }}>
          Tüm kullanıcılara veya belirli bir kullanıcıya bildirim gönderebilirsiniz.
        </Typography>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Typography variant="h6" sx={{ color: 'white' }}>
          Yükleniyor...
        </Typography>
      </Box>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Box sx={{ 
        minHeight: '100vh',
        width: '100vw',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        pt: 8,
        pb: 4
      }}>
        <Container maxWidth="xl" sx={{ width: '100%' }}>
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <Box sx={{ mb: 4, textAlign: 'center' }}>
              <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'white' }}>
                <AdminIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
                Admin Paneli
              </Typography>
              <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                Sistem yönetimi ve kullanıcı kontrolü
              </Typography>
            </Box>
          </motion.div>

          {/* Tabs */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'center' }}>
              <Card sx={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)' }}>
                <Box sx={{ display: 'flex' }}>
                  {tabs.map((tab) => (
                    <Button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      sx={{
                        color: activeTab === tab.id ? '#4CAF50' : 'rgba(255,255,255,0.7)',
                        borderBottom: activeTab === tab.id ? '2px solid #4CAF50' : 'none',
                        borderRadius: 0,
                        px: 3,
                        py: 2,
                        '&:hover': {
                          background: 'rgba(255,255,255,0.05)'
                        }
                      }}
                    >
                      {tab.icon}
                      <Typography sx={{ ml: 1, display: { xs: 'none', sm: 'block' } }}>
                        {tab.label}
                      </Typography>
                    </Button>
                  ))}
                </Box>
              </Card>
            </Box>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            {activeTab === 'dashboard' && renderDashboard()}
            {activeTab === 'users' && renderUsers()}
            {activeTab === 'posts' && renderPosts()}
            {activeTab === 'notifications' && renderNotifications()}
          </motion.div>
        </Container>
      </Box>

      {/* Notification Dialog */}
      <Dialog open={notificationDialog} onClose={() => setNotificationDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ color: 'white' }}>Bildirim Gönder</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Başlık"
            value={notificationData.title}
            onChange={(e) => setNotificationData({ ...notificationData, title: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            label="Mesaj"
            multiline
            rows={4}
            value={notificationData.message}
            onChange={(e) => setNotificationData({ ...notificationData, message: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Hedef Kullanıcı (Boş bırakırsanız tüm kullanıcılara gönderilir)"
            value={notificationData.target_username}
            onChange={(e) => setNotificationData({ ...notificationData, target_username: e.target.value })}
            placeholder="doguser"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotificationDialog(false)}>İptal</Button>
          <Button onClick={sendNotification} variant="contained" color="primary">
            Gönder
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </motion.div>
  );
};

export default Admin;
