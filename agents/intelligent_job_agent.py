#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı - JSearch API ile
CV analizi + JSearch API
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv

load_dotenv()

class IntelligentJobAgent:
    def __init__(self):
        # Gemini AI setup
        load_dotenv()
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            print("⚠️ GEMINI_API_KEY bulunamadı!")
        
        genai.configure(api_key=gemini_api_key)
        self.genai_client = genai
        
        # JSearch API setup
        self.jsearch_api_key = os.getenv('JSEARCH_API_KEY')
        if not self.jsearch_api_key:
            print("⚠️ JSEARCH_API_KEY bulunamadı!")
        else:
            print("✅ JSearch API hazır")
        
        # JSearch API endpoints
        self.jsearch_url = "https://jsearch.p.rapidapi.com/search"
        self.jsearch_headers = {
            "x-rapidapi-key": self.jsearch_api_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
    
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
            # Varsayılan CV analizi döndür
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
                "teknolojiler": ["Web Development"],
                "eğitim": ["Belirtilmemiş"],
                "deneyim_seviyesi": "entry",
                "ana_uzmanlık_alanı": "Web Development",
                "uygun_iş_alanları": ["Frontend Developer", "Web Developer", "JavaScript Developer"],
                "cv_kalitesi": "orta"
            }
    
    def search_jobs_with_jsearch(self, cv_analysis: Dict[str, Any], max_results: int = 20) -> List[Dict[str, Any]]:
        """
        JSearch API ile iş ilanları arar
        """
        print("🔍 JSearch API ile iş arama başlatılıyor...")
        
        if not self.jsearch_api_key:
            print("❌ JSearch API key bulunamadı!")
            return self._get_default_jobs()
        
        try:
            # CV analizinden arama terimlerini oluştur
            search_terms = self._generate_search_terms(cv_analysis)
            
            all_jobs = []
            
            # Her arama terimi için iş ara
            for term in search_terms[:3]:  # İlk 3 terimi kullan
                print(f"🔍 Aranan terim: {term}")
                
                querystring = {
                    "query": term,
                    "page": "1",
                    "num_pages": "1",
                    "country": "us",  # Varsayılan olarak US, daha sonra lokasyon bazlı yapılabilir
                    "date_posted": "all"
                }
                
                response = requests.get(
                    self.jsearch_url, 
                    headers=self.jsearch_headers, 
                    params=querystring
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('status') == 'OK' and data.get('data'):
                        jobs = data['data']
                        
                        # Her iş için skor hesapla
                        for job in jobs:
                            job['score'] = self._calculate_job_match_score(job, cv_analysis)
                            job['search_term'] = term
                        
                        all_jobs.extend(jobs)
                        print(f"✅ {term} için {len(jobs)} iş bulundu")
                    else:
                        print(f"⚠️ {term} için iş bulunamadı")
                else:
                    print(f"❌ API hatası: {response.status_code}")
            
            # Skorlara göre sırala ve en iyi sonuçları döndür
            all_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Benzersiz işleri filtrele (job_id'ye göre)
            unique_jobs = []
            seen_job_ids = set()
            
            for job in all_jobs:
                job_id = job.get('job_id')
                if job_id and job_id not in seen_job_ids:
                    unique_jobs.append(job)
                    seen_job_ids.add(job_id)
            
            # En iyi sonuçları döndür
            top_jobs = unique_jobs[:max_results]
            
            print(f"✅ Toplam {len(top_jobs)} benzersiz iş bulundu")
            return top_jobs
            
        except Exception as e:
            print(f"❌ JSearch API hatası: {e}")
            return self._get_default_jobs()
    
    def _generate_search_terms(self, cv_analysis: Dict[str, Any]) -> List[str]:
        """
        CV analizinden arama terimleri oluşturur
        """
        search_terms = []
        
        # Teknik becerilerden terimler oluştur
        technical_skills = cv_analysis.get('teknik_beceriler', [])
        programming_languages = cv_analysis.get('yazılım_dilleri', [])
        technologies = cv_analysis.get('teknolojiler', [])
        
        # Ana uzmanlık alanı
        main_expertise = cv_analysis.get('ana_uzmanlık_alanı', '')
        if main_expertise and main_expertise != 'Belirtilmemiş':
            search_terms.append(f"{main_expertise} jobs")
        
        # Uygun iş alanları
        suitable_job_areas = cv_analysis.get('uygun_iş_alanları', [])
        for area in suitable_job_areas[:2]:  # İlk 2 alanı kullan
            if area and area != 'Belirtilmemiş':
                search_terms.append(f"{area} jobs")
        
        # Teknik becerilerden terimler
        for skill in technical_skills[:3]:  # İlk 3 beceriyi kullan
            if skill and skill != 'Belirtilmemiş':
                search_terms.append(f"{skill} developer jobs")
        
        # Programlama dillerinden terimler
        for lang in programming_languages[:2]:  # İlk 2 dili kullan
            if lang and lang != 'Belirtilmemiş':
                search_terms.append(f"{lang} developer jobs")
        
        # Eğer hiç terim oluşturulamadıysa varsayılan terimler
        if not search_terms:
            search_terms = [
                "software developer jobs",
                "web developer jobs", 
                "programmer jobs"
            ]
        
        return search_terms
    
    def _calculate_job_match_score(self, job: Dict[str, Any], cv_analysis: Dict[str, Any]) -> float:
        """
        İş ilanı ile CV arasındaki uyum skorunu hesaplar
        """
        score = 0.0
        
        # İş başlığından skor hesapla
        job_title = job.get('job_title', '').lower()
        technical_skills = [skill.lower() for skill in cv_analysis.get('teknik_beceriler', [])]
        programming_languages = [lang.lower() for lang in cv_analysis.get('yazılım_dilleri', [])]
        
        # Teknik beceriler eşleşmesi
        for skill in technical_skills:
            if skill in job_title:
                score += 10
        
        # Programlama dilleri eşleşmesi
        for lang in programming_languages:
            if lang in job_title:
                score += 15
        
        # İş türü eşleşmesi
        employment_type = job.get('job_employment_type', '').lower()
        if 'full-time' in employment_type:
            score += 5
        elif 'part-time' in employment_type:
            score += 3
        
        # Şirket büyüklüğü (varsa)
        employer_name = job.get('employer_name', '').lower()
        if any(keyword in employer_name for keyword in ['google', 'microsoft', 'amazon', 'apple', 'meta']):
            score += 10
        
        return score
    
    def _get_default_jobs(self) -> List[Dict[str, Any]]:
        """
        API çalışmadığında varsayılan iş ilanları döndürür
        """
        return [
            {
                "job_id": "default_1",
                "job_title": "Frontend Developer",
                "employer_name": "Tech Company",
                "employer_logo": None,
                "employer_website": "https://example.com",
                "job_publisher": "LinkedIn",
                "job_employment_type": "Full-time",
                "job_apply_link": "https://example.com/apply",
                "job_apply_is_direct": False,
                "score": 85,
                "search_term": "frontend developer jobs"
            },
            {
                "job_id": "default_2", 
                "job_title": "JavaScript Developer",
                "employer_name": "Startup Inc",
                "employer_logo": None,
                "employer_website": "https://startup.com",
                "job_publisher": "Indeed",
                "job_employment_type": "Full-time",
                "job_apply_link": "https://startup.com/careers",
                "job_apply_is_direct": False,
                "score": 80,
                "search_term": "javascript developer jobs"
            }
        ]
    
    def process_cv_and_find_jobs(self, pdf_bytes: bytes, max_results: int = 20) -> Dict[str, Any]:
        """
        CV'yi analiz eder ve uygun işleri bulur
        """
        print("🚀 CV analizi ve iş arama başlatılıyor...")
        
        try:
            # CV analizi
            cv_analysis = self.analyze_cv_from_pdf(pdf_bytes)
            
            # İş arama
            jobs = self.search_jobs_with_jsearch(cv_analysis, max_results)
            
            return {
                'success': True,
                'cv_analysis': cv_analysis,
                'jobs': jobs,
                'stats': {
                    'total_jobs_found': len(jobs),
                    'cv_skills_count': len(cv_analysis.get('teknik_beceriler', [])),
                    'search_method': 'JSearch API',
                    'avg_match_score': sum(job.get('score', 0) for job in jobs) / len(jobs) if jobs else 0
                }
            }
            
        except Exception as e:
            print(f"❌ CV işleme hatası: {e}")
            return {
                'success': False,
                'error': str(e),
                'cv_analysis': None,
                'jobs': self._get_default_jobs(),
                'stats': {
                    'total_jobs_found': 0,
                    'cv_skills_count': 0,
                    'search_method': 'Default',
                    'avg_match_score': 0
                }
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
    
    # JSEARCH_API_KEY kontrolü
    if not agent.jsearch_api_key:
        print("❌ JSEARCH_API_KEY bulunamadı!")
        print("📝 .env dosyasına JSEARCH_API_KEY=your_api_key_here ekleyin")
        print("🔗 https://rapidapi.com/letscrape/api/jsearch adresinden ücretsiz API key alabilirsiniz")
    else:
        print("✅ JSEARCH_API_KEY bulundu, JSearch API test ediliyor...")
        jobs = agent.search_jobs_with_jsearch(test_cv_analysis, max_results=5)
        
        print(f"📊 Test sonucu: {len(jobs)} iş bulundu")
        for i, job in enumerate(jobs):
            print(f"  {i+1}. {job['job_title']} - {job['employer_name']} ({job['score']}%)")
            print(f"     URL: {job['job_apply_link']}")
            print()
