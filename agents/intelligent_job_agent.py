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
        Analyze this CV and return the result in the following JSON format:
        
        {
            "kişisel_bilgiler": {
                "ad_soyad": "Full name from CV",
                "email": "Email from CV",
                "telefon": "Phone from CV", 
                "lokasyon": "City from CV"
            },
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "Total work experience from CV",
            "staj_deneyimi": "Internship experience from CV",
            "teknik_beceriler": ["Technical skills from CV - use English terms like React, Node.js, Python, JavaScript, etc."],
            "yazılım_dilleri": ["Programming languages from CV - use English terms like Python, JavaScript, Java, etc."],
            "teknolojiler": ["Technologies from CV - use English terms like Web Development, Mobile Development, AI, etc."],
            "eğitim": ["Education from CV"],
            "deneyim_seviyesi": "entry|junior|mid|senior",
            "ana_uzmanlık_alanı": "Main expertise area from CV - choose ONLY ONE area: Web Development, AI, Machine Learning, Mobile Development, Data Science, DevOps, Backend Development, Frontend Development, Full Stack Development, Software Development",
            "uygun_iş_alanları": ["Suitable job areas - use English terms like Frontend Developer, Backend Developer, AI Developer, etc."],
            "cv_kalitesi": "zayıf|orta|iyi|mükemmel"
        }
        
        IMPORTANT: 
        1. Return only JSON, no other explanation
        2. Use English terms for technical skills, programming languages, technologies, and job areas
        3. Write "Belirtilmemiş" for missing information
        4. For technical skills, use terms like: React, Angular, Vue.js, Node.js, Python, Java, JavaScript, TypeScript, etc.
        5. For job areas, use terms like: Frontend Developer, Backend Developer, Full Stack Developer, AI Developer, Machine Learning Engineer, etc.
        6. For ana_uzmanlık_alanı, choose ONLY ONE area from the list - do not combine multiple areas
        7. Do not use commas or multiple areas in ana_uzmanlık_alanı - just one specific area
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
        Analyze this CV and return the result in the following JSON format:
        
        {
            "kişisel_bilgiler": {
                "ad_soyad": "Full name from CV",
                "email": "Email from CV",
                "telefon": "Phone from CV", 
                "lokasyon": "City from CV"
            },
            "deneyim_yılı": 0,
            "toplam_is_deneyimi": "Total work experience from CV",
            "staj_deneyimi": "Internship experience from CV",
            "teknik_beceriler": ["Technical skills from CV - use English terms like React, Node.js, Python, JavaScript, etc."],
            "yazılım_dilleri": ["Programming languages from CV - use English terms like Python, JavaScript, Java, etc."],
            "teknolojiler": ["Technologies from CV - use English terms like Web Development, Mobile Development, AI, etc."],
            "eğitim": ["Education from CV"],
            "deneyim_seviyesi": "entry|junior|mid|senior",
            "ana_uzmanlık_alanı": "Main expertise area from CV - choose ONLY ONE area: Web Development, AI, Machine Learning, Mobile Development, Data Science, DevOps, Backend Development, Frontend Development, Full Stack Development, Software Development",
            "uygun_iş_alanları": ["Suitable job areas - use English terms like Frontend Developer, Backend Developer, AI Developer, etc."],
            "cv_kalitesi": "zayıf|orta|iyi|mükemmel"
        }
        
        IMPORTANT: 
        1. Return only JSON, no other explanation
        2. Use English terms for technical skills, programming languages, technologies, and job areas
        3. Write "Belirtilmemiş" for missing information
        4. For technical skills, use terms like: React, Angular, Vue.js, Node.js, Python, Java, JavaScript, TypeScript, etc.
        5. For job areas, use terms like: Frontend Developer, Backend Developer, Full Stack Developer, AI Developer, Machine Learning Engineer, etc.
        6. For ana_uzmanlık_alanı, choose ONLY ONE area from the list - do not combine multiple areas
        7. Do not use commas or multiple areas in ana_uzmanlık_alanı - just one specific area
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
            for term in search_terms[:8]:  # İlk 8 terimi kullan (daha fazla arama)
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
        CV analizinden kişinin en çok ilgilendiği alanla ilgili İngilizce arama cümleleri oluşturur
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
        english_level = level_mapping.get(experience_level, 'Junior')
        
        # Türkçe-İngilizce çeviri sözlükleri
        expertise_mapping = {
            'Web Development': 'Web Developer',
            'Mobile Development': 'Mobile Developer', 
            'Data Science': 'Data Scientist',
            'Machine Learning': 'Machine Learning Engineer',
            'AI': 'AI Developer',
            'Artificial Intelligence': 'AI Developer',
            'Yapay Zeka': 'AI Developer',
            'Makine Öğrenmesi': 'Machine Learning Engineer',
            'Backend Development': 'Backend Developer',
            'Frontend Development': 'Frontend Developer',
            'Full Stack Development': 'Full Stack Developer',
            'DevOps': 'DevOps Engineer',
            'Software Development': 'Software Developer',
            'Yazılım Geliştirme': 'Software Developer',
            'Yazılım Geliştirici': 'Software Developer',
            'Yazılım Geliştirme, Yapay Zeka': 'AI Developer',
            'Yazılım Geliştirme, Yapay Zeka, Makine Öğrenmesi': 'AI Developer',
            'Yazılım Geliştirme, Makine Öğrenmesi': 'Machine Learning Engineer',
            'Yazılım Geliştirme, AI': 'AI Developer',
            'Yazılım Geliştirme, AI, Machine Learning': 'AI Developer'
        }
        
        job_area_mapping = {
            'Frontend Developer': 'Frontend Developer',
            'Backend Developer': 'Backend Developer', 
            'Full Stack Developer': 'Full Stack Developer',
            'Mobile Developer': 'Mobile Developer',
            'Data Scientist': 'Data Scientist',
            'Machine Learning Engineer': 'Machine Learning Engineer',
            'AI Developer': 'AI Developer',
            'DevOps Engineer': 'DevOps Engineer',
            'Software Engineer': 'Software Engineer',
            'Web Developer': 'Web Developer',
            'Yazılım Geliştirici': 'Software Developer',
            'Yapay Zeka Geliştirici': 'AI Developer',
            'Makine Öğrenmesi Mühendisi': 'Machine Learning Engineer',
            'Yazılım Geliştirme, Yapay Zeka': 'AI Developer',
            'Yazılım Geliştirme, Yapay Zeka, Makine Öğrenmesi': 'AI Developer',
            'Yazılım Geliştirme, Makine Öğrenmesi': 'Machine Learning Engineer',
            'Yazılım Geliştirme, AI': 'AI Developer',
            'Yazılım Geliştirme, AI, Machine Learning': 'AI Developer',

        }
        
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
            'Kotlin': 'Kotlin',
            'React': 'React',
            'Node.js': 'Node.js',
            'Angular': 'Angular',
            'Vue.js': 'Vue.js'
        }
        
        # 1. Ana uzmanlık alanından terim oluştur
        if main_expertise and main_expertise != 'Belirtilmemiş':
            # Türkçe terimleri temizle ve İngilizce'ye çevir
            english_expertise = expertise_mapping.get(main_expertise, main_expertise)
            
            # Eğer hala Türkçe terim varsa, varsayılan değer kullan
            if any(turkish_word in english_expertise.lower() for turkish_word in ['yazılım', 'yapay', 'zeka', 'makine', 'öğrenme', 'geliştirme']):
                english_expertise = 'Software Developer'
            
            # Format: "Junior AI Developer"
            search_terms.append(f"{english_level} {english_expertise}")
            
            # Format: "AI Developer jobs"
            search_terms.append(f"{english_expertise} jobs")
            
            # Format: "Machine Learning Engineer"
            search_terms.append(f"{english_expertise}")
        
        # 2. Uygun iş alanlarından terim oluştur (en çok 3 tane)
        for area in suitable_job_areas[:3]:
            if area and area != 'Belirtilmemiş':
                # Türkçe terimleri temizle ve İngilizce'ye çevir
                english_area = job_area_mapping.get(area, area)
                
                # Eğer hala Türkçe terim varsa, varsayılan değer kullan
                if any(turkish_word in english_area.lower() for turkish_word in ['yazılım', 'yapay', 'zeka', 'makine', 'öğrenme', 'geliştirme']):
                    english_area = 'Software Developer'
                
                # Format: "Junior Frontend Developer"
                search_terms.append(f"{english_level} {english_area}")
                
                # Format: "Frontend Developer jobs"
                search_terms.append(f"{english_area} jobs")
                
                # Format: "Frontend Developer"
                search_terms.append(f"{english_area}")
        
        # 3. Programlama dillerinden terim oluştur (en çok 3 tane)
        for lang in programming_languages[:3]:
            if lang and lang != 'Belirtilmemiş':
                english_lang = lang_mapping.get(lang, lang)
                
                # Format: "Junior Python Developer"
                search_terms.append(f"{english_level} {english_lang} Developer")
                
                # Format: "Python Developer jobs"
                search_terms.append(f"{english_lang} Developer jobs")
                
                # Format: "Python Developer"
                search_terms.append(f"{english_lang} Developer")
        
        # 4. Teknik becerilerden terim oluştur (en çok 2 tane)
        for skill in technical_skills[:2]:
            if skill and skill != 'Belirtilmemiş':
                english_skill = lang_mapping.get(skill, skill)
                
                # Format: "Junior React Developer"
                search_terms.append(f"{english_level} {english_skill} Developer")
                
                # Format: "React Developer jobs"
                search_terms.append(f"{english_skill} Developer jobs")
        
        # Eğer hiç terim oluşturulamadıysa varsayılan terimler
        if not search_terms:
            search_terms = [
                "Junior Software Developer",
                "Software Developer jobs",
                "Web Developer jobs",
                "Junior Web Developer",
                "Frontend Developer jobs",
                "Backend Developer jobs",
                "Full Stack Developer jobs",
                "JavaScript Developer jobs"
            ]
        
        # Benzersiz terimleri döndür (ilk 8'i)
        unique_terms = list(dict.fromkeys(search_terms))[:8]
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
