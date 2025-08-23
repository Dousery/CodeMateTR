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
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  Pagination,
  Alert,
  Snackbar,
  InputAdornment,
  Badge,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  ThumbUp as ThumbUpIcon,
  ThumbUpOutlined as ThumbUpOutlinedIcon,
  Comment as CommentIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  Tag as TagIcon,
  Person as PersonIcon,
  Forum as ForumIcon,

  EmojiEvents as EmojiEventsIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Report as ReportIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  AddComment as AddCommentIcon,
  Send as SendIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

const Forum = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPost, setSelectedPost] = useState(null);
  const [openPostDialog, setOpenPostDialog] = useState(false);
  const [openCommentDialog, setOpenCommentDialog] = useState(false);
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    post_type: 'discussion',
    interest: '',
    tags: []
  });
  const [newComment, setNewComment] = useState({
    content: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [postTypeFilter, setPostTypeFilter] = useState('all');
  const [interestFilter, setInterestFilter] = useState('all');
  const [sortBy, setSortBy] = useState('latest');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [leaderboard, setLeaderboard] = useState([]);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportData, setReportData] = useState({
    reason: '',
    description: '',
    post_id: null,
    comment_id: null
  });

  // Yeni state'ler ekle
  const [selectedPostForSolution, setSelectedPostForSolution] = useState(null);
  const [showSolutionDialog, setShowSolutionDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [postToDelete, setPostToDelete] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const postTypes = [
  { value: 'discussion', label: 'Tartışma' },
  { value: 'question', label: 'Soru' },
  { value: 'resource', label: 'Kaynak' },
  { value: 'announcement', label: 'Duyuru' }
];

const interestTypes = [
  { value: 'Data Science', label: 'Data Science' },
  { value: 'Web Development', label: 'Web Development' },
  { value: 'Mobile Development', label: 'Mobile Development' },
  { value: 'AI/ML', label: 'AI/ML' },
  { value: 'Cybersecurity', label: 'Cybersecurity' },
  { value: 'DevOps', label: 'DevOps' }
];

  const sortOptions = [
    { value: 'latest', label: 'En Yeni' },
    { value: 'popular', label: 'En Popüler' },
    { value: 'most_commented', label: 'En Çok Yorum Alan' }
  ];

  useEffect(() => {
    fetchPosts();
    fetchStats();
    fetchLeaderboard();
  }, [currentPage, searchTerm, postTypeFilter, interestFilter, sortBy]);

  // Admin kontrolü
  useEffect(() => {
    const checkAdminStatus = async () => {
      try {
        const response = await fetch('/api/profile', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          setIsAdmin(data.is_admin || false);
        }
      } catch (error) {
        console.error('Admin status check error:', error);
      }
    };
    
    checkAdminStatus();
  }, []);



  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_LEADERBOARD, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.leaderboard);
      }
    } catch (err) {
      console.error('Liderlik tablosu yüklenemedi:', err);
    }
  };

  const reportContent = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_REPORT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(reportData)
      });

      if (response.ok) {
        setShowReportDialog(false);
        setReportData({ reason: '', description: '', post_id: null, comment_id: null });
        setSnackbar({ open: true, message: 'İçerik başarıyla raporlandı', severity: 'success' });
      }
    } catch (error) {
      console.error('Raporlama hatası:', error);
      setSnackbar({ open: true, message: 'Raporlama yapılırken hata oluştu', severity: 'error' });
    }
  };



  // Yeni fonksiyonlar ekle
  const handleLikeComment = async (commentId) => {
    try {
      const response = await fetch(`http://localhost:5000/forum/comments/${commentId}/like`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        // Seçili gönderiyi yeniden yükle
        if (selectedPost) {
          const postResponse = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${selectedPost.post.id}`, {
            credentials: 'include'
          });
          if (postResponse.ok) {
            const data = await postResponse.json();
            setSelectedPost(data);
          }
        }
        
        // Gönderi listesini de güncelle (beğeni sayısı değişebilir)
        fetchPosts();
      }
    } catch (err) {
      console.error('Yorum beğenilemedi:', err);
      setSnackbar({ open: true, message: 'Yorum beğenilirken hata oluştu', severity: 'error' });
    }
  };

  const handleMarkAsSolution = async (postId, commentId, solvedBy) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${postId}/solve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          solved_by: solvedBy,
          comment_id: commentId
        })
      });

      if (response.ok) {
        setSnackbar({ open: true, message: 'Çözüm başarıyla işaretlendi!', severity: 'success' });
        setShowSolutionDialog(false);
        setSelectedPostForSolution(null);
        
        // Seçili gönderiyi hemen güncelle
        if (selectedPost) {
          const postResponse = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${selectedPost.post.id}`, {
            credentials: 'include'
          });
          if (postResponse.ok) {
            const data = await postResponse.json();
            setSelectedPost(data);
          }
        }
        
        // Gönderi listesini yenile
        fetchPosts();
        
        // Dialog'u kapat (veri güncellendikten sonra)
        setOpenCommentDialog(false);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Çözüm işaretlenemedi');
      }
    } catch (err) {
      console.error('Çözüm işaretlenemedi:', err);
      setSnackbar({ open: true, message: 'Çözüm işaretlenirken hata oluştu', severity: 'error' });
    }
  };

  const handleDeletePost = async (postId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${postId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        setSnackbar({ open: true, message: 'Gönderi başarıyla silindi!', severity: 'success' });
        setShowDeleteDialog(false);
        setPostToDelete(null);
        
        // Gönderi listesini yenile
        fetchPosts();
        fetchStats();
        
        // Eğer silinen gönderi açık dialog'da ise, dialog'u kapat
        if (selectedPost && selectedPost.post.id === postId) {
          setOpenCommentDialog(false);
          setSelectedPost(null);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Gönderi silinemedi');
      }
    } catch (err) {
      console.error('Gönderi silinemedi:', err);
      setSnackbar({ open: true, message: 'Gönderi silinirken hata oluştu', severity: 'error' });
    }
  };

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage,
        per_page: 10,
        type: postTypeFilter,
        interest: interestFilter,
        sort: sortBy,
        search: searchTerm
      });

      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}?${params}`, {
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 401) {
          // Session hatası - kullanıcıyı login sayfasına yönlendir
          localStorage.removeItem('username');
          localStorage.removeItem('interest');
          window.dispatchEvent(new Event('localStorageChange'));
          window.location.href = '/login';
          return;
        }
        throw new Error(errorData.error || 'Gönderiler yüklenemedi');
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

  const fetchStats = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_STATS, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('İstatistikler yüklenemedi:', err);
    }
  };

  const handleCreatePost = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.FORUM_POSTS, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(newPost)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Gönderi oluşturulamadı');
      }

      setSnackbar({
        open: true,
        message: 'Gönderi başarıyla oluşturuldu!',
        severity: 'success'
      });

      setOpenPostDialog(false);
      setNewPost({
        title: '',
        content: '',
        post_type: 'discussion',
        interest: '',
        tags: []
      });
      fetchPosts();
      fetchStats();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const handleLikePost = async (postId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${postId}/like`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        // Başarı mesajı göster
        setSnackbar({ open: true, message: 'Beğeni işlemi başarılı!', severity: 'success' });
        // Gönderi listesini güncelle
        fetchPosts();
      } else {
        throw new Error('Beğeni işlemi başarısız');
      }
    } catch (err) {
      console.error('Beğeni işlemi başarısız:', err);
      setSnackbar({ open: true, message: 'Beğeni işlemi başarısız oldu', severity: 'error' });
    }
  };

  const handlePostClick = async (post) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${post.id}`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedPost(data);
        setOpenCommentDialog(true);
      }
    } catch (err) {
      console.error('Gönderi detayları yüklenemedi:', err);
    }
  };

  const handleCreateComment = async () => {
    if (!selectedPost) return;
    
    try {
      const response = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${selectedPost.post.id}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(newComment)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Yorum eklenemedi');
      }

      setSnackbar({
        open: true,
        message: 'Yorum başarıyla eklendi!',
        severity: 'success'
      });

      setOpenCommentDialog(false);
      setNewComment({
        content: ''
      });
      
      // Gönderiyi yeniden yükle
              const postResponse = await fetch(`${API_ENDPOINTS.FORUM_POSTS}/${selectedPost.post.id}`, {
        credentials: 'include'
      });
      if (postResponse.ok) {
        const data = await postResponse.json();
        setSelectedPost(data);
      }
      
      fetchStats();
    } catch (err) {
      setSnackbar({
        open: true,
        message: err.message,
        severity: 'error'
      });
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPostTypeColor = (type) => {
    const colors = {
      discussion: 'primary',
      question: 'secondary',
      resource: 'success',
      announcement: 'warning'
    };
    return colors[type] || 'default';
  };

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
        pt: 8, // Add top padding to account for fixed header
        pb: 4
      }}>
        <Container maxWidth="lg" sx={{ width: '100%' }}>
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Box sx={{ mb: 4, display: 'flex', justifyContent: 'flex-end', alignItems: 'flex-start' }}>
          <Box sx={{ display: 'none' }}>
            <Typography variant="h4" component="h1" gutterBottom sx={{ color: 'white' }}>
              <ForumIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
              Forum
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              İlgi alanınızdaki diğer kullanıcılarla tartışın, sorular sorun ve deneyimlerinizi paylaşın.
            </Typography>
          </Box>
        </Box>
        </motion.div>

      {/* Stats Cards */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
            <Grid container spacing={2} sx={{ flex: 1 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'rgba(255,255,255,0.05)', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6">{stats.total_posts}</Typography>
                  <Typography variant="body2">Toplam Gönderi</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'rgba(255,255,255,0.05)', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6">{stats.total_comments}</Typography>
                  <Typography variant="body2">Toplam Yorum</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'rgba(255,255,255,0.05)', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6">{stats.user_posts}</Typography>
                  <Typography variant="body2">Sizin Gönderileriniz</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card sx={{ bgcolor: 'rgba(255,255,255,0.05)', color: 'white' }}>
                <CardContent>
                  <Typography variant="h6">{stats.user_comments}</Typography>
                  <Typography variant="body2">Sizin Yorumlarınız</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          
          <Box sx={{ display: 'flex', gap: 2, ml: 2 }}>
            <Tooltip title="Liderlik Tablosu">
              <IconButton
                onClick={() => setShowLeaderboard(!showLeaderboard)}
                sx={{
                  color: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
                }}
              >
                <EmojiEventsIcon />
              </IconButton>
            </Tooltip>
            

          </Box>
        </Box>
        </motion.div>
      )}



      {/* Leaderboard Panel */}
      {showLeaderboard && (
        <Card sx={{ 
          mb: 3, 
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          <CardContent>
            <Typography variant="h6" sx={{ 
              color: 'white', 
              mb: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              fontWeight: 'bold'
            }}>
              🏆 En İyi Çözüm Verenler
            </Typography>
            {leaderboard.length === 0 ? (
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center' }}>
                Henüz çözüm seçilmemiş.
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {leaderboard.map((user, index) => (
                  <Card key={user.username} sx={{ 
                    background: index === 0 ? 'rgba(255, 215, 0, 0.1)' : 
                              index === 1 ? 'rgba(192, 192, 192, 0.1)' : 
                              index === 2 ? 'rgba(205, 127, 50, 0.1)' : 'rgba(255,255,255,0.02)',
                    border: index === 0 ? '2px solid #FFD700' : 
                           index === 1 ? '2px solid #C0C0C0' : 
                           index === 2 ? '2px solid #CD7F32' : '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.3)'
                    }
                  }}>
                    <CardContent sx={{ py: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        {/* Sıralama */}
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          width: 40,
                          height: 40,
                          borderRadius: '50%',
                          background: index === 0 ? 'linear-gradient(45deg, #FFD700 0%, #FFA500 100%)' :
                                      index === 1 ? 'linear-gradient(45deg, #C0C0C0 0%, #A9A9A9 100%)' :
                                      index === 2 ? 'linear-gradient(45deg, #CD7F32 0%, #B8860B 100%)' :
                                      'rgba(255,255,255,0.1)',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '1.2rem',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
                        }}>
                          {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${user.rank}`}
                        </Box>
                        
                        {/* Avatar */}
                        <Avatar sx={{ 
                          width: 50, 
                          height: 50, 
                          background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                          fontWeight: 'bold',
                          fontSize: '1.2rem',
                          boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)'
                        }}>
                          {user.avatar}
                      </Avatar>
                        
                        {/* Kullanıcı Bilgileri */}
                      <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" sx={{ 
                            color: 'white', 
                            fontWeight: 'bold',
                            fontSize: '1.1rem'
                          }}>
                          {user.username}
                        </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                            <Typography variant="body2" sx={{ 
                              color: index === 0 ? '#FFD700' : 
                                     index === 1 ? '#C0C0C0' : 
                                     index === 2 ? '#CD7F32' : 'rgba(255,255,255,0.8)',
                              fontWeight: 'bold',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 0.5
                            }}>
                              <CheckCircleIcon sx={{ fontSize: 16 }} />
                              {user.solution_count} çözüm
                            </Typography>
                            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                              {user.total_points} puan
                        </Typography>
                      </Box>
                    </Box>
                        
                        {/* Başarı Rozeti */}
                        {index < 3 && (
                          <Box sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: 0.5
                          }}>
                            <Typography variant="caption" sx={{ 
                              color: index === 0 ? '#FFD700' : 
                                     index === 1 ? '#C0C0C0' : '#CD7F32',
                              fontWeight: 'bold',
                              textAlign: 'center'
                            }}>
                              {index === 0 ? 'Altın' : index === 1 ? 'Gümüş' : 'Bronz'}
                            </Typography>
                            <Typography variant="caption" sx={{ 
                              color: 'rgba(255,255,255,0.6)',
                              textAlign: 'center'
                            }}>
                              Çözüm
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filtering and Search */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Card sx={{ 
          mb: 3, 
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)'
        }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  placeholder="Gönderilerde ara..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon sx={{ color: 'rgba(255,255,255,0.7)' }} />
                      </InputAdornment>
                    ),
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 1
                    },
                    '& .MuiInputBase-input::placeholder': {
                      color: 'rgba(255,255,255,0.5)',
                      opacity: 1
                    }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Gönderi Türü</InputLabel>
                  <Select
                    value={postTypeFilter}
                    onChange={(e) => setPostTypeFilter(e.target.value)}
                    sx={{
                      color: 'white',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 1
                    }}
                  >
                    <MenuItem value="all">Tümü</MenuItem>
                    {postTypes.map(type => (
                      <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              {/* Admin için Interest Filter */}
              {isAdmin && (
                <Grid item xs={12} md={3}>
                  <FormControl fullWidth>
                    <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>İlgi Alanı</InputLabel>
                    <Select
                      value={interestFilter}
                      onChange={(e) => setInterestFilter(e.target.value)}
                      sx={{
                        color: 'white',
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                        '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: 1
                      }}
                    >
                      <MenuItem value="all">Tümü</MenuItem>
                      {interestTypes.map(interest => (
                        <MenuItem key={interest.value} value={interest.value}>{interest.label}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              )}
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Sıralama</InputLabel>
                  <Select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    sx={{
                      color: 'white',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: 1
                    }}
                  >
                    {sortOptions.map(option => (
                      <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => setOpenPostDialog(true)}
                  startIcon={<AddIcon />}
                  sx={{ 
                    background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                    '&:hover': { 
                      background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                      transform: 'translateY(-1px)'
                    },
                    borderRadius: '20px',
                    py: 1.5,
                    fontWeight: 'bold',
                    boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  Yeni Gönderi
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </motion.div>

      {/* Posts List */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <Box sx={{ mb: 3 }}>
          {posts.filter(post => !post.is_removed).map((post, index) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ 
                duration: 0.5, 
                delay: 0.5 + (index * 0.1),
                ease: "easeOut"
              }}
            >
          <Card
            key={post.id}
            sx={{
              mb: 2,
              background: post.is_solved ? 'rgba(76, 175, 80, 0.05)' : 'rgba(255,255,255,0.05)',
              backdropFilter: 'blur(20px)',
              border: post.is_solved ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
              '&:hover': {
                background: post.is_solved ? 'rgba(76, 175, 80, 0.08)' : 'rgba(255,255,255,0.08)',
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 40px rgba(0,0,0,0.4)',
                border: post.is_solved ? '2px solid #66BB6A' : '1px solid rgba(255,255,255,0.2)'
              }
            }}
            onClick={() => handlePostClick(post)}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                      {post.title}
                    </Typography>
                    {post.is_admin_post && (
                      <Chip
                        label="👑 ADMIN"
                        size="small"
                        sx={{
                          background: 'linear-gradient(45deg, #FFD700 0%, #FFA500 100%)',
                          color: 'black',
                          fontWeight: 'bold',
                          fontSize: '0.7rem',
                          boxShadow: '0 2px 8px rgba(255, 215, 0, 0.3)'
                        }}
                      />
                    )}
                    {post.is_solved && (
                      <Chip
                        label="✅ Çözüldü"
                        size="small"
                        sx={{
                          background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.7rem',
                          boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
                        }}
                      />
                    )}
                  </Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 2, lineHeight: 1.6 }}>
                    {post.content}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {post.is_solved && (
                    <Chip
                      label="SOLVED"
                      size="small"
                      sx={{
                        background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '0.6rem',
                        alignSelf: 'flex-end',
                        boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
                      }}
                    />
                  )}
                  <Chip
                    label={postTypes.find(t => t.value === post.post_type)?.label || post.post_type}
                    color={getPostTypeColor(post.post_type)}
                      size="small"
                      sx={{ 
                      background: 'rgba(255,255,255,0.1)',
                      backdropFilter: 'blur(10px)',
                      border: '1px solid rgba(255,255,255,0.2)'
                      }}
                    />
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ 
                    width: 28, 
                    height: 28, 
                    background: post.author_is_admin 
                      ? 'linear-gradient(45deg, #FFD700 0%, #FFA500 100%)' 
                      : 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                    fontWeight: 'bold',
                    border: post.author_is_admin ? '2px solid #FFD700' : 'none'
                  }}>
                    {post.author.charAt(0).toUpperCase()}
                  </Avatar>
                  <Typography variant="body2" sx={{ 
                    color: post.author_is_admin ? '#FFD700' : 'rgba(255,255,255,0.8)', 
                    fontWeight: post.author_is_admin ? 'bold' : 500 
                  }}>
                    {post.author}
                    {post.author_is_admin && ' 👑'}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                  {formatDate(post.created_at)}
                </Typography>
              </Box>

              {post.tags.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  {post.tags.map((tag, index) => (
                    <Chip
                      key={index}
                      label={tag}
                      size="small"
                      icon={<TagIcon />}
                      sx={{ 
                        mr: 1, 
                        mb: 1, 
                        background: 'rgba(79, 70, 229, 0.2)',
                        backdropFilter: 'blur(10px)',
                        color: 'white',
                        border: '1px solid rgba(79, 70, 229, 0.3)'
                      }}
                    />
                  ))}
                </Box>
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLikePost(post.id);
                    }}
                    sx={{ 
                      color: post.user_liked ? '#4f46e5' : 'rgba(255,255,255,0.7)',
                      '&:hover': { 
                        bgcolor: 'rgba(79, 70, 229, 0.1)',
                        transform: 'scale(1.1)'
                      },
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {post.user_liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                  </IconButton>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {post.likes_count}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CommentIcon sx={{ color: 'rgba(255,255,255,0.7)' }} />
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {post.comments_count}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <VisibilityIcon sx={{ color: 'rgba(255,255,255,0.7)' }} />
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {post.views}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {/* Sadece gönderi sahibi olmayan kullanıcılar raporlayabilir */}
                  {post.author !== localStorage.getItem('username') && (
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setReportData(prev => ({ ...prev, post_id: post.id, comment_id: null }));
                        setShowReportDialog(true);
                      }}
                      sx={{ 
                        color: 'rgba(255,255,255,0.7)',
                        '&:hover': { 
                          bgcolor: 'rgba(244, 67, 54, 0.1)',
                          transform: 'scale(1.1)'
                        },
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <ReportIcon />
                    </IconButton>
                  )}
                  
                  {/* Sadece gönderi sahibi silebilir */}
                  {post.author === localStorage.getItem('username') && (
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPostToDelete(post);
                        setShowDeleteDialog(true);
                      }}
                      sx={{ 
                        color: 'rgba(255,255,255,0.7)',
                        '&:hover': { 
                          bgcolor: 'rgba(244, 67, 54, 0.2)',
                          transform: 'scale(1.1)'
                        },
                        transition: 'all 0.2s ease'
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
            </motion.div>
          ))}
        </Box>
        </motion.div>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={currentPage}
            onChange={(e, page) => setCurrentPage(page)}
            color="primary"
            sx={{
              '& .MuiPaginationItem-root': {
                color: 'white',
                '&.Mui-selected': {
                  bgcolor: '#4f46e5'
                }
              }
            }}
          />
        </Box>
      )}

      {/* Create Post Dialog */}
      <Dialog
        open={openPostDialog}
        onClose={() => setOpenPostDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(20, 20, 40, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            color: 'white'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'rgba(30, 30, 50, 0.9)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          fontWeight: 600
        }}>
          Yeni Gönderi Oluştur
        </DialogTitle>
        <DialogContent sx={{ 
          background: 'rgba(20, 20, 40, 0.9)',
          backdropFilter: 'blur(20px)',
          pt: 3
        }}>
          <TextField
            fullWidth
            label="Başlık"
            value={newPost.title}
            onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
            margin="normal"
            sx={{
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 1
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
              '& .MuiInputLabel-root.Mui-focused': { color: '#4f46e5' }
            }}
          />
          <TextField
            fullWidth
            label="İçerik"
            value={newPost.content}
            onChange={(e) => setNewPost(prev => ({ ...prev, content: e.target.value }))}
            margin="normal"
            multiline
            rows={6}
            sx={{
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 1
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
              '& .MuiInputLabel-root.Mui-focused': { color: '#4f46e5' }
            }}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Gönderi Türü</InputLabel>
            <Select
              value={newPost.post_type}
              onChange={(e) => setNewPost(prev => ({ ...prev, post_type: e.target.value }))}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#4f46e5' },
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 1
              }}
            >
              {postTypes.map(type => (
                <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Admin için Interest Seçimi */}
          {isAdmin && (
            <FormControl fullWidth margin="normal">
              <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>İlgi Alanı</InputLabel>
              <Select
                value={newPost.interest}
                onChange={(e) => setNewPost(prev => ({ ...prev, interest: e.target.value }))}
                sx={{
                  color: 'white',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                  '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#4f46e5' },
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: 1
                }}
              >
                {interestTypes.map(interest => (
                  <MenuItem key={interest.value} value={interest.value}>{interest.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          
        </DialogContent>
        <DialogActions sx={{ 
          background: 'rgba(30, 30, 50, 0.9)',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          p: 2
        }}>
          <Button 
            onClick={() => setOpenPostDialog(false)} 
              sx={{
              color: 'rgba(255,255,255,0.7)',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
            }}
          >
            İptal
          </Button>
          <Button
            onClick={handleCreatePost}
            variant="contained"
            sx={{ 
              background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
              '&:hover': { 
                background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                transform: 'translateY(-1px)'
              },
              borderRadius: '20px',
              px: 3,
              py: 1,
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)',
              transition: 'all 0.2s ease'
            }}
          >
            Oluştur
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Post and Comments Dialog */}
      <Dialog
        open={openCommentDialog}
        onClose={() => setOpenCommentDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(20, 20, 40, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            maxHeight: '90vh',
            color: 'white'
          }
        }}
      >
        {selectedPost && (
          <>
            {/* Header */}
            <DialogTitle sx={{ 
              borderBottom: '1px solid rgba(255,255,255,0.1)', 
              pb: 2,
              background: 'rgba(30, 30, 50, 0.9)',
              backdropFilter: 'blur(20px)',
              fontWeight: 600
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                <Typography variant="h5" sx={{ fontWeight: 'bold', color: 'white' }}>
                  {selectedPost.post.title}
              </Typography>
                {selectedPost.post.is_solved && (
                  <Chip
                    label="✅ Çözüldü"
                    size="small"
                    sx={{
                      background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
                      color: 'white',
                      fontWeight: 'bold',
                      fontSize: '0.8rem',
                      boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
                    }}
                  />
                )}
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ 
                    width: 32, 
                    height: 32, 
                    background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                    fontWeight: 'bold'
                  }}>
                    {selectedPost.post.author.charAt(0).toUpperCase()}
                  </Avatar>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 500 }}>
                    {selectedPost.post.author}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                  {formatDate(selectedPost.post.created_at)}
                </Typography>
                <Chip
                  label={postTypes.find(t => t.value === selectedPost.post.post_type)?.label || selectedPost.post.post_type}
                  color={getPostTypeColor(selectedPost.post.post_type)}
                  size="small"
                  sx={{
                    background: 'rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)'
                  }}
                />
              </Box>
            </DialogTitle>

            <DialogContent sx={{ 
              p: 3,
              background: 'rgba(20, 20, 40, 0.9)',
              backdropFilter: 'blur(20px)'
            }}>
              {/* Post Content */}
              <Card sx={{ 
                mb: 4, 
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: 2,
                boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  transform: 'translateY(-2px)'
                }
              }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="body1" sx={{ 
                    lineHeight: 1.7, 
                    fontSize: '1.1rem',
                    color: 'rgba(255,255,255,0.9)',
                    mb: 4  // Başlık ve içerik arasındaki boşluğu artır
                  }}>
                {selectedPost.post.content}
              </Typography>
              
                  {/* Post Stats */}
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 3, 
                    pt: 3,
                    borderTop: '1px solid rgba(255,255,255,0.1)'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleLikePost(selectedPost.post.id)}
                        sx={{ 
                          color: selectedPost.post.user_liked ? '#4f46e5' : 'rgba(255,255,255,0.7)',
                          '&:hover': { 
                            bgcolor: 'rgba(79, 70, 229, 0.1)',
                            transform: 'scale(1.1)'
                          },
                          transition: 'all 0.2s ease'
                        }}
                      >
                        {selectedPost.post.user_liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                      </IconButton>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {selectedPost.post.likes_count}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CommentIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 20 }} />
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {selectedPost.post.comments_count}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <VisibilityIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 20 }} />
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {selectedPost.post.views}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
              
              {/* Comments Section */}
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" sx={{ 
                  mb: 3, 
                  color: 'white',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1
                }}>
                  <CommentIcon sx={{ color: '#4f46e5' }} />
                  Yorumlar ({selectedPost.comments.length})
                </Typography>
              
                {selectedPost.comments.length === 0 ? (
                  <Card sx={{ 
                    background: 'rgba(255,255,255,0.02)',
                    backdropFilter: 'blur(20px)',
                    border: '1px dashed rgba(255,255,255,0.2)',
                    borderRadius: 2
                  }}>
                    <CardContent sx={{ textAlign: 'center', py: 4 }}>
                      <CommentIcon sx={{ fontSize: 48, color: 'rgba(255,255,255,0.3)', mb: 2 }} />
                      <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                        Henüz yorum yapılmamış. İlk yorumu siz yapın!
                      </Typography>
                    </CardContent>
                  </Card>
                ) : (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {selectedPost.comments.map((comment) => (
                      <Card key={comment.id} sx={{ 
                    border: comment.is_solution ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 2,
                        background: comment.is_solution ? 'rgba(76, 175, 80, 0.05)' : 'rgba(255,255,255,0.05)',
                        backdropFilter: 'blur(20px)',
                        position: 'relative',
                        overflow: 'visible',
                        boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          background: comment.is_solution ? 'rgba(76, 175, 80, 0.08)' : 'rgba(255,255,255,0.08)',
                          transform: 'translateY(-2px)',
                          boxShadow: '0 8px 24px rgba(0,0,0,0.3)'
                        }
                      }}>
                        {comment.is_solution && (
                          <Box sx={{
                            position: 'absolute',
                            top: -10,
                            right: 20,
                            background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
                            color: 'white',
                            px: 2,
                            py: 0.5,
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            fontWeight: 'bold',
                            boxShadow: '0 4px 12px rgba(76, 175, 80, 0.4)',
                            backdropFilter: 'blur(10px)'
                  }}>
                            ✅ Çözüm
                          </Box>
                        )}
                        
                        <CardContent>
                          {/* Comment Header */}
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Avatar sx={{ 
                              width: 40, 
                              height: 40, 
                              background: comment.is_solution ? 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)' : 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                              fontWeight: 'bold'
                            }}>
                        {comment.author.charAt(0).toUpperCase()}
                      </Avatar>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="body1" sx={{ 
                                color: 'white', 
                                fontWeight: 500,
                                fontSize: '1rem'
                              }}>
                        {comment.author}
                      </Typography>
                              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.6)' }}>
                        {formatDate(comment.created_at)}
                      </Typography>
                            </Box>
                    </Box>
                    
                          {/* Comment Content */}
                          <Typography variant="body1" sx={{ 
                            mb: 3, 
                            lineHeight: 1.6,
                            color: 'rgba(255,255,255,0.9)',
                            fontSize: '1rem'
                          }}>
                      {comment.content}
                    </Typography>
                    
                          {/* Comment Actions */}
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            gap: 2,
                            pt: 2,
                            borderTop: '1px solid rgba(255,255,255,0.1)'
                          }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => handleLikeComment(comment.id)}
                                sx={{ 
                                  color: comment.user_liked ? '#4f46e5' : 'rgba(255,255,255,0.7)',
                                  '&:hover': { 
                                    bgcolor: 'rgba(79, 70, 229, 0.1)',
                                    transform: 'scale(1.1)'
                                  },
                                  transition: 'all 0.2s ease'
                                }}
                      >
                        {comment.user_liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                      </IconButton>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {comment.likes_count || 0}
                      </Typography>
                            </Box>
                      
                            {/* Solution Button */}
                      {(selectedPost.post.author_username === localStorage.getItem('username') || 
                        selectedPost.post.author === localStorage.getItem('username')) && 
                       !selectedPost.post.is_solved && !comment.is_solution && (
                        <Button
                          size="small"
                          variant="contained"
                          onClick={() => {
                            setSelectedPostForSolution({
                              ...selectedPost,
                              clickedCommentId: comment.id
                            });
                            setShowSolutionDialog(true);
                          }}
                                startIcon={<CheckCircleIcon />}
                          sx={{ 
                                  background: 'linear-gradient(45deg, #4CAF50 0%, #66BB6A 100%)',
                            color: 'white',
                                  '&:hover': { 
                                    background: 'linear-gradient(45deg, #388E3C 0%, #4CAF50 100%)',
                                    transform: 'translateY(-1px)'
                                  },
                                  fontWeight: 'bold',
                                  borderRadius: 2,
                                  boxShadow: '0 4px 12px rgba(76, 175, 80, 0.3)',
                                  transition: 'all 0.2s ease'
                          }}
                        >
                                Çözüm Olarak İşaretle
                        </Button>
                      )}
                      
                            {/* Report Button */}
                      <IconButton
                        size="small"
                        onClick={() => {
                          setReportData(prev => ({ ...prev, post_id: selectedPost.post.id, comment_id: comment.id }));
                          setShowReportDialog(true);
                        }}
                              sx={{ 
                                color: 'rgba(255,255,255,0.7)',
                                '&:hover': { 
                                  bgcolor: 'rgba(244, 67, 54, 0.1)',
                                  transform: 'scale(1.1)'
                                },
                                transition: 'all 0.2s ease'
                              }}
                      >
                        <ReportIcon />
                      </IconButton>
                    </Box>
                        </CardContent>
                      </Card>
                ))}
                  </Box>
                )}
              </Box>
              
              {/* Add Comment Section */}
              <Card sx={{ 
                background: 'rgba(79, 70, 229, 0.05)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(79, 70, 229, 0.2)',
                borderRadius: 2,
                boxShadow: '0 8px 32px rgba(79, 70, 229, 0.1)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(79, 70, 229, 0.08)',
                  border: '1px solid rgba(79, 70, 229, 0.3)',
                  transform: 'translateY(-2px)'
                }
              }}>
                <CardContent>
                  <Typography variant="h6" sx={{ 
                    mb: 2, 
                    color: 'white',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1
                  }}>
                    <AddCommentIcon sx={{ color: '#4f46e5' }} />
                    Yorum Ekle
                  </Typography>
                <TextField
                  fullWidth
                    label="Yorumunuzu yazın..."
                  value={newComment.content}
                  onChange={(e) => setNewComment(prev => ({ ...prev, content: e.target.value }))}
                  multiline
                    rows={4}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                        '& fieldset': { borderColor: 'rgba(79, 70, 229, 0.3)' },
                        '&:hover fieldset': { borderColor: 'rgba(79, 70, 229, 0.5)' },
                        '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                        background: 'rgba(255,255,255,0.05)',
                        borderRadius: 1
                    },
                      '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' },
                      '& .MuiInputLabel-root.Mui-focused': { color: '#4f46e5' }
                  }}
                />
                </CardContent>
              </Card>
            </DialogContent>
            
            <DialogActions sx={{ 
              p: 3, 
              borderTop: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(30, 30, 50, 0.9)',
              backdropFilter: 'blur(20px)'
            }}>
              <Button 
                onClick={() => setOpenCommentDialog(false)} 
                sx={{ 
                  color: 'rgba(255,255,255,0.7)',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
                }}
              >
                Kapat
              </Button>
              <Button
                onClick={handleCreateComment}
                variant="contained"
                disabled={!newComment.content.trim()}
                startIcon={<SendIcon />}
                sx={{ 
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  '&:hover': { 
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                    transform: 'translateY(-1px)'
                  },
                  '&:disabled': { 
                    background: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.3)'
                  },
                  borderRadius: '20px',
                  px: 3,
                  py: 1,
                  fontWeight: 'bold',
                  boxShadow: '0 4px 12px rgba(79, 70, 229, 0.3)',
                  transition: 'all 0.2s ease'
                }}
              >
                Yorum Ekle
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Solution Marking Dialog */}
      <Dialog
        open={showSolutionDialog}
        onClose={() => setShowSolutionDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: 'rgba(30, 30, 30, 0.95)',
            color: 'white'
          }
        }}
      >
        <DialogTitle>Çözüm Olarak İşaretle</DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Bu yorumu çözüm olarak işaretlemek istediğinizden emin misiniz?
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
            Bu işlem geri alınamaz ve yorum sahibine bildirim gönderilecektir.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSolutionDialog(false)} sx={{ color: 'rgba(255,255,255,0.7)' }}>
            İptal
          </Button>
          <Button
            onClick={() => {
              if (selectedPostForSolution) {
                // Tıklanan yorumu bul (selectedPostForSolution'da saklanan yorum ID'si)
                const clickedCommentId = selectedPostForSolution.clickedCommentId;
                const comment = selectedPostForSolution.comments.find(c => c.id === clickedCommentId);
                if (comment) {
                  handleMarkAsSolution(
                    selectedPostForSolution.post.id, 
                    comment.id, 
                    comment.author
                  );
                }
              }
            }}
            variant="contained"
            sx={{ bgcolor: '#4CAF50', '&:hover': { bgcolor: '#388E3C' } }}
          >
            Çözüm Olarak İşaretle
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Report Dialog */}
      <Dialog open={showReportDialog} onClose={() => setShowReportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ bgcolor: '#1a1a1a', color: 'white' }}>
          İçerik Raporla
        </DialogTitle>
        <DialogContent sx={{ bgcolor: '#1a1a1a' }}>
          <FormControl fullWidth margin="normal">
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Rapor Nedeni</InputLabel>
            <Select
              value={reportData.reason}
              onChange={(e) => setReportData(prev => ({ ...prev, reason: e.target.value }))}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' }
              }}
            >
              <MenuItem value="spam">Spam</MenuItem>
              <MenuItem value="inappropriate">Uygunsuz İçerik</MenuItem>
              <MenuItem value="duplicate">Tekrar</MenuItem>
              <MenuItem value="other">Diğer</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Açıklama"
            value={reportData.description}
            onChange={(e) => setReportData(prev => ({ ...prev, description: e.target.value }))}
            margin="normal"
            sx={{
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' }
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ bgcolor: '#1a1a1a' }}>
          <Button onClick={() => setShowReportDialog(false)} sx={{ color: 'white' }}>
            İptal
          </Button>
          <Button onClick={reportContent} variant="contained" sx={{ bgcolor: '#f44336', color: 'white' }}>
            Raporla
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Post Dialog */}
      <Dialog 
        open={showDeleteDialog} 
        onClose={() => setShowDeleteDialog(false)} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            background: 'rgba(20, 20, 40, 0.95)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: 3,
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            color: 'white'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'rgba(30, 30, 50, 0.9)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          fontWeight: 600
        }}>
          Gönderiyi Sil
        </DialogTitle>
        <DialogContent sx={{ 
          background: 'rgba(20, 20, 40, 0.9)',
          backdropFilter: 'blur(20px)',
          pt: 3
        }}>
          <Typography variant="body1" sx={{ mb: 2, color: 'white' }}>
            Bu gönderiyi silmek istediğinizden emin misiniz?
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 3 }}>
            Bu işlem geri alınamaz. Gönderi ve tüm yorumları kalıcı olarak silinecektir.
          </Typography>
          {postToDelete && (
            <Card sx={{ 
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 2
            }}>
              <CardContent>
                <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
                  {postToDelete.title}
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                  {postToDelete.content.substring(0, 100)}...
                </Typography>
              </CardContent>
            </Card>
          )}
        </DialogContent>
        <DialogActions sx={{ 
          background: 'rgba(30, 30, 50, 0.9)',
          backdropFilter: 'blur(20px)',
          borderTop: '1px solid rgba(255,255,255,0.1)',
          p: 2
        }}>
          <Button 
            onClick={() => setShowDeleteDialog(false)} 
            sx={{
              color: 'rgba(255,255,255,0.7)',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
            }}
          >
            İptal
          </Button>
          <Button
            onClick={() => postToDelete && handleDeletePost(postToDelete.id)}
            variant="contained"
            sx={{ 
              background: 'linear-gradient(45deg, #f44336 0%, #d32f2f 100%)',
              '&:hover': { 
                background: 'linear-gradient(45deg, #d32f2f 0%, #b71c1c 100%)',
                transform: 'translateY(-1px)'
              },
              borderRadius: '20px',
              px: 3,
              py: 1,
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(244, 67, 54, 0.3)',
              transition: 'all 0.2s ease'
            }}
          >
            Sil
          </Button>
        </DialogActions>
      </Dialog>
        </Container>
      </Box>
    </motion.div>
  );
};

export default Forum; 