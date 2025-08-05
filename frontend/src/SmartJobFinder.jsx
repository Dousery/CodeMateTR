import React, { useState, useEffect } from 'react';
import API_ENDPOINTS from './config.js';
import axios from 'axios';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Grid,
  Rating,
  Divider,
  Tooltip,
  Error
} from '@mui/material';
import { motion } from 'framer-motion';
import {
  CloudUpload,
  Work,
  Psychology,
  TipsAndUpdates,
  ExpandMore,
  CheckCircle,
  Star,
  LocationOn,
  Business,
  AccessTime,
  AttachMoney,
  Schedule,
  Lightbulb
} from '@mui/icons-material';

const steps = ['CV Yükle', 'CV Analizi', 'İş Arama', 'Sonuçlar'];

const SmartJobFinder = () => {
  const [loading, setLoading] = useState(false);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [serpapiStatus, setSerpapiStatus] = useState(null); // SerpAPI durumu

  // Component mount olduğunda session kontrolü yap
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log('Checking session status for smart job finder...');
        const sessionRes = await axios.get(API_ENDPOINTS.SESSION_STATUS, { 
          withCredentials: true,
          timeout: 5000
        });
        console.log('Session status:', sessionRes.data);
        
        // Smart job finder endpoint'ini de kontrol et
        const smartJobRes = await axios.get(API_ENDPOINTS.SMART_JOB_FINDER_PAGE, { 
          withCredentials: true,
          timeout: 5000
        });
        console.log('Smart job finder page status:', smartJobRes.data);
      } catch (err) {
        console.error('Session check failed for smart job finder:', err);
      }
    };
    
    checkSession();
  }, []);

  // SerpAPI durumunu kontrol et
  const checkSerpapiStatus = async () => {
    try {
      setSerpapiStatus('checking');
      const response = await axios.get(API_ENDPOINTS.TEST_SERPAPI, {
        withCredentials: true,
        timeout: 10000
      });
      
      if (response.data.success) {
        setSerpapiStatus('working');
        console.log('✅ SerpAPI çalışıyor');
      } else {
        setSerpapiStatus('error');
        console.log('❌ SerpAPI çalışmıyor');
      }
    } catch (error) {
      setSerpapiStatus('error');
      console.error('SerpAPI test hatası:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
      // Otomatik olarak analiz başlat
      setTimeout(() => {
        analyzeCvWithFile(file);
      }, 500);
    } else {
      setError('Lütfen sadece PDF dosyası seçin');
    }
  };

  const analyzeCvWithFile = async (file) => {
    if (!file) {
      setError('Lütfen önce bir CV dosyası seçin');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('cv_file', file);

    try {
      // Yeni entegrasyon: Tek seferde CV analizi ve iş arama
      console.log('Processing CV with new integration:', API_ENDPOINTS.PROCESS_CV_FILE);
      console.log('CV file data:', { 
        filename: file.name,
        size: file.size,
        type: file.type
      });
      
      const response = await axios.post(API_ENDPOINTS.PROCESS_CV_FILE, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000 // 2 dakika timeout
      });

      const data = response.data;
      console.log('CV processing response:', data);

      if (data.success) {
        setCvAnalysis(data.cv_analysis);
        setJobs(data.jobs || []);
        setStats(data.stats || {});
        setActiveStep(3); // Direkt sonuçlar adımına geç
        
        console.log(`✅ CV analizi ve iş arama tamamlandı: ${data.jobs?.length || 0} iş bulundu`);
      } else {
        setError(data.error || 'CV işleme başarısız');
      }
    } catch (error) {
      console.error('CV işleme hatası:', error);
      console.error('Error response:', error.response);
      
      // Fallback: Eski yöntemi dene
      try {
        console.log('Fallback: Eski CV analiz yöntemini deniyor...');
        const fallbackResponse = await axios.post(API_ENDPOINTS.ANALYZE_CV, formData, {
          withCredentials: true,
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        });

        const fallbackData = fallbackResponse.data;
        console.log('Fallback CV analysis response:', fallbackData);

        if (fallbackData.success) {
          setCvAnalysis(fallbackData.cv_analysis);
          setActiveStep(1);
          
          // Otomatik olarak iş arama adımına geç
          setTimeout(() => {
            searchJobs(fallbackData.cv_analysis);
          }, 1000);
        } else {
          setError(fallbackData.error || 'CV analizi başarısız');
        }
      } catch (fallbackError) {
        console.error('Fallback CV analizi de başarısız:', fallbackError);
        if (error.response?.status === 401) {
          setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
        } else if (error.code === 'ECONNABORTED') {
          setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
        } else {
          setError(error.response?.data?.error || 'CV işleme sırasında bir hata oluştu. Lütfen tekrar deneyin.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const searchJobs = async (analysis = cvAnalysis) => {
    if (!analysis) {
      setError('CV analizi bulunamadı');
      return;
    }

    setLoading(true);
    setActiveStep(2);

    try {
      console.log('Searching jobs with:', API_ENDPOINTS.SEARCH_JOBS);
      console.log('Search data:', { 
        cv_analysis_keys: Object.keys(analysis),
        location: 'Türkiye',
        max_jobs: 20
      });
      
      const response = await axios.post(API_ENDPOINTS.SEARCH_JOBS, {
        cv_analysis: analysis,
        location: 'Türkiye',
        max_jobs: 20
      }, {
        withCredentials: true,
        timeout: 60000
      });

      const data = response.data;
      console.log('Job search response:', data);

      if (data.success) {
        setJobs(data.jobs);
        setStats(data.stats);
        setActiveStep(3);
      } else {
        setError(data.error || 'İş arama başarısız');
      }
    } catch (error) {
      console.error('İş arama hatası:', error);
      console.error('Error response:', error.response);
      if (error.response?.status === 401) {
        setError('Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.');
      } else if (error.code === 'ECONNABORTED') {
        setError('Bağlantı zaman aşımı. Lütfen tekrar deneyin.');
      } else {
        setError(error.response?.data?.error || 'İş arama sırasında bir hata oluştu. Lütfen tekrar deneyin.');
      }
    } finally {
      setLoading(false);
    }
  };

  const getJobApplicationTips = async (job) => {
    try {
      console.log('Getting job application tips with:', API_ENDPOINTS.JOB_TIPS);
      console.log('Job data:', { 
        job_title: job.title,
        company: job.company,
        url: job.url
      });
      
      const response = await axios.post(API_ENDPOINTS.JOB_TIPS, {
        cv_analysis: cvAnalysis,
        job: job
      }, {
        withCredentials: true,
        timeout: 30000
      });

      const data = response.data;
      console.log('Job tips response:', data);
      
      if (data.success) {
        // Tips'i job objesine ekle
        const updatedJobs = jobs.map(j => 
          j.url === job.url ? { ...j, tips: data.tips } : j
        );
        setJobs(updatedJobs);
      }
    } catch (err) {
      console.error('Başvuru önerileri alınamadı:', err);
      console.error('Error response:', err.response);
      if (err.response?.status === 401) {
        console.error('Session expired while getting job tips');
      } else if (err.code === 'ECONNABORTED') {
        console.error('Timeout while getting job tips');
      }
    }
  };

  const resetProcess = () => {
    setActiveStep(0);
    setCvAnalysis(null);
    setJobs([]);
    setSelectedFile(null);
    setError('');
    setStats(null);
    setSerpapiStatus(null); // SerpAPI durumunu da sıfırla
  };

  const renderCvAnalysis = () => {
    if (!cvAnalysis) return null;

    return (
      <Card 
        component={motion.div}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        sx={{ 
          mb: 3, 
          backgroundColor: 'rgba(255,255,255,0.1)', 
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <CardContent sx={{ color: 'white' }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#E6E6FA' }}>
            <Psychology sx={{ mr: 1, color: '#E6E6FA' }} />
            CV Analiz Sonuçları
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
                  Kişisel Bilgiler
                </Typography>
                <Typography variant="body2">
                  Ad Soyad: {cvAnalysis.kişisel_bilgiler?.ad_soyad || 'Belirtilmemiş'}
                </Typography>
                <Typography variant="body2">
                  Lokasyon: {cvAnalysis.kişisel_bilgiler?.lokasyon || 'Belirtilmemiş'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
                  Deneyim Bilgileri
                </Typography>
                <Typography variant="body1">
                  <strong>{cvAnalysis.deneyim_yılı || 0} yıl</strong> profesyonel deneyim
                </Typography>
                {cvAnalysis.toplam_is_deneyimi && (
                  <Typography variant="body2" color="text.secondary">
                    {cvAnalysis.toplam_is_deneyimi}
                  </Typography>
                )}
                {cvAnalysis.staj_deneyimi && cvAnalysis.staj_deneyimi !== 'Belirtilmemiş' && (
                  <Typography variant="body2" color="text.secondary">
                    Staj: {cvAnalysis.staj_deneyimi}
                  </Typography>
                )}
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 1 }}>
                  <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 'bold' }}>
                    Aday seviyesi:
                  </Typography>
                  <Tooltip title="Deneyim seviyesi: Entry Level (Başlangıç Seviyesi) - 0-2 yıl profesyonel deneyim. Yeni mezun, stajyer veya ilk iş deneyimi olan kişiler için uygun pozisyonlar." arrow>
                    <Chip 
                      label={cvAnalysis.deneyim_seviyesi || 'entry'} 
                      sx={{ 
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        borderColor: 'rgba(255,255,255,0.3)',
                        fontWeight: 'bold'
                      }}
                      size="small"
                      variant="outlined"
                    />
                  </Tooltip>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
                  Ana Uzmanlık Alanı
                </Typography>
                <Typography variant="body1">
                  {cvAnalysis.ana_uzmanlık_alanı || 'Belirtilmemiş'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
                  CV Kalitesi
                </Typography>
                <Tooltip title="CV'nizin genel kalite değerlendirmesi" arrow>
                  <Chip 
                    label={cvAnalysis.cv_kalitesi || 'orta'} 
                    sx={{
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      color: 'white',
                      borderColor: 'rgba(255,255,255,0.3)',
                      fontWeight: 'bold'
                    }}
                    size="small"
                    variant="outlined"
                  />
                </Tooltip>
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
                  Teknik Beceriler
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {(cvAnalysis.teknik_beceriler || []).slice(0, 8).map((skill, index) => (
                    <Chip
                      key={index}
                      label={skill}
                      size="small"
                      sx={{ 
                        mr: 1, 
                        mb: 1,
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        color: 'white',
                        borderColor: 'rgba(255,255,255,0.3)'
                      }}
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
              
              {cvAnalysis.öneriler && cvAnalysis.öneriler.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ color: '#ed6c02', fontWeight: 'bold' }}>
                    CV Geliştirme Önerileri
                  </Typography>
                  <List dense>
                    {cvAnalysis.öneriler.slice(0, 3).map((oneri, index) => (
                      <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 20 }}>
                          <TipsAndUpdates sx={{ fontSize: 16, color: 'warning.main' }} />
                        </ListItemIcon>
                        <ListItemText 
                          primary={oneri}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const renderJobCard = (job, index) => (
    <Card 
      key={index} 
      component={motion.div}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      sx={{ 
        mb: 2, 
        backgroundColor: 'rgba(255,255,255,0.1)', 
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        '&:hover': {
          backgroundColor: 'rgba(255,255,255,0.15)',
          transform: 'translateY(-2px)',
          transition: 'all 0.3s ease'
        }
      }}
    >
      <CardContent sx={{ color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="div" gutterBottom sx={{ color: '#E6E6FA' }}>
              {job.title}
            </Typography>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Business sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {job.company}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <LocationOn sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {job.location}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AccessTime sx={{ mr: 1, fontSize: 20, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                {new Date(job.posted_date).toLocaleDateString('tr-TR')}
              </Typography>
            </Box>
          </Box>
          
          <Box sx={{ textAlign: 'right' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Star sx={{ mr: 1, color: '#E6E6FA' }} />
              <Typography variant="h6" sx={{ color: '#E6E6FA' }}>
                {job.score || 0}%
              </Typography>
            </Box>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)' }}>
              Uyum Oranı
            </Typography>
          </Box>
        </Box>

        {/* Uyum Detayları */}
        {job.match_reasons && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ color: '#90EE90' }} gutterBottom>
              ✓ Neden Uygun:
            </Typography>
            <List dense>
              {job.match_reasons.slice(0, 3).map((reason, idx) => (
                <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 20 }}>
                    <CheckCircle sx={{ fontSize: 16, color: '#90EE90' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary={reason}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Eksik Beceriler */}
        {job.missing_skills && job.missing_skills.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ color: '#FFB347' }} gutterBottom>
              ⚠ Geliştirilebilir Alanlar:
            </Typography>
            <Box>
              {job.missing_skills.slice(0, 3).map((skill, idx) => (
                <Chip
                  key={idx}
                  label={skill}
                  size="small"
                  color="warning"
                  variant="outlined"
                  sx={{ mr: 1, mb: 1 }}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Öneriler */}
        {job.recommendations && job.recommendations.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ color: '#87CEEB' }} gutterBottom>
              💡 Öneriler:
            </Typography>
            <List dense>
              {job.recommendations.slice(0, 3).map((rec, idx) => (
                <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 20 }}>
                    <Lightbulb sx={{ fontSize: 16, color: '#87CEEB' }} />
                  </ListItemIcon>
                  <ListItemText 
                    primary={rec}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}



        {/* Başvuru Önerileri */}
        {job.tips && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <TipsAndUpdates sx={{ mr: 1 }} />
              <Typography variant="subtitle2">
                Başvuru Önerileri
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box>
                <Typography variant="body2" sx={{ mb: 1, fontWeight: 'bold' }}>
                  Başarı Olasılığı: {job.tips.success_probability}%
                </Typography>
                
                {job.tips.cover_letter_tips && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Cover Letter İpuçları:
                    </Typography>
                    <List dense>
                      {job.tips.cover_letter_tips.map((tip, idx) => (
                        <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                          <ListItemText 
                            primary={`• ${tip}`}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                
                {job.tips.application_strategy && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Başvuru Stratejisi:
                    </Typography>
                    <Typography variant="body2">
                      {job.tips.application_strategy}
                    </Typography>
                  </Box>
                )}
              </Box>
            </AccordionDetails>
          </Accordion>
        )}

        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            color="primary"
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            size="small"
          >
            İlanı Görüntüle
          </Button>
          
          {!job.tips && (
            <Button
              variant="outlined"
              size="small"
              onClick={() => getJobApplicationTips(job)}
            >
              <TipsAndUpdates sx={{ mr: 1, fontSize: 16 }} />
              Başvuru Önerileri
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Paper 
        component={motion.div} 
        initial={{ opacity: 0, y: 40 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.7 }} 
        elevation={8} 
        className="glass-card"
        sx={{ p: 5, minWidth: 400, maxWidth: 800, borderRadius: 4, maxHeight: '90vh', overflow: 'auto' }}
      >
        <Typography variant="h4" fontWeight={700} mb={2} color="#FFFFFF" textAlign="center">
          💼 İş Bulma Asistanı
        </Typography>
        
        <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.9)">
          CV'nizi yükleyin, yapay zeka ile analiz edelim ve size en uygun işleri bulalım!
        </Typography>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ 
          mb: 4, 
          '& .MuiStepLabel-label': { color: 'rgba(255,255,255,0.9)' },
          '& .MuiStepLabel-label.Mui-active': { color: '#E6E6FA' },
          '& .MuiStepLabel-label.Mui-completed': { color: '#98FB98' },
          '& .MuiStepIcon-root': { color: 'rgba(255,255,255,0.5)' },
          '& .MuiStepIcon-root.Mui-active': { color: '#E6E6FA' },
          '& .MuiStepIcon-root.Mui-completed': { color: '#98FB98' }
        }}>
          {steps.map((label, index) => (
            <Step key={label} completed={activeStep > index}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Loading */}
        {loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <CircularProgress sx={{ mb: 2, color: '#E6E6FA' }} />
            <Typography variant="body2" sx={{ color: '#E6E6FA', fontWeight: 'bold' }}>
              {activeStep === 0 ? 'CV analiz ediliyor...' : 
               activeStep === 1 ? 'İş ilanları aranıyor...' : 
               'İşlemler tamamlanıyor...'}
            </Typography>
          </Box>
        )}

        {/* File Upload */}
        {activeStep === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h4" gutterBottom sx={{ color: '#E6E6FA', mb: 3 }}>
              Akıllı İş Bulma Asistanı
            </Typography>
            
            <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.8)', mb: 4 }}>
              CV'nizi yükleyin, AI destekli analiz ile size en uygun iş ilanlarını bulalım.
            </Typography>

            {/* SerpAPI Durum Göstergesi */}
            <Box sx={{ mb: 3, p: 2, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 2 }}>
              <Typography variant="subtitle2" sx={{ color: '#E6E6FA', mb: 1 }}>
                Google Jobs Bağlantısı
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
                {serpapiStatus === null && (
                  <>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
                      Durum kontrol edilmedi
                    </Typography>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      onClick={checkSerpapiStatus}
                      sx={{ color: '#E6E6FA', borderColor: '#E6E6FA' }}
                    >
                      Test Et
                    </Button>
                  </>
                )}
                {serpapiStatus === 'checking' && (
                  <>
                    <CircularProgress size={20} sx={{ color: '#E6E6FA' }} />
                    <Typography variant="body2" sx={{ color: '#FFB347' }}>
                      Kontrol ediliyor...
                    </Typography>
                  </>
                )}
                {serpapiStatus === 'working' && (
                  <>
                    <CheckCircle sx={{ color: '#90EE90', fontSize: 20 }} />
                    <Typography variant="body2" sx={{ color: '#90EE90' }}>
                      Google Jobs çalışıyor
                    </Typography>
                  </>
                )}
                {serpapiStatus === 'error' && (
                  <>
                    <Error sx={{ color: '#FF6B6B', fontSize: 20 }} />
                    <Typography variant="body2" sx={{ color: '#FF6B6B' }}>
                      Google Jobs bağlantısı yok
                    </Typography>
                    <Button 
                      size="small" 
                      variant="outlined" 
                      onClick={checkSerpapiStatus}
                      sx={{ color: '#FF6B6B', borderColor: '#FF6B6B' }}
                    >
                      Tekrar Dene
                    </Button>
                  </>
                )}
              </Box>
            </Box>
            
            <label htmlFor="cv-upload">
              <Button
                component="span"
                variant="contained"
                size="large"
                startIcon={<CloudUpload />}
                sx={{
                  backgroundColor: '#E6E6FA',
                  color: '#2C2C2C',
                  '&:hover': {
                    backgroundColor: '#D8D8D8'
                  }
                }}
              >
                CV Dosyası Seç (PDF)
              </Button>
            </label>
            
            <input
              accept="application/pdf"
              style={{ display: 'none' }}
              id="cv-upload"
              type="file"
              onChange={handleFileSelect}
            />
            
            {selectedFile && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ color: '#98FB98', fontWeight: 'bold' }}>
                  ✓ Seçilen dosya: {selectedFile.name}
                </Typography>
              </Box>
            )}
            

          </Box>
        )}

        {/* CV Analysis Results */}
        {cvAnalysis && renderCvAnalysis()}

        {/* Stats */}
        {stats && (
          <Card 
            component={motion.div}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            sx={{ 
              mb: 3, 
              backgroundColor: 'rgba(255,255,255,0.1)', 
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'white'
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ color: '#E6E6FA' }}>
                Arama İstatistikleri
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{stats.total_jobs || stats.total_found || 0}</Typography>
                  <Typography variant="body2">Toplam Bulunan</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{jobs.length}</Typography>
                  <Typography variant="body2">Uygun İş</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{Math.round(jobs.reduce((acc, job) => acc + (job.score || 0), 0) / Math.max(jobs.length, 1))}%</Typography>
                  <Typography variant="body2">Ortalama Uyum</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{stats.search_method === 'SerpAPI' ? 'Google Jobs' : 'Varsayılan'}</Typography>
                  <Typography variant="body2">Arama Kaynağı</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Job Results */}
        {jobs.length > 0 && (
          <Box>
            <Typography variant="h5" gutterBottom sx={{ color: '#E6E6FA' }}>
              Size Uygun İş İlanları ({jobs.length})
            </Typography>
            
            {jobs.map((job, index) => renderJobCard(job, index))}
            
            <Box sx={{ textAlign: 'center', mt: 3 }}>
              <Button variant="outlined" onClick={resetProcess}>
                Yeni Arama Yap
              </Button>
            </Box>
          </Box>
        )}

        {/* No Results */}
        {activeStep === 3 && jobs.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" sx={{ color: '#E6E6FA' }} gutterBottom>
              Şu anda size uygun iş ilanı bulunamadı
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)', mb: 3 }}>
              Farklı kriterlerle tekrar deneyin veya daha sonra tekrar kontrol edin.
            </Typography>
            <Button variant="contained" onClick={resetProcess}>
              Yeni Arama Yap
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default SmartJobFinder;
