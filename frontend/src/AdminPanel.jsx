import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Grid, Tabs, Tab, 
  Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Button, Chip, Dialog,
  DialogTitle, DialogContent, DialogActions,
  TextField, Alert, IconButton, Tooltip
} from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';
import API_ENDPOINTS from './config.js';
import DeleteIcon from '@mui/icons-material/Delete';
import RestoreIcon from '@mui/icons-material/Restore';
import AnnouncementIcon from '@mui/icons-material/Announcement';
import ReportIcon from '@mui/icons-material/Report';
import VisibilityIcon from '@mui/icons-material/Visibility';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState(0);
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [announcementDialog, setAnnouncementDialog] = useState(false);
  const [announcementData, setAnnouncementData] = useState({ title: '', content: '', interest: 'all' });
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [reportsRes, statsRes] = await Promise.all([
        axios.get(API_ENDPOINTS.ADMIN_REPORTS, { withCredentials: true }),
        axios.get(API_ENDPOINTS.ADMIN_STATS, { withCredentials: true })
      ]);
      
      setReports(reportsRes.data.reports);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Admin veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemovePost = async (postId, reason = 'Uygunsuz içerik') => {
    try {
      await axios.post(API_ENDPOINTS.ADMIN_REMOVE_POST, {
        post_id: postId,
        removal_reason: reason
      }, { withCredentials: true });
      
      setSuccessMessage('Gönderi başarıyla kaldırıldı');
      fetchData();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Gönderi kaldırma hatası:', error);
    }
  };

  const handleRestorePost = async (postId) => {
    try {
      await axios.post(API_ENDPOINTS.ADMIN_RESTORE_POST, {
        post_id: postId
      }, { withCredentials: true });
      
      setSuccessMessage('Gönderi başarıyla geri yüklendi');
      fetchData();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Gönderi geri yükleme hatası:', error);
    }
  };

  const handleCreateAnnouncement = async () => {
    try {
      await axios.post(API_ENDPOINTS.ADMIN_ANNOUNCEMENT, announcementData, { withCredentials: true });
      
      setSuccessMessage('Duyuru başarıyla oluşturuldu');
      setAnnouncementDialog(false);
      setAnnouncementData({ title: '', content: '', interest: 'all' });
      fetchData();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      console.error('Duyuru oluşturma hatası:', error);
    }
  };

  const getReportReasonColor = (reason) => {
    switch (reason) {
      case 'spam': return 'warning';
      case 'inappropriate': return 'error';
      case 'offensive': return 'error';
      default: return 'info';
    }
  };

  if (loading) {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="white">Yükleniyor...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', py: 10, px: 2, display: 'flex', justifyContent: 'center', alignItems: 'flex-start' }}>
      <Box sx={{ maxWidth: "1200px", width: '90%' }}>
        {successMessage && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {successMessage}
          </Alert>
        )}

        <Typography variant="h4" fontWeight={700} color="white" mb={3} textAlign="center">
          🛡️ Admin Paneli
        </Typography>

        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 30 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.6 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 3, borderRadius: 4 }}
        >
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{ 
              borderBottom: 1, 
              borderColor: 'rgba(255,255,255,0.2)',
              '& .MuiTab-root': { color: 'rgba(255,255,255,0.7)' },
              '& .Mui-selected': { color: 'white' }
            }}
          >
            <Tab label="Şikayetler" icon={<ReportIcon />} />
            <Tab label="İstatistikler" icon={<VisibilityIcon />} />
            <Tab label="Duyuru Oluştur" icon={<AnnouncementIcon />} />
          </Tabs>

          {/* Şikayetler Tab */}
          {activeTab === 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" color="white" mb={2}>
                Bekleyen Şikayetler ({reports.length})
              </Typography>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Gönderi</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Yazar</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Alan</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Şikayet Eden</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Sebep</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Tarih</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>İşlemler</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {reports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell sx={{ color: 'white' }}>
                          <Typography variant="body2" fontWeight={600}>
                            {report.post_title}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ color: 'white' }}>{report.post_author}</TableCell>
                        <TableCell sx={{ color: 'white' }}>{report.post_interest}</TableCell>
                        <TableCell sx={{ color: 'white' }}>{report.reporter_username}</TableCell>
                        <TableCell>
                          <Chip 
                            label={report.report_reason} 
                            color={getReportReasonColor(report.report_reason)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell sx={{ color: 'white' }}>
                          {new Date(report.created_at).toLocaleDateString('tr-TR')}
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Gönderiyi Kaldır">
                            <IconButton 
                              onClick={() => handleRemovePost(report.post_id)}
                              sx={{ color: '#f44336', mr: 1 }}
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
              
              {reports.length === 0 && (
                <Typography color="rgba(255,255,255,0.7)" textAlign="center" py={4}>
                  Bekleyen şikayet bulunmuyor
                </Typography>
              )}
            </Box>
          )}

          {/* İstatistikler Tab */}
          {activeTab === 1 && stats && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" color="white" mb={3}>
                Forum Genel İstatistikleri
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(76, 175, 80, 0.2)' }}>
                    <Typography variant="h4" color="#4caf50" fontWeight={700}>
                      {stats.total_posts}
                    </Typography>
                    <Typography color="white">Toplam Gönderi</Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(33, 150, 243, 0.2)' }}>
                    <Typography variant="h4" color="#2196f3" fontWeight={700}>
                      {stats.total_comments}
                    </Typography>
                    <Typography color="white">Toplam Yorum</Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(255, 152, 0, 0.2)' }}>
                    <Typography variant="h4" color="#ff9800" fontWeight={700}>
                      {stats.total_users}
                    </Typography>
                    <Typography color="white">Toplam Kullanıcı</Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'rgba(244, 67, 54, 0.2)' }}>
                    <Typography variant="h4" color="#f44336" fontWeight={700}>
                      {stats.pending_reports}
                    </Typography>
                    <Typography color="white">Bekleyen Şikayet</Typography>
                  </Paper>
                </Grid>
              </Grid>

              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" color="white" mb={2}>
                  En Çok Şikayet Edilen Gönderiler
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ color: 'white', fontWeight: 600 }}>Gönderi</TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 600 }}>Yazar</TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 600 }}>Şikayet Sayısı</TableCell>
                        <TableCell sx={{ color: 'white', fontWeight: 600 }}>İşlemler</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.top_reported_posts.map((post) => (
                        <TableRow key={post.post_id}>
                          <TableCell sx={{ color: 'white' }}>{post.title}</TableCell>
                          <TableCell sx={{ color: 'white' }}>{post.author}</TableCell>
                          <TableCell sx={{ color: 'white' }}>
                            <Chip label={post.report_count} color="error" size="small" />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="Gönderiyi Kaldır">
                              <IconButton 
                                onClick={() => handleRemovePost(post.post_id)}
                                sx={{ color: '#f44336' }}
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
              </Box>
            </Box>
          )}

          {/* Duyuru Oluştur Tab */}
          {activeTab === 2 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" color="white" mb={3}>
                Yeni Duyuru Oluştur
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Duyuru Başlığı"
                    value={announcementData.title}
                    onChange={(e) => setAnnouncementData({...announcementData, title: e.target.value})}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        color: 'white',
                        '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                        '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                        '&.Mui-focused fieldset': { borderColor: 'white' }
                      },
                      '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                      '& .MuiInputLabel-root.Mui-focused': { color: 'white' }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Duyuru İçeriği"
                    value={announcementData.content}
                    onChange={(e) => setAnnouncementData({...announcementData, content: e.target.value})}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        color: 'white',
                        '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                        '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                        '&.Mui-focused fieldset': { borderColor: 'white' }
                      },
                      '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                      '& .MuiInputLabel-root.Mui-focused': { color: 'white' }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    select
                    label="Hedef Alan"
                    value={announcementData.interest}
                    onChange={(e) => setAnnouncementData({...announcementData, interest: e.target.value})}
                    SelectProps={{
                      native: true,
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        color: 'white',
                        '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                        '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                        '&.Mui-focused fieldset': { borderColor: 'white' }
                      },
                      '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                      '& .MuiInputLabel-root.Mui-focused': { color: 'white' }
                    }}
                  >
                    <option value="all">Tüm Alanlar</option>
                    <option value="AI">AI</option>
                    <option value="Data Science">Data Science</option>
                    <option value="Web Development">Web Development</option>
                    <option value="Mobile">Mobile</option>
                    <option value="Cyber Security">Cyber Security</option>
                  </TextField>
                </Grid>
                
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    onClick={handleCreateAnnouncement}
                    disabled={!announcementData.title || !announcementData.content}
                    sx={{
                      bgcolor: '#4caf50',
                      '&:hover': { bgcolor: '#45a049' },
                      px: 4,
                      py: 1.5
                    }}
                  >
                    Duyuru Oluştur
                  </Button>
                </Grid>
              </Grid>
            </Box>
          )}
        </Paper>
      </Box>
    </Box>
  );
}
