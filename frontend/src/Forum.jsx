import React, { useState, useEffect } from 'react';
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
  Notifications as NotificationsIcon,
  NotificationsActive as NotificationsActiveIcon,
  EmojiEvents as EmojiEventsIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Report as ReportIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon
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
    tags: [],
    is_anonymous: false
  });
  const [newComment, setNewComment] = useState({
    content: '',
    is_anonymous: false
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [postTypeFilter, setPostTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('latest');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [notifications, setNotifications] = useState([]);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
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

  const postTypes = [
    { value: 'discussion', label: 'Tartışma' },
    { value: 'question', label: 'Soru' },
    { value: 'resource', label: 'Kaynak' },
    { value: 'announcement', label: 'Duyuru' }
  ];

  const sortOptions = [
    { value: 'latest', label: 'En Yeni' },
    { value: 'popular', label: 'En Popüler' },
    { value: 'most_commented', label: 'En Çok Yorum Alan' }
  ];

  useEffect(() => {
    fetchPosts();
    fetchStats();
    fetchNotifications();
    fetchLeaderboard();
  }, [currentPage, searchTerm, postTypeFilter, sortBy]);

  const fetchNotifications = async () => {
    try {
      const response = await fetch('http://localhost:5000/forum/notifications', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications);
        setUnreadNotifications(data.notifications.filter(n => !n.is_read).length);
      } else if (response.status === 401) {
        // Session hatası - sessizce işlemi durdur
        return;
      }
    } catch (err) {
      console.error('Bildirimler yüklenemedi:', err);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch('http://localhost:5000/forum/leaderboard', {
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
      const response = await fetch('http://localhost:5000/forum/report', {
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

  const markNotificationsRead = async () => {
    try {
      const response = await fetch('http://localhost:5000/forum/notifications/mark-read', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        setUnreadNotifications(0);
        fetchNotifications();
      }
    } catch (err) {
      console.error('Bildirimler işaretlenemedi:', err);
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
          const postResponse = await fetch(`http://localhost:5000/forum/posts/${selectedPost.post.id}`, {
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
      const response = await fetch(`http://localhost:5000/forum/posts/${postId}/solve`, {
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
          const postResponse = await fetch(`http://localhost:5000/forum/posts/${selectedPost.post.id}`, {
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

  const fetchPosts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage,
        per_page: 10,
        type: postTypeFilter,
        sort: sortBy,
        search: searchTerm
      });

      const response = await fetch(`http://localhost:5000/forum/posts?${params}`, {
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
      const response = await fetch('http://localhost:5000/forum/stats', {
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
      const response = await fetch('http://localhost:5000/forum/posts', {
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
        tags: [],
        is_anonymous: false
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
      const response = await fetch(`http://localhost:5000/forum/posts/${postId}/like`, {
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
      const response = await fetch(`http://localhost:5000/forum/posts/${post.id}`, {
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
      const response = await fetch(`http://localhost:5000/forum/posts/${selectedPost.post.id}/comments`, {
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
        content: '',
        is_anonymous: false
      });
      
      // Gönderiyi yeniden yükle
      const postResponse = await fetch(`http://localhost:5000/forum/posts/${selectedPost.post.id}`, {
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

  if (loading && posts.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h6" align="center" sx={{ color: 'white' }}>Yükleniyor...</Typography>
      </Container>
    );
  }

  return (
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
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom sx={{ color: 'white' }}>
              <ForumIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
              Forum
            </Typography>
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              İlgi alanınızdaki diğer kullanıcılarla tartışın, sorular sorun ve deneyimlerinizi paylaşın.
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
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
            
            <Tooltip title="Bildirimler">
              <IconButton
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  if (unreadNotifications > 0) {
                    markNotificationsRead();
                  }
                }}
                sx={{
                  color: 'white',
                  bgcolor: 'rgba(255,255,255,0.1)',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' }
                }}
              >
                <Badge badgeContent={unreadNotifications} color="error">
                  {unreadNotifications > 0 ? <NotificationsActiveIcon /> : <NotificationsIcon />}
                </Badge>
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 4 }}>
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
      )}

            {/* Notifications Panel */}
      <Card sx={{ 
        mb: 3, 
        bgcolor: 'rgba(255,255,255,0.05)', 
        maxHeight: showNotifications ? 400 : 0,
        overflow: 'hidden',
        transition: 'max-height 0.3s ease-in-out',
        opacity: showNotifications ? 1 : 0,
        position: 'relative',
        zIndex: 1
      }}>
        {showNotifications && (
          <CardContent>
            <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
              Bildirimler ({notifications.length})
            </Typography>
            {notifications.length === 0 ? (
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center' }}>
                Henüz bildiriminiz yok.
              </Typography>
            ) : (
              <List>
                {notifications.map((notification) => (
                  <ListItem key={notification.id} sx={{ 
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    bgcolor: notification.is_read ? 'transparent' : 'rgba(79, 70, 229, 0.1)'
                  }}>
                    <ListItemText
                      primary={notification.title}
                      secondary={
                        <Box>
                          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                            {notification.message}
                          </Typography>
                          <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                            {formatDate(notification.created_at)}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        )}
      </Card>

      {/* Leaderboard Panel */}
      {showLeaderboard && (
        <Card sx={{ mb: 3, bgcolor: 'rgba(255,255,255,0.05)' }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: 'white', mb: 2 }}>
              🏆 Liderlik Tablosu
            </Typography>
            {leaderboard.length === 0 ? (
              <Typography sx={{ color: 'rgba(255,255,255,0.7)', textAlign: 'center' }}>
                Henüz yeterli veri yok.
              </Typography>
            ) : (
              <List>
                {leaderboard.slice(0, 10).map((user, index) => (
                  <ListItem key={user.username} sx={{ 
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    bgcolor: index < 3 ? 'rgba(255, 215, 0, 0.1)' : 'transparent'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                      <Typography variant="h6" sx={{ 
                        color: index < 3 ? '#FFD700' : 'white',
                        minWidth: 40
                      }}>
                        #{user.rank}
                      </Typography>
                      <Avatar sx={{ bgcolor: '#4f46e5' }}>
                        {user.username.charAt(0).toUpperCase()}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" sx={{ color: 'white' }}>
                          {user.username}
                        </Typography>
                        <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                          {user.total_points} puan • {user.activity_count} aktivite
                        </Typography>
                      </Box>
                    </Box>
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filters and Search */}
      <Card sx={{ mb: 3, bgcolor: 'rgba(255,255,255,0.05)' }}>
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
                  )
                }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    color: 'white',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' }
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
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' }
                  }}
                >
                  <MenuItem value="all">Tümü</MenuItem>
                  {postTypes.map(type => (
                    <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Sıralama</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  sx={{
                    color: 'white',
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' }
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
                sx={{ bgcolor: '#4f46e5', '&:hover': { bgcolor: '#4338ca' } }}
              >
                Yeni Gönderi
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Posts List */}
      <Box sx={{ mb: 3 }}>
        {posts.map((post) => (
          <Card
            key={post.id}
            sx={{
              mb: 2,
              bgcolor: post.is_solved ? 'rgba(76, 175, 80, 0.1)' : 'rgba(255,255,255,0.05)',
              border: post.is_solved ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                bgcolor: post.is_solved ? 'rgba(76, 175, 80, 0.15)' : 'rgba(255,255,255,0.08)',
                transform: 'translateY(-2px)'
              }
            }}
            onClick={() => handlePostClick(post)}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Typography variant="h6" sx={{ color: 'white' }}>
                      {post.title}
                    </Typography>
                    {post.is_solved && (
                      <Chip
                        label="✅ Çözüldü"
                        size="small"
                        sx={{
                          bgcolor: '#4CAF50',
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.7rem'
                        }}
                      />
                    )}
                  </Box>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mb: 2 }}>
                    {post.content}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {post.is_solved && (
                    <Chip
                      label="SOLVED"
                      size="small"
                      sx={{
                        bgcolor: '#4CAF50',
                        color: 'white',
                        fontWeight: 'bold',
                        fontSize: '0.6rem',
                        alignSelf: 'flex-end'
                      }}
                    />
                  )}
                  <Chip
                    label={postTypes.find(t => t.value === post.post_type)?.label || post.post_type}
                    color={getPostTypeColor(post.post_type)}
                    size="small"
                  />
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon />
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {post.author}
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
                      sx={{ mr: 1, mb: 1, bgcolor: 'rgba(79, 70, 229, 0.2)', color: 'white' }}
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
                    sx={{ color: post.user_liked ? '#4f46e5' : 'rgba(255,255,255,0.7)' }}
                  >
                    {post.user_liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                  </IconButton>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                    {post.likes_count}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setReportData(prev => ({ ...prev, post_id: post.id, comment_id: null }));
                      setShowReportDialog(true);
                    }}
                    sx={{ color: 'rgba(255,255,255,0.7)' }}
                  >
                    <ReportIcon />
                  </IconButton>
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
                
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>

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
            bgcolor: 'rgba(30, 30, 30, 0.95)',
            color: 'white'
          }
        }}
      >
        <DialogTitle>Yeni Gönderi Oluştur</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Başlık"
            value={newPost.title}
            onChange={(e) => setNewPost(prev => ({ ...prev, title: e.target.value }))}
            margin="normal"
            sx={{
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' }
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
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
                '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' }
              },
              '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
            }}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Gönderi Türü</InputLabel>
            <Select
              value={newPost.post_type}
              onChange={(e) => setNewPost(prev => ({ ...prev, post_type: e.target.value }))}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' }
              }}
            >
              {postTypes.map(type => (
                <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPostDialog(false)} sx={{ color: 'rgba(255,255,255,0.7)' }}>
            İptal
          </Button>
          <Button
            onClick={handleCreatePost}
            variant="contained"
            sx={{ bgcolor: '#4f46e5', '&:hover': { bgcolor: '#4338ca' } }}
          >
            Oluştur
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Post and Comments Dialog */}
      <Dialog
        open={openCommentDialog}
        onClose={() => setOpenCommentDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: 'rgba(30, 30, 30, 0.95)',
            color: 'white',
            maxHeight: '80vh'
          }
        }}
      >
        {selectedPost && (
          <>
            <DialogTitle>
              <Typography variant="h6">{selectedPost.post.title}</Typography>
              <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)', mt: 1 }}>
                {selectedPost.post.author} • {formatDate(selectedPost.post.created_at)}
              </Typography>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" sx={{ mb: 3 }}>
                {selectedPost.post.content}
              </Typography>
              
              <Divider sx={{ my: 2, borderColor: 'rgba(255,255,255,0.2)' }} />
              
              <Typography variant="h6" sx={{ mb: 2 }}>Yorumlar ({selectedPost.comments.length})</Typography>
              
              <List>
                {selectedPost.comments.map((comment) => (
                  <ListItem key={comment.id} sx={{ 
                    flexDirection: 'column', 
                    alignItems: 'flex-start',
                    border: comment.is_solution ? '2px solid #4CAF50' : '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 2,
                    mb: 2,
                    bgcolor: comment.is_solution ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1, width: '100%' }}>
                      <Avatar sx={{ width: 32, height: 32, bgcolor: '#4f46e5' }}>
                        {comment.author.charAt(0).toUpperCase()}
                      </Avatar>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {comment.author}
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.5)' }}>
                        {formatDate(comment.created_at)}
                      </Typography>
                      
                      {/* Çözüm işareti */}
                      {comment.is_solution && (
                        <Chip
                          label="✅ Çözüm"
                          size="small"
                          sx={{ 
                            bgcolor: '#4CAF50', 
                            color: 'white',
                            ml: 'auto'
                          }}
                        />
                      )}
                    </Box>
                    
                    <Typography variant="body1" sx={{ mb: 2, width: '100%' }}>
                      {comment.content}
                    </Typography>
                    
                    {/* Yorum aksiyonları */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                      {/* Beğen butonu */}
                      <IconButton
                        size="small"
                        onClick={() => handleLikeComment(comment.id)}
                        sx={{ color: comment.user_liked ? '#4f46e5' : 'rgba(255,255,255,0.7)' }}
                      >
                        {comment.user_liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
                      </IconButton>
                      <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                        {comment.likes_count || 0}
                      </Typography>
                      
                      {/* Çözüm olarak işaretle butonu (sadece gönderi sahibi görebilir) */}
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
                          sx={{ 
                            bgcolor: '#4CAF50',
                            color: 'white',
                            '&:hover': { bgcolor: '#388E3C' },
                            fontWeight: 'bold'
                          }}
                        >
                          ✅ Çözüm Olarak İşaretle
                        </Button>
                      )}
                      
                      {/* Gönderi sahibi değilse bilgi mesajı */}
                      {selectedPost.post.author_username !== localStorage.getItem('username') && 
                       !selectedPost.post.is_solved && (
                        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', ml: 1 }}>
                          💡 Sadece gönderi sahibi çözüm işaretleyebilir
                        </Typography>
                      )}
                      
                      {/* Rapor butonu */}
                      <IconButton
                        size="small"
                        onClick={() => {
                          setReportData(prev => ({ ...prev, post_id: selectedPost.post.id, comment_id: comment.id }));
                          setShowReportDialog(true);
                        }}
                        sx={{ color: 'rgba(255,255,255,0.7)' }}
                      >
                        <ReportIcon />
                      </IconButton>
                    </Box>
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Yorum Ekle</Typography>
                <TextField
                  fullWidth
                  label="Yorumunuz"
                  value={newComment.content}
                  onChange={(e) => setNewComment(prev => ({ ...prev, content: e.target.value }))}
                  multiline
                  rows={3}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: 'rgba(255,255,255,0.7)' }
                  }}
                />
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setOpenCommentDialog(false)} sx={{ color: 'rgba(255,255,255,0.7)' }}>
                Kapat
              </Button>
              <Button
                onClick={handleCreateComment}
                variant="contained"
                sx={{ bgcolor: '#4f46e5', '&:hover': { bgcolor: '#4338ca' } }}
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
      </Container>
      </Box>
    );
  };

export default Forum; 