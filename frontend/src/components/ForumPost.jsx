import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  IconButton,
  Collapse,
  Avatar,
  Tooltip,
  Divider
} from '@mui/material';
import {
  ThumbUp as ThumbUpIcon,
  ThumbUpOutlined as ThumbUpOutlinedIcon,
  Comment as CommentIcon,
  Visibility as VisibilityIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AdminPanelSettings as AdminIcon,
  Announcement as AnnouncementIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const ForumPost = ({ post, onLike, onComment, onView }) => {
  const { user } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const [liked, setLiked] = useState(post.user_liked || false);

  const handleLike = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`/forum/posts/${post.id}/like`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (response.ok) {
        setLiked(!liked);
        if (onLike) onLike(post.id, !liked);
      }
    } catch (error) {
      console.error('Like error:', error);
    }
  };

  const handleComment = () => {
    if (onComment) onComment(post.id);
  };

  const handleView = () => {
    if (onView) onView(post.id);
  };

  const getPostTypeIcon = (postType) => {
    switch (postType) {
      case 'announcement':
        return <AnnouncementIcon fontSize="small" />;
      case 'question':
        return <CommentIcon fontSize="small" />;
      case 'resource':
        return <VisibilityIcon fontSize="small" />;
      default:
        return <CommentIcon fontSize="small" />;
    }
  };

  const getPostTypeColor = (postType) => {
    switch (postType) {
      case 'announcement':
        return 'warning';
      case 'question':
        return 'info';
      case 'resource':
        return 'success';
      default:
        return 'default';
    }
  };

  const getPostTypeLabel = (postType) => {
    switch (postType) {
      case 'announcement':
        return 'Duyuru';
      case 'question':
        return 'Soru';
      case 'resource':
        return 'Kaynak';
      case 'tutorial':
        return 'Öğretici';
      default:
        return 'Tartışma';
    }
  };

  // Admin gönderisi için özel stil
  const getCardStyle = () => {
    if (post.is_admin_post) {
      return {
        mb: 2,
        border: '2px solid #1976d2', // Mavi border (admin için)
        backgroundColor: '#f3f8ff', // Açık mavi arka plan
        boxShadow: '0 4px 8px rgba(25, 118, 210, 0.1)' // Mavi gölge
      };
    }
    
    if (post.is_solved) {
      return {
        mb: 2,
        border: '2px solid #4caf50', // Yeşil border (çözülen sorular için)
        backgroundColor: '#f8fff8', // Açık yeşil arka plan
        boxShadow: '0 4px 8px rgba(76, 175, 80, 0.1)' // Yeşil gölge
      };
    }
    
    return {
      mb: 2,
      border: '1px solid #e0e0e0',
      backgroundColor: 'inherit'
    };
  };

  return (
    <Card sx={getCardStyle()}>
      <CardContent>
        {/* Başlık ve Admin İşaretlemesi */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="h2" gutterBottom>
              {post.title}
            </Typography>
            
            {/* Admin ve Post Type Chips */}
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
              {post.is_admin_post && (
                <Chip
                  icon={<AdminIcon />}
                  label="Admin"
                  color="primary" // Mavi renk (admin için)
                  size="small"
                  variant="filled"
                />
              )}
              
              <Chip
                icon={getPostTypeIcon(post.post_type)}
                label={getPostTypeLabel(post.post_type)}
                color={getPostTypeColor(post.post_type)}
                size="small"
                variant="outlined"
              />
              
              {post.is_solved && (
                <Chip
                  label="Çözüldü"
                  color="success" // Yeşil renk (çözülen sorular için)
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </Box>

        {/* İçerik */}
        <Typography 
          variant="body2" 
          color="textSecondary" 
          sx={{ 
            mb: 2,
            maxHeight: expanded ? 'none' : '4.5em',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: expanded ? 'none' : 3,
            WebkitBoxOrient: 'vertical'
          }}
        >
          {post.content}
        </Typography>

        {/* Etiketler */}
        {post.tags && post.tags.length > 0 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
            {post.tags.map((tag, index) => (
              <Chip
                key={index}
                label={tag}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.75rem' }}
              />
            ))}
          </Box>
        )}

        {/* Meta Bilgiler */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
              {post.author.charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="body2" color="textSecondary">
              {post.author}
            </Typography>
          </Box>
          
          <Typography variant="body2" color="textSecondary">
            {new Date(post.created_at).toLocaleDateString('tr-TR')}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <VisibilityIcon fontSize="small" color="action" />
            <Typography variant="body2" color="textSecondary">
              {post.views}
            </Typography>
          </Box>
        </Box>

        {/* İstatistikler */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              size="small" 
              onClick={handleLike}
              color={liked ? 'primary' : 'default'}
            >
              {liked ? <ThumbUpIcon /> : <ThumbUpOutlinedIcon />}
            </IconButton>
            <Typography variant="body2" color="textSecondary">
              {post.likes_count}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CommentIcon fontSize="small" color="action" />
            <Typography variant="body2" color="textSecondary">
              {post.comments_count}
            </Typography>
          </Box>
        </Box>

        {/* Çözüm Bilgisi */}
        {post.is_solved && post.solved_by && (
          <Box sx={{ 
            backgroundColor: '#e8f5e8', 
            p: 1, 
            borderRadius: 1, 
            mb: 2,
            border: '1px solid #4caf50'
          }}>
            <Typography variant="body2" color="success.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip label="Çözüldü" color="success" size="small" />
              {post.solved_by} tarafından çözüldü
              {post.solved_at && (
                <span> - {new Date(post.solved_at).toLocaleDateString('tr-TR')}</span>
              )}
            </Typography>
          </Box>
        )}
      </CardContent>

      <Divider />

      <CardActions sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            startIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Daha Az' : 'Daha Fazla'}
          </Button>
          
          <Button
            size="small"
            startIcon={<CommentIcon />}
            onClick={handleComment}
          >
            Yorum Yap
          </Button>
        </Box>

        <Button
          size="small"
          variant="outlined"
          onClick={handleView}
        >
          Görüntüle
        </Button>
      </CardActions>
    </Card>
  );
};

export default ForumPost;
