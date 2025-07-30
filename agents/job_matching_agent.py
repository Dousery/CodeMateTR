import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class JobMatchingAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_cv(self, cv_text):
        """CV'yi analiz eder ve anahtar kelimeleri çıkarır"""
        try:
            prompt = f"""
            Aşağıdaki CV'yi çok dikkatli analiz et ve gerçek bilgileri çıkar:
            
            CV METNİ:
            {cv_text}
            
            ÖNEMLİ TALİMATLAR:
            1. Deneyim süresini çok dikkatli hesapla. İş başlangıç ve bitiş tarihlerini kontrol et.
            2. Eğer sadece birkaç aylık deneyim varsa (0.1-0.5 yıl), bunu doğru yansıt.
            3. Yeni mezun, stajyer veya öğrenci olabilir - bu durumu belirt.
            4. Gerçekte olmayan becerileri ekleme.
            5. Eğitim bilgilerini doğru analiz et (mezuniyet yılı, bölüm).
            6. Proje deneyimi ile iş deneyimini karıştırma.
            
            Aşağıdaki JSON formatında analiz et:
            {{
                "skills": ["sadece CV'de geçen gerçek beceriler"],
                "experience_years": 0.1,
                "experience_level": "Entry/Junior/Mid/Senior",
                "job_titles": ["sadece CV'de geçen gerçek pozisyonlar"],
                "education": ["gerçek eğitim bilgisi - üniversite, bölüm, yıl"],
                "technologies": ["sadece CV'de bahsedilen teknolojiler"],
                "industry_experience": ["gerçek sektör deneyimi"],
                "summary": "Gerçek durumu yansıtan kısa özet",
                "career_stage": "Yeni mezun/Öğrenci/Junior/Experienced"
            }}
            
            Sadece JSON formatında döndür, gerçek bilgileri yaz.
            """
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # JSON kısmını ayıkla
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group(0))
            else:
                return {
                    "skills": [],
                    "experience_years": 0,
                    "job_titles": [],
                    "education": [],
                    "technologies": [],
                    "industry_experience": [],
                    "summary": "CV analizi yapılamadı"
                }
        except Exception as e:
            print(f"CV analiz hatası: {e}")
            return {
                "skills": [],
                "experience_years": 0,
                "job_titles": [],
                "education": [],
                "technologies": [],
                "industry_experience": [],
                "summary": "CV analizi yapılamadı"
            }

    def match_jobs_with_cv(self, cv_analysis, job_listings):
        """CV analizi ile iş ilanlarını eşleştirir ve skorlar"""
        try:
            jobs_text = "\n".join([f"İlan {i+1}: {job['title']} - {job['company']} - {job['description'][:200]}..." 
                                 for i, job in enumerate(job_listings)])
            
            prompt = f"""
            Aşağıdaki CV analizi ile iş ilanlarını eşleştir ve her bir iş için uygunluk skoru (0-100) ver:
            
            CV ANALİZİ:
            Beceriler: {', '.join(cv_analysis.get('skills', []))}
            Deneyim: {cv_analysis.get('experience_years', 0)} yıl
            Teknolojiler: {', '.join(cv_analysis.get('technologies', []))}
            Pozisyonlar: {', '.join(cv_analysis.get('job_titles', []))}
            Eğitim: {', '.join(cv_analysis.get('education', []))}
            
            İŞ İLANLARI:
            {jobs_text}
            
            Her iş için uygunluk skorunu ve neden uygun olduğunu açıkla.
            Aşağıdaki JSON formatında döndür:
            {{
                "matches": [
                    {{
                        "job_index": 0,
                        "score": 85,
                        "match_reasons": ["Neden 1", "Neden 2"],
                        "missing_skills": ["Eksik beceri 1"]
                    }}
                ]
            }}
            
            Sadece JSON formatında döndür.
            """
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # JSON kısmını ayıkla
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group(0))
            else:
                return {"matches": []}
        except Exception as e:
            print(f"İş eşleştirme hatası: {e}")
            return {"matches": []}

    def generate_mock_job_listings(self, interest, count=10):
        """Gerçek iş ilanları olmadığı için kullanıcıyı direkt iş arama sitelerine yönlendirir"""
        try:
            # Gerçek iş arama siteleri
            search_sites = [
                {
                    "site_name": "LinkedIn",
                    "search_url": f"https://www.linkedin.com/jobs/search/?keywords={interest.replace(' ', '%20')}&location=Turkey",
                    "description": "Dünya çapında profesyonel iş ağı"
                },
                {
                    "site_name": "Kariyer.net",
                    "search_url": f"https://www.kariyer.net/is-ilanlari?q={interest.replace(' ', '+')}",
                    "description": "Türkiye'nin en büyük iş arama sitesi"
                },
                {
                    "site_name": "Yenibiris.com",
                    "search_url": f"https://www.yenibiris.com/is-ara?q={interest.replace(' ', '+')}",
                    "description": "Türkiye'de iş arama platformu"
                },
                {
                    "site_name": "Indeed Türkiye",
                    "search_url": f"https://tr.indeed.com/jobs?q={interest.replace(' ', '+')}&l=Turkey",
                    "description": "Uluslararası iş arama motoru"
                },
                {
                    "site_name": "SecretCV",
                    "search_url": f"https://www.secretcv.com/is-ilanlari?q={interest.replace(' ', '+')}",
                    "description": "Gizli profil ile iş arama"
                }
            ]
            
            # Kullanıcıya gerçek iş arama sitelerini öner
            return {
                "jobs": [],
                "search_recommendations": search_sites,
                "message": f"{interest} alanında güncel iş ilanları için aşağıdaki siteleri kontrol edin:"
            }
            
        except Exception as e:
            print(f"İş arama sitesi yönlendirme hatası: {e}")
            return {
                "jobs": [],
                "search_recommendations": [
                    {
                        "site_name": "LinkedIn",
                        "search_url": f"https://www.linkedin.com/jobs/search/?keywords={interest.replace(' ', '%20')}&location=Turkey",
                        "description": "Profesyonel iş ağı"
                    }
                ],
                "message": "İş arama sitelerine yönlendiriliyorsunuz..."
            }
