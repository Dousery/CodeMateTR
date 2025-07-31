import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Button, 
  CircularProgress, 
  Alert,
  Stack,
  Card,
  CardContent,
  CardActions,
  Chip,
  LinearProgress,
  Input,
  FormControl,
  InputLabel,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { 
  CloudUpload as UploadIcon,
  Work as WorkIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Star as StarIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  OpenInNew as OpenInNewIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function JobSearch() {
  const [cvFile, setCvFile] = useState(null);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [matchedJobs, setMatchedJobs] = useState([]);
  const [searchRecommendations, setSearchRecommendations] = useState([]);
  const [positionsFound, setPositionsFound] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState('upload'); // upload, results
  const [totalJobsAnalyzed, setTotalJobsAnalyzed] = useState(0);

  const handleCvUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Dosya kontrolü
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(file.type)) {
        setError('Sadece PDF, DOC ve DOCX dosyaları kabul edilir.');
        return;
      }
      
      if (file.size > 16 * 1024 * 1024) { // 16MB
        setError('Dosya boyutu 16MB\'dan küçük olmalıdır.');
        return;
      }
      
      setCvFile(file);
      setError('');
    }
  };

  const handleJobSearch = async () => {
    if (!cvFile) {
      setError('Lütfen CV dosyanızı yükleyin.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('cv', cvFile);

      const response = await axios.post('http://localhost:5000/job_search', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        withCredentials: true
      });

      if (response.data.success) {
        setCvAnalysis(response.data.cv_analysis);
        setMatchedJobs(response.data.jobs || []);
        setStep('results');
      } else {
        setError(response.data.error || 'İş eşleştirmesi başarısız oldu.');
      }
    } catch (err) {
      console.error('İş arama hatası:', err);
      setError(err.response?.data?.error || 'İş arama sırasında bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  const resetSearch = () => {
    setCvFile(null);
    setCvAnalysis(null);
    setMatchedJobs([]);
    setSearchRecommendations([]);
    setPositionsFound([]);
    setError('');
    setStep('upload');
    setTotalJobsAnalyzed(0);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#4caf50'; // Green
    if (score >= 60) return '#ff9800'; // Orange
    return '#f44336'; // Red
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Mükemmel Uyum';
    if (score >= 60) return 'İyi Uyum';
    return 'Orta Uyum';
  };

  if (step === 'upload') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card" 
          sx={{ p: 5, minWidth: 400, maxWidth: 600, borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={2} color="white" textAlign="center">
            İş Bulma Asistanı
          </Typography>
          <Typography textAlign="center" mb={3} color="rgba(255,255,255,0.8)">
            CV'nizi yükleyin, size uygun iş ilanlarını bulalım!
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          {/* CV Upload Section */}
          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <Input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleCvUpload}
                sx={{ display: 'none' }}
                id="cv-upload"
              />
              <label htmlFor="cv-upload">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<UploadIcon />}
                  fullWidth
                  sx={{
                    py: 2,
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'rgba(255,255,255,0.5)',
                      background: 'rgba(255,255,255,0.1)',
                    }
                  }}
                >
                  {cvFile ? cvFile.name : 'CV Dosyası Seçin (PDF, DOC, DOCX)'}
                </Button>
              </label>
            </FormControl>
            
            {cvFile && (
              <Typography variant="body2" color="rgba(255,255,255,0.7)" textAlign="center">
                Seçilen dosya: {cvFile.name} ({(cvFile.size / 1024 / 1024).toFixed(2)} MB)
              </Typography>
            )}
          </Box>

          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={handleJobSearch}
            disabled={loading || !cvFile}
            endIcon={loading && <CircularProgress size={20} color="inherit" />}
            startIcon={<WorkIcon />}
            sx={{
              background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
              borderRadius: '25px',
              py: 1.5,
              textTransform: 'none',
              fontWeight: 600,
              boxShadow: '0 4px 15px rgba(79, 70, 229, 0.4)',
              '&:hover': {
                background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                boxShadow: '0 6px 20px rgba(79, 70, 229, 0.6)',
              }
            }}
          >
            {loading ? 'İş İlanları Aranıyor...' : 'İş İlanlarını Ara'}
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'results') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        <Grid container spacing={4} sx={{ maxWidth: 1200, mx: 'auto', px: 2 }}>
          {/* Header */}
          <Grid item xs={12}>
            <Paper 
              component={motion.div} 
              initial={{ opacity: 0, y: 20 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.5 }} 
              elevation={8} 
              className="glass-card" 
              sx={{ p: 3, borderRadius: 4 }}
            >
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight={700} color="white" mb={1}>
                    İş Eşleştirme Sonuçları
                  </Typography>
                  <Typography color="rgba(255,255,255,0.8)">
                    {totalJobsAnalyzed} iş ilanı analiz edildi, {matchedJobs.length} uygun iş bulundu
                  </Typography>
                </Box>
                <Button 
                  variant="outlined" 
                  startIcon={<RefreshIcon />}
                  onClick={resetSearch}
                  sx={{
                    borderColor: 'rgba(255,255,255,0.3)',
                    color: 'white',
                    '&:hover': {
                      borderColor: 'rgba(255,255,255,0.5)',
                      background: 'rgba(255,255,255,0.1)',
                    }
                  }}
                >
                  Yeni Arama
                </Button>
              </Stack>
            </Paper>
          </Grid>

          {/* CV Analysis */}
          {cvAnalysis && (
            <Grid item xs={12}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.5, delay: 0.1 }} 
                elevation={8} 
                className="glass-card" 
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Typography variant="h6" fontWeight={600} color="white" mb={2}>
                  CV Analizi
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                      <strong>Deneyim:</strong> {cvAnalysis.experience_years} yıl
                    </Typography>
                    <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                      <strong>Beceriler:</strong>
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      {cvAnalysis.skills.map((skill, index) => (
                        <Chip 
                          key={index} 
                          label={skill} 
                          size="small" 
                          sx={{ 
                            mr: 1, 
                            mb: 1, 
                            bgcolor: 'rgba(79, 70, 229, 0.3)',
                            color: 'white'
                          }} 
                        />
                      ))}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                      <strong>Teknolojiler:</strong>
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      {cvAnalysis.technologies.map((tech, index) => (
                        <Chip 
                          key={index} 
                          label={tech} 
                          size="small" 
                          sx={{ 
                            mr: 1, 
                            mb: 1, 
                            bgcolor: 'rgba(124, 58, 237, 0.3)',
                            color: 'white'
                          }} 
                        />
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          )}

          {/* İş Arama Siteleri Önerileri */}
          {searchRecommendations.length > 0 && (
            <Grid item xs={12}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.5, delay: 0.2 }} 
                elevation={8} 
                className="glass-card" 
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Typography variant="h6" fontWeight={600} color="white" mb={2}>
                  🔍 Önerilen İş Arama Siteleri
                </Typography>
                <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={3}>
                  CV analiziniz tamamlandı. Aşağıdaki sitelerde güncel iş ilanlarını bulabilirsiniz:
                </Typography>
                
                <Grid container spacing={2}>
                  {searchRecommendations.map((site, index) => (
                    <Grid item xs={12} sm={6} md={4} key={index}>
                      <Card 
                        component={motion.div}
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ 
                          duration: 0.5, 
                          delay: 0.3 + (index * 0.1),
                          type: "spring",
                          stiffness: 120
                        }}
                        elevation={4}
                        className="glass-card"
                        sx={{
                          borderRadius: 3,
                          cursor: 'pointer',
                          transition: 'all 0.3s ease',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                          }
                        }}
                        onClick={() => window.open(site.search_url, '_blank')}
                      >
                        <CardContent sx={{ p: 2 }}>
                          <Typography variant="h6" fontWeight={600} color="white" mb={1}>
                            {site.site_name}
                          </Typography>
                          <Typography variant="body2" color="rgba(255,255,255,0.7)" mb={2}>
                            {site.description}
                          </Typography>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<OpenInNewIcon />}
                            sx={{
                              borderColor: 'rgba(255,255,255,0.5)',
                              color: 'white',
                              '&:hover': {
                                borderColor: 'white',
                                background: 'rgba(255,255,255,0.1)',
                              }
                            }}
                          >
                            Siteyi Ziyaret Et
                          </Button>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            </Grid>
          )}

          {/* Job Listings - Forum Style */}
          {matchedJobs.length > 0 && (
            <Grid item xs={12}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.5, delay: 0.3 }} 
                elevation={8} 
                className="glass-card" 
                sx={{ p: 3, borderRadius: 4 }}
              >
                <Typography variant="h6" fontWeight={600} color="white" mb={3}>
                  🎯 Size Uygun İş İlanları ({matchedJobs.length})
                </Typography>
                
                <Stack spacing={2}>
                  {matchedJobs.map((job, index) => (
                    <Card 
                      key={index}
                      component={motion.div}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ 
                        duration: 0.5, 
                        delay: 0.4 + (index * 0.1),
                        type: "spring",
                        stiffness: 100
                      }}
                      elevation={4}
                      className="glass-card"
                      sx={{
                        borderRadius: 2,
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'translateX(8px)',
                          boxShadow: '0 4px 20px rgba(0,0,0,0.15)'
                        }
                      }}
                      onClick={() => window.open(job.url, '_blank')}
                    >
                      <CardContent sx={{ p: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          {/* Sol taraf - İş bilgileri */}
                          <Box sx={{ flex: 1, mr: 2 }}>
                            <Typography variant="h6" fontWeight="bold" color="white" mb={1}>
                              {job.title}
                            </Typography>
                            
                            <Stack spacing={1} sx={{ mb: 2 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <BusinessIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 16 }} />
                                <Typography color="rgba(255,255,255,0.8)" variant="body2">
                                  {job.company}
                                </Typography>
                              </Box>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <LocationIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 16 }} />
                                <Typography color="rgba(255,255,255,0.8)" variant="body2">
                                  {job.location}
                                </Typography>
                              </Box>
                            </Stack>

                            {/* İş açıklaması */}
                            <Typography variant="body2" color="rgba(255,255,255,0.7)" sx={{ mb: 2 }}>
                              {job.description.length > 120 
                                ? `${job.description.substring(0, 120)}...` 
                                : job.description
                              }
                            </Typography>

                            {/* Etiketler */}
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              <Chip 
                                label={job.experience_level} 
                                size="small" 
                                sx={{ bgcolor: 'rgba(79, 70, 229, 0.3)', color: 'white' }}
                              />
                              <Chip 
                                label={job.employment_type} 
                                size="small" 
                                sx={{ bgcolor: 'rgba(124, 58, 237, 0.3)', color: 'white' }}
                              />
                              <Chip 
                                label="LinkedIn" 
                                size="small" 
                                sx={{ bgcolor: 'rgba(0, 119, 181, 0.3)', color: 'white' }}
                              />
                            </Box>
                          </Box>

                          {/* Sağ taraf - Uygunluk skoru */}
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 80 }}>
                            <Box 
                              sx={{ 
                                bgcolor: getScoreColor(job.match_score),
                                color: 'white',
                                px: 2,
                                py: 1,
                                borderRadius: 2,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                mb: 1
                              }}
                            >
                              <StarIcon sx={{ fontSize: 20, mb: 0.5 }} />
                              <Typography variant="h6" fontWeight="bold">
                                {job.match_score}%
                              </Typography>
                              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                                {getScoreLabel(job.match_score)}
                              </Typography>
                            </Box>
                            
                            {/* Uygunluk çubuğu */}
                            <LinearProgress 
                              variant="determinate" 
                              value={job.match_score} 
                              sx={{
                                width: 60,
                                height: 6,
                                borderRadius: 3,
                                bgcolor: 'rgba(255,255,255,0.2)',
                                '& .MuiLinearProgress-bar': {
                                  bgcolor: getScoreColor(job.match_score),
                                  borderRadius: 3
                                }
                              }}
                            />
                          </Box>
                        </Box>

                        {/* Uygunluk nedenleri */}
                        {job.match_reasons && job.match_reasons.length > 0 && (
                          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                            <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                              <strong>✅ Neden Uygun:</strong>
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {job.match_reasons.slice(0, 3).map((reason, idx) => (
                                <Chip 
                                  key={idx}
                                  label={reason} 
                                  size="small" 
                                  sx={{ 
                                    bgcolor: 'rgba(76, 175, 80, 0.2)', 
                                    color: '#4caf50',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}

                        {/* Eksik beceriler */}
                        {job.missing_skills && job.missing_skills.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                              <strong>⚠️ Geliştirilecek:</strong>
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {job.missing_skills.slice(0, 2).map((skill, idx) => (
                                <Chip 
                                  key={idx}
                                  label={skill} 
                                  size="small" 
                                  sx={{ 
                                    bgcolor: 'rgba(255, 152, 0, 0.2)', 
                                    color: '#ff9800',
                                    fontSize: '0.75rem'
                                  }}
                                />
                              ))}
                            </Box>
                          </Box>
                        )}
                      </CardContent>
                      
                      {/* Başvuru butonu */}
                      <CardActions sx={{ p: 2, pt: 0 }}>
                        <Button
                          variant="contained"
                          fullWidth
                          startIcon={<OpenInNewIcon />}
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(job.url, '_blank');
                          }}
                          sx={{
                            background: 'linear-gradient(135deg, #0077b5 0%, #005885 100%)',
                            color: 'white',
                            fontWeight: 600,
                            py: 1.5,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #005885 0%, #004268 100%)',
                            }
                          }}
                        >
                          LinkedIn'de Başvur
                        </Button>
                      </CardActions>
                    </Card>
                  ))}
                </Stack>
              </Paper>
            </Grid>
          )}

          {/* No Results */}
          {matchedJobs.length === 0 && (
            <Grid item xs={12}>
              <Paper 
                component={motion.div} 
                initial={{ opacity: 0, y: 30, scale: 0.9 }} 
                animate={{ opacity: 1, y: 0, scale: 1 }} 
                transition={{ 
                  duration: 0.7, 
                  type: "spring",
                  stiffness: 80
                }} 
                elevation={8} 
                className="glass-card" 
                sx={{ 
                  p: 5, 
                  borderRadius: 4,
                  textAlign: 'center'
                }}
              >
                <Typography variant="h6" color="white" mb={2}>
                  Henüz uygun iş ilanı bulunamadı
                </Typography>
                <Typography color="rgba(255,255,255,0.7)" mb={3}>
                  CV'nizi güncelleyin veya farklı anahtar kelimeler kullanın.
                </Typography>
                <Button 
                  variant="contained" 
                  onClick={resetSearch}
                  sx={{
                    background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                    borderRadius: '25px',
                    px: 4
                  }}
                >
                  Yeni Arama Yap
                </Button>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Box>
    );
  }
} 