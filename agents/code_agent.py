from google import genai
from google.genai import types
import os
import json
import traceback


class CodeAIAgent:
    def __init__(self, interest):
        self.interest = interest
        # Gemini 2.5 Flash modelini code execution ile yapılandır
        self.client = genai.Client()
        self.model = "gemini-2.0-flash-exp"
        
    def generate_coding_question(self, difficulty="orta"):
        """
        Belirtilen zorluk seviyesinde Python kodlama sorusu üretir
        """
        difficulty_levels = {
            "kolay": "başlangıç seviyesi, temel Python syntax",
            "orta": "orta seviye, fonksiyonlar, listeler, döngüler",
            "zor": "ileri seviye, algoritmalar, veri yapıları, optimizasyon"
        }
        
        level_desc = difficulty_levels.get(difficulty, "orta seviye")
        
        prompt = f"""
        {self.interest} alanında {level_desc} bir kısa Python kodlama sorusu üret.
        
        Format:
        - Problem (2-3 cümle)
        - Örnek: input -> output
        
        Sadece soruyu ver, çözüm yok.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            return f"Hata oluştu: {str(e)}"

    def evaluate_code_with_execution(self, user_code, question):
        """
        Kullanıcının kodunu çalıştırarak değerlendirir
        """
        prompt = f"""
        Python kodunu çalıştır ve kısa değerlendir:
        
        Soru: {question}
        
        Kod:
        ```python
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
        prompt = f"""
        Bu Python sorusu için çalışan kod yaz ve test et:
        
        Soru: {question}
        
        Sadece:
        1. Kısa açıklama (2 cümle)
        2. Python kodu yaz ve çalıştır
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
        prompt = f"""
        Bu Python kodundaki hatayı bul ve düzelt:
        
        ```python
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
        Belirtilen konu için Python öğrenme kaynakları önerir - Google Search ile gerçek linkler
        """
        prompt = f"""
        {topic} konusunda Python öğrenmek için en iyi {num_resources} kaynak ara ve öner.
        
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
            {topic} için {num_resources} Python kaynağı öner.
            
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
        prompt = f"""
        Bu Python kodunun karmaşıklığını kısaca analiz et:
        
        ```python
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
        prompt = f"""
        Python kodunu kısaca değerlendir:
        
        Soru: {question}
        
        Kod:
        ```python
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