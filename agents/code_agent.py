import google.generativeai as genai
import os
import json
import traceback
import re
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class CodeAIAgent:
    def __init__(self, interest, language='python'):
        self.interest = interest
        self.language = language
        # Configure Gemini API
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        # Dil konfigürasyonları
        self.language_configs = {
            'python': {
                'name': 'Python',
                'extension': '.py',
                'comment': '#',
                'keywords': ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'import', 'from', 'as', 'return', 'yield', 'break', 'continue', 'pass', 'True', 'False', 'None'],
                'syntax': 'Python syntax',
                'examples': ['def solution():\n    return "Hello World"\n\nprint(solution())']
            },
            'javascript': {
                'name': 'JavaScript',
                'extension': '.js',
                'comment': '//',
                'keywords': ['function', 'class', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch', 'case', 'default', 'return', 'break', 'continue', 'var', 'let', 'const', 'import', 'export', 'async', 'await'],
                'syntax': 'JavaScript syntax',
                'examples': ['function solution() {\n    return "Hello World";\n}\n\nconsole.log(solution());']
            },
            'java': {
                'name': 'Java',
                'extension': '.java',
                'comment': '//',
                'keywords': ['public', 'private', 'protected', 'class', 'interface', 'extends', 'implements', 'static', 'final', 'abstract', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'switch', 'case', 'default', 'return', 'break', 'continue', 'new', 'import', 'package'],
                'syntax': 'Java syntax',
                'examples': ['public class Solution {\n    public static void main(String[] args) {\n        System.out.println("Hello World");\n    }\n}']
            },
            'cpp': {
                'name': 'C++',
                'extension': '.cpp',
                'comment': '//',
                'keywords': ['int', 'float', 'double', 'char', 'bool', 'string', 'vector', 'class', 'struct', 'public', 'private', 'protected', 'if', 'else', 'for', 'while', 'try', 'catch', 'switch', 'case', 'default', 'return', 'break', 'continue', 'new', 'delete', 'include', 'using', 'namespace'],
                'syntax': 'C++ syntax',
                'examples': ['#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello World" << endl;\n    return 0;\n}']
            }
        }
        
    def generate_coding_question(self, difficulty="orta"):
        """
        Belirtilen zorluk seviyesinde kodlama sorusu üretir
        """
        if not self.model:
            return "API bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin."
            
        difficulty_levels = {
            "kolay": "başlangıç seviyesi, temel syntax",
            "orta": "orta seviye, fonksiyonlar, döngüler, veri yapıları",
            "zor": "ileri seviye, algoritmalar, optimizasyon, tasarım desenleri"
        }
        
        level_desc = difficulty_levels.get(difficulty, "orta seviye")
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        {self.interest} alanında {config['name']} dili için {level_desc} bir kısa kodlama sorusu üret.
        
        Format:
        - Problem (2-3 cümle)
        - Örnek: input -> output
        
        {config['name']} dilinde yazılacak şekilde sor.
        Sadece soruyu ver, çözüm yok.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Kodlama sorusu üretilemedi: {str(e)}"

    def evaluate_code_with_execution(self, user_code, question):
        """
        Kullanıcının kodunu çalıştırarak değerlendirir
        """
        if not self.model:
            return {
                "evaluation": "API bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin.",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": True,
                "corrected_code": ""
            }
        
        config = self.language_configs.get(self.language, self.language_configs['python'])
            
        prompt = f"""
        {config['name']} kodunu çalıştır ve kısa değerlendir:
        
        Soru: {question}
        
        Kod:
        ```{self.language}
        {user_code}
        ```
        
        Kısa çıktı ver:
        1. Kodu çalıştır
        2. Doğru/yanlış (1 cümle)
        3. Ana sorun varsa belirt (1 cümle)
        4. Kısa öneri (1 cümle)
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            result = {
                "evaluation": "",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": False,
                "corrected_code": ""
            }
            
            # Yanıtı parse et
            result["evaluation"] = response.text
            
            return result
            
        except Exception as e:
            return {
                "evaluation": f"Değerlendirme hatası: {str(e)}",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": True,
                "corrected_code": ""
            }

    def generate_code_solution(self, question):
        """
        Verilen soru için örnek çözüm üretir
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        {config['name']} dilinde bu soruyu çöz:
        
        Soru: {question}
        
        Lütfen aşağıdaki formatı kullan:
        
        **Açıklama:**
        Sorunun nasıl çözüleceğini kısaca açıkla (2-3 cümle)
        
        **Kod:**
        ```{self.language}
        # Çözüm kodunu buraya yaz
        ```
        
        **Test:**
        Kodun nasıl çalıştığını göster ve test sonuçlarını açıkla.
        """
        
        try:
            # Yeni Gemini API kullan
            response = self.model.generate_content(prompt)
            
            # Yanıtı parse et
            response_text = response.text
            
            result = {
                "explanation": "",
                "code": "",
                "test_results": "",
                "complexity_analysis": ""
            }
            
            # Text'i parse et
            lines = response_text.split('\n')
            current_section = "explanation"
            code_block = False
            
            for line in lines:
                line = line.strip()
                
                # Section başlıklarını tespit et
                if "**Açıklama:**" in line or "Açıklama:" in line:
                    current_section = "explanation"
                    continue
                elif "**Kod:**" in line or "Kod:" in line:
                    current_section = "code"
                    continue
                elif "**Test:**" in line or "Test:" in line:
                    current_section = "test_results"
                    continue
                
                # Kod bloğu başlangıcı
                if line.startswith("```") and current_section == "code":
                    code_block = not code_block
                    continue
                
                # İçeriği ilgili bölüme ekle
                if current_section == "explanation" and line:
                    result["explanation"] += line + "\n"
                elif current_section == "code" and code_block and line:
                    result["code"] += line + "\n"
                elif current_section == "code" and not code_block and line and not line.startswith("```"):
                    result["code"] += line + "\n"
                elif current_section == "test_results" and line:
                    result["test_results"] += line + "\n"
            
            # Eğer parsing başarısız olduysa, tüm metni explanation'a ekle
            if not result["explanation"] and not result["code"]:
                result["explanation"] = response_text
                
                # Kod bloğunu manuel olarak bul
                code_matches = re.findall(r'```(?:python|javascript|java)?\n(.*?)```', response_text, re.DOTALL)
                if code_matches:
                    result["code"] = code_matches[0].strip()
            
            # Boş alanları temizle
            result["explanation"] = result["explanation"].strip()
            result["code"] = result["code"].strip()
            result["test_results"] = result["test_results"].strip()
            
            return result
            
        except Exception as e:
            print(f"Code solution generation error: {e}")
            return {
                "explanation": f"Çözüm oluşturma hatası: {str(e)}",
                "code": "# Kod oluşturulamadı",
                "test_results": "Test sonucu mevcut değil",
                "complexity_analysis": ""
            }

    def generate_solution(self, question):
        """
        Frontend'den çağrılacak generate_solution metodu
        """
        return self.generate_code_solution(question)

    def debug_code(self, code_with_error):
        """
        Hatalı kodu debug eder ve düzeltir
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        Bu {config['name']} kodundaki hatayı bul ve düzelt:
        
        ```{self.language}
        {code_with_error}
        ```
        
        Kısaca:
        1. Ana hata nedir? (1 cümle)
        2. Düzeltilmiş kodu yaz ve çalıştır
        3. Neden hata oldu? (1 cümle)
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            debug_result = {
                "error_explanation": "",
                "corrected_code": "",
                "execution_result": "",
                "prevention_tips": ""
            }
            
            # Parse response text
            response_text = response.text
            debug_result["error_explanation"] = response_text
            
            # Try to extract corrected code
            code_matches = re.findall(r'```(?:python|javascript|java)?\n(.*?)```', response_text, re.DOTALL)
            if code_matches:
                debug_result["corrected_code"] = code_matches[0].strip()
            
            return debug_result
            
        except Exception as e:
            return {
                "error_explanation": f"Debug hatası: {str(e)}",
                "corrected_code": "",
                "execution_result": "",
                "prevention_tips": ""
            }

    def suggest_resources(self, topic, num_resources=3):
        """
        Belirtilen konu için öğrenme kaynakları önerir - Google Search ile gerçek linkler
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        {config['name']} dili için {topic} konusunda öğrenmek için en iyi {num_resources} kaynak ara ve öner.
        
        Her kaynak için:
        - Kaynak adı
        - Kısa açıklama (1 cümle)
        - Neden faydalı (1 cümle)
        - Zorluk seviyesi (Başlangıç/Orta/İleri)
        
        Güncel ve kaliteli kaynakları bul.
        """
        
        try:
            # Basit text generation kullan
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            # Fallback: Basit öneri
            fallback_prompt = f"""
            {config['name']} dili için {topic} konusunda {num_resources} kaynak öner.
            
            Format:
            1. Kaynak adı - açıklama (1 cümle)
            2. Kaynak adı - açıklama (1 cümle)
            3. Kaynak adı - açıklama (1 cümle)
            
            Kısa ve net ol.
            """
            
            try:
                fallback_response = self.model.generate_content(fallback_prompt)
                return fallback_response.text.strip()
            except:
                return f"Kaynak hatası: {str(e)}"

    def analyze_algorithm_complexity(self, code):
        """
        Verilen algoritmanın zaman ve alan karmaşıklığını analiz eder
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        Bu {config['name']} kodunun karmaşıklığını kısaca analiz et:
        
        ```{self.language}
        {code}
        ```
        
        Sadece:
        1. Zaman karmaşıklığı: O(?)
        2. Alan karmaşıklığı: O(?)
        3. Kısa açıklama (2 cümle)
        4. Optimizasyon var mı? (1 cümle)
        
        Uzun matematiksel açıklama yapma.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            return f"Analiz hatası: {str(e)}"

    def evaluate_code(self, user_code, question):
        """
        Kullanıcının kodunu geleneksel yöntemle değerlendirir (eski uyumlulık için)
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        {config['name']} kodunu kısaca değerlendir:
        
        Soru: {question}
        
        Kod:
        ```{self.language}
        {user_code}
        ```
        
        Kısaca:
        1. Doğru/yanlış (1 cümle)
        2. Ana sorun varsa (1 cümle)
        3. Kısa öneri (1 cümle)
        
        Uzun açıklama yapma.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Değerlendirme hatası: {str(e)}" 