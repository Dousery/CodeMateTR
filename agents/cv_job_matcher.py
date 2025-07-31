from google import genai
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=GEMINI_API_KEY)

class CVJobMatcher:
    def __init__(self):
        self.client = client

    def analyze_cv_and_find_jobs(self, cv_analysis):
        """CV'yi analiz eder ve uygun iş alanlarını belirler"""
        try:
            cv_text = self._format_cv_for_analysis(cv_analysis)
            
            prompt = f"""
            Bu CV'yi analiz et ve bu kişinin hangi iş alanlarında çalışabileceğini belirle.
            
            CV İÇERİĞİ:
            {cv_text}
            
            Bu kişinin arayabileceği 3-5 iş pozisyonu öner. Sadece pozisyon adlarını döndür:
            
            Örnek:
            - Data Scientist
            - Machine Learning Engineer
            - Python Developer
            - Business Analyst
            - Software Engineer
            
            Sadece pozisyon adlarını yaz, açıklama ekleme.
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )

            text = response.text.strip()
            positions = [line.strip().replace('- ', '').replace('• ', '') for line in text.split('\n') if line.strip()]
            
            return positions[:5]  # En fazla 5 pozisyon
            
        except Exception as e:
            print(f"CV analiz hatası: {e}")
            return self._get_fallback_positions(cv_analysis)

    def generate_job_listings(self, positions):
        """Belirlenen pozisyonlar için gerçekçi iş ilanları oluşturur"""
        all_jobs = []
        
        for position in positions:
            jobs_for_position = self._create_jobs_for_position(position)
            all_jobs.extend(jobs_for_position)
        
        return all_jobs

    def calculate_similarity_score(self, cv_analysis, job_description, job_title, job_requirements=None):
        """CV ile iş açıklamasını karşılaştırıp benzerlik skoru hesaplar"""
        try:
            cv_text = self._format_cv_for_comparison(cv_analysis)
            job_text = self._format_job_for_comparison(job_description, job_title, job_requirements)

            prompt = f"""
            CV ile iş açıklamasını karşılaştır ve 0-100 arası benzerlik skoru ver.
            
            CV:
            {cv_text}
            
            İŞ:
            {job_text}
            
            Değerlendirme:
            - Beceri uyumluluğu (40 puan)
            - Deneyim seviyesi (25 puan) 
            - Teknoloji uyumluluğu (20 puan)
            - Eğitim uyumluluğu (15 puan)
            
            JSON formatında döndür:
            {{
                "similarity_score": 85,
                "match_reasons": ["Python becerisi uyumlu", "2 yıl deneyim uygun"],
                "missing_skills": ["Docker eksik"]
            }}
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )

            text = response.text.strip()
            if text.startswith('```json'):
                text = text.replace('```json', '').replace('```', '').strip()
            elif text.startswith('```'):
                text = text.replace('```', '').strip()

            try:
                result = json.loads(text)
                return result
            except json.JSONDecodeError:
                return self._fallback_similarity(cv_analysis, job_description, job_title)

        except Exception as e:
            print(f"Benzerlik hesaplama hatası: {e}")
            return self._fallback_similarity(cv_analysis, job_description, job_title)

    def _format_cv_for_analysis(self, cv_analysis):
        """CV analizini formatlar"""
        parts = []
        if cv_analysis.get('skills'):
            parts.append(f"Beceriler: {', '.join(cv_analysis['skills'])}")
        if cv_analysis.get('technologies'):
            parts.append(f"Teknolojiler: {', '.join(cv_analysis['technologies'])}")
        if cv_analysis.get('job_titles'):
            parts.append(f"Önceki Pozisyonlar: {', '.join(cv_analysis['job_titles'])}")
        if cv_analysis.get('education'):
            parts.append(f"Eğitim: {', '.join(cv_analysis['education'])}")
        if cv_analysis.get('experience_years'):
            parts.append(f"Deneyim: {cv_analysis['experience_years']} yıl")
        
        return '\n'.join(parts)

    def _format_cv_for_comparison(self, cv_analysis):
        """CV'yi karşılaştırma için formatlar"""
        return self._format_cv_for_analysis(cv_analysis)

    def _format_job_for_comparison(self, job_description, job_title, job_requirements):
        """İş açıklamasını karşılaştırma için formatlar"""
        parts = [f"Pozisyon: {job_title}"]
        if job_description:
            parts.append(f"Açıklama: {job_description}")
        if job_requirements:
            parts.append(f"Gereksinimler: {job_requirements}")
        
        return '\n'.join(parts)

    def _create_jobs_for_position(self, position):
        """Bir pozisyon için gerçekçi iş ilanları oluşturur"""
        companies = [
            "Yapı Kredi Teknoloji", "Garanti BBVA", "İş Bankası", "Akbank", "QNB Finansbank",
            "Deel", "Remote.com", "Upwork", "Fiverr", "Toptal",
            "Getir", "Trendyol", "Hepsiburada", "N11", "GittiGidiyor",
            "Turkcell", "Vodafone", "Turk Telekom", "Superonline", "Netgsm",
            "Microsoft", "Google", "Amazon", "Meta", "Apple",
            "Borusan", "Koç Holding", "Sabancı Holding", "Doğuş Holding", "Eczacıbaşı"
        ]
        
        locations = [
            "İstanbul, Türkiye", "Ankara, Türkiye", "İzmir, Türkiye", "Bursa, Türkiye", "Antalya, Türkiye"
        ]
        
        work_types = [
            "Tam Zamanlı", "Yarı Zamanlı", "Uzaktan", "Hibrit"
        ]
        
        experience_levels = [
            "Junior", "Mid", "Senior", "Lead", "Manager"
        ]
        
        jobs = []
        
        for i in range(2):  # Her pozisyon için 2 iş ilanı
            company = companies[i % len(companies)]
            location = locations[i % len(locations)]
            work_type = work_types[i % len(work_types)]
            experience = experience_levels[i % len(experience_levels)]
            
            # Pozisyona göre başlık oluştur
            if experience == "Junior":
                title = f"Junior {position}"
            elif experience == "Senior":
                title = f"Senior {position}"
            elif experience == "Lead":
                title = f"Lead {position}"
            elif experience == "Manager":
                title = f"{position} Manager"
            else:
                title = position
            
            # Gerçekçi açıklama oluştur
            description = self._generate_job_description(position, experience, company)
            requirements = self._generate_job_requirements(position, experience)
            
            # LinkedIn URL oluştur
            url = self._create_linkedin_url(title, company, location)
            
            job = {
                'title': title,
                'company': company,
                'location': f"{location} ({work_type})",
                'url': url,
                'posted_time': f"{i+1} gün önce",
                'employment_type': work_type,
                'source': 'LinkedIn',
                'description': description,
                'experience_level': experience,
                'requirements': requirements,
                'match_score': 0,
                'match_reasons': [],
                'missing_skills': []
            }
            
            jobs.append(job)
        
        return jobs

    def _generate_job_description(self, position, experience, company):
        """İş açıklaması oluşturur"""
        descriptions = {
            "Data Scientist": f"{company} bünyesinde {experience.lower()} seviye Data Scientist arıyoruz. Veri analizi, makine öğrenmesi ve istatistiksel modelleme konularında deneyimli adaylar tercih edilir.",
            "Machine Learning Engineer": f"{company} için {experience.lower()} Machine Learning Engineer pozisyonu. ML modellerinin geliştirilmesi, deployment ve optimizasyon konularında deneyimli adaylar arıyoruz.",
            "Python Developer": f"{company} bünyesinde {experience.lower()} Python Developer arıyoruz. Web geliştirme, API tasarımı ve veritabanı yönetimi konularında deneyimli adaylar tercih edilir.",
            "Software Engineer": f"{company} için {experience.lower()} Software Engineer pozisyonu. Yazılım geliştirme, sistem tasarımı ve kod kalitesi konularında deneyimli adaylar arıyoruz.",
            "Business Analyst": f"{company} bünyesinde {experience.lower()} Business Analyst arıyoruz. İş süreçleri analizi, veri analizi ve raporlama konularında deneyimli adaylar tercih edilir."
        }
        
        return descriptions.get(position, f"{company} bünyesinde {experience.lower()} {position} pozisyonu için deneyimli adaylar arıyoruz.")

    def _generate_job_requirements(self, position, experience):
        """İş gereksinimleri oluşturur"""
        base_requirements = {
            "Data Scientist": "Python, SQL, Machine Learning, Statistics",
            "Machine Learning Engineer": "Python, TensorFlow, PyTorch, AWS, Docker",
            "Python Developer": "Python, Django/Flask, SQL, Git, REST API",
            "Software Engineer": "Java/Python/C++, Git, Agile, System Design",
            "Business Analyst": "SQL, Excel, Tableau, Business Process Analysis"
        }
        
        experience_requirements = {
            "Junior": "0-2 yıl deneyim",
            "Mid": "2-5 yıl deneyim", 
            "Senior": "5+ yıl deneyim",
            "Lead": "7+ yıl deneyim, takım liderliği",
            "Manager": "8+ yıl deneyim, yönetim deneyimi"
        }
        
        base = base_requirements.get(position, "İlgili alanlarda deneyim")
        exp = experience_requirements.get(experience, "Deneyimli")
        
        return f"{base}, {exp}"

    def _create_linkedin_url(self, title, company, location):
        """LinkedIn URL oluşturur"""
        title_encoded = title.replace(' ', '%20')
        company_encoded = company.replace(' ', '%20')
        location_encoded = location.split(',')[0].replace(' ', '%20')
        
        return f"https://www.linkedin.com/jobs/search/?keywords={title_encoded}%20{company_encoded}&location={location_encoded}&f_TPR=r86400"

    def _get_fallback_positions(self, cv_analysis):
        """CV analizi başarısız olursa fallback pozisyonlar"""
        positions = []
        
        if cv_analysis.get('skills'):
            if any('python' in skill.lower() for skill in cv_analysis['skills']):
                positions.append('Python Developer')
            if any('data' in skill.lower() for skill in cv_analysis['skills']):
                positions.append('Data Scientist')
            if any('machine' in skill.lower() or 'ml' in skill.lower() for skill in cv_analysis['skills']):
                positions.append('Machine Learning Engineer')
        
        if cv_analysis.get('technologies'):
            if any('java' in tech.lower() for tech in cv_analysis['technologies']):
                positions.append('Software Engineer')
            if any('sql' in tech.lower() for tech in cv_analysis['technologies']):
                positions.append('Business Analyst')
        
        if not positions:
            positions = ['Software Engineer', 'Data Scientist', 'Business Analyst']
        
        return positions[:3]

    def _fallback_similarity(self, cv_analysis, job_description, job_title):
        """Fallback benzerlik hesaplama"""
        score = 50  # Ortalama skor
        
        # Basit kelime eşleştirme
        cv_text = ' '.join([
            ' '.join(cv_analysis.get('skills', [])),
            ' '.join(cv_analysis.get('technologies', [])),
            ' '.join(cv_analysis.get('job_titles', []))
        ]).lower()
        
        job_text = f"{job_title} {job_description}".lower()
        
        cv_words = set(cv_text.split())
        job_words = set(job_text.split())
        
        if cv_words and job_words:
            common_words = cv_words.intersection(job_words)
            score = min(100, 50 + len(common_words) * 10)
        
        return {
            "similarity_score": score,
            "match_reasons": ["Temel beceri uyumluluğu"],
            "missing_skills": []
        } 