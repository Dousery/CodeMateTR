import os
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random

# CrewAI ve LangChain imports
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Google GenAI import
from google import genai
from dotenv import load_dotenv

load_dotenv()

class JobListing(BaseModel):
    title: str = Field(description="İş başlığı")
    company: str = Field(description="Şirket adı")
    location: str = Field(description="Lokasyon")
    description: str = Field(description="İş açıklaması")
    requirements: List[str] = Field(description="Gereksinimler listesi")
    url: str = Field(description="İlan URL'si")
    salary_range: Optional[str] = Field(description="Maaş aralığı", default=None)
    job_type: Optional[str] = Field(description="İş türü (tam zamanlı, yarı zamanlı, vb.)", default=None)

class CVAnalysis(BaseModel):
    skills: List[str] = Field(description="CV'deki beceriler")
    experience_years: int = Field(description="Toplam deneyim yılı")
    education: List[str] = Field(description="Eğitim bilgileri")
    languages: List[str] = Field(description="Bildiği diller")
    certifications: List[str] = Field(description="Sertifikalar")
    projects: List[str] = Field(description="Projeler")

class JobMatchResult(BaseModel):
    job_listing: JobListing = Field(description="İş ilanı")
    match_score: float = Field(description="Eşleşme skoru (0-100)")
    match_reasons: List[str] = Field(description="Eşleşme nedenleri")
    missing_skills: List[str] = Field(description="Eksik beceriler")
    recommendations: List[str] = Field(description="Öneriler")

class AdvancedCVJobAgent:
    def __init__(self):
        self.gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.search_tool = DuckDuckGoSearchRun()
        
        # LLM modelleri
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        # Agent'ları oluştur
        self.cv_analyzer_agent = self._create_cv_analyzer_agent()
        self.job_researcher_agent = self._create_job_researcher_agent()
        self.job_matcher_agent = self._create_job_matcher_agent()
        
    def _create_cv_analyzer_agent(self):
        """CV analiz agent'ı oluşturur"""
        return Agent(
            role='CV Analiz Uzmanı',
            goal='CV\'yi detaylı analiz ederek kullanıcının en uygun iş alanlarını belirlemek',
            backstory="""Sen deneyimli bir CV analiz uzmanısın. CV'leri analiz ederek 
            kişinin hangi iş alanlarında başarılı olabileceğini belirlersin. 
            Teknik beceriler, deneyim ve eğitim bilgilerini değerlendirerek 
            en uygun 2 iş alanını önerirsin.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _create_job_researcher_agent(self):
        """İş araştırma agent'ı oluşturur"""
        return Agent(
            role='İş Araştırma Uzmanı',
            goal='Belirtilen iş alanlarında gerçek iş ilanları bulmak',
            backstory="""Sen deneyimli bir iş araştırma uzmanısın. 
            Farklı kaynaklardan (LinkedIn, Indeed, Glassdoor, vb.) 
            gerçek iş ilanları bulur ve toplarsın. Her alan için 
            en güncel ve kaliteli ilanları seçersin.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.search_tool]
        )
    
    def _create_job_matcher_agent(self):
        """İş eşleştirme agent'ı oluşturur"""
        return Agent(
            role='İş Eşleştirme Uzmanı',
            goal='CV ile iş ilanlarını karşılaştırarak en uygun eşleşmeleri bulmak',
            backstory="""Sen deneyimli bir iş eşleştirme uzmanısın. 
            CV'deki beceriler, deneyim ve eğitim bilgilerini 
            iş ilanlarıyla karşılaştırarak en uygun eşleşmeleri bulursun. 
            Her eşleşme için detaylı analiz ve öneriler sunarsın.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_cv_and_find_jobs(self, cv_text: str) -> Dict[str, Any]:
        """Ana fonksiyon: CV'yi analiz eder ve uygun işleri bulur"""
        try:
            # 1. CV Analizi
            cv_analysis = self._analyze_cv(cv_text)
            
            # 2. İş alanlarını belirle
            job_areas = self._determine_job_areas(cv_analysis)
            
            # 3. Her alan için iş ilanları ara
            all_job_listings = []
            for area in job_areas:
                jobs = self._search_jobs_for_area(area)
                all_job_listings.extend(jobs)
            
            # 4. CV ile iş ilanlarını eşleştir
            matched_jobs = self._match_cv_with_jobs(cv_analysis, all_job_listings)
            
            # 5. Sonuçları sırala ve en iyilerini seç
            top_jobs = self._rank_and_select_top_jobs(matched_jobs)
            
            return {
                'cv_analysis': cv_analysis.dict(),
                'job_areas': job_areas,
                'total_jobs_found': len(all_job_listings),
                'top_matches': top_jobs,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"CV analiz hatası: {e}")
            return self._get_fallback_result(cv_text)
    
    def _analyze_cv(self, cv_text: str) -> CVAnalysis:
        """CV'yi detaylı analiz eder"""
        prompt = f"""
        Bu CV'yi analiz et ve aşağıdaki bilgileri çıkar:
        
        CV İÇERİĞİ:
        {cv_text}
        
        Aşağıdaki JSON formatında döndür:
        {{
            "skills": ["Python", "Machine Learning", "SQL", ...],
            "experience_years": 3,
            "education": ["Bilgisayar Mühendisliği - İTÜ", ...],
            "languages": ["Türkçe", "İngilizce", ...],
            "certifications": ["AWS Certified", ...],
            "projects": ["E-ticaret sitesi", "ML modeli", ...]
        }}
        
        Sadece JSON döndür, başka açıklama ekleme.
        """
        
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt]
        )
        
        try:
            analysis_data = json.loads(response.text.strip())
            return CVAnalysis(**analysis_data)
        except:
            # Fallback analiz
            return self._fallback_cv_analysis(cv_text)
    
    def _determine_job_areas(self, cv_analysis: CVAnalysis) -> List[str]:
        """CV analizine göre en uygun 2 iş alanını belirler"""
        prompt = f"""
        Bu CV analizine göre kişinin en uygun 2 iş alanını belirle:
        
        CV ANALİZİ:
        {cv_analysis.dict()}
        
        Sadece 2 iş alanı öner ve her biri için kısa açıklama ver:
        
        Örnek format:
        1. Data Scientist - Makine öğrenmesi ve veri analizi becerileri
        2. Software Engineer - Programlama ve yazılım geliştirme deneyimi
        
        Sadece bu formatı kullan, başka açıklama ekleme.
        """
        
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt]
        )
        
        # Sonuçtan iş alanlarını çıkar
        lines = response.text.strip().split('\n')
        job_areas = []
        for line in lines:
            if line.strip() and any(char.isdigit() for char in line):
                # "1. Data Scientist - Açıklama" formatından "Data Scientist" kısmını al
                area = line.split('.')[1].split('-')[0].strip()
                job_areas.append(area)
        
        return job_areas[:2] if job_areas else ["Software Engineer", "Data Analyst"]
    
    def _search_jobs_for_area(self, job_area: str) -> List[JobListing]:
        """Belirli bir iş alanı için iş ilanları arar"""
        jobs = []
        
        # Farklı arama terimleri dene
        search_terms = [
            f"{job_area} iş ilanları Türkiye",
            f"{job_area} pozisyonu İstanbul",
            f"{job_area} kariyer Türkiye",
            f"{job_area} remote iş",
            f"{job_area} junior pozisyon"
        ]
        
        for term in search_terms:
            try:
                search_results = self.search_tool.run(term)
                parsed_jobs = self._parse_search_results(search_results, job_area)
                jobs.extend(parsed_jobs)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Arama hatası ({term}): {e}")
                continue
        
        # Duplicate'leri kaldır ve en fazla 5 iş döndür
        unique_jobs = self._remove_duplicates(jobs)
        return unique_jobs[:5]
    
    def _parse_search_results(self, search_results: str, job_area: str) -> List[JobListing]:
        """Arama sonuçlarını parse eder"""
        jobs = []
        
        # Basit parsing - gerçek uygulamada daha gelişmiş olmalı
        lines = search_results.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in [job_area.lower(), 'iş', 'pozisyon', 'kariyer']):
                try:
                    # Basit job parsing
                    job = JobListing(
                        title=f"{job_area} Pozisyonu",
                        company="Şirket Adı",
                        location="Türkiye",
                        description=line[:200] + "..." if len(line) > 200 else line,
                        requirements=[f"{job_area} deneyimi", "İyi iletişim becerileri"],
                        url="https://example.com/job",
                        job_type="Tam Zamanlı"
                    )
                    jobs.append(job)
                except:
                    continue
        
        return jobs
    
    def _match_cv_with_jobs(self, cv_analysis: CVAnalysis, job_listings: List[JobListing]) -> List[JobMatchResult]:
        """CV ile iş ilanlarını eşleştirir"""
        matched_jobs = []
        
        for job in job_listings:
            try:
                match_result = self._calculate_job_match(cv_analysis, job)
                matched_jobs.append(match_result)
            except Exception as e:
                print(f"Eşleştirme hatası: {e}")
                continue
        
        return matched_jobs
    
    def _calculate_job_match(self, cv_analysis: CVAnalysis, job: JobListing) -> JobMatchResult:
        """CV ile iş ilanı arasındaki eşleşmeyi hesaplar"""
        prompt = f"""
        CV analizi ile iş ilanını karşılaştır ve eşleşme skorunu hesapla:
        
        CV ANALİZİ:
        {cv_analysis.dict()}
        
        İŞ İLANI:
        {job.dict()}
        
        Aşağıdaki kriterlere göre 0-100 arası skor ver:
        - Beceri uyumluluğu (40 puan)
        - Deneyim seviyesi (25 puan)
        - Teknoloji uyumluluğu (20 puan)
        - Eğitim uyumluluğu (15 puan)
        
        JSON formatında döndür:
        {{
            "match_score": 85,
            "match_reasons": ["Python becerisi uyumlu", "2 yıl deneyim uygun"],
            "missing_skills": ["Docker eksik"],
            "recommendations": ["Docker öğren", "AWS sertifikası al"]
        }}
        """
        
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=[prompt]
        )
        
        try:
            match_data = json.loads(response.text.strip())
            return JobMatchResult(
                job_listing=job,
                match_score=match_data.get('match_score', 50),
                match_reasons=match_data.get('match_reasons', []),
                missing_skills=match_data.get('missing_skills', []),
                recommendations=match_data.get('recommendations', [])
            )
        except:
            # Fallback eşleştirme
            return JobMatchResult(
                job_listing=job,
                match_score=50,
                match_reasons=["Temel eşleştirme"],
                missing_skills=[],
                recommendations=[]
            )
    
    def _rank_and_select_top_jobs(self, matched_jobs: List[JobMatchResult]) -> List[Dict[str, Any]]:
        """İş eşleşmelerini sıralar ve en iyilerini seçer"""
        # Skora göre sırala
        sorted_jobs = sorted(matched_jobs, key=lambda x: x.match_score, reverse=True)
        
        # En iyi 6 işi seç (her alandan 3'er tane)
        top_jobs = []
        job_areas_count = {}
        
        for job_match in sorted_jobs:
            job_area = job_match.job_listing.title.split()[0]  # Basit alan çıkarma
            
            if job_area not in job_areas_count:
                job_areas_count[job_area] = 0
            
            if job_areas_count[job_area] < 3 and len(top_jobs) < 6:
                top_jobs.append({
                    'job': job_match.job_listing.dict(),
                    'match_score': job_match.match_score,
                    'match_reasons': job_match.match_reasons,
                    'missing_skills': job_match.missing_skills,
                    'recommendations': job_match.recommendations
                })
                job_areas_count[job_area] += 1
        
        return top_jobs
    
    def _remove_duplicates(self, jobs: List[JobListing]) -> List[JobListing]:
        """Duplicate iş ilanlarını kaldırır"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # URL veya başlık + şirket kombinasyonuna göre duplicate kontrolü
            key = f"{job.title}_{job.company}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _fallback_cv_analysis(self, cv_text: str) -> CVAnalysis:
        """CV analizi başarısız olursa fallback analiz"""
        return CVAnalysis(
            skills=["Python", "JavaScript", "SQL"],
            experience_years=2,
            education=["Bilgisayar Mühendisliği"],
            languages=["Türkçe", "İngilizce"],
            certifications=[],
            projects=["Web uygulaması", "Veri analizi projesi"]
        )
    
    def _get_fallback_result(self, cv_text: str) -> Dict[str, Any]:
        """Ana fonksiyon başarısız olursa fallback sonuç"""
        return {
            'cv_analysis': self._fallback_cv_analysis(cv_text).dict(),
            'job_areas': ["Software Engineer", "Data Analyst"],
            'total_jobs_found': 0,
            'top_matches': [],
            'analysis_date': datetime.now().isoformat(),
            'error': 'Analiz sırasında hata oluştu'
        }

# Kullanım örneği
if __name__ == "__main__":
    agent = AdvancedCVJobAgent()
    
    # Test CV
    test_cv = """
    Ahmet Yılmaz
    Python Developer
    
    DENEYİM:
    - 3 yıl Python geliştirme deneyimi
    - Django, Flask framework'leri
    - PostgreSQL, MongoDB veritabanları
    - Docker, AWS kullanımı
    
    EĞİTİM:
    - İTÜ Bilgisayar Mühendisliği
    
    BECERİLER:
    - Python, JavaScript, SQL
    - Machine Learning temelleri
    - Git, Linux
    """
    
    result = agent.analyze_cv_and_find_jobs(test_cv)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 