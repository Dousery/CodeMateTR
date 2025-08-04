import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, Typography, Paper, Button, TextField, CircularProgress, Alert, 
  Tabs, Tab, Select, MenuItem, FormControl, InputLabel, Card, CardContent,
  Accordion, AccordionSummary, AccordionDetails, Chip, Grid, Switch, FormControlLabel,
  Dialog, DialogTitle, DialogContent, DialogActions, IconButton
} from '@mui/material';
import { 
  ExpandMore, PlayArrow, BugReport, Analytics, School, Code as CodeIcon,
  AutoFixHigh, Speed, Psychology, Close
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';
import API_ENDPOINTS from './config.js';

export default function Code() {
  const [question, setQuestion] = useState('');
  const [userCode, setUserCode] = useState('');
  const [step, setStep] = useState('start'); // start, coding, result
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [difficulty, setDifficulty] = useState('orta');
  const [activeTab, setActiveTab] = useState(0);
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [cursorPosition, setCursorPosition] = useState(0);
  const codeEditorRef = useRef(null);
  
  const [generatedSolution, setGeneratedSolution] = useState(null);
  const [resources, setResources] = useState(null);
  const [executionOutput, setExecutionOutput] = useState(null); // Yeni state: çalıştırma çıktısı
  const [autoCopyToIDE, setAutoCopyToIDE] = useState(false); // Otomatik IDE'ye kopyalama
  const [showAiSolution, setShowAiSolution] = useState(false); // AI çözümünü göster/gizle
  const [copyNotification, setCopyNotification] = useState(false); // Kopyalama bildirimi
  


  // State'leri sıfırlama fonksiyonu
  const resetAllStates = () => {
    setQuestion('');
    setUserCode('');
    setStep('start');
    setLoading(false);
    setResult(null);
    setError('');
    setDifficulty('orta');
    setActiveTab(0);
    setSelectedLanguage('python');
    setCursorPosition(0);
    setGeneratedSolution(null);
    setResources(null);
    setExecutionOutput(null);
    setAutoCopyToIDE(false);
    setShowAiSolution(false);
    setCopyNotification(false);
  };

  // Component mount olduğunda state'leri sıfırla
  useEffect(() => {
    resetAllStates();
  }, []); // Sadece component mount olduğunda çalışır

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
  const formatCode = async () => {
    if (!userCode.trim()) return;
    
    setLoading(true);
    try {
      const res = await axios.post(API_ENDPOINTS.CODE_FORMAT, {
        code: userCode,
        language: selectedLanguage
      }, { withCredentials: true });
      
      if (res.data.success) {
        setUserCode(res.data.formatted_code);
        setError('✅ Kod başarıyla formatlandı!');
        setTimeout(() => {
          setError('');
        }, 3000);
      }
    } catch (err) {
      setError('❌ Kod formatlanamadı: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  // AI çözümü için kod formatlama fonksiyonu
  const formatCodeString = async (code, language) => {
    if (!code.trim()) return code;
    
    try {
      const res = await axios.post(API_ENDPOINTS.CODE_FORMAT, {
        code: code,
        language: language
      }, { withCredentials: true });
      
      if (res.data.success) {
        return res.data.formatted_code;
      }
    } catch (err) {
      console.error('AI çözümü formatlanamadı:', err);
    }
    
    // Fallback: Basit formatlama
    return code;
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
      const res = await axios.post(API_ENDPOINTS.CODE_ROOM, {
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



  // Yeni fonksiyon: Sadece kodu çalıştır
  const handleRunCode = async () => {
    if (!userCode.trim()) {
      setError('Lütfen kodunuzu yazın.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      // Sadece kod çalıştırma - analiz yok
      const res = await axios.post(API_ENDPOINTS.CODE_RUN_SIMPLE, {
        user_code: userCode,
        language: selectedLanguage
      }, { withCredentials: true });
      
      if (res.data.success) {
        const result = res.data.result;
        
        // Sadece çalıştırma sonucunu göster
        const simpleOutput = {
          execution_output: '',
          has_errors: false,
          execution_time: 'N/A',
          memory_usage: 'N/A',
          code_analysis: '',
          suggestions: ''
        };
        
        // Sadece çıktı/hata - kod gösterme
        let output = '';
        
        if (result.output) {
          output += `${result.output}\n`;
        }
        
        if (result.error) {
          output += `${result.error}\n`;
          simpleOutput.has_errors = true;
        }
        
        simpleOutput.execution_output = output.trim();
        setExecutionOutput(simpleOutput);
        
        if (!simpleOutput.has_errors) {
          console.log('✅ Kod başarıyla çalıştırıldı!');
        }
      } else {
        setError(res.data.error || 'Kod çalıştırma başarısız.');
      }
    } catch (err) {
      // Fallback: Eski API'yi dene
      try {
        console.log('🔄 Yeni API başarısız, eski API deneniyor...');
        const fallbackRes = await axios.post(API_ENDPOINTS.CODE_RUN, {
          user_code: userCode,
          language: selectedLanguage
        }, { withCredentials: true });
        setExecutionOutput(fallbackRes.data.result);
      } catch (fallbackErr) {
        setError(err.response?.data?.error || fallbackErr.response?.data?.error || 'Kod çalıştırma başarısız.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Yeni fonksiyon: Kod çalıştır ve analiz et
  const handleEvaluateCode = async () => {
    if (!userCode.trim()) {
      setError('Lütfen kodunuzu yazın.');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      // Mevcut code odası evaluate fonksiyonunu kullan
      const res = await axios.post(API_ENDPOINTS.CODE_EVALUATE, {
        question: question,
        user_code: userCode,
        use_execution: true, // Çalıştır ve analiz et
        language: selectedLanguage
      }, { withCredentials: true });
      
      // Sonucu formatla
      const evaluationResult = {
        evaluation: res.data.evaluation || '',
        execution_output: res.data.execution_output || '',
        code_suggestions: res.data.code_suggestions || '',
        has_errors: res.data.has_errors || false,
        corrected_code: res.data.corrected_code || '',
        score: res.data.score || 0,
        feedback: res.data.feedback || '',
        use_execution: true
      };
      
      setResult(evaluationResult);
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
      const res = await axios.post(API_ENDPOINTS.CODE_GENERATE, {
        question: question,
        language: selectedLanguage
      }, { withCredentials: true });
      
      console.log('AI Response:', res.data); // Debug için
      
      // Kodu formatla
      let formattedCode = '';
      if (res.data && (res.data.code || res.data.solution?.code || res.data.solution || res.data.generated_code)) {
        const rawCode = res.data.code || res.data.solution?.code || res.data.solution || res.data.generated_code || '';
        formattedCode = await formatCodeString(rawCode, selectedLanguage);
        
        // Formatlanmış kodu response'a ekle
        res.data.formatted_code = formattedCode;
      }
      
      setGeneratedSolution(res.data);
      
      // AI çözümü üretildikten sonra sadece çözümü göster
      if (res.data && (res.data.code || res.data.solution?.code || res.data.solution || res.data.generated_code)) {
        console.log('AI solution generated successfully'); // Debug için
        
        // Başarı mesajını göster
        setError('✅ AI çözümü başarıyla üretildi!');
        
        // AI çözümünü göster
        setShowAiSolution(true);
        
        // 15 saniye sonra başarı mesajını temizle
        setTimeout(() => {
          setError('');
        }, 15000);
      } else {
        console.log('No code found in response'); // Debug için
        setError('❌ AI çözümünde kod bulunamadı!');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Çözüm üretilemedi.');
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
        
      const res = await axios.post(API_ENDPOINTS.CODE_SUGGEST, {
        topic: searchTopic,
        num_resources: 5
      }, { withCredentials: true });
      
            setResources(res.data);
      // setActiveTab(3); // Kaynaklar sekmesine geç
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
          handleRunCode();
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
      <Box sx={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', pt: 8 }}>
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
      <Box sx={{ minHeight: '100vh', width: '100vw', py: 4, pt: 12 }}>
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
                    onClick={() => formatCode()}
                    sx={{ 
                      color: 'rgba(255,255,255,0.8)', 
                      borderColor: 'rgba(255,255,255,0.3)',
                      fontSize: '12px',
                      '&:hover': { borderColor: 'white', backgroundColor: 'rgba(255,255,255,0.1)' }
                    }}
                  >
                    🔧 Format
                  </Button>
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
              
              {error && (
                <Alert 
                  severity={error.startsWith('✅') ? 'success' : 'error'} 
                  action={
                    error.startsWith('✅') && (
                      <Button
                        color="inherit"
                        size="small"
                        onClick={() => setError('')}
                        sx={{ 
                          color: '#4caf50',
                          '&:hover': { backgroundColor: 'rgba(76, 175, 80, 0.1)' }
                        }}
                      >
                        ✕
                      </Button>
                    )
                  }
                  sx={{ 
                    mb: 2,
                    ...(error.startsWith('✅') && {
                      backgroundColor: 'rgba(76, 175, 80, 0.1)',
                      border: '1px solid rgba(76, 175, 80, 0.3)',
                      color: '#4caf50'
                    })
                  }}
                >
                  {error}
                </Alert>
              )}
              

              
              {/* Basit çalıştırma çıktısı kartı */}
              {executionOutput && (
                <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                  <CardContent>
                    <Typography variant="h6" color="white" mb={2}>
                      📊 Çıktı
                    </Typography>
                    <Box sx={{ 
                      backgroundColor: 'rgba(0,0,0,0.3)', 
                      p: 2, 
                      borderRadius: 1,
                      border: executionOutput.has_errors ? '1px solid #f44336' : '1px solid #4caf50'
                    }}>
                      <Typography 
                        color={executionOutput.has_errors ? '#f44336' : '#4caf50'} 
                        sx={{ 
                          whiteSpace: 'pre-wrap', 
                          fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                          fontSize: '14px'
                        }}
                      >
                        {executionOutput.execution_output}
                      </Typography>
                    </Box>
                    {executionOutput.has_errors ? (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        ⚠️ Kodunuzda hatalar tespit edildi. "Değerlendir" butonunu kullanarak detaylı analiz alabilirsiniz.
                      </Alert>
                    ) : (
                      <Alert severity="success" sx={{ mt: 2 }}>
                        ✅ Kod başarıyla çalıştırıldı! Detaylı analiz için "Değerlendir" butonunu kullanın.
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              )}
              
              {/* AI Çözümü Kartı */}
              {showAiSolution && generatedSolution && (
                <Card sx={{ mb: 3, backgroundColor: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" color="white">🤖 AI Çözümü</Typography>
                      <Button
                        size="small"
                        onClick={() => setShowAiSolution(false)}
                        sx={{ 
                          color: 'rgba(255,255,255,0.7)',
                          '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
                        }}
                      >
                        ✕
                      </Button>
                    </Box>
                    
                    <Accordion defaultExpanded sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.05)' }}>
                      <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                        <Typography color="white">💡 Açıklama</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap' }}>
                          {generatedSolution.explanation || generatedSolution.solution?.explanation || 'Açıklama bulunamadı'}
                        </Typography>
                      </AccordionDetails>
                    </Accordion>
                    
                    <Accordion defaultExpanded sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.05)' }}>
                      <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                        <Typography color="white">{languageConfigs[selectedLanguage].icon} {languageConfigs[selectedLanguage].name} Kodu</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ position: 'relative' }}>
                          <TextField
                            multiline
                            fullWidth
                            rows={8}
                            value={generatedSolution.formatted_code || generatedSolution.code || generatedSolution.solution?.code || generatedSolution.solution || generatedSolution.generated_code || 'Kod bulunamadı'}
                            InputProps={{ readOnly: true }}
                            sx={{
                              '& .MuiOutlinedInput-root': {
                                color: 'white',
                                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                                backgroundColor: 'rgba(0,0,0,0.3)',
                                '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                              },
                            }}
                          />
                          <Button
                            size="small"
                            onClick={() => {
                              const codeToCopy = generatedSolution.formatted_code || generatedSolution.code || generatedSolution.solution?.code || generatedSolution.solution || generatedSolution.generated_code || '';
                              if (codeToCopy) {
                                navigator.clipboard.writeText(codeToCopy);
                                setCopyNotification(true);
                                setTimeout(() => {
                                  setCopyNotification(false);
                                }, 2000);
                              }
                            }}
                            sx={{
                              position: 'absolute',
                              top: 8,
                              right: 40,
                              minWidth: 'auto',
                              width: 32,
                              height: 32,
                              backgroundColor: copyNotification ? 'rgba(76, 175, 80, 0.9)' : 'rgba(0,0,0,0.7)',
                              color: copyNotification ? 'white' : 'rgba(255,255,255,0.8)',
                              transition: 'all 0.3s ease',
                              '&:hover': {
                                backgroundColor: copyNotification ? 'rgba(76, 175, 80, 1)' : 'rgba(0,0,0,0.9)',
                                color: 'white',
                              },
                            }}
                          >
                            {copyNotification ? '✅' : '📋'}
                          </Button>
                          
                          {/* Kopyalama Bildirimi */}
                          {copyNotification && (
                            <Box
                              sx={{
                                position: 'absolute',
                                top: -40,
                                right: 0,
                                backgroundColor: 'rgba(76, 175, 80, 0.95)',
                                color: 'white',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                fontSize: '12px',
                                fontWeight: 500,
                                zIndex: 1000,
                                animation: 'slideIn 0.3s ease',
                                '@keyframes slideIn': {
                                  '0%': {
                                    opacity: 0,
                                    transform: 'translateY(10px)',
                                  },
                                  '100%': {
                                    opacity: 1,
                                    transform: 'translateY(0)',
                                  },
                                },
                              }}
                            >
                              ✅ Kod panoya kopyalandı!
                            </Box>
                          )}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                    
                    {(generatedSolution.test_results || generatedSolution.solution?.test_results) && (
                      <Accordion sx={{ mb: 2, backgroundColor: 'rgba(255,255,255,0.05)' }}>
                        <AccordionSummary expandIcon={<ExpandMore sx={{ color: 'white' }} />}>
                          <Typography color="white">🧪 Test Sonuçları</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography color="rgba(255,255,255,0.8)" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                            {generatedSolution.test_results || generatedSolution.solution?.test_results}
                          </Typography>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </CardContent>
                </Card>
              )}
              
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    fullWidth
                    onClick={handleRunCode} 
                    disabled={loading || !userCode.trim()} 
                    endIcon={loading && <CircularProgress size={20} color="inherit" />}
                    startIcon={<PlayArrow />}
                    sx={{
                      background: 'linear-gradient(45deg, #4caf50 0%, #66bb6a 100%)',
                      borderRadius: '15px',
                      py: 1.2,
                      textTransform: 'none',
                      fontWeight: 600,
                      '&:hover': {
                        background: 'linear-gradient(45deg, #388e3c 0%, #4caf50 100%)',
                      }
                    }}
                  >
                    {loading ? 'Çalıştırılıyor...' : '🚀 Çalıştır'}
                  </Button>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Button 
                    variant="contained" 
                    color="secondary" 
                    fullWidth
                    onClick={handleEvaluateCode} 
                    disabled={loading || !userCode.trim()} 
                    endIcon={loading && <CircularProgress size={20} color="inherit" />}
                    startIcon={<Psychology />}
                    sx={{
                      background: 'linear-gradient(45deg, #ff9800 0%, #ffb74d 100%)',
                      borderRadius: '15px',
                      py: 1.2,
                      textTransform: 'none',
                      fontWeight: 600,
                      '&:hover': {
                        background: 'linear-gradient(45deg, #f57c00 0%, #ff9800 100%)',
                      }
                    }}
                  >
                    {loading ? 'Değerlendiriliyor...' : '🧠 Değerlendir'}
                  </Button>
                </Grid>
                <Grid item xs={12} md={4}>
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
                <Grid item xs={3}>
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
      <Dialog 
        open={true} 
        maxWidth="md" 
        fullWidth 
        PaperProps={{
          component: motion.div,
          initial: { opacity: 0, scale: 0.8 },
          animate: { opacity: 1, scale: 1 },
          transition: { duration: 0.3 },
          sx: {
            backgroundColor: 'rgba(30, 30, 60, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 3,
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }
        }}
      >
        <DialogTitle sx={{ 
          backgroundColor: 'rgba(255,255,255,0.1)', 
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h5" fontWeight={700}>
            📊 {config.name} Kod Değerlendirme Sonucu
          </Typography>
          <IconButton 
            onClick={() => setStep('start')} 
            sx={{ color: 'white' }}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        
        <DialogContent sx={{ p: 3 }}>
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
        </DialogContent>
        
        <DialogActions sx={{ p: 3, backgroundColor: 'rgba(255,255,255,0.05)' }}>
          <Button 
            onClick={() => setStep('start')} 
            variant="contained" 
            sx={{ 
              backgroundColor: 'rgba(255,255,255,0.2)',
              color: 'white',
              '&:hover': { backgroundColor: 'rgba(255,255,255,0.3)' }
            }}
          >
            Kapat
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  // Ana return statement - coding step için
  return (
    <Box sx={{ minHeight: '100vh', width: '100vw', py: 4 }}>
      <Paper 
        component={motion.div} 
        initial={{ opacity: 0, y: 40 }} 
        animate={{ opacity: 1, y: 0 }} 
        transition={{ duration: 0.7 }} 
        elevation={8} 
        className="glass-card"
        sx={{ p: 5, maxWidth: 1200, mx: 'auto', borderRadius: 4 }}
      >

        
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
                resetAllStates();
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