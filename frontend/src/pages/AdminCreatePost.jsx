import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  OutlinedInput,
  Alert,
  Paper,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Add as AddIcon,
  Send as SendIcon,
  Forum as ForumIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const AdminCreatePost = () => {
  const { user } = useAuth();
  const [postData, setPostData] = useState({
    title: '',
    content: '',
    interest: '',
    post_type: 'announcement',
    tags: []
  });
  const [newTag, setNewTag] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // İlgi alanları listesi
  const interests = [
    'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust',
    'React', 'Vue', 'Angular', 'Node.js', 'Django', 'Flask', 'Spring', 'Laravel',
    'Machine Learning', 'Data Science', 'DevOps', 'Mobile Development', 'Game Development'
  ];

  // Post türleri
  const postTypes = [
    { value: 'announcement', label: 'Duyuru' },
    { value: 'discussion', label: 'Tartışma' },
    { value: 'question', label: 'Soru' },
    { value: 'resource', label: 'Kaynak' },
    { value: 'tutorial', label: 'Öğretici' }
  ];

  const handleAddTag = () => {
    if (newTag.trim() && !postData.tags.includes(newTag.trim())) {
      setPostData({
        ...postData,
        tags: [...postData.tags, newTag.trim()]
      });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setPostData({
      ...postData,
      tags: postData.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!postData.title || !postData.content || !postData.interest) {
      setError('Başlık, içerik ve ilgi alanı zorunludur');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/admin/forum/create-post', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(postData)
      });

      if (response.ok) {
        const result = await response.json();
        setSuccess('Admin gönderisi başarıyla oluşturuldu!');
        
        // Formu temizle
        setPostData({
          title: '',
          content: '',
          interest: '',
          post_type: 'announcement',
          tags: []
        });
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Gönderi oluşturulamadı');
      }
    } catch (err) {
      setError('Sunucu hatası oluştu');
    } finally {
      setLoading(false);
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

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <ForumIcon /> Admin Gönderisi Oluştur
      </Typography>

      <Grid container spacing={3}>
        {/* Sol taraf - Form */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <form onSubmit={handleSubmit}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                  {error}
                </Alert>
              )}

              {success && (
                <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                  {success}
                </Alert>
              )}

              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Başlık"
                    value={postData.title}
                    onChange={(e) => setPostData({ ...postData, title: e.target.value })}
                    required
                    placeholder="Gönderi başlığı"
                    inputProps={{ maxLength: 200 }}
                    helperText={`${postData.title.length}/200 karakter`}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={8}
                    label="İçerik"
                    value={postData.content}
                    onChange={(e) => setPostData({ ...postData, content: e.target.value })}
                    required
                    placeholder="Gönderi içeriği..."
                    inputProps={{ maxLength: 10000 }}
                    helperText={`${postData.content.length}/10000 karakter`}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth required>
                    <InputLabel>İlgi Alanı</InputLabel>
                    <Select
                      value={postData.interest}
                      onChange={(e) => setPostData({ ...postData, interest: e.target.value })}
                      label="İlgi Alanı"
                    >
                      {interests.map((interest) => (
                        <MenuItem key={interest} value={interest}>
                          {interest}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Gönderi Türü</InputLabel>
                    <Select
                      value={postData.post_type}
                      onChange={(e) => setPostData({ ...postData, post_type: e.target.value })}
                      label="Gönderi Türü"
                    >
                      {postTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Etiketler
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      <TextField
                        size="small"
                        placeholder="Yeni etiket ekle"
                        value={newTag}
                        onChange={(e) => setNewTag(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                        sx={{ flexGrow: 1 }}
                      />
                      <Button
                        variant="outlined"
                        onClick={handleAddTag}
                        disabled={!newTag.trim()}
                        startIcon={<AddIcon />}
                      >
                        Ekle
                      </Button>
                    </Box>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {postData.tags.map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          onDelete={() => handleRemoveTag(tag)}
                          color="primary"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                </Grid>

                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      size="large"
                      disabled={loading || !postData.title || !postData.content || !postData.interest}
                      startIcon={<SendIcon />}
                    >
                      {loading ? 'Oluşturuluyor...' : 'Gönderiyi Oluştur'}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
          </Paper>
        </Grid>

        {/* Sağ taraf - Bilgi kartları */}
        <Grid item xs={12} md={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Admin Gönderisi Özellikleri
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    Admin olarak oluşturduğunuz gönderiler özel olarak işaretlenir ve 
                    kullanıcılar tarafından kolayca tanınır.
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label="Admin" color="primary" size="small" />
                    <Typography variant="body2">
                      Admin tarafından atıldığı belirtilir
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Gönderi Türleri
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {postTypes.map((type) => (
                      <Box key={type.value} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip 
                          label={type.label} 
                          size="small" 
                          variant={postData.post_type === type.value ? "filled" : "outlined"}
                          color={postData.post_type === type.value ? "primary" : "default"}
                        />
                      </Box>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    İpuçları
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    • Başlık net ve açıklayıcı olmalı
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    • İçerik detaylı ve faydalı olmalı
                  </Typography>
                  <Typography variant="body2" color="textSecondary" paragraph>
                    • Etiketler konuyu iyi yansıtmalı
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    • İlgi alanı doğru seçilmeli
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Container>
  );
};

export default AdminCreatePost;
