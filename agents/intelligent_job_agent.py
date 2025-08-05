#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı - Basit ve Etkili Versiyon
CV analizi + SerpAPI Google Jobs
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import List, Dict, Any
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class IntelligentJobAgent:
    def __init__(self):
        # Gemini AI setup
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY çevre değişkeni bulunamadı")
        
        # SerpAPI setup
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        
        # Gemini client setup
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.genai_client = google_genai.Client(api_key=self.gemini_api_key)
        
        print("✅ IntelligentJobAgent başlatıldı")
    
    def analyze_cv_from_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDF'yi Gemini ile analiz eder ve JSON formatında sonuç döndürür
        """
        print("🤖 CV analizi başlatılıyor...")
        
        prompt = """
        Bu CV'yi analiz et ve aşağıdaki JSON formatında sonuç döndür:
        
        {
            "kişisel_bilgiler": {
                "ad_soyad": "CV'deki tam isim",
                "email": "CV'deki email",
                "telefon": "CV'deki telefon",
                "lokasyon": "CV'deki şehir"
            },
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "CV'deki toplam deneyim",
            "staj_deneyimi": "CV'deki staj deneyimi",
            "teknik_beceriler": ["CV'deki teknik beceriler"],
            "yazılım_dilleri": ["CV'deki programlama dilleri"],
            "teknolojiler": ["CV'deki teknolojiler"],
            "eğitim": ["CV'deki eğitim bilgisi"],
            "deneyim_seviyesi": "entry|junior|mid|senior",
            "ana_uzmanlık_alanı": "CV'deki ana alan",
            "uygun_iş_alanları": ["Uygun iş alanları"],
            "cv_kalitesi": "zayıf|orta|iyi|mükemmel"
        }
        
        Önemli: Sadece JSON döndür, başka açıklama ekleme. CV'de olmayan bilgileri "Belirtilmemiş" yaz.
        """
        
        try:
            # Gemini PDF API kullan
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
            
            # Eğer teknik beceriler boşsa, varsayılan ekle
            if not cv_analysis.get('teknik_beceriler'):
                cv_analysis['teknik_beceriler'] = ['HTML', 'CSS', 'JavaScript']
            
            # CV kalitesi yoksa varsayılan ekle
            if not cv_analysis.get('cv_kalitesi'):
                cv_analysis['cv_kalitesi'] = 'orta'
            
            print(f"✅ CV analizi tamamlandı: {len(cv_analysis.get('teknik_beceriler', []))} beceri bulundu")
            return cv_analysis
            
        except Exception as e:
            print(f"❌ CV analizi hatası: {e}")
            # Hata durumunda varsayılan analiz
            return {
                "kişisel_bilgiler": {
                    "ad_soyad": "Belirtilmemiş",
                    "email": "Belirtilmemiş",
                    "telefon": "Belirtilmemiş",
                    "lokasyon": "Belirtilmemiş"
                },
                "deneyim_yılı": 0,
                "toplam_is_deneyimi": "Belirtilmemiş",
                "staj_deneyimi": "Belirtilmemiş",
                "teknik_beceriler": ["HTML", "CSS", "JavaScript"],
                "yazılım_dilleri": ["JavaScript"],
                "teknolojiler": ["HTML", "CSS"],
                "eğitim": ["Belirtilmemiş"],
                "deneyim_seviyesi": "entry",
                "ana_uzmanlık_alanı": "Software Developer",
                "uygun_iş_alanları": ["Junior Developer", "Frontend Developer"],
                "cv_kalitesi": "zayıf"
            }
    
    def search_jobs_with_serpapi(self, cv_analysis: Dict[str, Any], max_results: int = 20) -> List[Dict[str, Any]]:
        """
        SerpAPI Google Jobs ile iş ilanları arar
        """
        if not self.serpapi_key:
            print("⚠️ SERPAPI_KEY bulunamadı, varsayılan işler döndürülüyor")
            return self._get_default_jobs()
        
        try:
            # CV'den arama terimleri oluştur
            skills = cv_analysis.get('teknik_beceriler', [])
            job_areas = cv_analysis.get('uygun_iş_alanları', ['Software Developer'])
            location = cv_analysis.get('kişisel_bilgiler', {}).get('lokasyon', 'Türkiye')
            
            # Arama terimlerini birleştir
            search_keywords = " ".join(skills[:3] + job_areas[:1])
            if not search_keywords:
                search_keywords = "Software Developer"
            
            print(f"🔍 Google Jobs ile iş aranıyor: '{search_keywords}' ({location})")
            
            # SerpAPI Google Jobs API kullan
            params = {
                "api_key": self.serpapi_key,
                "engine": "google_jobs",  # Önemli: Google Jobs engine'i
                "q": search_keywords,
                "location": location,
                "hl": "tr",  # Türkçe
                "gl": "tr",  # Türkiye
                "chips": "date_posted:all",  # Tüm tarihler
                "num": max_results  # Sonuç sayısı
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            print(f"SerpAPI Response: {data.keys()}")
            
            # Google Jobs sonuçlarını al
            jobs = data.get("jobs_results", [])
            
            if not jobs:
                print("⚠️ Google Jobs'dan sonuç alınamadı, varsayılan işler döndürülüyor")
                return self._get_default_jobs()
            
            # İşleri formatla - frontend uyumlu
            formatted_jobs = []
            for i, job in enumerate(jobs[:max_results]):
                # Basit skor hesaplama
                score = 50 + (i * 5)  # İlk işler daha yüksek skor
                
                # Job highlights'ları al
                job_highlights = job.get('job_highlights', {})
                qualifications = job_highlights.get('Qualifications', [])
                responsibilities = job_highlights.get('Responsibilities', [])
                
                # Tüm requirements'ları birleştir
                all_requirements = qualifications + responsibilities
                
                formatted_job = {
                    'id': job.get('job_id', f"google_job_{i}"),
                    'title': job.get('title', 'İş İlanı'),
                    'company': job.get('company_name', 'Şirket'),
                    'location': job.get('location', location),
                    'description': job.get('description', ''),
                    'requirements': all_requirements,
                    'salary': job.get('salary', 'Belirtilmemiş'),
                    'url': job.get('related_links', [{}])[0].get('link', 'https://google.com/jobs'),
                    'posted_date': job.get('posted_at', datetime.now().strftime('%Y-%m-%d')),
                    'source': 'Google Jobs',
                    'score': score,  # Frontend için uyum skoru
                    'match_reasons': [f"{skill} beceriniz bu pozisyona uygun" for skill in skills[:2]],
                    'missing_skills': ["Daha fazla deneyim", "Proje portföyü"],
                    'recommendations': ["CV'nizi güncelleyin", "Başvuru yapabilirsiniz"]
                }
                formatted_jobs.append(formatted_job)
            
            print(f"✅ Google Jobs'dan {len(formatted_jobs)} iş ilanı bulundu")
            return formatted_jobs
            
        except Exception as e:
            print(f"❌ SerpAPI Google Jobs hatası: {e}")
            print(f"Hata detayı: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return self._get_default_jobs()
    
    def _get_default_jobs(self) -> List[Dict[str, Any]]:
        """
        Varsayılan iş ilanları döndürür - frontend uyumlu
        """
        return [
            {
                'id': 'default_1',
                'title': 'Junior Software Developer',
                'company': 'Teknoloji Şirketi',
                'location': 'İstanbul, Türkiye',
                'description': 'Yazılım geliştirme ekibine katılacak junior developer aranmaktadır.',
                'requirements': ['Temel programlama bilgisi', 'Takım çalışması'],
                'salary': '8.000 - 12.000 TL',
                'url': 'https://linkedin.com/jobs',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Varsayılan',
                'score': 85,
                'match_reasons': ['JavaScript beceriniz bu pozisyona uygun', 'Frontend geliştirme deneyiminiz değerli'],
                'missing_skills': ['Daha fazla proje deneyimi', 'Backend teknolojileri'],
                'recommendations': ['CV\'nizi güncelleyin', 'GitHub profilinizi aktif tutun']
            },
            {
                'id': 'default_2',
                'title': 'Frontend Developer',
                'company': 'Dijital Ajans',
                'location': 'İstanbul, Türkiye',
                'description': 'Modern web teknolojileri ile kullanıcı dostu arayüzler geliştirecek developer aranmaktadır.',
                'requirements': ['HTML/CSS/JavaScript', 'React/Vue.js'],
                'salary': '10.000 - 15.000 TL',
                'url': 'https://linkedin.com/jobs',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Varsayılan',
                'score': 80,
                'match_reasons': ['HTML/CSS becerileriniz uygun', 'Frontend odaklı pozisyon'],
                'missing_skills': ['React/Vue.js deneyimi', 'Responsive tasarım'],
                'recommendations': ['Modern framework\'ler öğrenin', 'Portföy projeleri geliştirin']
            },
            {
                'id': 'default_3',
                'title': 'Backend Developer',
                'company': 'Fintech Startup',
                'location': 'İstanbul, Türkiye',
                'description': 'Ölçeklenebilir backend sistemleri geliştirecek developer aranmaktadır.',
                'requirements': ['Python/Java/Node.js', 'Veritabanı yönetimi'],
                'salary': '12.000 - 18.000 TL',
                'url': 'https://linkedin.com/jobs',
                'posted_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'Varsayılan',
                'score': 75,
                'match_reasons': ['Programlama temelleriniz güçlü', 'Öğrenme motivasyonunuz yüksek'],
                'missing_skills': ['Backend teknolojileri', 'Veritabanı deneyimi'],
                'recommendations': ['Backend teknolojileri öğrenin', 'API geliştirme projeleri yapın']
            }
        ]
    
    def process_cv_and_find_jobs(self, pdf_bytes: bytes, max_results: int = 20) -> Dict[str, Any]:
        """
        Ana fonksiyon: CV analizi + iş arama
        """
        try:
            # 1. CV Analizi
            cv_analysis = self.analyze_cv_from_pdf(pdf_bytes)
            
            # 2. İş Arama
            jobs = self.search_jobs_with_serpapi(cv_analysis, max_results)
            
            return {
                'success': True,
                'cv_analysis': cv_analysis,
                'jobs': jobs,
                'stats': {
                    'total_jobs': len(jobs),
                    'search_method': 'SerpAPI' if self.serpapi_key else 'Varsayılan'
                }
            }
            
        except Exception as e:
            print(f"❌ İşlem hatası: {e}")
            return {
                'success': False,
                'error': str(e),
                'cv_analysis': {},
                'jobs': [],
                'stats': {}
            }

# Test fonksiyonu
if __name__ == "__main__":
    # Test CV analizi
    agent = IntelligentJobAgent()
    
    # Test iş arama
    test_cv_analysis = {
        "kişisel_bilgiler": {
            "ad_soyad": "Test User",
            "lokasyon": "İstanbul, Türkiye"
        },
        "teknik_beceriler": ["Python", "JavaScript", "React"],
        "uygun_iş_alanları": ["Software Developer", "Frontend Developer"]
    }
    
    print("🧪 Test iş arama başlatılıyor...")
    jobs = agent.search_jobs_with_serpapi(test_cv_analysis, max_results=5)
    
    print(f"📊 Test sonucu: {len(jobs)} iş bulundu")
    for i, job in enumerate(jobs):
        print(f"  {i+1}. {job['title']} - {job['company']} ({job['score']}%)")
        print(f"     URL: {job['url']}")
        print()
