import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardActions,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Forum as ForumIcon,
  Report as ReportIcon,
  Notifications as NotificationsIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Send as SendIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const AdminDashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState(0);
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notificationDialog, setNotificationDialog] = useState(false);
  const [notificationData, setNotificationData] = useState({
    title: '',
    message: '',
    target_users: 'all',
    interest: '',
    usernames: ''
  });

  useEffect(() => {
    if (user?.is_admin) {
      loadDashboardData();
    }
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Dashboard istatistikleri
      const statsResponse = await fetch('/admin/dashboard', {
        credentials: 'include'
      });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Kullanıcılar
      const usersResponse = await fetch('/admin/users', {
        credentials: 'include'
      });
      if (usersResponse.ok) {
        const usersData = await usersResponse.json();
        setUsers(usersData.users || []);
      }

      // Gönderiler
      const postsResponse = await fetch('/admin/posts', {
        credentials: 'include'
      });
      if (postsResponse.ok) {
        const postsData = await postsResponse.json();
        setPosts(postsData.posts || []);
      }

      // Raporlar
      const reportsResponse = await fetch('/admin/reports', {
        credentials: 'include'
      });
      if (reportsResponse.ok) {
        const reportsData = await reportsResponse.json();
        setReports(reportsData.reports || []);
      }

    } catch (err) {
      setError('Veri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (userId, currentStatus) => {
    try {
      const response = await fetch(`/admin/users/${userId}/toggle-admin`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        // Kullanıcı listesini güncelle
        setUsers(users.map(user => 
          user.id === userId 
            ? { ...user, is_admin: !currentStatus }
            : user
        ));
      }
    } catch (err) {
      setError('Admin yetkisi değiştirilemedi');
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Bu gönderiyi silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await fetch(`/admin/posts/${postId}/delete`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (response.ok) {
        setPosts(posts.filter(post => post.id !== postId));
      }
    } catch (err) {
      setError('Gönderi silinemedi');
    }
  };

  const handleResolveReport = async (reportId, action) => {
    try {
      const response = await fetch(`/admin/reports/${reportId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action })
      });
      
      if (response.ok) {
        // Rapor listesini güncelle
        setReports(reports.map(report => 
          report.id === reportId 
            ? { ...report, status: 'resolved' }
            : report
        ));
      }
    } catch (err) {
      setError('Rapor çözülemedi');
    }
  };

  const handleSendNotification = async () => {
    try {
      const response = await fetch('/admin/notifications/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(notificationData)
      });
      
      if (response.ok) {
        setNotificationDialog(false);
        setNotificationData({
          title: '',
          message: '',
          target_users: 'all',
          interest: '',
          usernames: ''
        });
        setError('');
      }
    } catch (err) {
      setError('Bildirim gönderilemedi');
    }
  };

  if (!user?.is_admin) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">
          Bu sayfaya erişim yetkiniz yok. Admin yetkisi gerekli.
        </Alert>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography>Yükleniyor...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <DashboardIcon /> Admin Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* İstatistik Kartları */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Toplam Kullanıcı
              </Typography>
              <Typography variant="h4">
                {stats.total_users || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Toplam Gönderi
              </Typography>
              <Typography variant="h4">
                {stats.total_posts || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Bekleyen Rapor
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.pending_reports || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Son 7 Gün
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.recent_posts || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tab Menüsü */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Kullanıcılar" icon={<PeopleIcon />} />
          <Tab label="Gönderiler" icon={<ForumIcon />} />
          <Tab label="Raporlar" icon={<ReportIcon />} />
          <Tab label="Bildirimler" icon={<NotificationsIcon />} />
        </Tabs>
      </Box>

      {/* Kullanıcılar Tab */}
      {activeTab === 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Kullanıcı Adı</TableCell>
                <TableCell>İlgi Alanı</TableCell>
                <TableCell>Admin</TableCell>
                <TableCell>CV</TableCell>
                <TableCell>İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.interest || '-'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={user.is_admin ? 'Admin' : 'Kullanıcı'}
                      color={user.is_admin ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={user.has_cv ? 'Var' : 'Yok'}
                      color={user.has_cv ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleToggleAdmin(user.id, user.is_admin)}
                      disabled={user.username === 'doguser'} // Kendini admin yapamaz
                    >
                      {user.is_admin ? 'Admin Kaldır' : 'Admin Yap'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Gönderiler Tab */}
      {activeTab === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Başlık</TableCell>
                <TableCell>Yazar</TableCell>
                <TableCell>İlgi Alanı</TableCell>
                <TableCell>Tür</TableCell>
                <TableCell>Admin</TableCell>
                <TableCell>İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {posts.map((post) => (
                <TableRow key={post.id}>
                  <TableCell>{post.title}</TableCell>
                  <TableCell>{post.author}</TableCell>
                  <TableCell>{post.interest}</TableCell>
                  <TableCell>{post.post_type}</TableCell>
                  <TableCell>
                    {post.is_admin_post && (
                      <Chip label="Admin" color="success" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Görüntüle">
                      <IconButton size="small">
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Sil">
                      <IconButton 
                        size="small" 
                        color="error"
                        onClick={() => handleDeletePost(post.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Raporlar Tab */}
      {activeTab === 2 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Rapor Eden</TableCell>
                <TableCell>Rapor Edilen</TableCell>
                <TableCell>Sebep</TableCell>
                <TableCell>Durum</TableCell>
                <TableCell>İşlemler</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>{report.reporter}</TableCell>
                  <TableCell>{report.reported_user}</TableCell>
                  <TableCell>{report.reason}</TableCell>
                  <TableCell>
                    <Chip 
                      label={report.status}
                      color={report.status === 'pending' ? 'warning' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {report.status === 'pending' && (
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleResolveReport(report.id, 'dismiss')}
                        >
                          Reddet
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="warning"
                          onClick={() => handleResolveReport(report.id, 'warn_user')}
                        >
                          Uyarı
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          onClick={() => handleResolveReport(report.id, 'delete_content')}
                        >
                          İçeriği Sil
                        </Button>
                      </Box>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Bildirimler Tab */}
      {activeTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Toplu Bildirim Gönder
            </Typography>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => setNotificationDialog(true)}
            >
              Yeni Bildirim
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Bildirim Dialog */}
      <Dialog open={notificationDialog} onClose={() => setNotificationDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Toplu Bildirim Gönder</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Başlık"
                value={notificationData.title}
                onChange={(e) => setNotificationData({...notificationData, title: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Mesaj"
                value={notificationData.message}
                onChange={(e) => setNotificationData({...notificationData, message: e.target.value})}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                select
                fullWidth
                label="Hedef Kullanıcılar"
                value={notificationData.target_users}
                onChange={(e) => setNotificationData({...notificationData, target_users: e.target.value})}
                SelectProps={{ native: true }}
              >
                <option value="all">Tüm Kullanıcılar</option>
                <option value="specific_interest">Belirli İlgi Alanı</option>
                <option value="specific_users">Belirli Kullanıcılar</option>
              </TextField>
            </Grid>
            {notificationData.target_users === 'specific_interest' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="İlgi Alanı"
                  value={notificationData.interest}
                  onChange={(e) => setNotificationData({...notificationData, interest: e.target.value})}
                  placeholder="örn: Python, JavaScript, Java"
                />
              </Grid>
            )}
            {notificationData.target_users === 'specific_users' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Kullanıcı Adları (virgülle ayırın)"
                  value={notificationData.usernames}
                  onChange={(e) => setNotificationData({...notificationData, usernames: e.target.value})}
                  placeholder="örn: user1, user2, user3"
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotificationDialog(false)}>İptal</Button>
          <Button 
            onClick={handleSendNotification}
            variant="contained"
            disabled={!notificationData.title || !notificationData.message}
          >
            Gönder
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminDashboard;
