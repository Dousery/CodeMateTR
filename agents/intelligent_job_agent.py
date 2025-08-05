#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı - Optimized Version
CV analizi + SerpAPI Google Jobs + Gemini AI eşleştirme
"""

import os
import json
import time
import re

from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import requests
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
from dotenv import load_dotenv
from functools import lru_cache
from dataclasses import dataclass
import pathlib
import io
import PyPDF2



load_dotenv()

@dataclass
class CVData:
    """CV'den çıkarılan veri yapısı"""
    name: str
    email: str
    phone: str
    skills: List[str]
    experience_years: int
    education: str
    location: str
    job_titles: List[str]
    languages: List[str]
    summary: str
    certifications: List[str]

class GeminiCVExtractor:
    """Gemini API kullanarak CV'den bilgi çıkarma sınıfı (sadece PDF için)"""
    
    def __init__(self, gemini_api_key: str):
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        else:
            raise ValueError("Gemini API anahtarı sağlanmalıdır.")
        
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        self.extraction_prompt = """
Bu CV dosyasından aşağıdaki bilgileri JSON formatında çıkar. Eğer bir bilgi bulunamazsa null değeri ver:

{
  "name": "Kişinin tam adı",
  "email": "Email adresi", 
  "phone": "Türkiye telefon numarası",
  "location": "Şehir/Konum bilgisi",
  "summary": "Kısa özet/profil bilgisi",
  "experience_years": "Toplam iş deneyimi yılı (sayı olarak)",
  "current_job_title": "Mevcut/son iş unvanı",
  "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "Docker", "AWS", "MongoDB", "REST API"],
  "job_titles": ["Software Developer", "Full Stack Developer", "Backend Developer"],
  "education": "En yüksek eğitim durumu",
  "languages": ["Türkçe", "İngilizce"],
  "certifications": ["Sertifikalar"]
}

ÖNEMLİ TALİMATLAR:
1. skills alanında CV'de geçen TÜM teknik becerileri, programlama dillerini, framework'leri, araçları ve teknolojileri listele
2. CV'de hiç beceri yoksa bile en az 3-5 genel beceri ekle (örn: "Problem Solving", "Team Work", "Communication")
3. Boş liste döndürme, mutlaka beceri listesi ver
4. CV'deki her teknik terimi, yazılım adını, araç adını beceri olarak ekle

ÖRNEK BECERİLER:
- Programlama Dilleri: Python, Java, JavaScript, C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin
- Framework'ler: React, Angular, Vue.js, Django, Flask, Spring, .NET, Laravel, Express.js
- Veritabanları: MySQL, PostgreSQL, MongoDB, Redis, SQLite, Oracle
- Araçlar: Git, Docker, Kubernetes, Jenkins, Jira, AWS, Azure, Google Cloud
- Diğer: REST API, GraphQL, Microservices, Agile, Scrum, DevOps

Sadece JSON formatında yanıt ver, başka açıklama ekleme. Türkçe karakterleri düzgün kullan.
"""

    def extract_from_file(self, file_path: str) -> CVData:
        filepath = pathlib.Path(file_path)
        if not filepath.exists() or filepath.suffix.lower() != '.pdf':
            raise ValueError(f"Geçersiz dosya. Lütfen var olan bir PDF dosyası sağlayın: {file_path}")
        
        try:
            file_part = types.Part(
                mime_type='application/pdf',
                data=filepath.read_bytes()
            )
            response = self.model.generate_content([self.extraction_prompt, file_part])
            
            cv_data_dict = self._parse_gemini_response(response.text)
            return self._dict_to_cvdata(cv_data_dict)
            
        except Exception as e:
            print(f"Gemini API hatası: {e}")
            return self._empty_cvdata()
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        try:
            json_text = re.sub(r'```json\n|```', '', response_text, flags=re.DOTALL).strip()
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse hatası: {e}")
            return {}
    
    def _dict_to_cvdata(self, data: Dict) -> CVData:
        # current_job_title'ı job_titles listesine ekle
        job_titles = data.get('job_titles', [])
        current_job_title = data.get('current_job_title', '')
        if current_job_title and current_job_title not in job_titles:
            job_titles.insert(0, current_job_title)
        
        # skills alanını kontrol et ve boşsa varsayılan değerler ekle
        skills = data.get('skills', [])
        if not skills or len(skills) == 0:
            skills = ["Software Development", "Problem Solving", "Team Work", "Communication", "Learning Ability"]
        elif len(skills) < 3:
            # Eğer çok az beceri varsa, genel beceriler ekle
            default_skills = ["Problem Solving", "Team Work", "Communication"]
            for skill in default_skills:
                if skill not in skills:
                    skills.append(skill)
        
        return CVData(
            name=data.get('name', 'Bilinmiyor'),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            skills=skills,
            experience_years=data.get('experience_years', 0),
            education=data.get('education', ''),
            location=data.get('location', ''),
            job_titles=job_titles,
            languages=data.get('languages', []),
            summary=data.get('summary', ''),
            certifications=data.get('certifications', [])
        )
    
    def _empty_cvdata(self) -> CVData:
        return CVData(
            name="", email="", phone="", skills=[], experience_years=0,
            education="", location="", job_titles=[], languages=[],
            summary="", certifications=[]
        )

class SerpAPIGoogleJobs:
    """SerpAPI kullanarak Google Jobs API'dan iş ilanları çeker."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://serpapi.com/search"
        
    def search_jobs(self, keywords: str, location: str, max_results: int = 20) -> List[Dict]:
        """
        Belirtilen anahtar kelimeler ve konum için iş ilanlarını arar.
        
        Args:
            keywords: Aranacak anahtar kelimeler (örn. "Python Developer").
            location: İş konum bilgisi (örn. "İstanbul, Türkiye").
            max_results: Maksimum sonuç sayısı.
        
        Returns:
            API'dan dönen iş ilanlarının listesi.
        """
        if not self.api_key:
            raise ValueError("SerpAPI anahtarı sağlanmalıdır.")
            
        params = {
            "api_key": self.api_key,
            "engine": "google_jobs",
            "q": keywords,
            "location": location,
            "chips": f"date_posted:all",
            "hl": "tr",
            "gl": "tr"
        }
        
        try:
            response = requests.get(self.endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            job_results = data.get("jobs_results", [])
            return job_results[:max_results]
        
        except requests.exceptions.HTTPError as err:
            print(f"HTTP Hatası: {err}")
            return []
        except Exception as e:
            print(f"SerpAPI hatası: {e}")
            return []

class IntelligentJobAgent:
    def __init__(self):
        # Gemini AI setup
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY çevre değişkeni bulunamadı")
        
        # SerpAPI setup
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        
        # Traditional Gemini setup
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # New Gemini client for PDF processing
        self.genai_client = google_genai.Client(api_key=self.gemini_api_key)
        
        # Initialize CV extractor and job finder
        self.cv_extractor = GeminiCVExtractor(self.gemini_api_key)
        if self.serpapi_key:
            self.job_finder = SerpAPIGoogleJobs(self.serpapi_key)
        else:
            self.job_finder = None
            print("⚠️ SERPAPI_KEY bulunamadı, Google Jobs API kullanılamayacak")
        
        # Performance optimizations
        self.cache = {}
        self.cache_ttl = 3600  # 1 saat cache
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        
        
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
    
    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Gemini API yanıtını JSON'a çevirir"""
        try:
            json_text = re.sub(r'```json\n|```', '', response_text, flags=re.DOTALL).strip()
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"JSON parse hatası: {e}")
            return {}
    
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
            print(f"Gemini API'ye PDF gönderiliyor...")
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
            print(f"Gemini API yanıtı alındı: {response.text[:200]}...")
            
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
            print(f"Hata detayı: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            # PDF'den metin çıkarmayı dene
            try:
                print("PDF'den metin çıkarma deneniyor...")
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
                cv_text = ""
                for page in pdf_reader.pages:
                    cv_text += page.extract_text() + "\n"
                
                print(f"PDF'den çıkarılan metin uzunluğu: {len(cv_text)}")
                if len(cv_text.strip()) > 50:  # Yeterli metin varsa
                    print("Text-based CV analizi yapılıyor...")
                    text_analysis = self.analyze_cv_with_gemini(cv_text)
                    self._cache_analysis(cv_hash, text_analysis)
                    return text_analysis
                else:
                    print("PDF'den yeterli metin çıkarılamadı")
            except Exception as text_error:
                print(f"PDF metin çıkarma hatası: {text_error}")
            
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
    
    def analyze_cv_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        PDF dosyasından CV analizi yapar ve uygun işleri bulur
        """
        try:
            print("CV analizi için Gemini API'ya gönderiliyor...")
            cv_data = self.cv_extractor.extract_from_file(file_path)
            
            print(f"CV Analiz Sonuçları:")
            print(f"- Ad: {cv_data.name}")
            print(f"- Skills: {cv_data.skills}")
            print(f"- Job Titles: {cv_data.job_titles}")
            print(f"- Experience: {cv_data.experience_years} yıl")
            
            # CVData'yı Dict formatına çevir
            cv_analysis = {
                "kişisel_bilgiler": {
                    "ad_soyad": cv_data.name,
                    "email": cv_data.email,
                    "telefon": cv_data.phone,
                    "lokasyon": cv_data.location
                },
                "deneyim_yılı": cv_data.experience_years,
                "teknik_beceriler": cv_data.skills,
                "yazılım_dilleri": [skill for skill in cv_data.skills if any(lang in skill.lower() for lang in ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin'])],
                "teknolojiler": cv_data.skills,
                "eğitim": [cv_data.education] if cv_data.education else [],
                "sertifikalar": cv_data.certifications,
                "diller": cv_data.languages,
                "deneyim_seviyesi": self._determine_experience_level(cv_data.experience_years),
                "ana_uzmanlık_alanı": cv_data.job_titles[0] if cv_data.job_titles else "Software Developer",
                "uygun_iş_alanları": cv_data.job_titles if cv_data.job_titles else ["Software Developer"],
                "güçlü_yönler": cv_data.skills[:5],
                "cv_kalitesi": "iyi",
                "öneriler": []
            }
            
            print(f"✅ CV analizi tamamlandı - {len(cv_data.skills)} beceri bulundu")
            return cv_analysis
            
        except Exception as e:
            print(f"CV dosya analizi hatası: {e}")
            return self._fallback_cv_analysis("")
    
    def _determine_experience_level(self, experience_years: int) -> str:
        """Deneyim yılına göre seviye belirler"""
        if experience_years == 0:
            return "entry"
        elif experience_years <= 2:
            return "junior"
        elif experience_years <= 5:
            return "mid"
        else:
            return "senior"
    
    def find_jobs_with_serpapi(self, cv_analysis: Dict[str, Any], max_results: int = 20) -> List[Dict[str, Any]]:
        """
        SerpAPI kullanarak CV'ye uygun işleri arar
        """
        if not self.job_finder:
            print("⚠️ SerpAPI kullanılamıyor, fallback moduna geçiliyor...")
            return self._fallback_job_search(
                cv_analysis.get('uygun_iş_alanları', ['Software Developer']),
                cv_analysis.get('kişisel_bilgiler', {}).get('lokasyon', 'Türkiye'),
                max_results
            )
        
        try:
            # CV'den arama terimleri oluştur
            skills = cv_analysis.get('teknik_beceriler', [])
            job_titles = cv_analysis.get('uygun_iş_alanları', [])
            location = cv_analysis.get('kişisel_bilgiler', {}).get('lokasyon', 'Türkiye')
            
            # Arama terimlerini birleştir
            search_keywords = " ".join(skills[:3] + (job_titles[:1] if job_titles else []))
            
            if not search_keywords:
                search_keywords = "Software Developer"
            
            print(f"SerpAPI'den iş ilanları aranıyor: '{search_keywords}' ({location})")
            
            # SerpAPI ile iş ara
            jobs = self.job_finder.search_jobs(
                keywords=search_keywords,
                location=location,
                max_results=max_results
            )
            
            # İşleri formatla
            formatted_jobs = []
            for job in jobs:
                formatted_job = {
                    'id': job.get('job_id', f"serpapi_{hash(job.get('title', ''))}"),
                    'title': job.get('title', 'İş İlanı'),
                    'company': job.get('company_name', 'Şirket'),
                    'location': job.get('location', location),
                    'description': job.get('description', ''),
                    'requirements': job.get('job_highlights', {}).get('Qualifications', []),
                    'salary': job.get('salary', 'Belirtilmemiş'),
                    'url': job.get('related_links', [{}])[0].get('link', 'https://google.com/jobs'),
                    'posted_date': job.get('posted_at', ''),
                    'source': 'Google Jobs (SerpAPI)',
                    'match_score': 85  # SerpAPI işleri için yüksek skor
                }
                formatted_jobs.append(formatted_job)
            
            print(f"✅ SerpAPI'den {len(formatted_jobs)} iş ilanı bulundu")
            return formatted_jobs
            
        except Exception as e:
            print(f"SerpAPI iş arama hatası: {e}")
            return self._fallback_job_search(
                cv_analysis.get('uygun_iş_alanları', ['Software Developer']),
                cv_analysis.get('kişisel_bilgiler', {}).get('lokasyon', 'Türkiye'),
                max_results
            )
    
    def process_cv_and_find_jobs(self, cv_file_path: str, max_results: int = 20) -> Dict[str, Any]:
        """
        PDF CV'yi analiz eder ve uygun iş ilanlarını bulur (Ana metod)
        """
        try:
            # 1. CV Analizi
            cv_analysis = self.analyze_cv_from_file(cv_file_path)
            
            if not cv_analysis:
                return {'error': 'CV analizi başarısız', 'success': False}
            
            # 2. İş Arama (SerpAPI öncelikli, fallback ile)
            jobs = self.find_jobs_with_serpapi(cv_analysis, max_results)
            
            # 3. CV-İş Eşleştirme
            matched_jobs = self.match_cv_with_jobs(cv_analysis, jobs)
            
            return {
                'success': True,
                'cv_analysis': cv_analysis,
                'job_results': matched_jobs,
                'stats': {
                    'total_found': len(jobs),
                    'matched': len(matched_jobs),
                    'search_method': 'SerpAPI' if self.job_finder else 'Fallback'
                }
            }
            
        except Exception as e:
            print(f"CV işleme hatası: {e}")
            return {'error': f'İşlem hatası: {str(e)}', 'success': False}
    
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
        """CV analizi başarısız olursa AI ile fallback"""
        try:
            # AI ile beceri çıkarma
            skills_prompt = f"""
            Bu CV metninden teknik becerileri çıkar:
            
            CV METNİ:
            {cv_text if cv_text else "Software Developer CV"}
            
            Aşağıdaki becerileri JSON formatında döndür:
            {{
                "skills": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "Docker", "AWS", "MongoDB", "REST API"],
                "job_titles": ["Software Developer", "Full Stack Developer", "Backend Developer"],
                "experience_years": 0,
                "education": "Bachelor's Degree",
                "location": "Turkey"
            }}
            
            ÖNEMLİ: Eğer CV'de hiç beceri yoksa bile en az 5 genel beceri ekle (Problem Solving, Team Work, Communication, Learning Ability, Software Development).
            Sadece JSON döndür, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(skills_prompt)
            ai_data = self._parse_gemini_response(response.text)
            
            skills = ai_data.get('skills', [])
            job_titles = ai_data.get('job_titles', [])
            experience_years = ai_data.get('experience_years', 0)
            education = ai_data.get('education', '')
            location = ai_data.get('location', '')
            
            # Eğer AI'dan beceri gelmezse varsayılan beceriler
            if not skills:
                skills = ["Software Development", "Problem Solving", "Team Work", "Communication", "Learning Ability"]
            
            # Email ve telefon çıkarma
            email = self.email_pattern.search(cv_text) if cv_text else None
            phone = self.phone_pattern.search(cv_text) if cv_text else None
        
        except Exception as e:
            print(f"AI fallback hatası: {e}")
            # AI başarısız olursa varsayılan değerler
            skills = ["Software Development", "Problem Solving", "Team Work", "Communication", "Learning Ability"]
            job_titles = ["Software Developer"]
            experience_years = 0
            education = ""
            location = ""
            email = None
            phone = None
        
        return {
            "kişisel_bilgiler": {
                "ad_soyad": "Belirtilmemiş",
                "email": email.group() if email else "Belirtilmemiş",
                "telefon": phone.group() if phone else "Belirtilmemiş",
                "lokasyon": location or "Belirtilmemiş"
            },
            "deneyim_yılı": experience_years,
            "toplam_is_deneyimi": "Belirtilmemiş",
            "staj_deneyimi": "Belirtilmemiş",
            "teknik_beceriler": skills,
            "yazılım_dilleri": [skill for skill in skills if skill.lower() in ['python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin']],
            "teknolojiler": [skill for skill in skills if skill.lower() in ['react', 'angular', 'vue.js', 'django', 'flask', 'spring', '.net', 'laravel', 'express.js']],
            "veritabanları": [skill for skill in skills if skill.lower() in ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle']],
            "eğitim": [education] if education else ["Belirtilmemiş"],
            "sertifikalar": [],
            "projeler": [],
            "diller": ["Türkçe"],
            "deneyim_seviyesi": self._determine_experience_level(experience_years),
            "ana_uzmanlık_alanı": job_titles[0] if job_titles else "Software Developer",
            "uygun_iş_alanları": job_titles if job_titles else ["Software Developer"],
            "güçlü_yönler": skills[:3],
            "gelişim_alanları": ["Profesyonel deneyim", "Proje portföyü"],
            "uzaktan_çalışma_uygunluğu": True,
            "sektör_tercihi": ["Teknoloji"],
            "cv_kalitesi": "orta",
            "öneriler": [
                "CV'ye daha detaylı kişisel bilgiler ekleyin",
                "Proje portföyünüzü geliştirin",
                "Teknik becerilerinizi belirgin şekilde listeleyin"
            ]
        }
    

    

    

    

    

    

    

    

    

    

    
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
    
    def _fallback_job_search(self, job_areas: List[str], location: str = "Istanbul, Turkey", max_per_search: int = 10) -> List[Dict[str, Any]]:
        """
        Selenium başarısız olduğunda kullanılan fallback iş arama yöntemi
        Gemini AI ile simüle edilmiş iş ilanları oluşturur
        """
        print("🔄 Fallback iş arama modu aktif - AI ile simüle edilmiş iş ilanları oluşturuluyor...")
        
        fallback_jobs = []
        
        for job_area in job_areas:
            try:
                # Her iş alanı için simüle edilmiş iş ilanları oluştur
                prompt = f"""
                Aşağıdaki iş alanı için {max_per_search} adet gerçekçi iş ilanı oluştur:
                
                İş Alanı: {job_area}
                Lokasyon: {location}
                
                Her iş ilanı için şu bilgileri içeren JSON formatında yanıt ver:
                - title: İş başlığı
                - company: Şirket adı
                - location: Lokasyon
                - description: İş açıklaması (kısa)
                - requirements: Gereksinimler (liste halinde)
                - salary: Maaş aralığı (opsiyonel)
                - url: Şirket web sitesi URL'i
                - posted_date: İlan tarihi
                
                Sadece JSON formatında yanıt ver, başka açıklama ekleme.
                """
                
                response = self.model.generate_content(prompt)
                json_text = response.text.strip()
                
                # JSON parsing
                if json_text.startswith('```json'):
                    json_text = json_text[7:-3]
                elif json_text.startswith('```'):
                    json_text = json_text[3:-3]
                
                jobs = json.loads(json_text)
                
                # Eğer tek bir iş ise listeye çevir
                if isinstance(jobs, dict):
                    jobs = [jobs]
                
                # Her işe unique ID ekle
                for job in jobs:
                    job['id'] = f"fallback_{hash(job.get('title', '') + job.get('company', ''))}"
                    job['source'] = 'AI Generated'
                    job['match_score'] = 85  # Fallback işler için yüksek skor
                
                fallback_jobs.extend(jobs)
                print(f"✅ '{job_area}' için {len(jobs)} fallback iş ilanı oluşturuldu")
                
            except Exception as e:
                print(f"❌ Fallback iş oluşturma hatası ({job_area}): {e}")
                # Basit fallback iş oluştur
                fallback_jobs.append({
                    'id': f"fallback_{job_area}_{len(fallback_jobs)}",
                    'title': f"{job_area}",
                    'company': 'Çeşitli Şirketler',
                    'location': location,
                    'description': f'{job_area} pozisyonu için deneyimli kişiler aranmaktadır.',
                    'requirements': ['İlgili alanda deneyim', 'Takım çalışması', 'Problem çözme becerisi'],
                    'salary': 'Müzakere edilebilir',
                    'url': 'https://linkedin.com/jobs',
                    'posted_date': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'AI Generated',
                    'match_score': 80
                })
        
        print(f"📊 Toplamda {len(fallback_jobs)} fallback iş ilanı oluşturuldu")
        return fallback_jobs




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
        
        # 2. İş İlanları Arama
        print("\n🔍 İş ilanları aranıyor...")
        jobs = agent.find_jobs_with_serpapi(
            cv_analysis=cv_analysis,
            max_results=5
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
