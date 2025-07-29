from google import genai
from google.genai import types
import os
import json
import traceback
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class CodeAIAgent:
    def __init__(self, interest, language='python'):
        self.interest = interest
        self.language = language
        # Configure the client with API key
        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Google GenAI client initialization error: {e}")
            # Fallback: Set environment variable
            os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
            try:
                self.client = genai.Client()
            except Exception as e2:
                print(f"Fallback client initialization error: {e2}")
                self.client = None
        
        # Dil bazlı model seçimi
        self.model = "gemini-2.0-flash-exp"
        
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
        if not self.client:
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            return f"Kodlama sorusu üretilemedi: {str(e)}"

    def evaluate_code_with_execution(self, user_code, question):
        """
        Kullanıcının kodunu çalıştırarak değerlendirir
        """
        if not self.client:
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                ),
            )
            
            result = {
                "evaluation": "",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": False,
                "corrected_code": ""
            }
            
            # Tüm parçaları birleştir
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    result["evaluation"] += part.text + "\n"
                elif part.executable_code is not None:
                    result["code_suggestions"] += f"Kod:\n{part.executable_code.code}\n"
                elif part.code_execution_result is not None:
                    result["execution_output"] += f"Çıktı:\n{part.code_execution_result.output}\n"
            
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
        Verilen soru için örnek çözüm üretir ve test eder
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        Bu {config['name']} sorusu için çalışan kod yaz ve test et:
        
        Soru: {question}
        
        Sadece:
        1. Kısa açıklama (2 cümle)
        2. {config['name']} kodu yaz ve çalıştır
        3. Test sonucu göster
        
        Uzun açıklama yapma, direkt kod ver.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                ),
            )
            
            result = {
                "explanation": "",
                "code": "",
                "test_results": "",
                "complexity_analysis": ""
            }
            
            # Yanıtı parçalara ayır
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    result["explanation"] += part.text + "\n"
                elif part.executable_code is not None:
                    result["code"] += part.executable_code.code + "\n"
                elif part.code_execution_result is not None:
                    result["test_results"] += part.code_execution_result.output + "\n"
            
            return result
            
        except Exception as e:
            return {
                "explanation": f"Çözüm hatası: {str(e)}",
                "code": "",
                "test_results": "",
                "complexity_analysis": ""
            }

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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution())]
                ),
            )
            
            debug_result = {
                "error_explanation": "",
                "corrected_code": "",
                "execution_result": "",
                "prevention_tips": ""
            }
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    debug_result["error_explanation"] += part.text + "\n"
                elif part.executable_code is not None:
                    debug_result["corrected_code"] += part.executable_code.code + "\n"
                elif part.code_execution_result is not None:
                    debug_result["execution_result"] += part.code_execution_result.output + "\n"
            
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
            # Google Search tool ile gerçek kaynakları ara
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                ),
            )
            
            return response.text.strip()
            
        except Exception as e:
            # Fallback: Google Search başarısız olursa basit öneri
            fallback_prompt = f"""
            {config['name']} dili için {topic} konusunda {num_resources} kaynak öner.
            
            Format:
            1. Kaynak adı - açıklama (1 cümle)
            2. Kaynak adı - açıklama (1 cümle)
            3. Kaynak adı - açıklama (1 cümle)
            
            Kısa ve net ol.
            """
            
            try:
                fallback_response = self.client.models.generate_content(
                    model=self.model,
                    contents=fallback_prompt
                )
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            return f"Değerlendirme hatası: {str(e)}" 