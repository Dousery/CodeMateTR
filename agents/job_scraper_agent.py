import os
import json
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
import re
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class JobScraperAgent:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Chrome options for Selenium
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument(f'--user-agent={self.ua.random}')
        
    def search_jobs(self, job_title: str, location: str = "Türkiye", max_jobs: int = 5) -> List[Dict[str, Any]]:
        """Farklı kaynaklardan iş ilanları arar"""
        all_jobs = []
        
        # Farklı kaynaklardan arama yap
        sources = [
            self._search_linkedin,
            self._search_indeed,
            self._search_glassdoor,
            self._search_kariyer_net,
            self._search_secretcv
        ]
        
        for source_func in sources:
            try:
                jobs = source_func(job_title, location, max_jobs // len(sources))
                all_jobs.extend(jobs)
                time.sleep(random.uniform(1, 3))  # Rate limiting
            except Exception as e:
                print(f"Kaynak hatası ({source_func.__name__}): {e}")
                continue
        
        # Duplicate'leri kaldır ve en iyi sonuçları döndür
        unique_jobs = self._remove_duplicates(all_jobs)
        return unique_jobs[:max_jobs]
    
    def _search_linkedin(self, job_title: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """LinkedIn'den iş ilanları çeker"""
        jobs = []
        
        try:
            # LinkedIn arama URL'si
            search_query = f"{job_title} {location}"
            encoded_query = quote_plus(search_query)
            url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}&location={quote_plus(location)}"
            
            # Selenium ile LinkedIn'i aç
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # Sayfanın yüklenmesini bekle
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-search-card"))
            )
            
            # İş kartlarını bul
            job_cards = driver.find_elements(By.CLASS_NAME, "job-search-card")
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find_element(By.CLASS_NAME, "job-search-card__title")
                    company_elem = card.find_element(By.CLASS_NAME, "job-search-card__subtitle")
                    location_elem = card.find_element(By.CLASS_NAME, "job-search-card__location")
                    
                    job = {
                        'title': title_elem.text.strip(),
                        'company': company_elem.text.strip(),
                        'location': location_elem.text.strip(),
                        'source': 'LinkedIn',
                        'url': card.find_element(By.TAG_NAME, "a").get_attribute("href"),
                        'description': self._get_job_description(card.find_element(By.TAG_NAME, "a").get_attribute("href")),
                        'requirements': [],
                        'salary_range': None,
                        'job_type': 'Tam Zamanlı'
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    print(f"LinkedIn kart parse hatası: {e}")
                    continue
            
            driver.quit()
            
        except Exception as e:
            print(f"LinkedIn arama hatası: {e}")
        
        return jobs
    
    def _search_indeed(self, job_title: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Indeed'den iş ilanları çeker"""
        jobs = []
        
        try:
            # Indeed arama URL'si
            search_query = f"{job_title} {location}"
            encoded_query = quote_plus(search_query)
            url = f"https://tr.indeed.com/jobs?q={encoded_query}&l={quote_plus(location)}"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # İş kartlarını bul
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'source': 'Indeed',
                            'url': urljoin(url, title_elem.find('a')['href']) if title_elem.find('a') else None,
                            'description': '',
                            'requirements': [],
                            'salary_range': None,
                            'job_type': 'Tam Zamanlı'
                        }
                        
                        jobs.append(job)
                        
                except Exception as e:
                    print(f"Indeed kart parse hatası: {e}")
                    continue
                    
        except Exception as e:
            print(f"Indeed arama hatası: {e}")
        
        return jobs
    
    def _search_glassdoor(self, job_title: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Glassdoor'dan iş ilanları çeker"""
        jobs = []
        
        try:
            # Glassdoor arama URL'si
            search_query = f"{job_title} {location}"
            encoded_query = quote_plus(search_query)
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={encoded_query}&locT=N&locId=115&jobType=&fromAge=-1&minSalary=0&includeUnknownSalary=false&remoteWorkType=0&minExperience=0&includeRemoteWorkType=0"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # İş kartlarını bul
            job_cards = soup.find_all('li', class_='react-job-listing')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('a', class_='jobLink')
                    company_elem = card.find('a', class_='job-search-key-l2wjgv')
                    location_elem = card.find('span', class_='job-search-key-iiw14g')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'source': 'Glassdoor',
                            'url': urljoin(url, title_elem['href']) if title_elem.get('href') else None,
                            'description': '',
                            'requirements': [],
                            'salary_range': None,
                            'job_type': 'Tam Zamanlı'
                        }
                        
                        jobs.append(job)
                        
                except Exception as e:
                    print(f"Glassdoor kart parse hatası: {e}")
                    continue
                    
        except Exception as e:
            print(f"Glassdoor arama hatası: {e}")
        
        return jobs
    
    def _search_kariyer_net(self, job_title: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """Kariyer.net'ten iş ilanları çeker"""
        jobs = []
        
        try:
            # Kariyer.net arama URL'si
            search_query = f"{job_title} {location}"
            encoded_query = quote_plus(search_query)
            url = f"https://www.kariyer.net/is-ilanlari?kw={encoded_query}&city={quote_plus(location)}"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # İş kartlarını bul
            job_cards = soup.find_all('div', class_='job-list-item')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('h3', class_='job-title')
                    company_elem = card.find('span', class_='company-name')
                    location_elem = card.find('span', class_='location')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'source': 'Kariyer.net',
                            'url': urljoin(url, title_elem.find('a')['href']) if title_elem.find('a') else None,
                            'description': '',
                            'requirements': [],
                            'salary_range': None,
                            'job_type': 'Tam Zamanlı'
                        }
                        
                        jobs.append(job)
                        
                except Exception as e:
                    print(f"Kariyer.net kart parse hatası: {e}")
                    continue
                    
        except Exception as e:
            print(f"Kariyer.net arama hatası: {e}")
        
        return jobs
    
    def _search_secretcv(self, job_title: str, location: str, max_jobs: int) -> List[Dict[str, Any]]:
        """SecretCV'den iş ilanları çeker"""
        jobs = []
        
        try:
            # SecretCV arama URL'si
            search_query = f"{job_title} {location}"
            encoded_query = quote_plus(search_query)
            url = f"https://www.secretcv.com/is-ilanlari?q={encoded_query}&location={quote_plus(location)}"
            
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # İş kartlarını bul
            job_cards = soup.find_all('div', class_='job-card')
            
            for card in job_cards[:max_jobs]:
                try:
                    title_elem = card.find('h3', class_='job-title')
                    company_elem = card.find('span', class_='company')
                    location_elem = card.find('span', class_='location')
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'source': 'SecretCV',
                            'url': urljoin(url, title_elem.find('a')['href']) if title_elem.find('a') else None,
                            'description': '',
                            'requirements': [],
                            'salary_range': None,
                            'job_type': 'Tam Zamanlı'
                        }
                        
                        jobs.append(job)
                        
                except Exception as e:
                    print(f"SecretCV kart parse hatası: {e}")
                    continue
                    
        except Exception as e:
            print(f"SecretCV arama hatası: {e}")
        
        return jobs
    
    def _get_job_description(self, job_url: str) -> str:
        """İş ilanının detay sayfasından açıklama çeker"""
        try:
            if not job_url:
                return ""
            
            response = self.session.get(job_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Farklı siteler için farklı selector'lar
            selectors = [
                '.job-description',
                '.job-details',
                '.description',
                '.content',
                'article',
                '.job-content'
            ]
            
            for selector in selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    return desc_elem.get_text(strip=True)[:500] + "..."
            
            return ""
            
        except Exception as e:
            print(f"İş açıklaması çekme hatası: {e}")
            return ""
    
    def _remove_duplicates(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Duplicate iş ilanlarını kaldırır"""
        seen = set()
        unique_jobs = []
        
        for job in jobs:
            # Başlık + şirket kombinasyonuna göre duplicate kontrolü
            key = f"{job['title']}_{job['company']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def extract_requirements_from_description(self, description: str) -> List[str]:
        """İş açıklamasından gereksinimleri çıkarır"""
        requirements = []
        
        # Yaygın gereksinim kalıpları
        patterns = [
            r'(?:gereksinimler?|requirements?|aranan|beklenen)[:\s]*(.*?)(?:\n|\.)',
            r'(?:deneyim|experience)[:\s]*(.*?)(?:\n|\.)',
            r'(?:beceri|skill)[:\s]*(.*?)(?:\n|\.)',
            r'(?:eğitim|education)[:\s]*(.*?)(?:\n|\.)',
            r'(?:nitelik|qualification)[:\s]*(.*?)(?:\n|\.)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            requirements.extend(matches)
        
        # Teknik becerileri çıkar
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'React', 'Angular', 'Vue',
            'Node.js', 'Django', 'Flask', 'Spring', 'SQL', 'MongoDB',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git',
            'Machine Learning', 'AI', 'Data Science', 'DevOps'
        ]
        
        for skill in tech_skills:
            if skill.lower() in description.lower():
                requirements.append(skill)
        
        return list(set(requirements))[:10]  # En fazla 10 gereksinim
    
    def extract_salary_info(self, description: str) -> Optional[str]:
        """İş açıklamasından maaş bilgisini çıkarır"""
        salary_patterns = [
            r'(\d{1,3}(?:\.\d{3})*(?:\s*-\s*\d{1,3}(?:\.\d{3})*)?)\s*(?:TL|₺|lira)',
            r'(?:maaş|salary|ücret)[:\s]*(\d{1,3}(?:\.\d{3})*(?:\s*-\s*\d{1,3}(?:\.\d{3})*)?)',
            r'(\d{1,3}(?:\.\d{3})*(?:\s*-\s*\d{1,3}(?:\.\d{3})*)?)\s*(?:bin|k|milyon)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1) + " TL"
        
        return None

# Kullanım örneği
if __name__ == "__main__":
    scraper = JobScraperAgent()
    
    # Test arama
    jobs = scraper.search_jobs("Python Developer", "İstanbul", 5)
    
    for job in jobs:
        print(f"Başlık: {job['title']}")
        print(f"Şirket: {job['company']}")
        print(f"Lokasyon: {job['location']}")
        print(f"Kaynak: {job['source']}")
        print(f"URL: {job['url']}")
        print("-" * 50) 