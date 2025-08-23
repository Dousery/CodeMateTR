import os
import json

import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class CodeAIAgent:
    def __init__(self, interest, language='python', api_key=None):
        self.interest = interest
        self.language = language
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        # Configure Gemini API with new client
        if not self.api_key:
            raise ValueError("API key is required. Please provide your Gemini API key.")
        
        # Initialize the new client
        self.client = genai.Client(api_key=self.api_key)
        
        # Create chat session with code execution capabilities
        self.chat = self.client.chats.create(
            model="gemini-2.0-flash-exp",
            config=types.GenerateContentConfig(
                tools=[types.Tool(code_execution=types.ToolCodeExecution)]
            ),
        )
        
        # Fallback model for non-code execution tasks (using old API for compatibility)
        import google.generativeai as old_genai
        old_genai.configure(api_key=self.api_key)
        self.fallback_model = old_genai.GenerativeModel('gemini-2.0-flash-lite')
        
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
        if not self.fallback_model:
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
            response = self.fallback_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Kodlama sorusu üretilemedi: {str(e)}"

    def run_code(self, user_code):
        """
        Kullanıcının kodunu gerçek zamanlı olarak çalıştırır ve sonuçları döndürür
        """
        if not self.chat:
            return {
                "execution_output": "API bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin.",
                "has_errors": True,
                "execution_time": 0,
                "memory_usage": "N/A"
            }
        
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        # Kod çalıştırma için özel prompt
        execution_prompt = f"""
        Bu {config['name']} kodunu çalıştır ve sonuçları göster:
        
        ```{self.language}
        {user_code}
        ```
        
        Kodu çalıştır ve sadece çıktıyı ver. Hata varsa hata mesajını da göster.
        """
        
        try:
            # Yeni chat session oluştur (her kod çalıştırma için temiz başlangıç)
            execution_chat = self.client.chats.create(
                model="gemini-2.0-flash-exp",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)]
                ),
            )
            
            # Kodu çalıştır
            response = execution_chat.send_message(execution_prompt)
            
            execution_output = ""
            has_errors = False
            code_output = ""
            error_output = ""
            
            # Response'u parse et
            for part in response.candidates[0].content.parts:
                if part.executable_code is not None:
                    code_output += f"Çalıştırılan Kod:\n{part.executable_code.code}\n\n"
                
                if part.code_execution_result is not None:
                    if hasattr(part.code_execution_result, 'output') and part.code_execution_result.output:
                        execution_output += f"Çıktı:\n{part.code_execution_result.output}\n"
                    if hasattr(part.code_execution_result, 'error') and part.code_execution_result.error:
                        error_output += f"Hata:\n{part.code_execution_result.error}\n"
                        has_errors = True
                    # Check for other possible error attributes
                    elif hasattr(part.code_execution_result, 'stderr') and part.code_execution_result.stderr:
                        error_output += f"Hata:\n{part.code_execution_result.stderr}\n"
                        has_errors = True
            
            # Eğer code execution sonucu yoksa, text response'u kullan
            if not execution_output and not error_output:
                execution_output = response.text.strip()
                has_errors = any(keyword in execution_output.lower() for keyword in 
                               ['error', 'hata', 'exception', 'traceback', 'failed', 'başarısız'])
            
            # Final output'u birleştir
            final_output = code_output + execution_output + error_output
            
            result = {
                "execution_output": final_output.strip(),
                "has_errors": has_errors,
                "execution_time": "N/A",  # Gerçek execution time için ayrı implementation gerek
                "memory_usage": "N/A"
            }
            
            return result
            
        except Exception as e:
            return {
                "execution_output": f"Çalıştırma hatası: {str(e)}",
                "has_errors": True,
                "execution_time": 0,
                "memory_usage": "N/A"
            }

    def evaluate_code_with_execution(self, user_code, question):
        """
        Kullanıcının kodunu çalıştırarak değerlendirir - PUANLAMA İÇİN
        """
        if not self.chat:
            return {
                "evaluation": "API bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin.",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": True,
                "corrected_code": "",
                "score": 0,
                "feedback": ""
            }
        
        config = self.language_configs.get(self.language, self.language_configs['python'])
            
        evaluation_prompt = f"""
        {config['name']} kodunu çalıştır, değerlendir ve puan ver:
        
        Soru: {question}
        
        Kod:
        ```{self.language}
        {user_code}
        ```
        
        Önce kodu çalıştır, sonra aşağıdaki formatı kullanarak değerlendirme yap:
        
        Çıktı/Sonuç: [Kod çıktısı]
        
        Doğruluk: [Doğru mu yanlış mı - 1 cümle]
        
        Puan: [0-100 arası]
        
        Ana Sorun: [Varsa - 1 cümle]
        
        Öneri: [Kısa iyileştirme önerisi - 1 cümle]
        
        NOT: Markdown formatı (#, ##, **) kullanma. Sadece düz metin olarak yaz.
        """
        
        try:
            # Yeni chat session oluştur (her değerlendirme için temiz başlangıç)
            evaluation_chat = self.client.chats.create(
                model="gemini-2.0-flash-exp",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)]
                ),
            )
            
            # Kodu çalıştır ve değerlendir
            response = evaluation_chat.send_message(evaluation_prompt)
            
            execution_output = ""
            evaluation_text = ""
            has_errors = False
            
            # Response'u parse et
            for part in response.candidates[0].content.parts:
                if part.executable_code is not None:
                    execution_output += f"Çalıştırılan Kod:\n{part.executable_code.code}\n\n"
                
                if part.code_execution_result is not None:
                    if hasattr(part.code_execution_result, 'output') and part.code_execution_result.output:
                        execution_output += f"Çıktı:\n{part.code_execution_result.output}\n"
                    if hasattr(part.code_execution_result, 'error') and part.code_execution_result.error:
                        execution_output += f"Hata:\n{part.code_execution_result.error}\n"
                        has_errors = True
                    # Check for other possible error attributes
                    elif hasattr(part.code_execution_result, 'stderr') and part.code_execution_result.stderr:
                        execution_output += f"Hata:\n{part.code_execution_result.stderr}\n"
                        has_errors = True
            
            # Text response'u al
            evaluation_text = response.text.strip()
            
            # Eğer code execution sonucu yoksa, sadece text response'u kullan
            if not execution_output:
                evaluation_text = response.text.strip()
                has_errors = any(keyword in evaluation_text.lower() for keyword in 
                               ['error', 'hata', 'exception', 'traceback', 'failed', 'başarısız'])
            
            # Markdown formatını temizle
            import re
            # # ve ## işaretlerini kaldır
            evaluation_text = re.sub(r'^#+\s*', '', evaluation_text, flags=re.MULTILINE)
            # ** işaretlerini kaldır
            evaluation_text = re.sub(r'\*\*(.*?)\*\*', r'\1', evaluation_text)
            # Fazla boşlukları temizle
            evaluation_text = re.sub(r'\n\s*\n\s*\n', '\n\n', evaluation_text)
            
            result = {
                "evaluation": evaluation_text,
                "execution_output": execution_output,
                "code_suggestions": "",
                "has_errors": has_errors,
                "corrected_code": "",
                "score": 0,
                "feedback": evaluation_text
            }
            
            # Puan çıkarmaya çalış
            score_match = re.search(r'puan[:\s]*(\d+)', evaluation_text.lower())
            if score_match:
                result["score"] = int(score_match.group(1))
            else:
                # Puan bulunamazsa, doğruluk durumuna göre tahmin et
                if any(word in evaluation_text.lower() for word in ['doğru', 'correct', 'başarılı', 'successful']):
                    result["score"] = 85
                elif any(word in evaluation_text.lower() for word in ['kısmen', 'partial', 'yarım']):
                    result["score"] = 60
                else:
                    result["score"] = 30
            
            return result
            
        except Exception as e:
            return {
                "evaluation": f"Değerlendirme hatası: {str(e)}",
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": True,
                "corrected_code": "",
                "score": 0,
                "feedback": f"Değerlendirme hatası: {str(e)}"
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
        
        Açıklama:
        Sorunun nasıl çözüleceğini kısaca açıkla (2-3 cümle)
        
        Kod:
        ```{self.language}
        # Çözüm kodunu buraya yaz
        ```
        
        Test:
        Kodun nasıl çalıştığını göster ve test sonuçlarını açıkla.
        
        NOT: Markdown formatı (**) kullanma. Sadece düz metin olarak yaz.
        """
        
        try:
            # Fallback model kullan (code execution gerekmiyor)
            response = self.fallback_model.generate_content(prompt)
            
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
                if "Açıklama:" in line:
                    current_section = "explanation"
                    continue
                elif "Kod:" in line:
                    current_section = "code"
                    continue
                elif "Test:" in line:
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
        
        Aşağıdaki formatı kullan:
        
        Ana Hata: [Ana hata nedir? - 1 cümle]
        
        Düzeltilmiş Kod:
        [Düzeltilmiş kodu buraya yaz]
        
        Hata Nedeni: [Neden hata oldu? - 1 cümle]
        
        NOT: Markdown formatı (#, ##, **) kullanma. Sadece düz metin olarak yaz.
        """
        
        try:
            response = self.fallback_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Markdown formatını temizle
            import re
            # # ve ## işaretlerini kaldır
            response_text = re.sub(r'^#+\s*', '', response_text, flags=re.MULTILINE)
            # ** işaretlerini kaldır
            response_text = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)
            # Fazla boşlukları temizle
            response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', response_text)
            
            debug_result = {
                "error_explanation": response_text,
                "corrected_code": "",
                "execution_result": "",
                "prevention_tips": ""
            }
            
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
        Belirtilen konu için öğrenme kaynakları önerir - Gerçek URL'ler ile
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        # Öncelikle gerçek URL'leri al
        real_resources = self._get_topic_specific_urls(topic, config['name'])
        
        if real_resources:
            # Gerçek kaynakları formatla
            formatted_resources = self._format_resources_with_urls(real_resources, topic)
            return formatted_resources
        
        # Gerçek kaynaklar bulunamazsa AI ile oluştur
        try:
            prompt = f"""
            {config['name']} dili için {topic} konusunda öğrenmek için en iyi {num_resources} kaynak öner.
            
            Her kaynak için şu formatı kullan:
            Kaynak Adı: [Kaynak başlığı]
            - URL: [Gerçek erişilebilir URL]
            - Açıklama: [Kısa açıklama - 1 cümle]
            - Neden Faydalı: [Faydası - 1 cümle]
            - Zorluk Seviyesi: [Başlangıç/Orta/İleri]
            
            Gerçek, erişilebilir URL'ler ver. Güncel ve kaliteli kaynakları öner.
            NOT: Markdown formatı (**) kullanma. Sadece düz metin olarak yaz.
            """
            
            response = self.chat.generate_content(prompt)
            response_text = response.text.strip()
            
            # Markdown formatını temizle
            import re
            # # ve ## işaretlerini kaldır
            response_text = re.sub(r'^#+\s*', '', response_text, flags=re.MULTILINE)
            # ** işaretlerini kaldır
            response_text = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)
            # Fazla boşlukları temizle
            response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', response_text)
            
            return response_text
            
        except Exception as e:
            # Fallback: Önceden tanımlanmış kaynaklar
            return self._get_fallback_resources_with_urls(topic, config['name'], num_resources)
    
    def _get_topic_specific_urls(self, topic, language):
        """Konuya özel gerçek URL'leri döndürür"""
        topic_lower = topic.lower()
        
        # Python için URL mapping
        python_resources = {
            'list': [
                {
                    'title': 'Python Lists - Official Documentation',
                    'url': 'https://docs.python.org/3/tutorial/introduction.html#lists',
                    'description': 'Python resmi dokümantasyonu - listeler bölümü',
                    'benefit': 'En güvenilir ve güncel Python liste bilgileri',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'Python Lists - W3Schools',
                    'url': 'https://www.w3schools.com/python/python_lists.asp',
                    'description': 'Adım adım Python liste öğretimi',
                    'benefit': 'İnteraktif örnekler ve tryit editörü ile pratik',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'Real Python - Python Lists and Tuples',
                    'url': 'https://realpython.com/python-lists-tuples/',
                    'description': 'Detaylı liste ve tuple açıklaması',
                    'benefit': 'Derinlemesine analiz ve gelişmiş örnekler',
                    'level': 'Orta'
                }
            ],
            'loop': [
                {
                    'title': 'Python For Loops - Official Tutorial',
                    'url': 'https://docs.python.org/3/tutorial/controlflow.html#for-statements',
                    'description': 'Python resmi for döngüsü öğreticisi',
                    'benefit': 'Resmi dokümantasyondan güvenilir bilgi',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'Python Loops - W3Schools',
                    'url': 'https://www.w3schools.com/python/python_for_loops.asp',
                    'description': 'Python döngüleri kapsamlı rehberi',
                    'benefit': 'Uygulamalı örnekler ve çevrimiçi editör',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'Real Python - Python for Loops',
                    'url': 'https://realpython.com/python-for-loop/',
                    'description': 'For döngülerinin derinlemesine incelenmesi',
                    'benefit': 'İleri seviye teknikler ve best practices',
                    'level': 'Orta'
                }
            ],
            'function': [
                {
                    'title': 'Python Functions - Official Documentation',
                    'url': 'https://docs.python.org/3/tutorial/controlflow.html#defining-functions',
                    'description': 'Python fonksiyon tanımlama resmi rehberi',
                    'benefit': 'En güncel ve doğru fonksiyon bilgileri',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'Python Functions - Real Python',
                    'url': 'https://realpython.com/defining-your-own-python-function/',
                    'description': 'Fonksiyon tanımlama ve kullanımı detaylı rehberi',
                    'benefit': 'Pratik örnekler ve gerçek dünya uygulamaları',
                    'level': 'Orta'
                },
                {
                    'title': 'Python Functions - Programiz',
                    'url': 'https://www.programiz.com/python-programming/function',
                    'description': 'Python fonksiyonları adım adım öğretimi',
                    'benefit': 'Görsel örnekler ve kolay anlaşılır açıklamalar',
                    'level': 'Başlangıç'
                }
            ],
            'data structure': [
                {
                    'title': 'Python Data Structures - Official Documentation',
                    'url': 'https://docs.python.org/3/tutorial/datastructures.html',
                    'description': 'Python veri yapıları resmi dokümantasyonu',
                    'benefit': 'Tüm veri yapıları için tek kaynak',
                    'level': 'Orta'
                },
                {
                    'title': 'Python Data Structures - GeeksforGeeks',
                    'url': 'https://www.geeksforgeeks.org/python-data-structures/',
                    'description': 'Python veri yapıları kapsamlı rehberi',
                    'benefit': 'Algoritmalar ve komplekslik analizleri',
                    'level': 'Orta'
                },
                {
                    'title': 'Data Structures and Algorithms in Python',
                    'url': 'https://realpython.com/python-data-structures/',
                    'description': 'Veri yapıları ve algoritmaları Python\'da',
                    'benefit': 'Performans odaklı yaklaşım ve optimizasyonlar',
                    'level': 'İleri'
                }
            ],
            'algorithm': [
                {
                    'title': 'Python Algorithms - GeeksforGeeks',
                    'url': 'https://www.geeksforgeeks.org/python-programming-language/',
                    'description': 'Python algoritmaları ve veri yapıları',
                    'benefit': 'Geniş algoritma koleksiyonu ve açıklamaları',
                    'level': 'Orta'
                },
                {
                    'title': 'Algorithms in Python - Real Python',
                    'url': 'https://realpython.com/python-thinking-recursively/',
                    'description': 'Python\'da algoritma düşüncesi geliştirme',
                    'benefit': 'Problem çözme yaklaşımları ve recursive thinking',
                    'level': 'İleri'
                },
                {
                    'title': 'LeetCode Python Solutions',
                    'url': 'https://leetcode.com/problemset/all/',
                    'description': 'Python ile algoritma problemleri çözme platformu',
                    'benefit': 'Uygulamalı algoritma pratiği ve interview hazırlığı',
                    'level': 'İleri'
                }
            ]
        }
        
        # JavaScript için URL mapping
        javascript_resources = {
            'array': [
                {
                    'title': 'JavaScript Arrays - MDN Web Docs',
                    'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array',
                    'description': 'JavaScript dizileri resmi dokümantasyonu',
                    'benefit': 'En güncel ve kapsamlı array metodları',
                    'level': 'Tüm Seviyeler'
                },
                {
                    'title': 'JavaScript Arrays - W3Schools',
                    'url': 'https://www.w3schools.com/js/js_arrays.asp',
                    'description': 'JavaScript array öğretimi',
                    'benefit': 'İnteraktif örnekler ve tryit editörü',
                    'level': 'Başlangıç'
                },
                {
                    'title': 'JavaScript Array Methods - JavaScript.info',
                    'url': 'https://javascript.info/array-methods',
                    'description': 'Array metodları detaylı açıklaması',
                    'benefit': 'Modern JavaScript yaklaşımları',
                    'level': 'Orta'
                }
            ],
            'function': [
                {
                    'title': 'JavaScript Functions - MDN',
                    'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions',
                    'description': 'JavaScript fonksiyonları resmi rehberi',
                    'benefit': 'Kapsamlı fonksiyon kavramları ve ES6+ özellikleri',
                    'level': 'Tüm Seviyeler'
                },
                {
                    'title': 'JavaScript Functions - JavaScript.info',
                    'url': 'https://javascript.info/function-basics',
                    'description': 'Fonksiyon temelleri modern yaklaşım',
                    'benefit': 'Modern JavaScript standartları',
                    'level': 'Başlangıç'
                }
            ]
        }
        
        # Dile göre kaynak seçimi
        if language.lower() == 'python':
            resources_map = python_resources
        elif language.lower() == 'javascript':
            resources_map = javascript_resources
        else:
            return None
        
        # Topic'e uygun kaynakları bul
        for key, resources in resources_map.items():
            if key in topic_lower or any(word in key for word in topic_lower.split()):
                return resources[:3]  # İlk 3 kaynağı döndür
        
        # Genel kaynakları döndür
        if language.lower() == 'python':
            return python_resources.get('list', [])[:3]
        elif language.lower() == 'javascript':
            return javascript_resources.get('array', [])[:3]
        
        return None
    
    def _format_resources_with_urls(self, resources, topic):
        """Kaynakları URL'li format ile döndürür"""
        formatted = f"📚 **{topic.title()} Öğrenme Kaynakları** 📚\n\n"
        formatted += "Gerçek URL'lerle erişilebilir kaynak önerileri:\n\n"
        
        for i, resource in enumerate(resources, 1):
            formatted += f"**{i}. {resource['title']}**\n"
            formatted += f"🔗 **URL:** {resource['url']}\n"
            formatted += f"📝 **Açıklama:** {resource['description']}\n"
            formatted += f"✅ **Neden Faydalı:** {resource['benefit']}\n"
            formatted += f"📊 **Zorluk Seviyesi:** {resource['level']}\n\n"
        
        formatted += "💡 **İpucu:** Bu kaynakları sırayla takip ederek konuyu derinlemesine öğrenebilirsiniz!\n"
        return formatted
    
    def _get_fallback_resources_with_urls(self, topic, language, num_resources):
        """Fallback kaynakları gerçek URL'ler ile"""
        if language.lower() == 'python':
            fallback = f"""📚 **{topic.title()} Python Öğrenme Kaynakları** 📚

**1. Python Resmi Dokümantasyonu**
🔗 **URL:** https://docs.python.org/3/
📝 **Açıklama:** Python'ın resmi dokümantasyonu ve öğreticileri
✅ **Neden Faydalı:** En güncel ve doğru bilgi kaynağı
📊 **Zorluk Seviyesi:** Tüm Seviyeler

**2. Real Python**
🔗 **URL:** https://realpython.com/
📝 **Açıklama:** Python için kapsamlı makaleler ve öğreticiler
✅ **Neden Faydalı:** Pratik örnekler ve gerçek dünya uygulamaları
📊 **Zorluk Seviyesi:** Orta-İleri

**3. W3Schools Python Tutorial**
🔗 **URL:** https://www.w3schools.com/python/
📝 **Açıklama:** Adım adım Python öğretimi
✅ **Neden Faydalı:** İnteraktif örnekler ve kolay takip
📊 **Zorluk Seviyesi:** Başlangıç

💡 **Bonus:** Python Practice - https://www.hackerrank.com/domains/python"""
        
        elif language.lower() == 'javascript':
            fallback = f"""📚 **{topic.title()} JavaScript Öğrenme Kaynakları** 📚

**1. MDN Web Docs**
🔗 **URL:** https://developer.mozilla.org/en-US/docs/Web/JavaScript
📝 **Açıklama:** JavaScript resmi dokümantasyonu
✅ **Neden Faydalı:** En kapsamlı ve güncel JavaScript kaynağı
📊 **Zorluk Seviyesi:** Tüm Seviyeler

**2. JavaScript.info**
🔗 **URL:** https://javascript.info/
📝 **Açıklama:** Modern JavaScript öğretimi
✅ **Neden Faydalı:** ES6+ özellikleri ve best practices
📊 **Zorluk Seviyesi:** Başlangıç-Orta

**3. W3Schools JavaScript**
🔗 **URL:** https://www.w3schools.com/js/
📝 **Açıklama:** JavaScript temel öğretimi
✅ **Neden Faydalı:** Uygulamalı örnekler ve tryit editörü
📊 **Zorluk Seviyesi:** Başlangıç"""
        
        else:
            fallback = f"""📚 **{topic.title()} Öğrenme Kaynakları** 📚

**1. Stack Overflow**
🔗 **URL:** https://stackoverflow.com/questions/tagged/{language.lower()}
📝 **Açıklama:** {language} ile ilgili soru-cevap platformu
✅ **Neden Faydalı:** Gerçek problemler ve çözümleri
📊 **Zorluk Seviyesi:** Tüm Seviyeler

**2. GitHub**
🔗 **URL:** https://github.com/search?q={topic}+{language}
📝 **Açıklama:** {topic} konusunda açık kaynak projeler
✅ **Neden Faydalı:** Gerçek kod örnekleri ve best practices
📊 **Zorluk Seviyesi:** Orta-İleri"""
        
        return fallback

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
            response = self.fallback_model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            return f"Analiz hatası: {str(e)}"

    def evaluate_code(self, user_code, question):
        """
        Kullanıcının kodunu geleneksel yöntemle değerlendirir (eski uyumlulık için)
        """
        config = self.language_configs.get(self.language, self.language_configs['python'])
        
        prompt = f"""
        {config['name']} kodunu detaylı değerlendir ve puan ver:
        
        Soru: {question}
        
        Kod:
        ```{self.language}
        {user_code}
        ```
        
        Aşağıdaki formatı kullanarak değerlendirme yap:
        
        Doğruluk: [Çözüm doğru mu? - 2 cümle]
        
        Kod Kalitesi: [Temizlik, okunabilirlik - 2 cümle]
        
        Verimlilik: [Algoritma verimi - 1 cümle]
        
        Puan: [0-100 arası]
        
        İyileştirme Önerileri:
        [3-4 madde halinde öneriler]
        
        NOT: Markdown formatı (#, ##, **) kullanma. Sadece düz metin olarak yaz.
        """
        
        try:
            response = self.fallback_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Markdown formatını temizle
            import re
            # # ve ## işaretlerini kaldır
            response_text = re.sub(r'^#+\s*', '', response_text, flags=re.MULTILINE)
            # ** işaretlerini kaldır
            response_text = re.sub(r'\*\*(.*?)\*\*', r'\1', response_text)
            # Fazla boşlukları temizle
            response_text = re.sub(r'\n\s*\n\s*\n', '\n\n', response_text)
            
            return response_text
            
        except Exception as e:
            return f"Detaylı değerlendirme hatası: {str(e)}" 

    def execute_complex_code(self, prompt, language='python'):
        """
        Karmaşık kod çalıştırma örneği - yeni API'nin tüm özelliklerini kullanır
        """
        if not self.chat:
            return {
                "success": False,
                "output": "API bağlantısı kurulamadı. Lütfen API anahtarınızı kontrol edin.",
                "code": "",
                "error": "API bağlantısı hatası"
            }
        
        try:
            # Yeni chat session oluştur
            execution_chat = self.client.chats.create(
                model="gemini-2.0-flash-exp",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(code_execution=types.ToolCodeExecution)]
                ),
            )
            
            # Kodu çalıştır
            response = execution_chat.send_message(prompt)
            
            result = {
                "success": True,
                "output": "",
                "code": "",
                "error": ""
            }
            
            # Response'u parse et
            for part in response.candidates[0].content.parts:
                if part.executable_code is not None:
                    result["code"] = part.executable_code.code
                
                if part.code_execution_result is not None:
                    if hasattr(part.code_execution_result, 'output') and part.code_execution_result.output:
                        result["output"] = part.code_execution_result.output
                    if hasattr(part.code_execution_result, 'error') and part.code_execution_result.error:
                        result["error"] = part.code_execution_result.error
                        result["success"] = False
                    # Check for other possible error attributes
                    elif hasattr(part.code_execution_result, 'stderr') and part.code_execution_result.stderr:
                        result["error"] = part.code_execution_result.stderr
                        result["success"] = False
            
            # Eğer code execution sonucu yoksa, text response'u kullan
            if not result["output"] and not result["error"]:
                result["output"] = response.text.strip()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "code": "",
                "error": f"Çalıştırma hatası: {str(e)}"
            }

    def solve_math_problem(self, problem_description):
        """
        Matematik problemlerini çözmek için kod çalıştırma örneği
        """
        prompt = f"""
        Bu matematik problemini çöz:
        
        {problem_description}
        
        Kodu çalıştır ve sonucu göster. Eğer hesaplama gerekiyorsa, 
        uygun bir programlama dili kullanarak hesapla.
        """
        
        return self.execute_complex_code(prompt)

    def analyze_data(self, data_description, analysis_type="basic"):
        """
        Veri analizi için kod çalıştırma örneği
        """
        prompt = f"""
        Bu veri analizi görevini gerçekleştir:
        
        Veri: {data_description}
        Analiz Türü: {analysis_type}
        
        Uygun bir programlama dili kullanarak veriyi analiz et ve sonuçları göster.
        """
        
        return self.execute_complex_code(prompt)