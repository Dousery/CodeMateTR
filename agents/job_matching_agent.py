from google import genai
from google.genai import types
import httpx
import json
import os
import re
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Yeni Google Gemini API yapısı
client = genai.Client(api_key=GEMINI_API_KEY)

class JobMatchingAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.client = client

    def analyze_cv_from_pdf_bytes(self, pdf_data):
        """PDF bytes'ından doğrudan CV analizi yapar - Yeni Google Gemini API"""
        try:
            prompt = f"""
            Aşağıdaki PDF CV'yi çok dikkatli analiz et ve gerçek bilgileri çıkar:
            
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
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_data,
                        mime_type='application/pdf',
                    ),
                    prompt
                ]
            )
            
            text = response.text.strip()
            
            # JSON parse etmeye çalış
            if text.startswith('```json'):
                text = text.replace('```json', '').replace('```', '').strip()
            elif text.startswith('```'):
                text = text.replace('```', '').strip()
            
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"JSON parse hatası: {e}")
                print(f"Raw response: {text}")
                # Fallback: Basit analiz yap
                return {
                    "skills": ["Genel beceriler"],
                    "experience_years": 1.0,
                    "experience_level": "Junior",
                    "job_titles": ["Belirsiz"],
                    "education": ["Üniversite mezunu"],
                    "technologies": ["Çeşitli teknolojiler"],
                    "industry_experience": [self.interest],
                    "summary": "CV analizi yapıldı",
                    "career_stage": "Junior"
                }
                
        except Exception as e:
            print(f"PDF CV analiz hatası: {e}")
            # Fallback return
            return {
                "skills": ["Genel beceriler"],
                "experience_years": 1.0,
                "experience_level": "Junior",
                "job_titles": ["Belirsiz"],
                "education": ["Üniversite mezunu"],
                "technologies": ["Çeşitli teknolojiler"],
                "industry_experience": [self.interest],
                "summary": "CV analizi yapılamadı",
                "career_stage": "Junior"
            }

    def analyze_cv(self, cv_text):
        """CV'yi analiz eder ve anahtar kelimeleri çıkarır (eski metin tabanlı metod)"""
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
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
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
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
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

    async def scrape_job_listings(self, query_term, count=10):
        """İş ilanlarını scrape eder"""
        jobs = []
        
        try:
            # Kariyer.net'ten scraping
            kariyer_jobs = await self.scrape_kariyer_net(query_term, count//2)
            jobs.extend(kariyer_jobs)
            
            # Indeed'den scraping
            indeed_jobs = await self.scrape_indeed_tr(query_term, count//2)
            jobs.extend(indeed_jobs)
            
            return jobs[:count]
            
        except Exception as e:
            print(f"Job scraping hatası: {e}")
            return []

    async def scrape_kariyer_net(self, query, limit=5):
        """Kariyer.net'ten iş ilanlarını scrape eder"""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://www.kariyer.net/is-ilanlari?q={quote_plus(query)}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = await client.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İş ilanı kartlarını bul
                job_cards = soup.find_all('div', class_='list-items', limit=limit)
                
                for card in job_cards:
                    try:
                        title_elem = card.find('a', class_='job-title')
                        company_elem = card.find('a', class_='company-name')
                        location_elem = card.find('span', class_='location')
                        desc_elem = card.find('p', class_='job-description')
                        
                        if title_elem and company_elem:
                            job = {
                                'title': title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True),
                                'location': location_elem.get_text(strip=True) if location_elem else 'Belirtilmemiş',
                                'description': desc_elem.get_text(strip=True) if desc_elem else 'Açıklama yok',
                                'url': f"https://www.kariyer.net{title_elem.get('href', '')}" if title_elem.get('href') else '',
                                'source': 'Kariyer.net'
                            }
                            jobs.append(job)
                    except Exception as e:
                        print(f"Kariyer.net iş kartı parse hatası: {e}")
                        continue
                        
        except Exception as e:
            print(f"Kariyer.net scraping hatası: {e}")
            
        return jobs

    async def scrape_indeed_tr(self, query, limit=5):
        """Indeed TR'den iş ilanlarını scrape eder"""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://tr.indeed.com/jobs?q={quote_plus(query)}&l=Turkey"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = await client.get(url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # İş ilanı kartlarını bul (Indeed'in yapısına göre)
                job_cards = soup.find_all('div', class_='job_seen_beacon', limit=limit)
                
                for card in job_cards:
                    try:
                        title_elem = card.find('h2', class_='jobTitle')
                        company_elem = card.find('span', class_='companyName')
                        location_elem = card.find('div', class_='companyLocation')
                        desc_elem = card.find('div', class_='summary')
                        
                        if title_elem and company_elem:
                            title_link = title_elem.find('a')
                            job = {
                                'title': title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True),
                                'company': company_elem.get_text(strip=True),
                                'location': location_elem.get_text(strip=True) if location_elem else 'Belirtilmemiş',
                                'description': desc_elem.get_text(strip=True) if desc_elem else 'Açıklama yok',
                                'url': f"https://tr.indeed.com{title_link.get('href', '')}" if title_link and title_link.get('href') else '',
                                'source': 'Indeed TR'
                            }
                            jobs.append(job)
                    except Exception as e:
                        print(f"Indeed iş kartı parse hatası: {e}")
                        continue
                        
        except Exception as e:
            print(f"Indeed scraping hatası: {e}")
            
        return jobs

    def generate_mock_job_listings(self, search_term, count=10, cv_analysis=None, use_interest=True):
        """Gerçek iş ilanlarını scrape eder veya yönlendirme yapar"""
        try:
            # Arama terimini belirle
            if use_interest:
                # Interest'e göre arama
                query_term = search_term
                message_prefix = f"{search_term} alanında"
            else:
                # CV analizine göre arama terimi oluştur
                if cv_analysis:
                    # CV'den çıkarılan beceriler ve pozisyonlara göre arama terimi oluştur
                    skills = cv_analysis.get('skills', [])
                    job_titles = cv_analysis.get('job_titles', [])
                    technologies = cv_analysis.get('technologies', [])
                    
                    # En uygun arama terimini oluştur
                    search_components = []
                    if job_titles:
                        search_components.extend(job_titles[:2])  # İlk 2 pozisyon
                    if technologies:
                        search_components.extend(technologies[:3])  # İlk 3 teknoloji
                    if skills and not search_components:
                        search_components.extend(skills[:2])  # Eğer başka şey yoksa beceriler
                    
                    query_term = ' '.join(search_components[:3]) if search_components else search_term
                    message_prefix = "CV analizinize göre"
                else:
                    query_term = search_term
                    message_prefix = f"{search_term} alanında"

            # Scraping işlemini senkron olarak çalıştır
            try:
                scraped_jobs = asyncio.run(self.scrape_job_listings(query_term, count))
                
                if scraped_jobs:
                    return {
                        "jobs": scraped_jobs,
                        "search_recommendations": [],
                        "search_term": query_term,
                        "search_method": "interest" if use_interest else "cv_based",
                        "message": f"{message_prefix} toplam {len(scraped_jobs)} iş ilanı bulundu."
                    }
            except Exception as scrape_error:
                print(f"Scraping işlemi başarısız: {scrape_error}")
            
            # Eğer scraping başarısız olursa fallback olarak temel siteler
            search_sites = [
                {
                    "site_name": "LinkedIn",
                    "search_url": f"https://www.linkedin.com/jobs/search/?keywords={query_term.replace(' ', '%20')}&location=Turkey",
                    "description": "Dünya çapında profesyonel iş ağı"
                },
                {
                    "site_name": "Kariyer.net",
                    "search_url": f"https://www.kariyer.net/is-ilanlari?q={query_term.replace(' ', '+')}",
                    "description": "Türkiye'nin en büyük iş arama sitesi"
                },
                {
                    "site_name": "Indeed Türkiye",
                    "search_url": f"https://tr.indeed.com/jobs?q={query_term.replace(' ', '+')}&l=Turkey",
                    "description": "Uluslararası iş arama motoru"
                }
            ]
            
            # Kullanıcıya gerçek iş arama sitelerini öner
            return {
                "jobs": [],
                "search_recommendations": search_sites,
                "search_term": query_term,
                "search_method": "interest" if use_interest else "cv_based",
                "message": f"{message_prefix} için iş scraping başarısız oldu. İş arama sitelerini kontrol edin:"
            }
            
        except Exception as e:
            print(f"İş arama sitesi yönlendirme hatası: {e}")
            return {
                "jobs": [],
                "search_recommendations": [
                    {
                        "site_name": "LinkedIn",
                        "search_url": f"https://www.linkedin.com/jobs/search/?keywords={search_term.replace(' ', '%20')}&location=Turkey",
                        "description": "Profesyonel iş ağı"
                    }
                ],
                "search_term": search_term,
                "search_method": "interest" if use_interest else "cv_based",
                "message": "İş arama sitelerine yönlendiriliyorsunuz..."
            }
