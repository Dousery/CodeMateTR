import re
from typing import List, Tuple
from enum import Enum

class Language(Enum):
    JAVA = "java"
    JAVASCRIPT = "javascript"
    PYTHON = "python"
    CPP = "cpp"

class CodeIndenter:
    """Çoklu dil desteği olan kod girintileme sınıfı"""
    
    def __init__(self):
        self.language_configs = {
            Language.JAVA: {
                'indent_size': 4,
                'indent_char': ' ',
                'open_brackets': ['{', '(', '['],
                'close_brackets': ['}', ')', ']'],
                'special_keywords': ['case', 'default'],
                'comment_patterns': ['//', '/*', '*/']
            },
            Language.JAVASCRIPT: {
                'indent_size': 2,
                'indent_char': ' ',
                'open_brackets': ['{', '(', '['],
                'close_brackets': ['}', ')', ']'],
                'special_keywords': ['case', 'default'],
                'comment_patterns': ['//', '/*', '*/']
            },
            Language.PYTHON: {
                'indent_size': 4,
                'indent_char': ' ',
                'open_brackets': [],
                'close_brackets': [],
                'special_keywords': ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 
                                   'try', 'except', 'finally', 'with'],
                'comment_patterns': ['#']
            },
            Language.CPP: {
                'indent_size': 4,
                'indent_char': ' ',
                'open_brackets': ['{', '(', '['],
                'close_brackets': ['}', ')', ']'],
                'special_keywords': ['case', 'default', 'namespace'],
                'comment_patterns': ['//', '/*', '*/']
            }
        }
    
    def detect_language(self, code: str) -> Language:
        """Kod içeriğinden dili otomatik tespit et"""
        # Python özgün anahtar kelimeler
        python_keywords = ['def ', 'import ', 'from ', 'print(', '__init__']
        # Java/C++ özgün yapılar
        java_cpp_patterns = ['public class', 'private ', 'std::', '#include', 'System.out']
        # JavaScript özgün yapılar
        js_patterns = ['function ', 'var ', 'let ', 'const ', 'console.log', '=>']
        
        python_score = sum(1 for keyword in python_keywords if keyword in code)
        java_cpp_score = sum(1 for pattern in java_cpp_patterns if pattern in code)
        js_score = sum(1 for pattern in js_patterns if pattern in code)
        
        # C++ vs Java ayrımı
        if java_cpp_score > 0:
            if '#include' in code or 'std::' in code or 'cout' in code:
                return Language.CPP
            else:
                return Language.JAVA
        
        if js_score > python_score and js_score > java_cpp_score:
            return Language.JAVASCRIPT
        elif python_score > 0:
            return Language.PYTHON
        else:
            # Varsayılan olarak Java
            return Language.JAVA
    
    def indent_java(self, code: str) -> str:
        """Java kodu girintileme"""
        lines = code.split('\n')
        result = []
        indent_level = 0
        config = self.language_configs[Language.JAVA]
        indent_str = config['indent_char'] * config['indent_size']
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                result.append('')
                continue
            
            # Kapanış parantezleri için girinti azalt
            if any(stripped.startswith(bracket) for bracket in config['close_brackets']):
                indent_level = max(0, indent_level - 1)
            
            # case ve default için özel durum
            if stripped.startswith('case ') or stripped.startswith('default:'):
                current_indent = indent_str * max(0, indent_level - 1)
            else:
                current_indent = indent_str * indent_level
            
            result.append(current_indent + stripped)
            
            # Açılış parantezleri için girinti artır
            if any(stripped.endswith(bracket) for bracket in config['open_brackets']):
                indent_level += 1
            
            # case/default için özel artış
            if stripped.endswith(':') and (stripped.startswith('case ') or stripped.startswith('default')):
                indent_level += 1
        
        return '\n'.join(result)
    
    def indent_javascript(self, code: str) -> str:
        """JavaScript kodu girintileme"""
        lines = code.split('\n')
        result = []
        indent_level = 0
        config = self.language_configs[Language.JAVASCRIPT]
        indent_str = config['indent_char'] * config['indent_size']
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                result.append('')
                continue
            
            # Çok satırlı yorum kontrolü
            if '/*' in stripped:
                in_multiline_comment = True
            if '*/' in stripped:
                in_multiline_comment = False
            
            if in_multiline_comment:
                result.append(indent_str * indent_level + stripped)
                continue
            
            # Kapanış parantezleri
            if any(stripped.startswith(bracket) for bracket in config['close_brackets']):
                indent_level = max(0, indent_level - 1)
            
            result.append(indent_str * indent_level + stripped)
            
            # Açılış parantezleri
            if any(stripped.endswith(bracket) for bracket in config['open_brackets']):
                indent_level += 1
            
            # Arrow function kontrolü
            if '=>' in stripped and stripped.endswith('{'):
                # Zaten artırıldı
                pass
        
        return '\n'.join(result)
    
    def indent_python(self, code: str) -> str:
        """Python kodu girintileme"""
        lines = code.split('\n')
        result = []
        indent_level = 0
        function_level = 0  # Fonksiyon seviyesini takip et
        config = self.language_configs[Language.PYTHON]
        indent_str = config['indent_char'] * config['indent_size']
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if not stripped:
                result.append('')
                continue
            
            # Fonksiyon tanımı kontrolü
            if stripped.startswith('def ') or stripped.startswith('class '):
                function_level = indent_level
            
            # Return satırı için özel kontrol
            if stripped.startswith('return'):
                # Return her zaman fonksiyon seviyesinde olmalı (1 seviye girinti)
                current_indent = indent_str * (function_level + 1)
                result.append(current_indent + stripped)
                continue
            
            # elif, else, except, finally için dedent
            dedent_keywords = ['elif ', 'else:', 'except', 'finally:']
            if any(stripped.startswith(keyword) for keyword in dedent_keywords):
                current_indent = indent_str * max(0, indent_level - 1)
            else:
                current_indent = indent_str * indent_level
            
            result.append(current_indent + stripped)
            
            # İndent artırma koşulları
            indent_keywords = ['def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 
                             'while ', 'try:', 'except', 'finally:', 'with ']
            
            if stripped.endswith(':') and any(stripped.startswith(keyword) for keyword in indent_keywords):
                indent_level += 1
            
            # Sonraki satır için dedent kontrolü
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if any(next_stripped.startswith(keyword) for keyword in dedent_keywords) and indent_level > 0:
                    indent_level -= 1
        
        return '\n'.join(result)
    
    def indent_cpp(self, code: str) -> str:
        """C++ kodu girintileme"""
        lines = code.split('\n')
        result = []
        indent_level = 0
        config = self.language_configs[Language.CPP]
        indent_str = config['indent_char'] * config['indent_size']
        in_multiline_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                result.append('')
                continue
            
            # Çok satırlı yorum kontrolü
            if '/*' in stripped:
                in_multiline_comment = True
            if '*/' in stripped:
                in_multiline_comment = False
            
            if in_multiline_comment:
                result.append(indent_str * indent_level + stripped)
                continue
            
            # Preprocessor direktifleri
            if stripped.startswith('#'):
                result.append(stripped)
                continue
            
            # Kapanış parantezleri
            if any(stripped.startswith(bracket) for bracket in config['close_brackets']):
                indent_level = max(0, indent_level - 1)
            
            # case ve default için özel durum
            if stripped.startswith('case ') or stripped.startswith('default:'):
                current_indent = indent_str * max(0, indent_level - 1)
            else:
                current_indent = indent_str * indent_level
            
            result.append(current_indent + stripped)
            
            # Açılış parantezleri
            if any(stripped.endswith(bracket) for bracket in config['open_brackets']):
                indent_level += 1
            
            # case/default için özel artış
            if stripped.endswith(':') and (stripped.startswith('case ') or stripped.startswith('default')):
                indent_level += 1
        
        return '\n'.join(result)
    
    def indent_code(self, code: str, language: Language = None) -> str:
        """Ana girintileme metodu"""
        if language is None:
            language = self.detect_language(code)
        
        if language == Language.JAVA:
            return self.indent_java(code)
        elif language == Language.JAVASCRIPT:
            return self.indent_javascript(code)
        elif language == Language.PYTHON:
            return self.indent_python(code)
        elif language == Language.CPP:
            return self.indent_cpp(code)
        else:
            raise ValueError(f"Desteklenmeyen dil: {language}")

# Global instance
code_indenter = CodeIndenter() 