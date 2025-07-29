import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Button, TextField, CircularProgress, Alert, 
  Tabs, Tab, Select, MenuItem, FormControl, InputLabel, Card, CardContent,
  Accordion, AccordionSummary, AccordionDetails, Chip, Grid, Switch, FormControlLabel
} from '@mui/material';
import { 
  ExpandMore, PlayArrow, BugReport, Analytics, School, Code as CodeIcon,
  AutoFixHigh, Speed, Psychology
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';

export default function Code() {
  const [question, setQuestion] = useState('');
  const [userCode, setUserCode] = useState('');
  const [step, setStep] = useState('start'); // start, coding, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [difficulty, setDifficulty] = useState('orta');
  const [activeTab, setActiveTab] = useState(0);
  const [useExecution, setUseExecution] = useState(true);
  
  // Debug ve analiz state'leri
  const [debugResult, setDebugResult] = useState(null);
  const [complexityAnalysis, setComplexityAnalysis] = useState(null);
  const [generatedSolution, setGeneratedSolution] = useState(null);
  const [resources, setResources] = useState(null);

  const fetchQuestion = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room', {
        difficulty: difficulty
      }, { withCredentials: true });
      setQuestion(res.data.coding_question);
      setStep('coding');
    } catch (err) {
      setError(err.response?.data?.error || 'Soru alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!userCode.trim()) {
      setError('Lütfen kodunuzu yazın.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room/evaluate', {
        question: question,
        user_code: userCode,
        use_execution: useExecution
      }, { withCredentials: true });
      setResult(res.data);
      setStep('result');
    } catch (err) {
      setError(err.response?.data?.error || 'Değerlendirme başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const generateSolution = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room/generate_solution', {
        question: question
      }, { withCredentials: true });
      setGeneratedSolution(res.data);
      setActiveTab(1); // Çözüm sekmesine geç
    } catch (err) {
      setError(err.response?.data?.error || 'Çözüm üretilemedi.');
    } finally {
      setLoading(false);
    }
  };

  const debugCode = async () => {
    if (!userCode.trim()) {
      setError('Debug için kod gerekli.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room/debug', {
        code: userCode
      }, { withCredentials: true });
      setDebugResult(res.data);
      setActiveTab(2); // Debug sekmesine geç
    } catch (err) {
      setError(err.response?.data?.error || 'Debug başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const analyzeComplexity = async () => {
    if (!userCode.trim()) {
      setError('Analiz için kod gerekli.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room/analyze_complexity', {
        code: userCode
      }, { withCredentials: true });
      setComplexityAnalysis(res.data);
      setActiveTab(3); // Analiz sekmesine geç
    } catch (err) {
      setError(err.response?.data?.error || 'Analiz başarısız.');
    } finally {
      setLoading(false);
    }
  };

  const getResources = async () => {
    setLoading(true);
    setError('');
    try {
      // Soru varsa soruya göre, yoksa genel Python kaynakları
      const searchTopic = question 
        ? `Python programlama ${question.slice(0, 100)}` 
        : 'Python programlama başlangıç orta seviye';
        
      const res = await axios.post('http://localhost:5000/code_room/suggest_resources', {
        topic: searchTopic,
        num_resources: 5
      }, { withCredentials: true });
      setResources(res.data);
      setActiveTab(4); // Kaynaklar sekmesine geç
    } catch (err) {
      setError(err.response?.data?.error || 'Kaynaklar alınamadı.');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'start') {
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
            🐍 Python Kodlama Odası
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Gemini AI ile gerçek kod çalıştırma deneyimi!
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
            <CardContent>
              <Typography variant="h6" color="white" mb={2}>✨ Yeni Özellikler</Typography>
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Chip icon={<PlayArrow />} label="Kod Çalıştırma" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<BugReport />} label="Debug Yardımı" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<Analytics />} label="Karmaşıklık Analizi" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<AutoFixHigh />} label="Çözüm Üretme" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<School />} label="Gerçek Linkler" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
          
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={8}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Zorluk Seviyesi</InputLabel>
                <Select
                  value={difficulty}
                  label="Zorluk Seviyesi"
                  onChange={(e) => setDifficulty(e.target.value)}
                  sx={{
                    color: 'white',
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#4f46e5' },
                  }}
                >
                  <MenuItem value="kolay">🟢 Kolay - Başlangıç</MenuItem>
                  <MenuItem value="orta">🟡 Orta - Geliştirme</MenuItem>
                  <MenuItem value="zor">🔴 Zor - İleri Seviye</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={4}>
              <Button 
                variant="outlined" 
                fullWidth
                onClick={getResources} 
                disabled={loading}
                startIcon={<School />}
                sx={{ 
                  color: 'white', 
                  borderColor: 'rgba(255,255,255,0.3)',
                  height: '56px', // Select ile aynı yükseklik
                  '&:hover': { borderColor: 'white', backgroundColor: 'rgba(255,255,255,0.1)' }
                }}
              >
                Kaynaklar
              </Button>
            </Grid>
          </Grid>
          
          <Button 
            variant="contained" 
            color="primary" 
            size="large" 
            fullWidth 
            onClick={fetchQuestion} 
            disabled={loading} 
            endIcon={loading && <CircularProgress size={20} color="inherit" />}
            startIcon={<CodeIcon />}
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
            {loading ? 'Soru Hazırlanıyor...' : 'Python Sorusu Al'}
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'coding') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 4, maxWidth: 1200, mx: 'auto', borderRadius: 4 }}
        >
          <Typography variant="h5" fontWeight={700} mb={3} color="white">
            🐍 Python Kodlama Problemi
          </Typography>
          
          <Tabs 
            value={activeTab} 
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{ 
              mb: 3,
              '& .MuiTab-root': { color: 'rgba(255,255,255,0.7)' },
              '& .Mui-selected': { color: 'white !important' },
              '& .MuiTabs-indicator': { backgroundColor: 'white' }
            }}
          >
            <Tab label="Problem & Kod" icon={<CodeIcon />} />
            <Tab label="AI Çözümü" icon={<AutoFixHigh />} />
            <Tab label="Debug" icon={<BugReport />} />
            <Tab label="Analiz" icon={<Analytics />} />
            <Tab label="Kaynaklar" icon={<School />} />
          </Tabs>

          {activeTab === 0 && (
            <Box>
              <Typography fontWeight={600} mb={2} color="white">Problem:</Typography>
              <Typography mb={3} color="rgba(255,255,255,0.8)" sx={{ 
                whiteSpace: 'pre-wrap', 
                backgroundColor: 'rgba(255,255,255,0.1)', 
                p: 2, 
                borderRadius: 2,
                border: '1px solid rgba(255,255,255,0.2)'
              }}>
                {question}
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography fontWeight={600} color="white">Python Kodunuzu Yazın:</Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={useExecution}
                      onChange={(e) => setUseExecution(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={
                    <Typography color="white" variant="body2">
                      {useExecution ? '⚡ Kod Çalıştır' : '📝 Sadece Analiz'}
                    </Typography>
                  }
                />
              </Box>
              
              <TextField
                multiline
                rows={12}
                fullWidth
                value={userCode}
                onChange={(e) => setUserCode(e.target.value)}
                placeholder={`# Python kodunuzu buraya yazın...
# Örnek:
def solution():
    # Kodunuz buraya
    pass

# Test
print(solution())`}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    color: 'white',
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                    '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                    '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.5)', opacity: 1 },
                  },
                }}
              />
              
              {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    fullWidth
                    onClick={handleSubmit} 
                    disabled={loading || !userCode.trim()} 
                    endIcon={loading && <CircularProgress size={20} color="inherit" />}
                    startIcon={<PlayArrow />}
                    sx={{
                      background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                      borderRadius: '15px',
                      py: 1.2,
                      textTransform: 'none',
                      fontWeight: 600,
                    }}
                  >
                    {loading ? 'Değerlendiriliyor...' : useExecution ? 'Çalıştır & Değerlendir' : 'Değerlendir'}
                  </Button>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button 
                    variant="outlined" 
                    fullWidth
                    onClick={generateSolution} 
                    disabled={loading}
                    startIcon={<AutoFixHigh />}
                    sx={{ 
                      color: 'white', 
                      borderColor: 'rgba(255,255,255,0.3)',
                      borderRadius: '15px',
                      py: 1.2,
                      '&:hover': { borderColor: 'white', backgroundColor: 'rgba(255,255,255,0.1)' }
                    }}
                  >
                    AI Çözümü Üret
                  </Button>
                </Grid>
              </Grid>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={4}>
                  <Button 
                    variant="text" 
                    fullWidth
                    onClick={debugCode} 
                    disabled={loading || !userCode.trim()}
                    startIcon={<BugReport />}
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                  >
                    Debug
                  </Button>
                </Grid>
                <Grid item xs={4}>
                  <Button 
                    variant="text" 
                    fullWidth
                    onClick={analyzeComplexity} 
                    disabled={loading || !userCode.trim()}
                    startIcon={<Speed />}
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                  >
                    Analiz
                  </Button>
                </Grid>
                <Grid item xs={4}>
                  <Button 
                    variant="text" 
                    fullWidth
                    onClick={getResources} 
                    disabled={loading}
                    startIcon={<School />}
                    sx={{ color: 'rgba(255,255,255,0.8)' }}
                  >
                    Kaynaklar
                  </Button>
                </Grid>
              </Grid>
            </Box>
          )}

          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" mb={2} color="white">🤖 AI Tarafından Üretilen Çözüm</Typography>
              {generatedSolution ? (
                <Box>
                  <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                    <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                      <Typography color="white">💡 Açıklama</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                        {generatedSolution.explanation}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>
                  
                  <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                    <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                      <Typography color="white">🐍 Python Kodu</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <TextField
                        multiline
                        fullWidth
                        value={generatedSolution.code}
                        InputProps={{ readOnly: true }}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            color: 'white',
                            fontFamily: 'monospace',
                            backgroundColor: 'rgba(0,0,0,0.3)',
                          },
                        }}
                      />
                    </AccordionDetails>
                  </Accordion>
                  
                  {generatedSolution.test_results && (
                    <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                      <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                        <Typography color="white">🧪 Test Sonuçları</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                          {generatedSolution.test_results}
                        </Typography>
                      </AccordionDetails>
                    </Accordion>
                  )}
                </Box>
              ) : (
                <Typography color="rgba(255,255,255,0.7)">
                  AI çözümü üretmek için "AI Çözümü Üret" butonuna tıklayın.
                </Typography>
              )}
            </Box>
          )}

          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" mb={2} color="white">🐛 Debug Yardımı</Typography>
              {debugResult ? (
                <Box>
                  <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                    <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                      <Typography color="white">🔍 Hata Açıklaması</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                        {debugResult.error_explanation}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>
                  
                  {debugResult.corrected_code && (
                    <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                      <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                        <Typography color="white">✅ Düzeltilmiş Kod</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <TextField
                          multiline
                          fullWidth
                          value={debugResult.corrected_code}
                          InputProps={{ readOnly: true }}
                          sx={{
                            '& .MuiOutlinedInput-root': {
                              color: 'white',
                              fontFamily: 'monospace',
                              backgroundColor: 'rgba(0,0,0,0.3)',
                            },
                          }}
                        />
                      </AccordionDetails>
                    </Accordion>
                  )}
                  
                  {debugResult.execution_result && (
                    <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                      <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                        <Typography color="white">🏃 Çalıştırma Sonucu</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                          {debugResult.execution_result}
                        </Typography>
                      </AccordionDetails>
                    </Accordion>
                  )}
                </Box>
              ) : (
                <Typography color="rgba(255,255,255,0.7)">
                  Debug yardımı almak için kodunuzu yazın ve "Debug" butonuna tıklayın.
                </Typography>
              )}
            </Box>
          )}

          {activeTab === 3 && (
            <Box>
              <Typography variant="h6" mb={2} color="white">📊 Algoritma Karmaşıklığı Analizi</Typography>
              {complexityAnalysis ? (
                <Card sx={{ backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                  <CardContent>
                    <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                      {complexityAnalysis.analysis}
                    </Typography>
                  </CardContent>
                </Card>
              ) : (
                <Typography color="rgba(255,255,255,0.7)">
                  Algoritma analizi için kodunuzu yazın ve "Analiz" butonuna tıklayın.
                </Typography>
              )}
            </Box>
          )}

          {activeTab === 4 && (
            <Box>
              <Typography variant="h6" mb={2} color="white">📚 Öğrenme Kaynakları</Typography>
              {resources ? (
                <Card sx={{ backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                  <CardContent>
                    <Typography 
                      color="rgba(255,255,255,0.8)" 
                      sx={{ 
                        whiteSpace: 'pre-wrap',
                        '& a': {
                          color: '#64b5f6',
                          textDecoration: 'underline',
                          '&:hover': {
                            color: '#90caf9'
                          }
                        }
                      }}
                      dangerouslySetInnerHTML={{
                        __html: resources.resources
                          .replace(/https?:\/\/[^\s]+/g, '<a href="$&" target="_blank" rel="noopener noreferrer">$&</a>')
                          .replace(/\n/g, '<br/>')
                      }}
                    />
                  </CardContent>
                </Card>
              ) : (
                <Typography color="rgba(255,255,255,0.7)">
                  Python öğrenme kaynakları için "Kaynaklar" butonuna tıklayın.
                </Typography>
              )}
            </Box>
          )}
        </Paper>
      </Box>
    );
  }

  if (step === 'result') {
    return (
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
        <Paper 
          component={motion.div} 
          initial={{ opacity: 0, y: 40 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.7 }} 
          elevation={8} 
          className="glass-card"
          sx={{ p: 5, maxWidth: 800, mx: 'auto', borderRadius: 4 }}
        >
          <Typography variant="h4" fontWeight={700} mb={3} color="white" textAlign="center">
            📊 Kod Değerlendirme Sonucu
          </Typography>
          
          {result && (
            <Box>
              {result.use_execution && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  ⚡ Bu değerlendirme gerçek kod çalıştırma ile yapılmıştır!
                </Alert>
              )}
              
              <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                  <Typography color="white">📝 Genel Değerlendirme</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                    {result.evaluation}
                  </Typography>
                </AccordionDetails>
              </Accordion>
              
              {result.execution_output && (
                <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                    <Typography color="white">🏃 Kod Çalıştırma Sonucu</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                      {result.execution_output}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              )}
              
              {result.code_suggestions && (
                <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                    <Typography color="white">💡 Kod Önerileri</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                      {result.code_suggestions}
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              )}
              
              {result.has_errors && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  ⚠️ Kodunuzda hatalar tespit edildi. Lütfen önerileri inceleyin.
                </Alert>
              )}
            </Box>
          )}
          
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Button 
                variant="outlined" 
                fullWidth
                onClick={() => { 
                  setStep('coding'); 
                  setResult(null);
                  setActiveTab(0);
                }}
                sx={{
                  color: 'rgba(255,255,255,0.7)', 
                  borderColor: 'rgba(255,255,255,0.3)',
                  '&:hover': { borderColor: 'rgba(255,255,255,0.7)' }
                }}
              >
                Kodu Düzenle
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button 
                variant="contained" 
                color="primary" 
                fullWidth
                onClick={() => { 
                  setStep('start'); 
                  setUserCode(''); 
                  setQuestion('');
                  setResult(null); 
                  setDebugResult(null);
                  setComplexityAnalysis(null);
                  setGeneratedSolution(null);
                  setResources(null);
                  setActiveTab(0);
                  setError('');
                }}
                sx={{
                  background: 'linear-gradient(45deg, #4f46e5 0%, #7c3aed 100%)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #4338ca 0%, #6d28d9 100%)',
                  }
                }}
              >
                Yeni Problem
              </Button>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    );
  }
}