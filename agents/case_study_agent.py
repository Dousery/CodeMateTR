import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class CaseStudyAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_case(self):
        # Gemini API hatası durumunda basit case study döndür
        try:
            print("Gemini API çağrılıyor...")
            prompt = f"""
                {self.interest} alanında, iki geliştiricinin birlikte çalışacağı teorik bir problem senaryosu oluştur.

                Senaryo:
                - Gerçek dünyadan esinlenmiş, açık uçlu bir durumu açıklasın.
                - Net bir çözümü olmayan, farklı yaklaşımlara açık bir problem olsun.
                - Geliştiriciler bu durumu yorumlayacak, tartışacak ve yaklaşım geliştirecek konumda olsun.
                - Sadece durum ve problemi anlat.
                - Son bölümde geliştiricilere 1–2 düşünsel soru sorarak senaryoyu sonlandır.

                Aşağıdaki JSON formatında çıktı ver:

                {{
                    "title": "Case Study Başlığı",
                    "description": "Senaryo açıklaması",
                    "interest": "{self.interest}"
                }}
                
                Sadece JSON formatında döndür, başka açıklama ekleme.
            """
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            print("Gemini API yanıtı:", text)
            # Sadece JSON kısmını ayıkla
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group(0))
            else:
                # JSON parse edilemezse basit format döndür
                return {
                    "title": f"{self.interest} Case Study",
                    "description": text,
                    "requirements": ["Çözümü tamamlayın"],
                    "constraints": ["30 dakika süre"],
                    "evaluation_criteria": ["Çözüm kalitesi", "Analiz derinliği"],
                    "interest": self.interest
                }
        except Exception as e:
            print(f"Gemini API hatası: {e}")
            # API hatası durumunda sabit case study döndür
            return {
                "title": f"{self.interest} Test Case Study",
                "description": f"Bu bir {self.interest} alanında test case study'sidir. Lütfen bu senaryoyu analiz edin ve çözüm önerin.",
                "requirements": ["Senaryoyu analiz edin", "Çözüm önerin", "Uygulama planı yapın"],
                "constraints": ["30 dakika süre", "Pratik çözümler önerin"],
                "evaluation_criteria": ["Analiz kalitesi", "Çözüm uygulanabilirliği", "Yaratıcılık"],
                "interest": self.interest
            }

    def evaluate_case_solution(self, case, solution):
        """Çözümü değerlendir"""
        try:
            print(f"Gemini API çağrılıyor - evaluate_case_solution...")
            print(f"Solution length: {len(solution)}")
            prompt = f"""
            Aşağıdaki case study çözümünü değerlendir:
            
            CASE STUDY:
            Başlık: {case.get('title', 'Case Study')}
            Açıklama: {case.get('description', '')}
            Problem: {case.get('problem', '')}
            Hedefler: {', '.join(case.get('objectives', []))}
            Kısıtlamalar: {', '.join(case.get('constraints', []))}
            Değerlendirme Kriterleri: {', '.join(case.get('evaluation_criteria', []))}
            
            ÇÖZÜM:
            {solution}
            
            Bu çözümü 0-100 arası puanla ve detaylı geri bildirim ver. 
            Aşağıdaki JSON formatında döndür:
            {{
                "score": 85,
                "feedback": "Detaylı geri bildirim metni...",
                "strengths": ["Güçlü yan 1", "Güçlü yan 2"],
                "improvements": ["İyileştirme önerisi 1", "İyileştirme önerisi 2"]
            }}
            
            Sadece JSON formatında döndür.
            """
            print(f"Prompt gönderiliyor...")
            response = self.model.generate_content(prompt)
            print(f"Gemini yanıtı: {response.text}")
            
            # Markdown kod bloğunu temizle
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]  # ```json kısmını kaldır
            if text.startswith('```'):
                text = text[3:]  # ``` kısmını kaldır
            if text.endswith('```'):
                text = text[:-3]  # Sondaki ``` kısmını kaldır
            
            text = text.strip()
            print(f"Temizlenmiş JSON: {text}")
            
            try:
                result = json.loads(text)
                print(f"JSON parse başarılı: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"JSON parse hatası: {e}")
                return {
                    "score": 70,
                    "feedback": "Çözüm değerlendirildi ancak detaylı analiz yapılamadı.",
                    "strengths": ["Çözüm sunuldu"],
                    "improvements": ["Daha detaylı analiz yapılabilir"]
                }
        except Exception as e:
            print(f"Gemini API hatası (evaluate): {e}")
            print(f"Hata türü: {type(e)}")
            # API hatası durumunda basit değerlendirme döndür
            return {
                "score": 75,
                "feedback": f"Çözümünüz değerlendirildi. {len(solution)} karakterlik bir çözüm sundunuz. Daha detaylı analiz için Gemini API'ye ihtiyaç var.",
                "strengths": ["Çözüm sunuldu", "Katılım gösterildi"],
                "improvements": ["Daha detaylı analiz yapılabilir", "Pratik örnekler eklenebilir"]
            }

    def evaluate_unified_performance(self, case, conversation_text, username):
        """Birleşik performans değerlendirmesi - hem çözüm hem mesajlaşma"""
        try:
            print(f"Gemini API çağrılıyor - evaluate_unified_performance...")
            print(f"Conversation length: {len(conversation_text)}")
            print(f"Evaluating user: {username}")
            prompt = f"""
            Aşağıdaki case study ve mesajlaşmayı analiz et ve {username} adlı kullanıcının genel performansını değerlendir:
            
            CASE STUDY:
            Başlık: {case.get('title', 'Case Study')}
            Açıklama: {case.get('description', '')}
            Problem: {case.get('problem', '')}
            Hedefler: {', '.join(case.get('objectives', []))}
            Kısıtlamalar: {', '.join(case.get('constraints', []))}
            Değerlendirme Kriterleri: {', '.join(case.get('evaluation_criteria', []))}
            
            MESAJLAŞMA:
            {conversation_text}
            
            {username} kullanıcısının genel performansını şu kriterlere göre değerlendir:
            1. Problem Analizi ve Anlama (0-25 puan)
            2. Çözüm Yaklaşımı ve Strateji (0-25 puan)
            3. İletişim ve İşbirliği (0-25 puan)
            4. Teknik Bilgi ve Uygulama (0-25 puan)
            
            Sadece {username} kullanıcısının mesajlarını ve katkılarını değerlendir. Diğer kullanıcıların mesajlarını sadece {username}'in yanıtlarını anlamak için kullan.
            
            Aşağıdaki JSON formatında döndür:
            {{
                "total_score": 85,
                "problem_analysis_score": 20,
                "solution_approach_score": 22,
                "communication_score": 23,
                "technical_score": 20,
                "feedback": "{username} kullanıcısının genel performans değerlendirmesi...",
                "strengths": ["{username} kullanıcısının güçlü yanı 1", "{username} kullanıcısının güçlü yanı 2"],
                "improvements": ["{username} kullanıcısı için iyileştirme 1", "{username} kullanıcısı için iyileştirme 2"],
                "detailed_analysis": "{username} kullanıcısının detaylı performans analizi..."
            }}
            
            Sadece JSON formatında döndür.
            """
            print(f"Prompt gönderiliyor...")
            response = self.model.generate_content(prompt)
            print(f"Gemini yanıtı: {response.text}")
            
            # Markdown kod bloğunu temizle
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]  # ```json kısmını kaldır
            if text.startswith('```'):
                text = text[3:]  # ``` kısmını kaldır
            if text.endswith('```'):
                text = text[:-3]  # Sondaki ``` kısmını kaldır
            
            text = text.strip()
            print(f"Temizlenmiş JSON: {text}")
            
            try:
                result = json.loads(text)
                print(f"JSON parse başarılı: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"JSON parse hatası: {e}")
                return self._default_unified_evaluation(username)
        except Exception as e:
            print(f"Gemini API hatası (evaluate_unified_performance): {e}")
            print(f"Hata türü: {type(e)}")
            return self._default_unified_evaluation(username)

    def evaluate_conversation(self, conversation_text, username):
        """Mesajlaşmayı değerlendir"""
        try:
            print(f"Gemini API çağrılıyor - evaluate_conversation...")
            print(f"Conversation length: {len(conversation_text)}")
            print(f"Evaluating user: {username}")
            prompt = f"""
            Aşağıdaki mesajlaşmayı analiz et ve {username} adlı kullanıcının performansını değerlendir:
            
            MESAJLAŞMA:
            {conversation_text}
            
            {username} kullanıcısının performansını şu kriterlere göre değerlendir:
            1. İletişim kalitesi (0-25 puan)
            2. İşbirliği ve takım çalışması (0-25 puan)
            3. Teknik bilgi ve açıklama (0-25 puan)
            4. Problem çözme yaklaşımı (0-25 puan)
            
            Sadece {username} kullanıcısının mesajlarını ve katkılarını değerlendir. Diğer kullanıcıların mesajlarını sadece {username}'in yanıtlarını anlamak için kullan.
            
            Aşağıdaki JSON formatında döndür:
            {{
                "total_score": 85,
                "communication_score": 20,
                "collaboration_score": 22,
                "technical_score": 23,
                "problem_solving_score": 20,
                "feedback": "{username} kullanıcısının detaylı geri bildirimi...",
                "strengths": ["{username} kullanıcısının güçlü yanı 1", "{username} kullanıcısının güçlü yanı 2"],
                "improvements": ["{username} kullanıcısı için iyileştirme 1", "{username} kullanıcısı için iyileştirme 2"],
                "conversation_analysis": "{username} kullanıcısının mesajlaşma analizi..."
            }}
            
            Sadece JSON formatında döndür.
            """
            print(f"Prompt gönderiliyor...")
            response = self.model.generate_content(prompt)
            print(f"Gemini yanıtı: {response.text}")
            
            # Markdown kod bloğunu temizle
            text = response.text.strip()
            if text.startswith('```json'):
                text = text[7:]  # ```json kısmını kaldır
            if text.startswith('```'):
                text = text[3:]  # ``` kısmını kaldır
            if text.endswith('```'):
                text = text[:-3]  # Sondaki ``` kısmını kaldır
            
            text = text.strip()
            print(f"Temizlenmiş JSON: {text}")
            
            try:
                result = json.loads(text)
                print(f"JSON parse başarılı: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"JSON parse hatası: {e}")
                return self._default_conversation_evaluation()
        except Exception as e:
            print(f"Gemini API hatası (evaluate_conversation): {e}")
            print(f"Hata türü: {type(e)}")
            return self._default_conversation_evaluation()

    def _default_unified_evaluation(self, username):
        """Varsayılan birleşik değerlendirme"""
        return {
            "total_score": 70,
            "problem_analysis_score": 18,
            "solution_approach_score": 17,
            "communication_score": 18,
            "technical_score": 17,
            "feedback": f"{username} kullanıcısının performansı değerlendirildi. Daha detaylı analiz için Gemini API'ye ihtiyaç var.",
            "strengths": ["Katılım gösterildi", "İletişim kuruldu"],
            "improvements": ["Daha detaylı analiz yapılabilir", "Teknik açıklamalar artırılabilir"],
            "detailed_analysis": f"{username} kullanıcısının detaylı performans analizi yapılamadı."
        }

    def _default_conversation_evaluation(self):
        """Varsayılan mesajlaşma değerlendirmesi"""
        return {
            "total_score": 70,
            "communication_score": 18,
            "collaboration_score": 17,
            "technical_score": 18,
            "problem_solving_score": 17,
            "feedback": "Mesajlaşma değerlendirildi. Daha detaylı analiz için Gemini API'ye ihtiyaç var.",
            "strengths": ["Mesajlaşma gerçekleşti", "İletişim kuruldu"],
            "improvements": ["Daha detaylı teknik tartışma yapılabilir", "İşbirliği artırılabilir"],
            "conversation_analysis": "Mesajlaşma analizi yapılamadı."
        } 