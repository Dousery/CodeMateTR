import React, { useState, useRef, useEffect } from 'react';
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
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [cursorPosition, setCursorPosition] = useState(0);
  const codeEditorRef = useRef(null);
  
  // Debug ve analiz state'leri
  const [debugResult, setDebugResult] = useState(null);
  const [complexityAnalysis, setComplexityAnalysis] = useState(null);
  const [generatedSolution, setGeneratedSolution] = useState(null);
  const [resources, setResources] = useState(null);

  // Dil konfigürasyonları
  const languageConfigs = {
    python: {
      name: 'Python',
      icon: '🐍',
      language: 'python',
      extension: '.py',
      comment: '#',
      indentSize: 4,
      keywords: ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'import', 'from', 'as', 'return', 'yield', 'break', 'continue', 'pass', 'True', 'False', 'None'],
      brackets: ['(', ')', '[', ']', '{', '}'],
      autoIndent: ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with'],
      deindent: ['return', 'break', 'continue', 'pass', 'raise']
    },
    javascript: {
      name: 'JavaScript',
      icon: '🟨',
      language: 'javascript',
      extension: '.js',
      comment: '//',
      indentSize: 2,
      keywords: ['function', 'class', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch', 'case', 'default', 'return', 'break', 'continue', 'var', 'let', 'const', 'import', 'export', 'async', 'await'],
      brackets: ['(', ')', '[', ']', '{', '}'],
      autoIndent: ['function', 'class', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch'],
      deindent: ['return', 'break', 'continue', 'throw']
    },
    java: {
      name: 'Java',
      icon: '☕',
      language: 'java',
      extension: '.java',
      comment: '//',
      indentSize: 4,
      keywords: ['public', 'private', 'protected', 'class', 'interface', 'extends', 'implements', 'static', 'final', 'abstract', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch', 'case', 'default', 'return', 'break', 'continue', 'new', 'import', 'package'],
      brackets: ['(', ')', '[', ']', '{', '}'],
      autoIndent: ['public', 'private', 'protected', 'class', 'interface', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch'],
      deindent: ['return', 'break', 'continue', 'throw']
    },
    cpp: {
      name: 'C++',
      icon: '⚡',
      language: 'cpp',
      extension: '.cpp',
      comment: '//',
      indentSize: 4,
      keywords: ['int', 'float', 'double', 'char', 'bool', 'string', 'vector', 'class', 'struct', 'public', 'private', 'protected', 'if', 'else', 'for', 'while', 'try', 'catch', 'switch', 'case', 'default', 'return', 'break', 'continue', 'new', 'delete', 'include', 'using', 'namespace'],
      brackets: ['(', ')', '[', ']', '{', '}'],
      autoIndent: ['class', 'struct', 'public', 'private', 'protected', 'if', 'else', 'for', 'while', 'try', 'catch', 'switch'],
      deindent: ['return', 'break', 'continue', 'throw']
    }
  };

  // Otomatik girinti işleme
  const handleCodeChange = (e) => {
    const newValue = e.target.value;
    const cursorPos = e.target.selectionStart;
    const prevValue = userCode;
    
    // Enter tuşuna basıldığında otomatik girinti
    if (newValue.length > prevValue.length && newValue[cursorPos - 1] === '\n') {
      const lines = newValue.split('\n');
      const currentLineIndex = newValue.substring(0, cursorPos).split('\n').length - 1;
      const currentLine = lines[currentLineIndex];
      const prevLine = lines[currentLineIndex - 1] || '';
      
      // Önceki satırın girintisini al
      const prevIndent = prevLine.match(/^\s*/)[0];
      let newIndent = prevIndent;
      
      const config = languageConfigs[selectedLanguage];
      
      // Akıllı girinti kuralları
      const shouldIndent = config.autoIndent.some(keyword => {
        const trimmedLine = prevLine.trim();
        return trimmedLine.startsWith(keyword) && 
               (trimmedLine.includes('(') || trimmedLine.includes(':') || 
                (config.language === 'javascript' && trimmedLine.includes('{')) ||
                (config.language === 'java' && trimmedLine.includes('{')) ||
                (config.language === 'cpp' && trimmedLine.includes('{')));
      });
      
      // Fonksiyon çıkışı için girinti azaltma
      const shouldDeindent = config.deindent.some(keyword => 
        currentLine.trim().startsWith(keyword)
      );
      
      // Özel durumlar için girinti azaltma
      const specialDeindent = config.language === 'python' ? 
        ['elif', 'else', 'except', 'finally'] : 
        ['else', 'catch', 'finally'];
      
      const shouldSpecialDeindent = specialDeindent.some(keyword => 
        currentLine.trim().startsWith(keyword)
      );
      
      if (shouldIndent) {
        newIndent += ' '.repeat(config.indentSize);
      } else if (shouldDeindent && prevIndent.length >= config.indentSize) {
        newIndent = prevIndent.slice(0, -config.indentSize);
      } else if (shouldSpecialDeindent && prevIndent.length >= config.indentSize) {
        newIndent = prevIndent.slice(0, -config.indentSize);
      }
      
      // Yeni satırı girintili olarak ekle
      const newLines = [...lines];
      newLines[currentLineIndex] = newIndent + currentLine;
      const finalValue = newLines.join('\n');
      
      setUserCode(finalValue);
      
      // Cursor pozisyonunu ayarla
      setTimeout(() => {
        const newCursorPos = cursorPos + newIndent.length;
        e.target.setSelectionRange(newCursorPos, newCursorPos);
      }, 0);
    } else {
      setUserCode(newValue);
    }
  };

  // Gelişmiş parantez eşleştirme ve akıllı özellikler
  const handleKeyDown = (e) => {
    const config = languageConfigs[selectedLanguage];
    const cursorPos = e.target.selectionStart;
    const value = userCode;
    const lines = value.split('\n');
    const currentLineIndex = value.substring(0, cursorPos).split('\n').length - 1;
    const currentLine = lines[currentLineIndex] || '';
    
    // Açılan parantez için otomatik kapanan parantez ekleme
    if (e.key === '(' || e.key === '[' || e.key === '{') {
      e.preventDefault();
      const closingBracket = {
        '(': ')',
        '[': ']',
        '{': '}'
      }[e.key];
      
      const newValue = value.slice(0, cursorPos) + e.key + closingBracket + value.slice(cursorPos);
      setUserCode(newValue);
      
      setTimeout(() => {
        e.target.setSelectionRange(cursorPos + 1, cursorPos + 1);
      }, 0);
    }
    
    // Kapanan parantez için akıllı davranış
    if (e.key === ')' || e.key === ']' || e.key === '}') {
      const nextChar = value[cursorPos];
      if (nextChar === e.key) {
        e.preventDefault();
        // Zaten kapanan parantez varsa sadece geç
        setTimeout(() => {
          e.target.setSelectionRange(cursorPos + 1, cursorPos + 1);
        }, 0);
      }
    }
    
    // Tab tuşu için girinti
    if (e.key === 'Tab') {
      e.preventDefault();
      const indent = ' '.repeat(config.indentSize);
      
      const newValue = value.slice(0, cursorPos) + indent + value.slice(cursorPos);
      setUserCode(newValue);
      
      setTimeout(() => {
        e.target.setSelectionRange(cursorPos + indent.length, cursorPos + indent.length);
      }, 0);
    }
    
    // Backspace ile girinti silme
    if (e.key === 'Backspace') {
      const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
      const lineBeforeCursor = value.slice(lineStart, cursorPos);
      
      // Eğer sadece boşluk varsa ve backspace'e basılırsa
      if (lineBeforeCursor.match(/^\s+$/) && lineBeforeCursor.length > 0) {
        e.preventDefault();
        const newIndent = ' '.repeat(Math.max(0, lineBeforeCursor.length - config.indentSize));
        const newValue = value.slice(0, lineStart) + newIndent + value.slice(cursorPos);
        setUserCode(newValue);
        
        setTimeout(() => {
          const newCursorPos = lineStart + newIndent.length;
          e.target.setSelectionRange(newCursorPos, newCursorPos);
        }, 0);
      }
    }
    
    // Enter ile akıllı satır bölme
    if (e.key === 'Enter') {
      const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
      const currentLine = value.slice(lineStart, cursorPos);
      const trimmedLine = currentLine.trim();
      
      // Eğer satırda sadece açılan parantez varsa, otomatik girinti ekle
      if (trimmedLine.endsWith('(') || trimmedLine.endsWith('{') || trimmedLine.endsWith('[')) {
        e.preventDefault();
        const config = languageConfigs[selectedLanguage];
        const currentIndent = currentLine.match(/^\s*/)[0];
        const newIndent = currentIndent + ' '.repeat(config.indentSize);
        
        const newValue = value.slice(0, cursorPos) + '\n' + newIndent + '\n' + currentIndent + value.slice(cursorPos);
        setUserCode(newValue);
        
        setTimeout(() => {
          const newCursorPos = cursorPos + 1 + newIndent.length;
          e.target.setSelectionRange(newCursorPos, newCursorPos);
        }, 0);
      }
    }
    
    // Otomatik noktalı virgül (JavaScript/Java/C++)
    if (e.key === 'Enter' && ['javascript', 'java', 'cpp'].includes(selectedLanguage)) {
      const lineStart = value.lastIndexOf('\n', cursorPos - 1) + 1;
      const currentLine = value.slice(lineStart, cursorPos);
      const trimmedLine = currentLine.trim();
      
      // Eğer satır noktalı virgül ile bitmiyorsa ve gerekliyse ekle
      if (!trimmedLine.endsWith(';') && !trimmedLine.endsWith('{') && !trimmedLine.endsWith('}') && 
          !trimmedLine.includes('//') && !trimmedLine.includes('/*') && trimmedLine.length > 0) {
        
        // Otomatik noktalı virgül ekleme kuralları
        const shouldAddSemicolon = [
          'return', 'break', 'continue', 'throw', 'import', 'export', 'var', 'let', 'const',
          'public', 'private', 'protected', 'static', 'final', 'abstract', 'class', 'interface'
        ].some(keyword => trimmedLine.startsWith(keyword));
        
        if (shouldAddSemicolon) {
          e.preventDefault();
          const newValue = value.slice(0, cursorPos) + ';' + '\n' + value.slice(cursorPos);
          setUserCode(newValue);
          
          setTimeout(() => {
            const newCursorPos = cursorPos + 2;
            e.target.setSelectionRange(newCursorPos, newCursorPos);
          }, 0);
        }
      }
    }
  };

  // Otomatik tamamlama önerileri
  const getAutoCompleteSuggestions = (currentLine, cursorPos) => {
    const config = languageConfigs[selectedLanguage];
    const suggestions = [];
    
    // Temel anahtar kelimeler
    suggestions.push(...config.keywords);
    
    // Dil bazlı özel öneriler
    if (selectedLanguage === 'python') {
      suggestions.push('print', 'len', 'range', 'list', 'dict', 'set', 'tuple', 'str', 'int', 'float', 'bool');
    } else if (selectedLanguage === 'javascript') {
      suggestions.push('console.log', 'Math', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Date');
    } else if (selectedLanguage === 'java') {
      suggestions.push('System.out.println', 'Math', 'String', 'Integer', 'Double', 'Boolean', 'ArrayList', 'HashMap');
    } else if (selectedLanguage === 'cpp') {
      suggestions.push('cout', 'cin', 'endl', 'string', 'vector', 'map', 'set', 'iostream', 'algorithm');
    }
    
    return suggestions.filter(suggestion => 
      suggestion.toLowerCase().includes(currentLine.toLowerCase())
    ).slice(0, 5);
  };

  // Kod formatlaması
  const formatCode = () => {
    const config = languageConfigs[selectedLanguage];
    let formattedCode = userCode;
    
    // Satır sonu boşlukları temizle
    formattedCode = formattedCode.replace(/[ \t]+$/gm, '');
    
    // Boş satırları normalize et
    formattedCode = formattedCode.replace(/\n\s*\n\s*\n/g, '\n\n');
    
    // Girintileri düzelt
    const lines = formattedCode.split('\n');
    const formattedLines = lines.map(line => {
      const trimmed = line.trim();
      if (trimmed === '') return '';
      
      // Girinti seviyesini hesapla
      let indentLevel = 0;
      for (let i = 0; i < lines.length; i++) {
        const currentLine = lines[i].trim();
        if (currentLine === trimmed) break;
        
        if (config.autoIndent.some(keyword => currentLine.startsWith(keyword))) {
          indentLevel++;
        } else if (config.deindent.some(keyword => currentLine.startsWith(keyword))) {
          indentLevel = Math.max(0, indentLevel - 1);
        }
      }
      
      return ' '.repeat(indentLevel * config.indentSize) + trimmed;
    });
    
    setUserCode(formattedLines.join('\n'));
  };

  // Syntax highlighting için basit renklendirme
  const getHighlightedCode = (code) => {
    const config = languageConfigs[selectedLanguage];
    let highlighted = code;
    
    // Yorumları renklendir
    const commentRegex = new RegExp(`(${config.comment}.*)`, 'g');
    highlighted = highlighted.replace(commentRegex, '<span style="color: #6a9955;">$1</span>');
    
    // Anahtar kelimeleri renklendir
    config.keywords.forEach(keyword => {
      const keywordRegex = new RegExp(`\\b${keyword}\\b`, 'g');
      highlighted = highlighted.replace(keywordRegex, `<span style="color: #569cd6;">${keyword}</span>`);
    });
    
    // String'leri renklendir
    highlighted = highlighted.replace(/(["'`])((?:\\.|(?!\1)[^\\])*?)\1/g, '<span style="color: #ce9178;">$1$2$1</span>');
    
    // Sayıları renklendir
    highlighted = highlighted.replace(/\b\d+\.?\d*\b/g, '<span style="color: #b5cea8;">$&</span>');
    
    return highlighted;
  };

  const fetchQuestion = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post('http://localhost:5000/code_room', {
        difficulty: difficulty,
        language: selectedLanguage
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
        use_execution: useExecution,
        language: selectedLanguage
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
        question: question,
        language: selectedLanguage
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
        code: userCode,
        language: selectedLanguage
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
        code: userCode,
        language: selectedLanguage
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
      const config = languageConfigs[selectedLanguage];
      const searchTopic = question 
        ? `${config.name} programlama ${question.slice(0, 100)}` 
        : `${config.name} programlama başlangıç orta seviye`;
        
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

  // Dil değiştiğinde placeholder'ı güncelle
  useEffect(() => {
    const config = languageConfigs[selectedLanguage];
    if (step === 'coding' && !userCode.trim()) {
      setUserCode(`// ${config.name} kodunuzu buraya yazın...
// Örnek:
${config.name === 'Python' ? 'def solution():\n    # Kodunuz buraya\n    pass\n\n# Test\nprint(solution())' :
  config.name === 'JavaScript' ? 'function solution() {\n    // Kodunuz buraya\n    return null;\n}\n\n// Test\nconsole.log(solution());' :
  config.name === 'Java' ? 'public class Solution {\n    public static void main(String[] args) {\n        // Kodunuz buraya\n        System.out.println("Hello World");\n    }\n}' :
  'int main() {\n    // Kodunuz buraya\n    return 0;\n}'}`);
    }
  }, [selectedLanguage]);

  // Klavye kısayolları
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+F ile kod formatla
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        formatCode();
      }
      
      // Ctrl+S ile kaydet (gelecekte kullanılabilir)
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        // Kaydetme özelliği eklenebilir
      }
      
      // Ctrl+Enter ile çalıştır
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        if (userCode.trim() && !loading) {
          handleSubmit();
        }
      }
    };

    if (step === 'coding') {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [step, userCode, loading]);

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
            💻 Kodlama Odası
          </Typography>
          <Typography textAlign="center" mb={4} color="rgba(255,255,255,0.8)">
            Gemini AI ile gerçek kod çalıştırma deneyimi!
          </Typography>
          
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          
          <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
            <CardContent>
              <Typography variant="h6" color="white" mb={2}>✨ Akıllı IDE Özellikleri</Typography>
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
                <Grid item xs={6}>
                  <Chip icon={<CodeIcon />} label="Syntax Highlighting" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<Speed />} label="Otomatik Girinti" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<AutoFixHigh />} label="Parantez Eşleştirme" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<CodeIcon />} label="Kod Formatlama" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
                <Grid item xs={6}>
                  <Chip icon={<Speed />} label="Klavye Kısayolları" size="small" sx={{ color: 'white', mb: 1 }} />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
          
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Programlama Dili</InputLabel>
                <Select
                  value={selectedLanguage}
                  label="Programlama Dili"
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  sx={{
                    color: 'white',
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' },
                    '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.5)' },
                    '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#4f46e5' },
                  }}
                >
                  <MenuItem value="python">🐍 Python</MenuItem>
                  <MenuItem value="javascript">🟨 JavaScript</MenuItem>
                  <MenuItem value="java">☕ Java</MenuItem>
                  <MenuItem value="cpp">⚡ C++</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
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
            {loading ? 'Soru Hazırlanıyor...' : `${languageConfigs[selectedLanguage].name} Sorusu Al`}
          </Button>
        </Paper>
      </Box>
    );
  }

  if (step === 'coding') {
    const config = languageConfigs[selectedLanguage];
    
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
            {config.icon} {config.name} Kodlama Problemi
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
                <Typography fontWeight={600} color="white">{config.name} Kodunuzu Yazın:</Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={formatCode}
                    sx={{ 
                      color: 'rgba(255,255,255,0.8)', 
                      borderColor: 'rgba(255,255,255,0.3)',
                      fontSize: '12px',
                      '&:hover': { borderColor: 'white', backgroundColor: 'rgba(255,255,255,0.1)' }
                    }}
                  >
                    🔧 Format
                  </Button>
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
              </Box>
              
              <Box sx={{ position: 'relative', mb: 3 }}>
                <TextField
                  ref={codeEditorRef}
                  multiline
                  rows={15}
                  fullWidth
                  value={userCode}
                  onChange={handleCodeChange}
                  onKeyDown={handleKeyDown}
                  placeholder={`// ${config.name} kodunuzu buraya yazın...
// Örnek:
${config.name === 'Python' ? 'def solution():\n    # Kodunuz buraya\n    pass\n\n# Test\nprint(solution())' :
  config.name === 'JavaScript' ? 'function solution() {\n    // Kodunuz buraya\n    return null;\n}\n\n// Test\nconsole.log(solution());' :
  config.name === 'Java' ? 'public class Solution {\n    public static void main(String[] args) {\n        // Kodunuz buraya\n        System.out.println("Hello World");\n    }\n}' :
  'int main() {\n    // Kodunuz buraya\n    return 0;\n}'}`}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: 'white',
                      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                      fontSize: '14px',
                      lineHeight: '1.5',
                      '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                      '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.5)' },
                      '&.Mui-focused fieldset': { borderColor: '#4f46e5' },
                      '& .MuiInputBase-input::placeholder': { color: 'rgba(255,255,255,0.5)', opacity: 1 },
                      backgroundColor: 'rgba(0,0,0,0.3)',
                    },
                  }}
                />
                
                {/* Gelişmiş IDE özellikleri bilgisi */}
                <Box sx={{ 
                  position: 'absolute', 
                  top: 10, 
                  right: 10, 
                  backgroundColor: 'rgba(0,0,0,0.8)', 
                  borderRadius: 1, 
                  p: 1.5,
                  fontSize: '11px',
                  color: 'rgba(255,255,255,0.8)',
                  maxWidth: '200px'
                }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>🚀 Akıllı IDE</div>
                  <div>Tab: Girinti</div>
                  <div>Enter: Otomatik girinti</div>
                  <div>Backspace: Girinti sil</div>
                  <div>(): Otomatik parantez</div>
                  <div>Shift+Enter: Akıllı satır böl</div>
                  <div>Ctrl+F: Format kod</div>
                </Box>
              </Box>
              
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
                      <Typography color="white">{config.icon} {config.name} Kodu</Typography>
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
                            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
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
                              fontFamily: 'Consolas, Monaco, "Courier New", monospace',
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
                  {config.name} öğrenme kaynakları için "Kaynaklar" butonuna tıklayın.
                </Typography>
              )}
            </Box>
          )}
        </Paper>
      </Box>
    );
  }

  if (step === 'result') {
    const config = languageConfigs[selectedLanguage];
    
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
            📊 {config.name} Kod Değerlendirme Sonucu
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