#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı - Optimized Version
CV analizi + LinkedIn scraping + Gemini AI eşleştirme
"""

import os
import json
import time
import re
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
import httpx
from dotenv import load_dotenv
from functools import lru_cache
import threading
from collections import defaultdict

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
        
        # Performance optimizations
        self.cache = {}
        self.cache_ttl = 3600  # 1 saat cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Job scraping keywords
        self.turkish_cities = [
            'istanbul', 'ankara', 'izmir', 'bursa', 'antalya', 'adana', 
            'konya', 'sancaktepe', 'kadıköy', 'beşiktaş', 'şişli', 'beyoğlu'
        ]
        
        # Selenium driver (will be initialized when needed)
        self.driver = None
        self.wait = None
        self.driver_lock = threading.Lock()
        
        # Pre-compiled regex patterns for performance
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+90|0)?[\s-]?[\(]?[0-9]{3}[\)]?[\s-]?[0-9]{3}[\s-]?[0-9]{2}[\s-]?[0-9]{2}')
        
        # Skill mapping for faster matching
        self.skill_mapping = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'javascript': ['javascript', 'js', 'react', 'vue', 'angular', 'node.js'],
            'java': ['java', 'spring', 'hibernate', 'maven'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'frontend': ['html', 'css', 'bootstrap', 'tailwind', 'sass'],
            'mobile': ['react native', 'flutter', 'kotlin', 'swift']
        }
    
    @lru_cache(maxsize=100)
    def _get_cached_analysis(self, cv_hash: str) -> Optional[Dict[str, Any]]:
        """Cache'den CV analizi alır"""
        if cv_hash in self.cache:
            cache_time, data = self.cache[cv_hash]
            if datetime.now().timestamp() - cache_time < self.cache_ttl:
                return data
            else:
                del self.cache[cv_hash]
        return None
    
    def _cache_analysis(self, cv_hash: str, analysis: Dict[str, Any]):
        """CV analizini cache'ler"""
        self.cache[cv_hash] = (datetime.now().timestamp(), analysis)
    
    def analyze_cv_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDF bytes'ını direkt Gemini ile analiz eder (Optimized)
        """
        # Cache key oluştur
        import hashlib
        cv_hash = hashlib.md5(pdf_bytes).hexdigest()
        
        # Cache'den kontrol et
        cached = self._get_cached_analysis(cv_hash)
        if cached:
            return cached
        
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
            
            # Cache'e kaydet
            self._cache_analysis(cv_hash, cv_analysis)
            
            return cv_analysis
            
        except Exception as e:
            print(f"PDF CV analizi hatası: {e}")
            # Fallback analiz
            fallback = self._fallback_cv_analysis("")
            self._cache_analysis(cv_hash, fallback)
            return fallback
    
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
        email = self.email_pattern.search(cv_text)
        phone = self.phone_pattern.search(cv_text)
        
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
        """Selenium WebDriver'ı başlatır (Optimized)"""
        with self.driver_lock:
            if self.driver:
                return  # Zaten başlatılmış
                
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            
            # Performance optimizations
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-field-trial-config")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")  # Sadece HTML parsing için
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            chrome_options.add_argument("--disk-cache-size=1")
            chrome_options.add_argument("--media-cache-size=1")
            chrome_options.add_argument("--disk-cache-dir=/dev/null")
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.wait = WebDriverWait(self.driver, 10)  # Timeout'u azalttık
            except Exception as e:
                print(f"Selenium driver başlatılamadı: {e}")
                self.driver = None
    
    def scrape_linkedin_jobs(self, job_areas: List[str], location: str = "Istanbul, Turkey", max_per_search: int = 10) -> List[Dict[str, Any]]:
        """
        LinkedIn'den CV'ye uygun iş ilanlarını çeker (Optimized)
        """
        # Cache key oluştur
        cache_key = f"jobs_{hash(tuple(job_areas))}_{location}_{max_per_search}"
        cached = self._get_cached_analysis(cache_key)
        if cached:
            return cached
        
        all_jobs = []
        
        # Selenium driver'ı başlat
        self.setup_selenium_driver(headless=True)
        if not self.driver:
            return []
        
        try:
            # Parallel processing için job areas'ları grupla
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_area = {}
                
                for job_area in job_areas:
                    search_terms = self._generate_search_terms(job_area)
                    print(f"   🔍 '{job_area}' için arama terimleri: {search_terms[:2]}")
                    future = executor.submit(
                        self._search_multiple_terms_parallel,
                        search_terms[:4],  # Her alan için en fazla 4 arama (ML/AI için daha fazla)
                        location,
                        max_per_search
                    )
                    future_to_area[future] = job_area
                
                # Sonuçları topla
                for future in concurrent.futures.as_completed(future_to_area):
                    area = future_to_area[future]
                    try:
                        jobs = future.result()
                        all_jobs.extend(jobs)
                        print(f"✅ '{area}' için {len(jobs)} iş bulundu")
                    except Exception as e:
                        print(f"❌ '{area}' arama hatası: {e}")
            
            # Duplicates'leri kaldır (optimized)
            original_count = len(all_jobs)
            unique_jobs = self._remove_duplicates_optimized(all_jobs)
            duplicate_count = original_count - len(unique_jobs)
            print(f"📊 Toplamda {len(unique_jobs)} benzersiz iş ilanı bulundu ({(duplicate_count)} duplicate kaldırıldı)")
            
            # Cache'e kaydet
            self._cache_analysis(cache_key, unique_jobs)
            
            return unique_jobs
            
        except Exception as e:
            print(f"LinkedIn scraping hatası: {e}")
            return []
        
        finally:
            self._close_driver()
    
    def _generate_search_terms(self, job_area: str) -> List[str]:
        """İş alanından arama terimleri oluşturur - Genişletilmiş ve esnek"""
        base_terms = []
        job_lower = job_area.lower()
        
        # Junior kelimesini çıkar - çok spesifik oluyor
        clean_job = job_lower.replace('junior ', '').replace('entry level ', '').replace('entry ', '')
        
        # Temel arama terimlerini ekle
        base_terms.extend([
            clean_job,
            job_lower  # Orijinal de dahil et
        ])
        
        # Machine Learning / AI alanları için çok geniş terimler
        if any(keyword in clean_job for keyword in ['veri bilimci', 'data scientist', 'data science', 'makine öğrenmesi', 'machine learning', 'ml', 'ai', 'yapay zeka', 'artificial intelligence']):
            base_terms.extend([
                'python developer',
                'python engineer', 
                'software developer',
                'software engineer',
                'backend developer',
                'full stack developer',
                'data analyst',
                'data engineer',
                'machine learning',
                'artificial intelligence',
                'python',
                'data science',
                'analytics',
                'developer',
                'engineer',
                'yazılım geliştirici',
                'yazılım mühendisi',
                'python geliştiricisi',
                'veri analisti'
            ])
        
        # Yazılım geliştirici için çok geniş terimler
        elif any(keyword in clean_job for keyword in ['yazılım', 'software', 'developer', 'geliştirici']):
            base_terms.extend([
                'python developer',
                'javascript developer',
                'java developer',
                'software developer',
                'software engineer',
                'backend developer',
                'frontend developer',
                'full stack developer',
                'web developer',
                'mobile developer',
                'developer',
                'engineer',
                'programmer',
                'yazılım geliştirici',
                'yazılım mühendisi',
                'web geliştiricisi',
                'mobil geliştirici',
                'programcı'
            ])
        
        # Diğer mühendislik alanları için geniş terimler
        elif any(keyword in clean_job for keyword in ['engineer', 'mühendis']):
            base_terms.extend([
                'software engineer',
                'software developer',
                'system engineer',
                'backend engineer',
                'frontend engineer',
                'devops engineer',
                'cloud engineer',
                'developer',
                'engineer',
                'yazılım mühendisi',
                'sistem mühendisi',
                'geliştirici'
            ])
        
        # Hiçbiri değilse genel terimler ekle
        else:
            base_terms.extend([
                'developer',
                'engineer',
                'software',
                'python',
                'javascript',
                'yazılım',
                'geliştirici',
                'mühendis'
            ])
        
        # Çok kısa terimleri filtrele ve unique yap
        filtered_terms = []
        for term in base_terms:
            if len(term.strip()) >= 3 and term.strip() not in filtered_terms:
                filtered_terms.append(term.strip())
        
        # En fazla 6 terim döndür (performans için)
        return filtered_terms[:6]
    
    def _search_multiple_terms_parallel(self, search_terms: List[str], location: str, max_results: int) -> List[Dict[str, Any]]:
        """Birden fazla arama terimini paralel olarak arar"""
        all_jobs = []
        
        for search_term in search_terms:
            try:
                jobs = self._search_single_term_optimized(search_term, location, max_results)
                all_jobs.extend(jobs)
                time.sleep(1)  # Rate limiting azaltıldı
            except Exception as e:
                print(f"Arama hatası ({search_term}): {e}")
                continue
        
        return all_jobs
    
    def _search_single_term_optimized(self, search_term: str, location: str, max_results: int) -> List[Dict[str, Any]]:
        """Tek bir terim için LinkedIn'de arama yapar (Optimized + Debug)"""
        jobs = []
        
        try:
            # LinkedIn arama URL'si
            base_url = "https://www.linkedin.com/jobs/search"
            params = f"?keywords={search_term.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_TPR=r86400&start=0"
            url = base_url + params
            
            print(f"      🔗 LinkedIn URL: {url}")
            self.driver.get(url)
            time.sleep(2)  # Bekleme süresini biraz artırdık
            
            # Sayfanın yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list")))
                print(f"      ✅ Sayfa yüklendi: {search_term}")
            except:
                print(f"      ❌ Sayfa yüklenemedi: {search_term}")
                return jobs
            
            # Sayfayı scroll et (optimized)
            self._scroll_page_optimized()
            
            # İş ilanlarını bul (batch processing)
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search__results-list li")
            print(f"      📋 {len(job_elements)} iş elementi bulundu")
            
            # Batch processing ile veri çıkar
            jobs = self._extract_job_data_batch(job_elements[:max_results], search_term)
            print(f"      ✅ {len(jobs)} uygun iş çıkarıldı")
            
        except Exception as e:
            print(f"      ❌ Arama hatası ({search_term}): {e}")
        
        return jobs
    
    def _extract_job_data_batch(self, job_elements: List, search_term: str) -> List[Dict[str, Any]]:
        """İş ilanı verilerini batch olarak çıkarır (Debug enabled)"""
        jobs = []
        total_elements = len(job_elements)
        
        for i, job_element in enumerate(job_elements):
            try:
                job_data = self._extract_job_data_optimized(job_element)
                if job_data:
                    is_relevant = self._is_relevant_job_fast(job_data, search_term)
                    if is_relevant:
                        jobs.append(job_data)
                        print(f"         ✅ İş #{i+1}: {job_data['title'][:50]} - {job_data['company'][:30]}")
                    else:
                        print(f"         ❌ İş #{i+1}: {job_data['title'][:50]} - Alakasız")
                else:
                    print(f"         ⚠️ İş #{i+1}: Veri çıkarılamadı")
            except Exception as e:
                print(f"         ❌ İş #{i+1} hatası: {e}")
                continue
        
        print(f"      📊 {len(jobs)}/{total_elements} iş filtrelendi")
        return jobs
    
    def _extract_job_data_optimized(self, job_element) -> Optional[Dict[str, Any]]:
        """İş ilanı verilerini çıkarır (Optimized)"""
        try:
            # Tek seferde tüm elementleri bul
            elements = {
                'title': job_element.find_elements(By.CSS_SELECTOR, "h3"),
                'url': job_element.find_elements(By.CSS_SELECTOR, "a[href*='jobs']"),
                'all_links': job_element.find_elements(By.CSS_SELECTOR, "a"),
                'spans': job_element.find_elements(By.CSS_SELECTOR, "span"),
                'time': job_element.find_elements(By.CSS_SELECTOR, "time")
            }
            
            # Başlık
            title = elements['title'][0].text.strip() if elements['title'] else "Başlık bulunamadı"
            
            # URL
            job_url = elements['url'][0].get_attribute("href") if elements['url'] else "URL bulunamadı"
            
            # Şirket
            company = "Şirket belirtilmemiş"
            if len(elements['all_links']) >= 2:
                company = elements['all_links'][1].text.strip()
            
            # Lokasyon
            location = "Lokasyon belirtilmemiş"
            for span in elements['spans']:
                    span_text = span.text.strip()
                    if any(city in span_text.lower() for city in self.turkish_cities):
                        location = span_text
                        break
            
            # Tarih
            posted_date = datetime.now().isoformat()
            if elements['time']:
                posted_date = elements['time'][0].get_attribute("datetime") or posted_date
            
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
    
    def _is_relevant_job_fast(self, job_data: Dict[str, Any], search_term: str) -> bool:
        """İş ilanının alakalı olup olmadığını hızlı kontrol eder - ÇOK ESNEK"""
        title_lower = job_data['title'].lower()
        
        # Sadece çok üst düzey pozisyonları filtrele (çok kısıtlayıcı filtreleri kaldırdık)
        if any(keyword in title_lower for keyword in ['ceo', 'cto', 'founder', 'co-founder']):
            return False
        
        # Alakasız sektörleri filtrele
        irrelevant_keywords = {
            'sales', 'marketing', 'hr', 'human resources', 'finance', 'accounting',
            'legal', 'lawyer', 'doctor', 'nurse', 'teacher', 'driver', 'chef',
            'cleaner', 'security guard', 'receptionist', 'cashier'
        }
        
        if any(keyword in title_lower for keyword in irrelevant_keywords):
            return False
        
        # Çok geniş teknoloji ve iş terimleri - neredeyse her teknoloji işini kabul et
        tech_keywords = {
            # Genel teknoloji
            'developer', 'engineer', 'programmer', 'software', 'backend', 'frontend',
            'full stack', 'specialist', 'architect', 'consultant', 'analyst',
            'technician', 'technical', 'it', 'system', 'web', 'mobile', 'app',
            
            # Programlama ve teknoloji
            'python', 'javascript', 'java', 'php', 'c++', 'c#', 'ruby', 'go',
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel',
            'node.js', 'express', 'api', 'rest', 'graphql', 'microservices',
            
            # Database ve data
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'database', 'data', 'analytics', 'bi', 'etl', 'pipeline',
            
            # ML/AI alanları
            'data science', 'machine learning', 'ml', 'ai', 'artificial intelligence',
            'deep learning', 'neural network', 'tensorflow', 'pytorch', 'scikit-learn',
            'computer vision', 'nlp', 'natural language processing',
            
            # Cloud ve DevOps
            'aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes', 'devops',
            'ci/cd', 'jenkins', 'terraform', 'ansible',
            
            # Türkçe terimler
            'yazılım', 'geliştirici', 'mühendis', 'programcı', 'sistem',
            'veri', 'analiz', 'teknoloji', 'bilişim', 'web', 'mobil'
        }
        
        # Eğer başlıkta herhangi bir teknoloji terimi varsa kabul et
        if any(keyword in title_lower for keyword in tech_keywords):
            return True
        
        # Arama teriminde geçen herhangi bir kelime başlıkta varsa kabul et
        search_words = search_term.lower().split()
        for word in search_words:
            if len(word) > 2 and word in title_lower:  # 3 harften uzun kelimeleri kontrol et
                return True
        
        # Eğer hiçbiri yoksa da genel bir kontrol yap - çok esnek
        general_keywords = {
            'junior', 'senior', 'mid', 'level', 'trainee', 'intern', 
            'entry', 'graduate', 'associate', 'lead', 'principal'
        }
        
        # Eğer pozisyon seviyesi belirten bir kelime varsa muhtemelen teknoloji işi
        if any(keyword in title_lower for keyword in general_keywords):
            return True
        
        # Son olarak, eğer şirket adında teknoloji ile ilgili kelime varsa
        company_lower = job_data.get('company', '').lower()
        company_tech_keywords = {'software', 'tech', 'technology', 'digital', 'systems', 'solutions', 'yazılım', 'teknoloji', 'bilişim'}
        if any(keyword in company_lower for keyword in company_tech_keywords):
            return True
            
        # Hiçbiri yoksa False döndür
        return False
    
    def _scroll_page_optimized(self):
        """Sayfayı scroll eder (Optimized)"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 2  # Scroll sayısını azalttık
            
            while scroll_count < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)  # Bekleme süresini azalttık
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1
        except:
            pass
    
    def _remove_duplicates_optimized(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Duplicate iş ilanlarını kaldırır (Optimized)"""
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        unique_jobs = []
        duplicate_count = 0
        
        for job in jobs:
            # URL'den parametreleri temizle
            clean_url = job['url'].split('?')[0] if job['url'] != "URL bulunamadı" else job['title']
            clean_title = job['title'].lower().strip()
            
            # Hem URL hem de başlık kontrolü
            is_duplicate = False
            if clean_url in seen_urls:
                is_duplicate = True
            elif clean_title in seen_titles:
                is_duplicate = True
            
            if not is_duplicate:
                unique_jobs.append(job)
                seen_urls.add(clean_url)
                seen_titles.add(clean_title)
            else:
                duplicate_count += 1
        
        if duplicate_count > 0:
            print(f"   🔄 {duplicate_count} duplicate iş ilanı temizlendi")
        
        return unique_jobs
    
    def match_cv_with_jobs(self, cv_analysis: Dict[str, Any], jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Gemini AI ile CV analizi ve iş ilanlarını eşleştirir (Ultra Optimized)
        """
        if not jobs:
            print("⚠️ Eşleştirilecek iş bulunamadı")
            return []
        
        print(f"🤖 {len(jobs)} iş için eşleştirme başlıyor...")
        
        # CV bilgilerini önceden hazırla
        try:
            cv_skills = set(skill.lower() for skill in cv_analysis.get('teknik_beceriler', []))
            cv_technologies = set(tech.lower() for tech in cv_analysis.get('teknolojiler', []))
            cv_experience = cv_analysis.get('deneyim_yılı', 0)
            cv_level = cv_analysis.get('deneyim_seviyesi', 'entry')
            
            print(f"   📊 CV Skills: {len(cv_skills)}, Technologies: {len(cv_technologies)}")
            print(f"   💼 Experience: {cv_experience} yıl, Level: {cv_level}")
            
        except Exception as e:
            print(f"❌ CV bilgileri hazırlama hatası: {e}")
            return []
        
        matched_jobs = []
        start_time = time.time()
        max_execution_time = 15  # 15 saniye timeout (daha kısa)
        
        # Her iş için hızlı eşleştirme
        for job_idx, job in enumerate(jobs):
            try:
                # Timeout kontrolü
                if time.time() - start_time > max_execution_time:
                    print(f"⚠️ Eşleştirme timeout'a uğradı ({max_execution_time}s)")
                    break
                
                if job_idx % 10 == 0:  # Her 10 işte bir progress
                    print(f"   📋 İş {job_idx + 1}/{len(jobs)} işleniyor...")
                
                # Hızlı skor hesaplama
                match_score = self._calculate_match_score_ultra_fast(
                    cv_skills, cv_technologies, cv_experience, cv_level, job
                )
                
                if match_score['score'] >= 15:  # Eşiği çok düşürdük (15%)
                    job_with_match = job.copy()
                    job_with_match.update(match_score)
                    matched_jobs.append(job_with_match)
            
            except Exception as e:
                print(f"❌ İş {job_idx + 1} hatası: {e}")
                continue
        
        # Skora göre sırala
        matched_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        total_time = time.time() - start_time
        print(f"✅ Eşleştirme tamamlandı: {total_time:.2f}s")
        print(f"📊 {len(matched_jobs)}/{len(jobs)} iş eşleşti (%{(len(matched_jobs)/len(jobs)*100):.1f})")
        
        return matched_jobs[:10]  # En iyi 10 eşleşme
    
    # Batch processing fonksiyonu kaldırıldı - artık kullanılmıyor
    
    def _calculate_match_score_ultra_fast(self, cv_skills: Set[str], cv_technologies: Set[str], 
                                        cv_experience: int, cv_level: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI destekli eşleşme skoru hesaplar - ÇOK ESNEK versiyon
        """
        try:
            title_lower = job['title'].lower()
            company_lower = job.get('company', '').lower()
            
            # Başlangıç skoru - her iş için temel puan
            base_score = 25  # Temel uyum puanı
            
            # Skill matching - daha esnek
            skill_score = 0
            matched_skills = []
            
            # CV'deki her skill için kontrol
            for skill in cv_skills:
                if skill in title_lower or skill in company_lower:
                    skill_score += 20  # Daha yüksek puan
                    matched_skills.append(skill)
            
            # Technology matching - daha esnek
            for tech in cv_technologies:
                if tech in title_lower or tech in company_lower:
                    skill_score += 15  # Teknoloji eşleşmesi
                    if tech not in matched_skills:
                        matched_skills.append(tech)
            
            # Genel teknoloji terimlerini kontrol et
            general_tech_terms = ['developer', 'engineer', 'programmer', 'software', 'full stack', 'backend', 'frontend']
            for term in general_tech_terms:
                if term in title_lower:
                    skill_score += 10  # Genel teknoloji terimi bonus
                    break
            
            # Experience level matching - çok esnek
            experience_score = 20  # Varsayılan deneyim skoru
            if cv_level == 'entry':
                # Entry level için tüm pozisyonları kabul et
                if any(word in title_lower for word in ['junior', 'trainee', 'intern', 'graduate']):
                    experience_score = 30  # Bonus
                elif 'senior' not in title_lower and 'lead' not in title_lower:
                    experience_score = 25  # Orta seviye uyum
            
            # Location matching - Türkiye için bonus
            location_score = 10  # Varsayılan lokasyon skoru
            location_lower = job.get('location', '').lower()
            if any(city in location_lower for city in ['istanbul', 'ankara', 'izmir', 'turkey', 'türkiye']):
                location_score = 20
            
            # Company tech bonus - teknoloji şirketleri için bonus
            company_bonus = 0
            tech_company_keywords = ['tech', 'software', 'teknoloji', 'yazılım', 'digital', 'ai', 'data']
            if any(keyword in company_lower for keyword in tech_company_keywords):
                company_bonus = 15
            
            # Total score hesapla
            total_score = min(100, base_score + skill_score + experience_score + location_score + company_bonus)
            
            # Minimum score garantisi - hiç eşleşme yoksa bile minimum puan ver
            if total_score < 25:
                total_score = 25
            
            # AI analiz (hızlı fallback)
            match_reasons = []
            if matched_skills:
                match_reasons.extend([f"{skill.title()} beceriniz bu pozisyona uygun" for skill in matched_skills[:2]])
            else:
                match_reasons.append("Genel teknoloji alanında deneyiminiz değerli")
            
            if any(word in title_lower for word in ['developer', 'engineer', 'programmer']):
                match_reasons.append("Yazılım geliştirme alanında çalışma fırsatı")
            
            missing_skills = ["Daha fazla proje deneyimi", "Portföy geliştirme", "Sektörel deneyim"]
            recommendations = ["CV'nizi güncellene", "GitHub profilinizi aktif tutun", "Açık kaynak projelere katkıda bulunun"]
            
            return {
                "score": total_score,
                "match_reasons": match_reasons[:3] if match_reasons else ["Teknoloji sektöründe gelişim fırsatı"],
                "missing_skills": missing_skills[:3],
                "recommendations": recommendations[:3]
            }
            
        except Exception as e:
            print(f"Skorlama hatası: {e}")
            # Fallback - her zaman en az bir miktar puan ver
            return {
                "score": 35,  # Minimum uyum skoru
                "match_reasons": ["Genel teknoloji alanında uyum"],
                "missing_skills": ["Proje deneyimi", "Teknik beceri gelişimi"],
                "recommendations": ["CV'nizi güncelleyin", "Projeler geliştirin"]
            }
    
    def _generate_ai_analysis(self, cv_skills: Set[str], cv_technologies: Set[str], 
                            cv_experience: int, cv_level: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI ile akıllı analiz yapar ve öneriler üretir
        """
        try:
            # AI prompt hazırla
            prompt = f"""
            CV analizi ve iş ilanı eşleştirmesi için akıllı öneriler üret.
            
            CV Bilgileri:
            - Teknik beceriler: {list(cv_skills)}
            - Teknolojiler: {list(cv_technologies)}
            - Deneyim yılı: {cv_experience}
            - Deneyim seviyesi: {cv_level}
            
            İş İlanı:
            - Pozisyon: {job['title']}
            - Şirket: {job['company']}
            - Lokasyon: {job['location']}
            
            Lütfen şu bilgileri JSON formatında döndür:
            {{
                "match_reasons": [
                    "CV'nizdeki hangi beceriler bu işe uygun (1-2 cümlelik açıklama)"
                ],
                "missing_skills": [
                    "Bu iş için gerekli olan ama CV'nizde eksik olan beceriler (1-2 cümlelik açıklama)"
                ],
                "recommendations": [
                    "Bu işe başvurmak için yapmanız gerekenler (1-2 cümlelik öneriler)"
                ]
            }}
            
            Önemli: Her öneri 1-2 cümlelik, pratik ve uygulanabilir olsun.
            """
            
            # AI'dan yanıt al
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON parse et
            import json
            try:
                # JSON kısmını bul
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                    
                    # Array'leri kontrol et ve düzelt
                    if not isinstance(analysis.get('match_reasons'), list):
                        analysis['match_reasons'] = ["CV'nizdeki beceriler bu pozisyona uygun"]
                    
                    if not isinstance(analysis.get('missing_skills'), list):
                        analysis['missing_skills'] = ["Temel programlama becerilerini geliştirin"]
                    
                    if not isinstance(analysis.get('recommendations'), list):
                        analysis['recommendations'] = ["CV'nizi güncelleyin ve deneyimlerinizi ekleyin"]
                    
                    # Maksimum 3 öneri
                    analysis['match_reasons'] = analysis['match_reasons'][:3]
                    analysis['missing_skills'] = analysis['missing_skills'][:3]
                    analysis['recommendations'] = analysis['recommendations'][:3]
                    
                    return analysis
                    
            except json.JSONDecodeError:
                pass
            
            # JSON parse edilemezse fallback
            return self._generate_fallback_analysis(cv_skills, cv_technologies, cv_experience, cv_level, job)
            
        except Exception as e:
            # AI hatası durumunda fallback
            return self._generate_fallback_analysis(cv_skills, cv_technologies, cv_experience, cv_level, job)
    
    def _generate_fallback_analysis(self, cv_skills: Set[str], cv_technologies: Set[str], 
                                  cv_experience: int, cv_level: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI başarısız olursa kullanılacak fallback analiz
        """
        title_lower = job['title'].lower()
        
        # Match reasons
        match_reasons = []
        if cv_skills:
            for skill in list(cv_skills)[:2]:
                if skill in title_lower:
                    match_reasons.append(f"{skill.title()} beceriniz bu pozisyon için uygun")
        
        if not match_reasons:
            match_reasons = ["CV'nizdeki teknik beceriler bu alanda değerli"]
        
        # Missing skills
        missing_skills = []
        if 'python' in title_lower and 'python' not in cv_skills:
            missing_skills.append("Python programlama dili öğrenmeniz gerekiyor")
        if 'javascript' in title_lower and 'javascript' not in cv_skills:
            missing_skills.append("JavaScript becerilerinizi geliştirmeniz önerilir")
        if 'sql' in title_lower and 'sql' not in cv_skills:
            missing_skills.append("Veritabanı yönetimi konusunda deneyim kazanın")
        
        if not missing_skills:
            missing_skills = ["Bu alanda daha fazla deneyim kazanmanız gerekiyor"]
        
        # Recommendations
        recommendations = []
        if cv_level == 'entry' and 'senior' in title_lower:
            recommendations.append("Önce junior pozisyonlarda deneyim kazanın")
        elif cv_level == 'senior' and 'junior' in title_lower:
            recommendations.append("Daha kıdemli pozisyonlara başvurun")
        else:
            recommendations.append("CV'nizi güncelleyin ve projelerinizi ekleyin")
        
        recommendations.append("LinkedIn profilinizi aktif tutun")
        recommendations.append("Sektördeki güncel teknolojileri takip edin")
        
        return {
            "match_reasons": match_reasons[:3],
            "missing_skills": missing_skills[:3],
            "recommendations": recommendations[:3]
        }
    
    def _calculate_match_score_fast(self, cv_skills: Set[str], cv_technologies: Set[str], 
                                  cv_experience: int, cv_level: str, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hızlı eşleşme skoru hesaplar (AI kullanmadan) - Optimized
        """
        try:
            title_lower = job['title'].lower()
            
            # Skill matching - Optimized with early break
            skill_score = 0
            matched_skills = []
            missing_skills = []
            
            # Limit iterations to prevent hanging
            max_skill_checks = 100
            skill_check_count = 0
            
            for skill_category, skill_list in self.skill_mapping.items():
                if skill_check_count >= max_skill_checks:
                    break
                    
                for skill in skill_list:
                    if skill_check_count >= max_skill_checks:
                        break
                        
                    skill_check_count += 1
                    if skill in title_lower:
                        if skill in cv_skills or skill in cv_technologies:
                            skill_score += 10
                            matched_skills.append(skill)
                        else:
                            missing_skills.append(skill)
            
            # Experience level matching - Simplified
            experience_score = 0
            title_words = title_lower.split()
            
            if cv_level == 'entry':
                if any(word in title_words for word in ['junior', 'entry', 'trainee', 'intern']):
                    experience_score = 30
            elif cv_level == 'junior':
                if any(word in title_words for word in ['junior', 'entry', 'mid']):
                    experience_score = 30
            elif cv_level == 'mid':
                if any(word in title_words for word in ['mid', 'senior']):
                    experience_score = 30
            elif cv_level == 'senior':
                if 'senior' in title_words:
                    experience_score = 30
            
            # Location matching - Optimized
            location_lower = job['location'].lower()
            location_score = 10 if any(city in location_lower for city in self.turkish_cities) else 5
            
            # Total score
            total_score = min(100, skill_score + experience_score + location_score)
            
            return {
                "score": total_score,
                "match_reasons": [f"{skill} becerisi uyumlu" for skill in matched_skills[:3]],
                "missing_skills": missing_skills[:5],
                "recommendations": [f"{skill} öğren" for skill in missing_skills[:3]]
            }
            
        except Exception as e:
            print(f"Match score calculation error: {e}")
            # Fallback score
            return {
                "score": 50,
                "match_reasons": ["Genel uyum"],
                "missing_skills": ["Detay analiz edilemedi"],
                "recommendations": ["İlan detaylarını incele"],
                "salary_estimate": "20000-30000 TL"
            }
    
    # Salary estimation function removed - no longer needed
    
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
