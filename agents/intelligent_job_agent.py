#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı
CV analizi + LinkedIn scraping + Gemini AI eşleştirme
"""

import os
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
import httpx
from dotenv import load_dotenv

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

class IntelligentJobAgent:
    def __init__(self):
        # Gemini AI setup
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY çevre değişkeni bulunamadı")
        
        # Traditional Gemini setup
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # New Gemini client for PDF processing
        self.genai_client = google_genai.Client(api_key=self.gemini_api_key)
        
        # Job scraping keywords
        self.turkish_cities = [
            'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 
            'konya', 'sancaktepe', 'kadıköy', 'beşiktaş', 'şişli', 'beyoğlu'
        ]
        
        # Selenium driver (will be initialized when needed)
        self.driver = None
        self.wait = None
    
    def analyze_cv_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDF bytes'ını direkt Gemini ile analiz eder (Yeni yöntem)
        """
        prompt = """
        Bu CV'yi çok detaylı ve dikkatli bir şekilde analiz et. Her bilgiyi CV'den AYNEN alarak analiz yap.
        
        ÖNEMLİ TALİMATLAR:
        1. Deneyim süresini CV'deki tarihlere göre hesapla (örn: 2023-2024 = 1 yıl, 2024-şimdi = birkaç ay)
        2. Sadece CV'de açıkça yazılan becerileri listele, varsayımda bulunma
        3. Eğer bir bilgi CV'de yoksa "Belirtilmemiş" yaz
        4. İş deneyimi yoksa deneyim_yılı: 0 yap
        5. Staj ve part-time işleri ayrı olarak değerlendir
        6. Öğrenci ise veya yeni mezun ise deneyim_seviyesi: "entry" yap
        
        Analiz sonucu JSON formatı:
        {
            "kişisel_bilgiler": {
                "ad_soyad": "CV'deki tam isim veya Belirtilmemiş",
                "email": "CV'deki email veya Belirtilmemiş", 
                "telefon": "CV'deki telefon veya Belirtilmemiş",
                "lokasyon": "CV'deki şehir/adres veya Belirtilmemiş"
            },
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "2 yıl 3 ay (detaylı açıklama)",
            "staj_deneyimi": "6 ay (eğer varsa)",
            "teknik_beceriler": ["Sadece CV'de yazılan teknik beceriler"],
            "yazılım_dilleri": ["Sadece CV'de belirtilen programlama dilleri"],
            "teknolojiler": ["Framework, araç ve teknolojiler"],
            "veritabanları": ["CV'de belirtilen veritabanları veya boş liste"],
            "eğitim": ["Tam eğitim bilgisi - Üniversite/Bölüm/Yıl"],
            "sertifikalar": ["CV'de belirtilen sertifikalar veya boş liste"],
            "projeler": ["CV'deki proje isimleri ve kısa açıklamaları"],
            "diller": ["CV'de belirtilen diller ve seviyeleri"],
            "deneyim_seviyesi": "entry|junior|mid|senior (gerçek deneyime göre)",
            "ana_uzmanlık_alanı": "CV'deki bilgilere göre belirlenen alan",
            "uygun_iş_alanları": ["Gerçek becerilere uygun iş alanları"],
            "güçlü_yönler": ["CV'den çıkarılan güçlü yönler"],
            "gelişim_alanları": ["Eksik görünen alanlar"],
            "uzaktan_çalışma_uygunluğu": true/false,
            "sektör_tercihi": ["CV'deki deneyim ve eğitime uygun sektörler"],
            "cv_kalitesi": "zayıf|orta|iyi|mükemmel",
            "öneriler": ["CV geliştirme önerileri"]
        }
        
        DENEYIM SEVİYESİ REHBERİ:
        - entry: 0-1 yıl deneyim, yeni mezun, stajyer
        - junior: 1-3 yıl deneyim
        - mid: 3-6 yıl deneyim  
        - senior: 6+ yıl deneyim
        
        Önemli: Sadece JSON döndür, başka açıklama ekleme. CV'de olmayan bilgileri uydurma!
        """
        
        try:
            # Yeni Gemini PDF API kullan
            response = self.genai_client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type='application/pdf',
                    ),
                    prompt
                ]
            )
            
            # JSON'u temizle ve parse et
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            cv_analysis = json.loads(json_text)
            
            # Post-processing: Deneyim kontrolü
            cv_analysis = self._validate_experience(cv_analysis)
            
            return cv_analysis
            
        except Exception as e:
            print(f"PDF CV analizi hatası: {e}")
            # Fallback analiz
            return self._fallback_cv_analysis("")
    
    def analyze_cv_with_gemini(self, cv_text: str) -> Dict[str, Any]:
        """
        Gemini AI ile CV'yi detaylı analiz eder
        """
        prompt = f"""
        Bu CV'yi çok detaylı ve dikkatli bir şekilde analiz et. Her bilgiyi CV'den AYNEN alarak analiz yap.
        
        CV İÇERİĞİ:
        {cv_text}
        
        ÖNEMLİ TALİMATLAR:
        1. Deneyim süresini CV'deki tarihlere göre hesapla (örn: 2023-2024 = 1 yıl, 2024-şimdi = birkaç ay)
        2. Sadece CV'de açıkça yazılan becerileri listele, varsayımda bulunma
        3. Eğer bir bilgi CV'de yoksa "Belirtilmemiş" yaz
        4. İş deneyimi yoksa deneyim_yılı: 0 yap
        5. Staj ve part-time işleri ayrı olarak değerlendir
        6. Öğrenci ise veya yeni mezun ise deneyim_seviyesi: "entry" yap
        
        Analiz sonucu JSON formatı:
        {{
            "kişisel_bilgiler": {{
                "ad_soyad": "CV'deki tam isim veya Belirtilmemiş",
                "email": "CV'deki email veya Belirtilmemiş", 
                "telefon": "CV'deki telefon veya Belirtilmemiş",
                "lokasyon": "CV'deki şehir/adres veya Belirtilmemiş"
            }},
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "2 yıl 3 ay (detaylı açıklama)",
            "staj_deneyimi": "6 ay (eğer varsa)",
            "teknik_beceriler": ["Sadece CV'de yazılan teknik beceriler"],
            "yazılım_dilleri": ["Sadece CV'de belirtilen programlama dilleri"],
            "teknolojiler": ["Framework, araç ve teknolojiler"],
            "veritabanları": ["CV'de belirtilen veritabanları veya boş liste"],
            "eğitim": ["Tam eğitim bilgisi - Üniversite/Bölüm/Yıl"],
            "sertifikalar": ["CV'de belirtilen sertifikalar veya boş liste"],
            "projeler": ["CV'deki proje isimleri ve kısa açıklamaları"],
            "diller": ["CV'de belirtilen diller ve seviyeleri"],
            "deneyim_seviyesi": "entry|junior|mid|senior (gerçek deneyime göre)",
            "ana_uzmanlık_alanı": "CV'deki bilgilere göre belirlenen alan",
            "uygun_iş_alanları": ["Gerçek becerilere uygun iş alanları"],
            "güçlü_yönler": ["CV'den çıkarılan güçlü yönler"],
            "gelişim_alanları": ["Eksik görünen alanlar"],
            "uzaktan_çalışma_uygunluğu": true/false,
            "sektör_tercihi": ["CV'deki deneyim ve eğitime uygun sektörler"],
            "cv_kalitesi": "zayıf|orta|iyi|mükemmel",
            "öneriler": ["CV geliştirme önerileri"]
        }}
        
        DENEYIM SEVİYESİ REHBERİ:
        - entry: 0-1 yıl deneyim, yeni mezun, stajyer
        - junior: 1-3 yıl deneyim
        - mid: 3-6 yıl deneyim  
        - senior: 6+ yıl deneyim
        
        Önemli: Sadece JSON döndür, başka açıklama ekleme. CV'de olmayan bilgileri uydurma!
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # JSON'u temizle ve parse et
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            cv_analysis = json.loads(json_text)
            
            # Post-processing: Deneyim kontrolü
            cv_analysis = self._validate_experience(cv_analysis)
            
            return cv_analysis
            
        except Exception as e:
            print(f"CV analizi hatası: {e}")
            # Fallback analiz
            return self._fallback_cv_analysis(cv_text)
    
    def _validate_experience(self, cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deneyim bilgilerini doğrular ve tutarlılık kontrol eder
        """
        try:
            deneyim_yili = cv_analysis.get('deneyim_yılı', 0)
            deneyim_seviyesi = cv_analysis.get('deneyim_seviyesi', 'entry')
            
            # Deneyim yılı ve seviye tutarlılığını kontrol et
            if deneyim_yili == 0:
                cv_analysis['deneyim_seviyesi'] = 'entry'
            elif deneyim_yili < 1:
                cv_analysis['deneyim_seviyesi'] = 'entry'
            elif deneyim_yili <= 3:
                if deneyim_seviyesi not in ['entry', 'junior']:
                    cv_analysis['deneyim_seviyesi'] = 'junior'
            elif deneyim_yili <= 6:
                if deneyim_seviyesi == 'senior':
                    cv_analysis['deneyim_seviyesi'] = 'mid'
            else:
                cv_analysis['deneyim_seviyesi'] = 'senior'
            
            # Eğer hiç teknik beceri yoksa entry seviye olmalı
            teknik_beceriler = cv_analysis.get('teknik_beceriler', [])
            if len(teknik_beceriler) == 0:
                cv_analysis['deneyim_seviyesi'] = 'entry'
                cv_analysis['deneyim_yılı'] = 0
                
            # İş alanlarını deneyim seviyesine göre ayarla
            uygun_is_alanlari = cv_analysis.get('uygun_iş_alanları', [])
            if cv_analysis['deneyim_seviyesi'] == 'entry':
                # Entry level için daha genel alanlar
                entry_jobs = []
                for job in uygun_is_alanlari:
                    if 'junior' not in job.lower() and 'entry' not in job.lower():
                        entry_jobs.append(f"Junior {job}")
                    else:
                        entry_jobs.append(job)
                cv_analysis['uygun_iş_alanları'] = entry_jobs[:5]  # En fazla 5 alan
            
            return cv_analysis
            
        except Exception as e:
            print(f"Deneyim doğrulama hatası: {e}")
            return cv_analysis
    
    def _fallback_cv_analysis(self, cv_text: str) -> Dict[str, Any]:
        """CV analizi başarısız olursa basit fallback"""
        # Basit regex ile beceri çıkarma
        skills = []
        common_skills = [
            'python', 'javascript', 'java', 'react', 'node.js', 'django', 
            'flask', 'sql', 'mysql', 'postgresql', 'mongodb', 'git', 
            'docker', 'kubernetes', 'aws', 'azure', 'linux'
        ]
        
        cv_lower = cv_text.lower()
        for skill in common_skills:
            if skill in cv_lower:
                skills.append(skill.title())
        
        # Email ve telefon çıkarma
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+90|0)?[\s-]?[\(]?[0-9]{3}[\)]?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}'
        
        email = re.search(email_pattern, cv_text)
        phone = re.search(phone_pattern, cv_text)
        
        return {
            "kişisel_bilgiler": {
                "ad_soyad": "Belirtilmemiş",
                "email": email.group() if email else "Belirtilmemiş",
                "telefon": phone.group() if phone else "Belirtilmemiş",
                "lokasyon": "Belirtilmemiş"
            },
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "Belirtilmemiş",
            "staj_deneyimi": "Belirtilmemiş",
            "teknik_beceriler": skills[:8],
            "yazılım_dilleri": [skill for skill in skills if skill.lower() in ['python', 'javascript', 'java', 'c++', 'c#']],
            "teknolojiler": [skill for skill in skills if skill.lower() in ['react', 'django', 'flask', 'node.js']],
            "veritabanları": [skill for skill in skills if skill.lower() in ['mysql', 'postgresql', 'mongodb']],
            "eğitim": ["Belirtilmemiş"],
            "sertifikalar": [],
            "projeler": [],
            "diller": ["Türkçe"],
            "deneyim_seviyesi": "entry",
            "ana_uzmanlık_alanı": "Genel Yazılım Geliştirme",
            "uygun_iş_alanları": ["Junior Software Developer", "Trainee Developer"],
            "güçlü_yönler": ["Motivasyon"],
            "gelişim_alanları": ["Profesyonel deneyim", "Proje portföyü"],
            "uzaktan_çalışma_uygunluğu": True,
            "sektör_tercihi": ["Teknoloji"],
            "cv_kalitesi": "zayıf",
            "öneriler": [
                "CV'ye daha detaylı kişisel bilgiler ekleyin",
                "Proje portföyünüzü geliştirin",
                "Teknik becerilerinizi belirgin şekilde listeleyin"
            ]
        }
    
    def setup_selenium_driver(self, headless: bool = True):
        """Selenium WebDriver'ı başlatır"""
        if self.driver:
            return  # Zaten başlatılmış
            
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 30)
        except Exception as e:
            print(f"Selenium driver başlatılamadı: {e}")
            self.driver = None
    
    def scrape_linkedin_jobs(self, job_areas: List[str], location: str = "Istanbul, Turkey", max_per_search: int = 10) -> List[Dict[str, Any]]:
        """
        LinkedIn'den CV'ye uygun iş ilanlarını çeker
        """
        all_jobs = []
        
        # Selenium driver'ı başlat
        self.setup_selenium_driver(headless=True)
        if not self.driver:
            return []
        
        try:
            for job_area in job_areas:
                print(f"🔍 '{job_area}' için iş aranıyor...")
                
                # Farklı arama terimleri oluştur
                search_terms = self._generate_search_terms(job_area)
                
                for search_term in search_terms[:2]:  # Her alan için en fazla 2 arama
                    jobs = self._search_single_term(search_term, location, max_per_search)
                    all_jobs.extend(jobs)
                    time.sleep(2)  # Rate limiting
            
            # Duplicates'leri kaldır
            unique_jobs = self._remove_duplicates(all_jobs)
            print(f"📊 Toplamda {len(unique_jobs)} benzersiz iş ilanı bulundu")
            
            return unique_jobs
            
        except Exception as e:
            print(f"LinkedIn scraping hatası: {e}")
            return []
        
        finally:
            self._close_driver()
    
    def _generate_search_terms(self, job_area: str) -> List[str]:
        """İş alanından arama terimleri oluşturur"""
        base_terms = [job_area.lower()]
        
        # Ekstra terimler
        if "developer" in job_area.lower():
            base_terms.extend([
                f"{job_area.lower().replace(' developer', '')} geliştirici",
                f"{job_area.lower()} engineer"
            ])
        elif "engineer" in job_area.lower():
            base_terms.extend([
                f"{job_area.lower().replace(' engineer', '')} mühendisi",
                f"{job_area.lower().replace(' engineer', '')} developer"
            ])
        
        return base_terms
    
    def _search_single_term(self, search_term: str, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Tek bir terim için LinkedIn'de arama yapar"""
        jobs = []
        
        try:
            # LinkedIn arama URL'si
            base_url = "https://www.linkedin.com/jobs/search"
            params = f"?keywords={search_term.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400"
            url = base_url + params
            
            self.driver.get(url)
            time.sleep(3)
            
            # Sayfanın yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list")))
            except:
                return jobs
            
            # Sayfayı scroll et
            self._scroll_page()
            
            # İş ilanlarını bul
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")
            
            for idx, job_element in enumerate(job_elements[:max_results]):
                try:
                    job_data = self._extract_job_data(job_element)
                    if job_data and self._is_relevant_job(job_data, search_term):
                        jobs.append(job_data)
                        print(f"✓ Bulundu: {job_data['title']} - {job_data['company']}")
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Arama hatası ({search_term}): {e}")
        
        return jobs
    
    def _extract_job_data(self, job_element) -> Optional[Dict[str, Any]]:
        """İş ilanı verilerini çıkarır"""
        try:
            # Başlık
            title = "Başlık bulunamadı"
            try:
                title_elem = job_element.find_element(By.CSS_SELECTOR, "h3")
                title = title_elem.text.strip()
            except:
                pass
            
            # URL
            job_url = "URL bulunamadı"
            try:
                url_elem = job_element.find_element(By.CSS_SELECTOR, "a[href*='jobs']")
                job_url = url_elem.get_attribute("href")
            except:
                pass
            
            # Şirket
            company = "Şirket belirtilmemiş"
            try:
                all_links = job_element.find_elements(By.CSS_SELECTOR, "a")
                if len(all_links) >= 2:
                    company_elem = all_links[1]
                    company = company_elem.text.strip()
            except:
                pass
            
            # Lokasyon
            location = "Lokasyon belirtilmemiş"
            try:
                spans = job_element.find_elements(By.CSS_SELECTOR, "span")
                for span in spans:
                    span_text = span.text.strip()
                    if any(city in span_text.lower() for city in self.turkish_cities):
                        location = span_text
                        break
            except:
                pass
            
            # Tarih
            posted_date = datetime.now().isoformat()
            try:
                time_elem = job_element.find_element(By.CSS_SELECTOR, "time")
                posted_date = time_elem.get_attribute("datetime") or posted_date
            except:
                pass
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'posted_date': posted_date,
                'scraped_at': datetime.now().isoformat(),
                'source': 'LinkedIn'
            }
            
        except Exception as e:
            return None
    
    def _is_relevant_job(self, job_data: Dict[str, Any], search_term: str) -> bool:
        """İş ilanının alakalı olup olmadığını kontrol eder"""
        title_lower = job_data['title'].lower()
        
        # Çok senior pozisyonları filtrele
        senior_keywords = [
            'senior manager', 'director', 'vp', 'vice president', 'head of',
            'chief', 'cto', 'ceo', 'principal', '15+ years', '10+ years'
        ]
        for keyword in senior_keywords:
            if keyword in title_lower:
                return False
        
        # Hedef alanla ilgili mi kontrol et
        tech_keywords = [
            'developer', 'engineer', 'programmer', 'software', 'backend', 'frontend',
            'full stack', 'data science', 'machine learning', 'ai', 'python', 
            'javascript', 'java', 'react', 'django', 'geliştirici', 'mühendis',
            'yazılım', 'programcı'
        ]
        
        return any(keyword in title_lower for keyword in tech_keywords)
    
    def _scroll_page(self):
        """Sayfayı scroll eder"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 3
            
            while scroll_count < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1
        except:
            pass
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Duplicate iş ilanlarını kaldırır"""
        seen_urls = set()
        unique_jobs = []
        
        for job in jobs:
            # URL'den parametreleri temizle
            clean_url = job['url'].split('?')[0] if job['url'] != "URL bulunamadı" else job['title']
            
            if clean_url not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(clean_url)
        
        return unique_jobs
    
    def match_cv_with_jobs(self, cv_analysis: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gemini AI ile CV analizi ve iş ilanlarını eşleştirir
        """
        if not jobs:
            return []
        
        matched_jobs = []
        
        for job in jobs:
            try:
                # Her iş için eşleşme skorunu hesapla
                match_score = self._calculate_match_score(cv_analysis, job)
                
                if match_score['score'] >= 50:  # En az %50 uyum
                    job_with_match = job.copy()
                    job_with_match.update(match_score)
                    matched_jobs.append(job_with_match)
            
            except Exception as e:
                print(f"Eşleştirme hatası: {e}")
                continue
        
        # Skora göre sırala
        matched_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return matched_jobs[:10]  # En iyi 10 eşleşme
    
    def _calculate_match_score(self, cv_analysis: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gemini AI ile CV ve iş ilanı arasındaki eşleşmeyi hesaplar
        """
        prompt = f"""
        CV analizi ile iş ilanını karşılaştır ve eşleşme skorunu hesapla:
        
        CV ANALİZİ:
        - Teknik Beceriler: {cv_analysis.get('teknik_beceriler', [])}
        - Deneyim Yılı: {cv_analysis.get('deneyim_yılı', 0)}
        - Ana Uzmanlık: {cv_analysis.get('ana_uzmanlık_alanı', '')}
        - Teknolojiler: {cv_analysis.get('teknolojiler', [])}
        - Deneyim Seviyesi: {cv_analysis.get('deneyim_seviyesi', '')}
        
        İŞ İLANI:
        - Başlık: {job.get('title', '')}
        - Şirket: {job.get('company', '')}
        - Lokasyon: {job.get('location', '')}
        
        Aşağıdaki kriterlere göre 0-100 arası skor ver:
        - Beceri uyumluluğu (40%)
        - Deneyim seviyesi uyumu (30%)
        - Alan uyumluluğu (20%)
        - Lokasyon uyumu (10%)
        
        JSON formatında döndür:
        {{
            "score": 85,
            "match_reasons": ["Python becerisi uyumlu", "Deneyim seviyesi uygun"],
            "missing_skills": ["Docker", "Kubernetes"],
            "recommendations": ["Docker öğren", "Kubernetes sertifikası al"],
            "salary_estimate": "20000-30000 TL"
        }}
        
        Sadece JSON döndür.
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            return json.loads(json_text)
            
        except Exception as e:
            # Fallback scoring
            return {
                "score": 60,
                "match_reasons": ["Genel teknoloji uyumu"],
                "missing_skills": ["Detaylı analiz yapılamadı"],
                "recommendations": ["İlan detaylarını incele"],
                "salary_estimate": "15000-25000 TL"
            }
    
    def generate_job_application_tips(self, cv_analysis: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Belirli bir iş için başvuru önerileri oluşturur
        """
        prompt = f"""
        Bu CV sahibinin "{job.get('title', '')}" pozisyonuna başvurması için öneriler ver:
        
        CV ÖZETİ:
        - Ana Uzmanlık: {cv_analysis.get('ana_uzmanlık_alanı', '')}
        - Teknik Beceriler: {cv_analysis.get('teknik_beceriler', [])}
        - Deneyim: {cv_analysis.get('deneyim_yılı', 0)} yıl
        - Güçlü Yönler: {cv_analysis.get('güçlü_yönler', [])}
        
        İŞ DETAYI:
        - Pozisyon: {job.get('title', '')}
        - Şirket: {job.get('company', '')}
        
        JSON formatında döndür:
        {{
            "cover_letter_tips": ["Hangi yeteneklerinizi vurgulayın", "..."],
            "interview_preparation": ["Bu konulara odaklanın", "..."],
            "skill_gaps": ["Eksik olan beceriler", "..."],
            "success_probability": 75,
            "application_strategy": "Önce LinkedIn'den HR ile bağlantı kur"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_text = response.text.strip()
            
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            return json.loads(json_text)
            
        except Exception as e:
            return {
                "cover_letter_tips": ["Deneyimlerinizi vurgulayın"],
                "interview_preparation": ["Temel teknik sorulara hazırlanın"],
                "skill_gaps": ["Detay analiz edilemedi"],
                "success_probability": 60,
                "application_strategy": "Direkt başvuru yapın"
            }
    
    def _close_driver(self):
        """Selenium driver'ı kapatır"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.wait = None
            except:
                pass
    
    def __del__(self):
        """Cleanup"""
        self._close_driver()


# Test fonksiyonu
if __name__ == "__main__":
    # Test CV metni
    test_cv = """
    John Doe
    Software Developer
    john@email.com | +90 555 123 4567 | İstanbul
    
    DENEYIM:
    - 3 yıl Python geliştirme deneyimi
    - Django ve Flask framework'leri ile web uygulaması geliştirme
    - PostgreSQL ve MongoDB veritabanları
    - Git, Docker kullanımı
    - REST API geliştirme
    
    EĞİTİM:
    - İTÜ Bilgisayar Mühendisliği Lisans (2019-2023)
    
    PROJELER:
    - E-ticaret web sitesi (Django + React)
    - Blog platformu (Flask + SQLAlchemy)
    - API servisleri (FastAPI)
    
    BECERİLER:
    - Python, JavaScript, HTML/CSS
    - Django, Flask, FastAPI
    - PostgreSQL, MongoDB
    - Git, Docker, Linux
    """
    
    try:
        agent = IntelligentJobAgent()
        
        # 1. CV Analizi
        print("🔍 CV Analiz ediliyor...")
        cv_analysis = agent.analyze_cv_with_gemini(test_cv)
        print("✅ CV Analizi tamamlandı!")
        print(f"Ana uzmanlık: {cv_analysis.get('ana_uzmanlık_alanı')}")
        print(f"Uygun iş alanları: {cv_analysis.get('uygun_iş_alanları')}")
        
        # 2. İş İlanları Scraping
        print("\n🔍 İş ilanları aranıyor...")
        jobs = agent.scrape_linkedin_jobs(
            job_areas=cv_analysis.get('uygun_iş_alanları', ['Python Developer']),
            max_per_search=5
        )
        print(f"✅ {len(jobs)} iş ilanı bulundu!")
        
        # 3. CV-İş Eşleştirme
        print("\n🤖 CV ile işler eşleştiriliyor...")
        matched_jobs = agent.match_cv_with_jobs(cv_analysis, jobs)
        print(f"✅ {len(matched_jobs)} uygun iş eşleşmesi!")
        
        # Sonuçları göster
        for i, job in enumerate(matched_jobs[:3], 1):
            print(f"\n{i}. {job['title']} - {job['company']}")
            print(f"   Uyum: {job.get('score', 0)}%")
            print(f"   Lokasyon: {job['location']}")
            print(f"   URL: {job['url'][:50]}...")
        
    except Exception as e:
        print(f"Test hatası: {e}")
