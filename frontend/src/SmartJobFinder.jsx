import React, { useState } from 'react';
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
  Divider
} from '@mui/material';
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
  Schedule
} from '@mui/icons-material';

const steps = ['CV Yükle', 'CV Analizi', 'İş Arama', 'Sonuçlar'];

const SmartJobFinder = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [cvAnalysis, setCvAnalysis] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setError('Lütfen sadece PDF dosyası seçin');
    }
  };

  const analyzeCv = async () => {
    if (!selectedFile) {
      setError('Lütfen önce bir CV dosyası seçin');
      return;
    }

    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('cv_file', selectedFile);

    try {
      const response = await fetch('http://localhost:5000/api/analyze-cv', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        setCvAnalysis(data.cv_analysis);
        setActiveStep(1);
        
        // Otomatik olarak iş arama adımına geç
        setTimeout(() => {
          searchJobs(data.cv_analysis);
        }, 1000);
      } else {
        setError(data.error || 'CV analizi başarısız');
      }
    } catch (error) {
      console.error('CV analizi hatası:', error);
      setError('CV analizi sırasında bir hata oluştu');
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
      const response = await fetch('http://localhost:5000/api/search-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cv_analysis: analysis,
          location: 'Türkiye',
          max_jobs: 20
        }),
        credentials: 'include'
      });

      const data = await response.json();

      if (data.success) {
        setJobs(data.jobs);
        setStats(data.stats);
        setActiveStep(3);
      } else {
        setError(data.error || 'İş arama başarısız');
      }
    } catch (error) {
      console.error('İş arama hatası:', error);
      setError('İş arama sırasında bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const getJobApplicationTips = async (job) => {
    try {
      const response = await fetch('http://localhost:5000/api/job-application-tips', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          cv_analysis: cvAnalysis,
          job: job
        }),
        credentials: 'include'
      });

      const data = await response.json();
      
      if (data.success) {
        // Tips'i job objesine ekle
        const updatedJobs = jobs.map(j => 
          j.url === job.url ? { ...j, tips: data.tips } : j
        );
        setJobs(updatedJobs);
      }
    } catch (err) {
      console.error('Başvuru önerileri alınamadı:', err);
    }
  };

  const resetProcess = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setCvAnalysis(null);
    setJobs([]);
    setStats(null);
    setError('');
  };

  const renderCvAnalysis = () => {
    if (!cvAnalysis) return null;

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <Psychology sx={{ mr: 1 }} />
            CV Analiz Sonuçları
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
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
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
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
                <Chip 
                  label={cvAnalysis.deneyim_seviyesi || 'entry'} 
                  color={
                    cvAnalysis.deneyim_seviyesi === 'senior' ? 'success' :
                    cvAnalysis.deneyim_seviyesi === 'mid' ? 'warning' :
                    cvAnalysis.deneyim_seviyesi === 'junior' ? 'info' : 'default'
                  } 
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
                  Ana Uzmanlık Alanı
                </Typography>
                <Typography variant="body1">
                  {cvAnalysis.ana_uzmanlık_alanı || 'Belirtilmemiş'}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
                  CV Kalitesi
                </Typography>
                <Chip 
                  label={cvAnalysis.cv_kalitesi || 'orta'} 
                  color={
                    cvAnalysis.cv_kalitesi === 'mükemmel' ? 'success' :
                    cvAnalysis.cv_kalitesi === 'iyi' ? 'info' :
                    cvAnalysis.cv_kalitesi === 'orta' ? 'warning' : 'error'
                  } 
                  size="small"
                />
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
                  Teknik Beceriler
                </Typography>
                <Box sx={{ mt: 1 }}>
                  {(cvAnalysis.teknik_beceriler || []).slice(0, 8).map((skill, index) => (
                    <Chip
                      key={index}
                      label={skill}
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                      variant="outlined"
                      color="primary"
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
    <Card key={index} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="div" gutterBottom>
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
              <Star sx={{ mr: 1, color: 'warning.main' }} />
              <Typography variant="h6" color="warning.main">
                {job.score || 0}%
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Uyum Oranı
            </Typography>
          </Box>
        </Box>

        {/* Uyum Detayları */}
        {job.match_reasons && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="success.main" gutterBottom>
              ✓ Neden Uygun:
            </Typography>
            <List dense>
              {job.match_reasons.slice(0, 3).map((reason, idx) => (
                <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 20 }}>
                    <CheckCircle sx={{ fontSize: 16, color: 'success.main' }} />
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
            <Typography variant="subtitle2" color="warning.main" gutterBottom>
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
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom align="center">
          <Work sx={{ mr: 2, verticalAlign: 'middle' }} />
          Akıllı İş Bulma Asistanı
        </Typography>
        
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 4 }}>
          CV'nizi yükleyin, yapay zeka ile analiz edelim ve size en uygun işleri bulalım!
        </Typography>

        {/* Stepper */}
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
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
            <CircularProgress sx={{ mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              {activeStep === 0 ? 'CV analiz ediliyor...' : 
               activeStep === 1 ? 'İş ilanları aranıyor...' : 
               'İşlemler tamamlanıyor...'}
            </Typography>
          </Box>
        )}

        {/* Step 0: File Upload */}
        {activeStep === 0 && (
          <Box sx={{ textAlign: 'center' }}>
            <input
              accept="application/pdf"
              style={{ display: 'none' }}
              id="cv-upload-button"
              type="file"
              onChange={handleFileSelect}
            />
            <label htmlFor="cv-upload-button">
              <Button
                variant="outlined"
                component="span"
                size="large"
                startIcon={<CloudUpload />}
                sx={{ mb: 2 }}
              >
                CV Dosyası Seç (PDF)
              </Button>
            </label>
            
            {selectedFile && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Seçilen dosya: {selectedFile.name}
                </Typography>
              </Box>
            )}
            
            <Button
              variant="contained"
              size="large"
              onClick={analyzeCv}
              disabled={!selectedFile || loading}
              sx={{ ml: 2 }}
            >
              CV'yi Analiz Et
            </Button>
          </Box>
        )}

        {/* CV Analysis Results */}
        {cvAnalysis && renderCvAnalysis()}

        {/* Stats */}
        {stats && (
          <Card sx={{ mb: 3, bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Arama İstatistikleri
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{stats.total_found}</Typography>
                  <Typography variant="body2">Toplam Bulunan</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{stats.matched}</Typography>
                  <Typography variant="body2">Uygun İş</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{Math.round(stats.avg_match_score || 0)}%</Typography>
                  <Typography variant="body2">Ortalama Uyum</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="h4">{stats.search_areas?.length || 0}</Typography>
                  <Typography variant="body2">Arama Alanı</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}

        {/* Job Results */}
        {jobs.length > 0 && (
          <Box>
            <Typography variant="h5" gutterBottom>
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
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Şu anda size uygun iş ilanı bulunamadı
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Farklı kriterlerle tekrar deneyin veya daha sonra tekrar kontrol edin.
            </Typography>
            <Button variant="contained" onClick={resetProcess}>
              Yeni Arama Yap
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default SmartJobFinder;
