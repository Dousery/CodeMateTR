#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Akıllı İş Bulma Asistanı - JSearch API ile
CV analizi + JSearch API
"""

import os
import json
import requests
import base64
from datetime import datetime
from typing import Dict, Any, List
import google.generativeai as genai
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
            print(f"🔍 PDF boyutu: {len(pdf_bytes)} bytes")
            print(f"🔍 Gemini API key mevcut: {bool(self.genai_client)}")
            
            # PDF'yi base64'e çevir
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Gemini PDF API kullan - güncel versiyon
            model = self.genai_client.GenerativeModel("gemini-1.5-flash")
            
            # PDF'yi image olarak gönder (Gemini 1.5-flash PDF'yi destekler)
            response = model.generate_content([
                {
                    "mime_type": "application/pdf",
                    "data": pdf_base64
                },
                prompt
            ])
            
            print(f"🔍 Gemini API response alındı: {response.text[:200]}...")
            
            # JSON'u temizle ve parse et
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            print(f"🔍 Temizlenmiş JSON: {json_text[:200]}...")
            
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
            import traceback
            print(f"❌ CV analizi traceback: {traceback.format_exc()}")
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
    
    def analyze_cv_from_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        PDF'yi Gemini ile analiz eder ve JSON formatında sonuç döndürür
        (Eski çalışan versiyon)
        """
        print("🤖 CV analizi (bytes) başlatılıyor...")
        
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
            print(f"🔍 PDF boyutu: {len(pdf_bytes)} bytes")
            print(f"🔍 Gemini API key mevcut: {bool(self.genai_client)}")
            
            # PDF'yi base64'e çevir
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Gemini PDF API kullan - güncel versiyon
            model = self.genai_client.GenerativeModel("gemini-1.5-flash")
            
            # PDF'yi image olarak gönder (Gemini 1.5-flash PDF'yi destekler)
            response = model.generate_content([
                {
                    "mime_type": "application/pdf",
                    "data": pdf_base64
                },
                prompt
            ])
            
            print(f"🔍 Gemini API response alındı: {response.text[:200]}...")
            
            # JSON'u temizle ve parse et
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            print(f"🔍 Temizlenmiş JSON: {json_text[:200]}...")
            
            cv_analysis = json.loads(json_text)
            
            # Eğer teknik beceriler boşsa, varsayılan ekle
            if not cv_analysis.get('teknik_beceriler'):
                cv_analysis['teknik_beceriler'] = ['HTML', 'CSS', 'JavaScript']
            
            # CV kalitesi yoksa varsayılan ekle
            if not cv_analysis.get('cv_kalitesi'):
                cv_analysis['cv_kalitesi'] = 'orta'
            
            print(f"✅ CV analizi (bytes) tamamlandı: {len(cv_analysis.get('teknik_beceriler', []))} beceri bulundu")
            return cv_analysis
            
        except Exception as e:
            print(f"❌ CV analizi (bytes) hatası: {e}")
            import traceback
            print(f"❌ CV analizi (bytes) traceback: {traceback.format_exc()}")
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
            for term in search_terms[:5]:  # İlk 5 terimi kullan
                print(f"🔍 Aranan terim: {term}")
                
                querystring = {
                    "query": term,
                    "page": "1",
                    "num_pages": "1",
                    "country": "tr",  # Türkiye için
                    "date_posted": "all"
                }
                
                print(f"🔍 JSearch API parametreleri: {querystring}")
                print(f"🔍 JSearch API URL: {self.jsearch_url}")
                print(f"🔍 JSearch API Headers: {self.jsearch_headers}")
                
                response = requests.get(
                    self.jsearch_url, 
                    headers=self.jsearch_headers, 
                    params=querystring
                )
                
                print(f"🔍 JSearch API Response Status: {response.status_code}")
                print(f"🔍 JSearch API Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"🔍 JSearch API Response Data: {data}")
                    
                    if data.get('status') == 'OK' and data.get('data'):
                        jobs = data['data']
                        print(f"🔍 JSearch API'den gelen iş sayısı: {len(jobs)}")
                        
                        # Her iş için skor hesapla
                        for job in jobs:
                            job['score'] = self._calculate_job_match_score(job, cv_analysis)
                            job['search_term'] = term
                        
                        all_jobs.extend(jobs)
                        print(f"✅ {term} için {len(jobs)} iş bulundu")
                    else:
                        print(f"⚠️ {term} için iş bulunamadı - API Response: {data}")
                else:
                    print(f"❌ API hatası: {response.status_code}")
                    print(f"❌ API Error Response: {response.text}")
            
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
        CV analizinden sade ve etkili arama terimleri oluşturur
        Format: "Country Level Job_Title" veya "Job_Title jobs in Country"
        """
        search_terms = []
        
        # Temel bilgileri al
        experience_level = cv_analysis.get('deneyim_seviyesi', '')
        main_expertise = cv_analysis.get('ana_uzmanlık_alanı', '')
        technical_skills = cv_analysis.get('teknik_beceriler', [])
        programming_languages = cv_analysis.get('yazılım_dilleri', [])
        suitable_job_areas = cv_analysis.get('uygun_iş_alanları', [])
        
        # Deneyim seviyesini İngilizce'ye çevir
        level_mapping = {
            'entry': 'Junior',
            'junior': 'Junior', 
            'mid': 'Mid-level',
            'senior': 'Senior'
        }
        english_level = level_mapping.get(experience_level, '')
        
        # Ana uzmanlık alanından terim oluştur
        if main_expertise and main_expertise != 'Belirtilmemiş':
            # Türkçe terimleri İngilizce'ye çevir
            expertise_mapping = {
                'Web Development': 'Web Developer',
                'Mobile Development': 'Mobile Developer',
                'Data Science': 'Data Scientist',
                'Machine Learning': 'Machine Learning Engineer',
                'AI': 'AI Developer',
                'Backend Development': 'Backend Developer',
                'Frontend Development': 'Frontend Developer',
                'Full Stack Development': 'Full Stack Developer',
                'DevOps': 'DevOps Engineer',
                'Software Development': 'Software Developer'
            }
            
            english_expertise = expertise_mapping.get(main_expertise, main_expertise)
            
            # Format 1: "Turkey Junior Machine Learning Engineer"
            if english_level:
                search_terms.append(f"Turkey {english_level} {english_expertise}")
            
            # Format 2: "Machine Learning Engineer jobs in Turkey"
            search_terms.append(f"{english_expertise} jobs in Turkey")
            
            # Format 3: "Machine Learning Engineer Turkey" (daha kısa)
            search_terms.append(f"{english_expertise} Turkey")
        
        # Uygun iş alanlarından terim oluştur
        for area in suitable_job_areas[:2]:
            if area and area != 'Belirtilmemiş':
                # Türkçe iş alanlarını İngilizce'ye çevir
                area_mapping = {
                    'Frontend Developer': 'Frontend Developer',
                    'Backend Developer': 'Backend Developer',
                    'Full Stack Developer': 'Full Stack Developer',
                    'Mobile Developer': 'Mobile Developer',
                    'Data Scientist': 'Data Scientist',
                    'Machine Learning Engineer': 'Machine Learning Engineer',
                    'AI Developer': 'AI Developer',
                    'DevOps Engineer': 'DevOps Engineer',
                    'Software Engineer': 'Software Engineer',
                    'Web Developer': 'Web Developer'
                }
                
                english_area = area_mapping.get(area, area)
                
                if english_level:
                    search_terms.append(f"Turkey {english_level} {english_area}")
                search_terms.append(f"{english_area} jobs in Turkey")
                search_terms.append(f"{english_area} Turkey")
        
        # Programlama dillerinden terim oluştur
        for lang in programming_languages[:2]:
            if lang and lang != 'Belirtilmemiş':
                # Dil adlarını normalize et
                lang_mapping = {
                    'JavaScript': 'JavaScript',
                    'Python': 'Python',
                    'Java': 'Java',
                    'C++': 'C++',
                    'C#': 'C#',
                    'PHP': 'PHP',
                    'Ruby': 'Ruby',
                    'Go': 'Go',
                    'Rust': 'Rust',
                    'Swift': 'Swift',
                    'Kotlin': 'Kotlin'
                }
                
                english_lang = lang_mapping.get(lang, lang)
                
                if english_level:
                    search_terms.append(f"Turkey {english_level} {english_lang} Developer")
                search_terms.append(f"{english_lang} Developer jobs in Turkey")
                search_terms.append(f"{english_lang} Developer Turkey")
        
        # Eğer hiç terim oluşturulamadıysa varsayılan terimler
        if not search_terms:
            search_terms = [
                "Turkey Junior Software Developer",
                "Software Developer Turkey",
                "Web Developer Turkey"
            ]
        
        # Benzersiz terimleri döndür (ilk 5'i)
        unique_terms = list(dict.fromkeys(search_terms))[:5]
        print(f"🔍 Oluşturulan arama terimleri: {unique_terms}")
        
        return unique_terms
    
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
            cv_analysis = self.analyze_cv_from_pdf_bytes(pdf_bytes)
            
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
