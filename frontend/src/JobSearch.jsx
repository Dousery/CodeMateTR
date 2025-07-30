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

      if (response.data.status === 'success') {
        setCvAnalysis(response.data.cv_analysis);
        setMatchedJobs(response.data.matched_jobs || []);
        setSearchRecommendations(response.data.search_recommendations || []);
        setTotalJobsAnalyzed(response.data.total_jobs_analyzed);
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

          {/* Job Listings */}
          {matchedJobs.length > 0 && (
            <Grid item xs={12}>
              <Grid 
                component={motion.div} 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }} 
                transition={{ duration: 0.5, delay: 0.3 }} 
                container 
                spacing={3}
              >
                {matchedJobs.map((job, index) => (
                  <Grid item xs={12} md={6} key={index}>
                    <Card 
                      component={motion.div}
                      initial={{ opacity: 0, y: 30, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ 
                        duration: 0.6, 
                        delay: 0.4 + (index * 0.1),
                        type: "spring",
                        stiffness: 100
                      }}
                      elevation={8}
                      className="glass-card"
                      sx={{
                        borderRadius: 3,
                        transition: 'transform 0.2s, box-shadow 0.2s',
                        '&:hover': {
                          transform: 'translateY(-4px)',
                          boxShadow: '0 8px 25px rgba(0,0,0,0.15)'
                        }
                      }}
                    >
                      <CardContent sx={{ p: 3 }}>
                        {/* Score Badge */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                          <Typography variant="h6" fontWeight="bold" color="white" sx={{ flex: 1 }}>
                            {job.title}
                          </Typography>
                          <Box 
                            sx={{ 
                              bgcolor: getScoreColor(job.match_score),
                              color: 'white',
                              px: 2,
                              py: 0.5,
                              borderRadius: 10,
                              display: 'flex',
                              alignItems: 'center',
                              gap: 0.5
                            }}
                          >
                            <StarIcon sx={{ fontSize: 16 }} />
                            <Typography variant="body2" fontWeight="bold">
                              {job.match_score}%
                            </Typography>
                          </Box>
                        </Box>

                        {/* Job Details */}
                        <Stack spacing={1} sx={{ mb: 2 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BusinessIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 18 }} />
                            <Typography color="rgba(255,255,255,0.8)" variant="body2">
                              {job.company}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LocationIcon sx={{ color: 'rgba(255,255,255,0.7)', fontSize: 18 }} />
                            <Typography color="rgba(255,255,255,0.8)" variant="body2">
                              {job.location}
                            </Typography>
                          </Box>
                        </Stack>

                        {/* Job Description */}
                        <Typography variant="body2" color="rgba(255,255,255,0.7)" sx={{ mb: 2 }}>
                          {job.description.length > 150 
                            ? `${job.description.substring(0, 150)}...` 
                            : job.description
                          }
                        </Typography>

                        {/* Employment Details */}
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
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
                        </Box>

                        {/* Match Score Progress */}
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                            Uygunluk: {getScoreLabel(job.match_score)}
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={job.match_score} 
                            sx={{
                              height: 8,
                              borderRadius: 4,
                              bgcolor: 'rgba(255,255,255,0.2)',
                              '& .MuiLinearProgress-bar': {
                                bgcolor: getScoreColor(job.match_score),
                                borderRadius: 4
                              }
                            }}
                          />
                        </Box>

                        {/* Match Reasons */}
                        {job.match_reasons && job.match_reasons.length > 0 && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                              <strong>Neden Uygun:</strong>
                            </Typography>
                            <List dense>
                              {job.match_reasons.slice(0, 3).map((reason, idx) => (
                                <ListItem key={idx} sx={{ py: 0, px: 0 }}>
                                  <ListItemIcon sx={{ minWidth: 20 }}>
                                    <CheckIcon sx={{ color: '#4caf50', fontSize: 16 }} />
                                  </ListItemIcon>
                                  <ListItemText 
                                    primary={reason} 
                                    primaryTypographyProps={{
                                      variant: 'body2',
                                      color: 'rgba(255,255,255,0.7)'
                                    }}
                                  />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}

                        {/* Missing Skills */}
                        {job.missing_skills && job.missing_skills.length > 0 && (
                          <Box>
                            <Typography variant="body2" color="rgba(255,255,255,0.8)" mb={1}>
                              <strong>Geliştirilecek Alanlar:</strong>
                            </Typography>
                            <List dense>
                              {job.missing_skills.slice(0, 2).map((skill, idx) => (
                                <ListItem key={idx} sx={{ py: 0, px: 0 }}>
                                  <ListItemIcon sx={{ minWidth: 20 }}>
                                    <CancelIcon sx={{ color: '#ff9800', fontSize: 16 }} />
                                  </ListItemIcon>
                                  <ListItemText 
                                    primary={skill} 
                                    primaryTypographyProps={{
                                      variant: 'body2',
                                      color: 'rgba(255,255,255,0.7)'
                                    }}
                                  />
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}
                      </CardContent>
                      
                      {/* Apply Button - Gerçek iş arama yönlendirmesi */}
                      <CardActions sx={{ p: 2, pt: 0 }}>
                        <Button
                          variant="contained"
                          fullWidth
                          startIcon={<OpenInNewIcon />}
                          onClick={() => {
                            // Şirket adı ve pozisyon ile LinkedIn'de arama
                            const searchQuery = `${job.title} ${job.company}`;
                            const linkedinUrl = `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(searchQuery)}&location=Turkey`;
                            window.open(linkedinUrl, '_blank');
                          }}
                          sx={{
                            background: 'linear-gradient(135deg, #0077b5 0%, #005885 100%)', // LinkedIn mavi
                            color: 'white',
                            fontWeight: 600,
                            py: 1.5,
                            '&:hover': {
                              background: 'linear-gradient(135deg, #005885 0%, #004268 100%)',
                            }
                          }}
                        >
                          LinkedIn'de Ara
                        </Button>
                        <Button
                          variant="outlined"
                          fullWidth
                          startIcon={<OpenInNewIcon />}
                          onClick={() => {
                            // Kariyer.net'te arama
                            const searchQuery = job.title;
                            const kariyerUrl = `https://www.kariyer.net/is-ilanlari?q=${encodeURIComponent(searchQuery)}`;
                            window.open(kariyerUrl, '_blank');
                          }}
                          sx={{
                            borderColor: 'rgba(255,255,255,0.3)',
                            color: 'white',
                            fontWeight: 600,
                            py: 1.5,
                            mt: 1,
                            '&:hover': {
                              borderColor: 'rgba(255,255,255,0.5)',
                              background: 'rgba(255,255,255,0.1)',
                            }
                          }}
                        >
                          Kariyer.net'te Ara
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
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