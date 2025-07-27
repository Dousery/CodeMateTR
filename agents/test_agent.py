import google.generativeai as genai
import json
import re
import requests
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import time

class TestAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def generate_questions(self, num_questions=10, difficulty='mixed'):
        prompt = f"""
        {self.interest} alanında geliştiriciler için {num_questions} adet çoktan seçmeli sınav sorusu üret. 
        Zorluk seviyesi: {difficulty} (beginner, intermediate, advanced, mixed)
        
        Sorular şu konuları kapsamalı:
        - Temel kavramlar ve terminoloji
        - Pratik uygulama senaryoları  
        - Best practices ve design patterns
        - Problem çözme becerileri
        - Güncel teknolojiler ve yaklaşımlar
        
        Her soru için JSON formatında yanıt ver:
        {{
            "questions": [
                {{
                    "id": 1,
                    "question": "Soru metni burada",
                    "options": [
                        "A) İlk seçenek",
                        "B) İkinci seçenek", 
                        "C) Üçüncü seçenek",
                        "D) Dördüncü seçenek"
                    ],
                    "correct_answer": "A",
                    "explanation": "Doğru cevabın açıklaması",
                    "difficulty": "intermediate",
                    "category": "Temel Kavramlar"
                }}
            ]
        }}
        
        Lütfen sadece geçerli JSON formatında yanıt ver, başka açıklama ekleme.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # JSON parse etmeye çalış
            response_text = response.text.strip()
            
            # JSON başlangıç ve bitiş noktalarını bul
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx]
                data = json.loads(json_text)
                questions = data.get('questions', [])
                
                # Eksik alanları kontrol et ve düzelt
                for i, q in enumerate(questions):
                    if 'id' not in q:
                        q['id'] = i + 1
                    if 'difficulty' not in q:
                        q['difficulty'] = 'intermediate'
                    if 'category' not in q:
                        q['category'] = self.interest
                    if 'explanation' not in q:
                        q['explanation'] = ''
                    
                    # Seçenekleri standart formata çevir
                    if 'options' in q:
                        formatted_options = []
                        for j, option in enumerate(q['options']):
                            letter = chr(65 + j)  # A, B, C, D
                            if not option.startswith(f'{letter})'):
                                option = f'{letter}) {option}'
                            formatted_options.append(option)
                        q['options'] = formatted_options
                
                return questions[:num_questions]
                
        except Exception as e:
            print(f"JSON parse hatası: {e}")
            # Fallback: Eski metod
            return self._generate_questions_fallback(num_questions)
            
    def _generate_questions_fallback(self, num_questions):
        """Gemini JSON döndüremezse eski yöntemle soru üret"""
        prompt = f"""
        {self.interest} alanında geliştiriciler için {num_questions} adet çoktan seçmeli sınav sorusu üret. 
        Her soru için 4 şık (A, B, C, D) ve doğru cevabı belirt. Format:
        
        Soru 1: [Soru metni]
        A) [Seçenek 1]
        B) [Seçenek 2] 
        C) [Seçenek 3]
        D) [Seçenek 4]
        Cevap: A
        
        Soru 2: [Soru metni]
        ...
        """
        response = self.model.generate_content(prompt)
        questions = []
        current = {}
        
        for line in response.text.split('\n'):
            line = line.strip()
            if line.startswith('Soru') and ':' in line:
                if current and 'question' in current:
                    questions.append(current)
                current = {
                    'id': len(questions) + 1,
                    'question': line.split(':', 1)[1].strip(), 
                    'options': [], 
                    'correct_answer': '',
                    'difficulty': 'intermediate',
                    'category': self.interest,
                    'explanation': ''
                }
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                if 'options' in current:
                    current['options'].append(line)
            elif line.startswith('Cevap:'):
                current['correct_answer'] = line.split(':')[1].strip()
                
        if current and 'question' in current:
            questions.append(current)
            
        return questions[:num_questions]

    def evaluate_answers(self, user_answers, questions, time_taken=None):
        """
        Kullanıcı cevaplarını değerlendir ve detaylı sonuç döndür
        """
        results = []
        correct_count = 0
        difficulty_stats = {'beginner': {'total': 0, 'correct': 0}, 
                           'intermediate': {'total': 0, 'correct': 0},
                           'advanced': {'total': 0, 'correct': 0}}
        
        for idx, (user_ans, q) in enumerate(zip(user_answers, questions)):
            # Doğru cevap harfini al (A, B, C, D)
            correct_letter = q.get('correct_answer', '').strip()
            user_letter = user_ans.strip() if user_ans else ''
            
            is_correct = (user_letter == correct_letter)
            if is_correct:
                correct_count += 1
                
            # Zorluk seviyesi istatistiklerini güncelle
            difficulty = q.get('difficulty', 'intermediate')
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty]['total'] += 1
                if is_correct:
                    difficulty_stats[difficulty]['correct'] += 1
            
            results.append({
                'question_id': q.get('id', idx + 1),
                'question': q['question'],
                'user_answer': user_ans,
                'correct_answer': correct_letter,
                'is_correct': is_correct,
                'explanation': q.get('explanation', ''),
                'difficulty': difficulty,
                'category': q.get('category', self.interest)
            })
        
        # Genel performans hesapla
        total_questions = len(questions)
        success_rate = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Seviye belirleme
        level = self._determine_skill_level(success_rate, difficulty_stats)
        
        # Zaman performansı
        time_performance = self._evaluate_time_performance(time_taken, total_questions) if time_taken else None
        
        # Öneriler
        recommendations = self._generate_recommendations(success_rate, difficulty_stats, results)
        
        return {
            'results': results,
            'summary': {
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'success_rate': round(success_rate, 2),
                'skill_level': level,
                'time_taken': time_taken,
                'time_performance': time_performance
            },
            'difficulty_breakdown': difficulty_stats,
            'recommendations': recommendations,
            'weak_areas': self._identify_weak_areas(results),
            'strong_areas': self._identify_strong_areas(results)
        }
    
    def _determine_skill_level(self, success_rate, difficulty_stats):
        """Başarı oranı ve zorluk seviyelerine göre genel seviye belirle"""
        if success_rate >= 90:
            return "Expert"
        elif success_rate >= 80:
            return "Advanced" 
        elif success_rate >= 70:
            return "Intermediate"
        elif success_rate >= 60:
            return "Beginner+"
        else:
            return "Beginner"
    
    def _evaluate_time_performance(self, time_taken, total_questions):
        """Zaman performansını değerlendir"""
        if not time_taken:
            return None
            
        # Soru başına ortalama süre (saniye)
        avg_time_per_question = time_taken / total_questions
        
        # İdeal süre: soru başına 2-3 dakika
        ideal_time_per_question = 150  # 2.5 dakika
        
        if avg_time_per_question <= ideal_time_per_question * 0.5:
            return "Çok Hızlı - Daha dikkatli olun"
        elif avg_time_per_question <= ideal_time_per_question:
            return "Optimal Hız"
        elif avg_time_per_question <= ideal_time_per_question * 1.5:
            return "Normal Hız"
        else:
            return "Yavaş - Daha hızlı karar verin"
    
    def _identify_weak_areas(self, results):
        """Zayıf olunan konuları belirle"""
        category_stats = {}
        for result in results:
            category = result['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'correct': 0}
            category_stats[category]['total'] += 1
            if result['is_correct']:
                category_stats[category]['correct'] += 1
        
        weak_areas = []
        for category, stats in category_stats.items():
            success_rate = (stats['correct'] / stats['total']) * 100
            if success_rate < 60:  # %60'ın altında başarı
                weak_areas.append({
                    'category': category,
                    'success_rate': round(success_rate, 2),
                    'questions_count': stats['total']
                })
        
        return sorted(weak_areas, key=lambda x: x['success_rate'])
    
    def _identify_strong_areas(self, results):
        """Güçlü olunan konuları belirle"""
        category_stats = {}
        for result in results:
            category = result['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'correct': 0}
            category_stats[category]['total'] += 1
            if result['is_correct']:
                category_stats[category]['correct'] += 1
        
        strong_areas = []
        for category, stats in category_stats.items():
            success_rate = (stats['correct'] / stats['total']) * 100
            if success_rate >= 80:  # %80'in üstünde başarı
                strong_areas.append({
                    'category': category,
                    'success_rate': round(success_rate, 2),
                    'questions_count': stats['total']
                })
        
        return sorted(strong_areas, key=lambda x: x['success_rate'], reverse=True)
    
    def _generate_recommendations(self, success_rate, difficulty_stats, results):
        """Performansa göre öneriler üret"""
        recommendations = []
        
        if success_rate < 50:
            recommendations.append("Temel kavramları tekrar gözden geçirin")
            recommendations.append("Daha fazla pratik yapın")
        elif success_rate < 70:
            recommendations.append("Orta seviye konulara odaklanın")
            recommendations.append("Pratik projeler yaparak deneyim kazanın")
        elif success_rate < 85:
            recommendations.append("İleri seviye konuları öğrenmeye başlayın")
            recommendations.append("Gerçek projeler üzerinde çalışın")
        else:
            recommendations.append("Mükemmel! Bilginizi başkalarıyla paylaşın")
            recommendations.append("Yeni teknolojileri takip etmeye devam edin")
        
        return recommendations

    def suggest_resources(self, topic, num_resources=5):
        """Belirli bir konu için kaynak önerisi"""
        prompt = f"""
        {topic} konusunda öğrenme eksikliklerini gidermek isteyen bir geliştiriciye {num_resources} adet kaliteli kaynak öner.
        
        Kaynaklar şunları içermeli:
        - YouTube videoları/kanalları
        - Online kurslar (Udemy, Coursera, vs)
        - Belgeler ve rehberler
        - Pratik projeler ve örnekler
        - Kitap önerileri
        
        Her kaynak için şu formatı kullan:
        - Başlık: [Kaynak başlığı]
        - Tür: [Video/Kurs/Doküman/Proje/Kitap]
        - Açıklama: [Kısa açıklama]
        - Seviye: [Başlangıç/Orta/İleri]
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Basitçe satır satır ayır ve formatla
            resources = []
            current_resource = {}
            
            for line in response.text.split('\n'):
                line = line.strip()
                if line.startswith('- Başlık:'):
                    if current_resource:
                        resources.append(current_resource)
                    current_resource = {'title': line.replace('- Başlık:', '').strip()}
                elif line.startswith('- Tür:'):
                    current_resource['type'] = line.replace('- Tür:', '').strip()
                elif line.startswith('- Açıklama:'):
                    current_resource['description'] = line.replace('- Açıklama:', '').strip()
                elif line.startswith('- Seviye:'):
                    current_resource['level'] = line.replace('- Seviye:', '').strip()
            
            if current_resource:
                resources.append(current_resource)
                
            return resources[:num_resources]
            
        except Exception as e:
            # Fallback basit kaynak listesi
            return [
                {
                    'title': f'{topic} temel rehberi',
                    'type': 'Doküman',
                    'description': 'Temel kavramları öğrenmek için',
                    'level': 'Başlangıç'
                }
            ]

    def search_web_resources(self, topic, num_results=5):
        """Web search ile YouTube video ve web sitesi önerisi - Gelişmiş versiyon"""
        try:
            # Kullanıcının alanına özgü arama terimleri oluştur
            search_terms = self._generate_smart_search_terms(topic)
            
            # Gemini ile alan-spesifik web kaynakları öner
            search_prompt = f"""
            {self.interest} alanında çalışan bir {topic} konusunda eksikliği olan geliştirici için kaynak öner.
            
            Önerilerin {self.interest} alanı ile doğrudan alakalı olmasına dikkat et. Şu türde kaynakları JSON formatında ver:
            {{
                "youtube_videos": [
                    {{
                        "title": "Video başlığı ({self.interest} odaklı)",
                        "description": "{self.interest} alanında {topic} konusunu anlatan video",
                        "search_query": "{self.interest} {topic} tutorial",
                        "level": "Başlangıç/Orta/İleri",
                        "duration_estimate": "15-45 dakika",
                        "relevance_score": 0.9,
                        "specific_skills": ["{self.interest} ile ilgili beceriler"]
                    }}
                ],
                "websites": [
                    {{
                        "title": "{self.interest} için {topic} rehberi", 
                        "description": "{self.interest} geliştiricilere yönelik {topic} açıklaması",
                        "search_query": "{self.interest} {topic} guide documentation",
                        "type": "Tutorial/Documentation/Blog/Course",
                        "level": "Başlangıç/Orta/İleri",
                        "relevance_score": 0.95,
                        "specific_skills": ["{self.interest} ile ilgili beceriler"]
                    }}
                ],
                "specialized_resources": [
                    {{
                        "title": "{self.interest} {topic} özel kaynağı",
                        "description": "Sadece {self.interest} alanına özel {topic} kaynağı",
                        "search_query": "{self.interest} specific {topic}",
                        "type": "Framework/Library/Tool",
                        "level": "Orta/İleri",
                        "relevance_score": 1.0,
                        "specific_skills": ["{self.interest} özel araçları"]
                    }}
                ]
            }}
            
            Her kategoriden en az 3 kaynak öner. Kaynaklar mutlaka {self.interest} alanıyla ilgili olmalı.
            Sadece JSON formatında yanıt ver, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(search_prompt)
            response_text = response.text.strip()
            
            # JSON parse et
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            try:
                search_results = json.loads(response_text)
                
                # URL'leri oluştur ve alan-spesifik hale getir
                self._enhance_search_results_with_urls(search_results, topic)
                
                # Alan-spesifik filtreleme ve scoring
                search_results = self._filter_and_score_results(search_results, topic)
                
                return search_results
                
            except json.JSONDecodeError:
                # Fallback
                return self._create_enhanced_fallback_resources(topic)
                
        except Exception as e:
            print(f"Enhanced web search error: {e}")
            return self._create_enhanced_fallback_resources(topic)
    
    def _generate_smart_search_terms(self, topic):
        """Kullanıcının alanına göre akıllı arama terimleri oluştur"""
        base_terms = [topic]
        
        # Alan-spesifik terimler ekle
        interest_specific_terms = {
            'Data Science': ['pandas', 'numpy', 'scikit-learn', 'matplotlib', 'jupyter'],
            'Web Development': ['javascript', 'react', 'node.js', 'html', 'css', 'framework'],
            'Machine Learning': ['tensorflow', 'pytorch', 'neural networks', 'deep learning'],
            'Mobile Development': ['flutter', 'react native', 'android', 'ios', 'app development'],
            'Backend Development': ['api', 'database', 'server', 'microservices'],
            'DevOps': ['docker', 'kubernetes', 'ci/cd', 'cloud', 'infrastructure'],
            'Cybersecurity': ['security', 'penetration testing', 'vulnerability', 'encryption'],
            'Game Development': ['unity', 'unreal', 'game engine', 'graphics', '3d modeling']
        }
        
        if self.interest in interest_specific_terms:
            base_terms.extend(interest_specific_terms[self.interest])
        
        return base_terms
    
    def _enhance_search_results_with_urls(self, search_results, topic):
        """Search sonuçlarına gelişmiş URL'ler ekle"""
        
        # YouTube videoları için URL'ler
        for video in search_results.get('youtube_videos', []):
            search_query = video.get('search_query', f"{self.interest} {topic} tutorial")
            query = quote_plus(search_query)
            video['url'] = f"https://www.youtube.com/results?search_query={query}"
            video['type'] = 'YouTube Video'
            
            # Alan-spesifik kanal önerileri
            if self.interest == 'Data Science':
                video['recommended_channels'] = ['3Blue1Brown', 'StatQuest', 'Krish Naik']
            elif self.interest == 'Web Development':
                video['recommended_channels'] = ['Traversy Media', 'The Net Ninja', 'Academind']
            elif self.interest == 'Machine Learning':
                video['recommended_channels'] = ['Two Minute Papers', 'DeepLearningAI', 'Lex Fridman']
        
        # Web siteleri için URL'ler
        for website in search_results.get('websites', []):
            search_query = website.get('search_query', f"{self.interest} {topic} guide")
            query = quote_plus(search_query)
            website['url'] = f"https://www.google.com/search?q={query}"
            
            # Alan-spesifik site önerileri
            if self.interest == 'Data Science':
                website['recommended_sites'] = ['Kaggle', 'Towards Data Science', 'DataCamp']
            elif self.interest == 'Web Development':
                website['recommended_sites'] = ['MDN Web Docs', 'W3Schools', 'CSS-Tricks']
            elif self.interest == 'Machine Learning':
                website['recommended_sites'] = ['Papers with Code', 'Distill.pub', 'Machine Learning Mastery']
        
        # Özel kaynaklar için URL'ler
        for resource in search_results.get('specialized_resources', []):
            search_query = resource.get('search_query', f"{self.interest} {topic} framework")
            query = quote_plus(search_query)
            resource['url'] = f"https://www.google.com/search?q={query}"
            resource['type'] = resource.get('type', 'Specialized Resource')
    
    def _filter_and_score_results(self, search_results, topic):
        """Sonuçları alan-spesifik olarak filtrele ve skorla"""
        
        # Relevance scoring için anahtar kelimeler
        interest_keywords = {
            'Data Science': ['data', 'analysis', 'statistics', 'pandas', 'python', 'visualization'],
            'Web Development': ['web', 'frontend', 'backend', 'javascript', 'html', 'css', 'framework'],
            'Machine Learning': ['ml', 'ai', 'neural', 'tensorflow', 'pytorch', 'algorithm'],
            'Mobile Development': ['mobile', 'app', 'android', 'ios', 'flutter', 'react native'],
            'Backend Development': ['api', 'server', 'database', 'backend', 'microservices'],
            'DevOps': ['devops', 'docker', 'kubernetes', 'cloud', 'infrastructure', 'deployment'],
            'Cybersecurity': ['security', 'cyber', 'penetration', 'vulnerability', 'encryption'],
            'Game Development': ['game', 'unity', 'unreal', 'graphics', '3d', 'gaming']
        }
        
        keywords = interest_keywords.get(self.interest, [])
        
        # Her kategoriyi skorla ve filtrele
        for category in ['youtube_videos', 'websites', 'specialized_resources']:
            if category in search_results:
                scored_items = []
                for item in search_results[category]:
                    score = self._calculate_relevance_score(item, keywords, topic)
                    if score > 0.3:  # Minimum relevance threshold
                        item['calculated_relevance_score'] = score
                        scored_items.append(item)
                
                # Score'a göre sırala
                scored_items.sort(key=lambda x: x.get('calculated_relevance_score', 0), reverse=True)
                search_results[category] = scored_items[:3]  # Top 3 al
        
        return search_results
    
    def _calculate_relevance_score(self, item, keywords, topic):
        """Item'ın alan ile uyumunu hesapla"""
        text_to_score = f"{item.get('title', '')} {item.get('description', '')} {item.get('search_query', '')}"
        text_to_score = text_to_score.lower()
        
        score = 0.0
        
        # Alan anahtar kelimeleri
        for keyword in keywords:
            if keyword.lower() in text_to_score:
                score += 0.2
        
        # Topic kelimesi
        if topic.lower() in text_to_score:
            score += 0.3
        
        # Interest alanı
        if self.interest.lower() in text_to_score:
            score += 0.4
        
        # Eğitim terimleri bonus
        education_terms = ['tutorial', 'guide', 'learning', 'course', 'documentation', 'examples']
        for term in education_terms:
            if term in text_to_score:
                score += 0.1
        
        return min(score, 1.0)  # Maximum 1.0
    
    def _create_enhanced_fallback_resources(self, topic):
        """Gelişmiş fallback kaynakları"""
        interest_specific_searches = {
            'Data Science': f"data science {topic} python pandas tutorial",
            'Web Development': f"web development {topic} javascript tutorial",
            'Machine Learning': f"machine learning {topic} tensorflow pytorch tutorial",
            'Mobile Development': f"mobile app development {topic} flutter react native",
            'Backend Development': f"backend development {topic} api database tutorial",
            'DevOps': f"devops {topic} docker kubernetes cloud tutorial",
            'Cybersecurity': f"cybersecurity {topic} ethical hacking tutorial",
            'Game Development': f"game development {topic} unity unreal tutorial"
        }
        
        specific_search = interest_specific_searches.get(self.interest, f"{self.interest} {topic} tutorial")
        youtube_query = quote_plus(specific_search)
        google_query = quote_plus(f"{self.interest} {topic} guide documentation")
        
        return {
            "youtube_videos": [
                {
                    "title": f"{self.interest} için {topic} Temelleri",
                    "description": f"{self.interest} alanında {topic} konusunu öğrenmek için video rehberi",
                    "url": f"https://www.youtube.com/results?search_query={youtube_query}",
                    "type": "YouTube Video",
                    "level": "Başlangıç",
                    "duration_estimate": "20-40 dakika",
                    "relevance_score": 0.8,
                    "specific_skills": [f"{self.interest} temel becerileri"]
                },
                {
                    "title": f"{self.interest} {topic} İleri Seviye",
                    "description": f"{self.interest} geliştiricileri için ileri seviye {topic} teknikleri",
                    "url": f"https://www.youtube.com/results?search_query={quote_plus(f'advanced {specific_search}')}",
                    "type": "YouTube Video", 
                    "level": "İleri",
                    "duration_estimate": "30-60 dakika",
                    "relevance_score": 0.9,
                    "specific_skills": [f"{self.interest} ileri seviye beceriler"]
                }
            ],
            "websites": [
                {
                    "title": f"{self.interest} {topic} Resmi Dokümantasyonu",
                    "description": f"{self.interest} alanında {topic} için resmi rehber ve API dokümantasyonu",
                    "url": f"https://www.google.com/search?q={google_query}",
                    "type": "Documentation",
                    "level": "Tüm Seviyeler",
                    "relevance_score": 0.95,
                    "specific_skills": [f"{self.interest} dokümantasyon okuma"]
                },
                {
                    "title": f"{self.interest} {topic} Pratik Örnekleri",
                    "description": f"{self.interest} projelerinde {topic} kullanımına dair pratik örnekler",
                    "url": f"https://www.google.com/search?q={quote_plus(f'{self.interest} {topic} examples projects')}",
                    "type": "Tutorial",
                    "level": "Orta",
                    "relevance_score": 0.85,
                    "specific_skills": [f"{self.interest} proje geliştirme"]
                }
            ],
            "specialized_resources": [
                {
                    "title": f"{self.interest} {topic} Araçları ve Kütüphaneler",
                    "description": f"{self.interest} geliştiricileri için {topic} konusunda özel araçlar",
                    "url": f"https://www.google.com/search?q={quote_plus(f'{self.interest} {topic} tools libraries frameworks')}",
                    "type": "Tools & Libraries",
                    "level": "Orta/İleri",
                    "relevance_score": 1.0,
                    "specific_skills": [f"{self.interest} araç kullanımı"]
                }
            ]
        }
    
    def _create_fallback_web_resources(self, topic):
        """Basit fallback kaynakları (eski versiyon uyumluluğu için)"""
        return self._create_enhanced_fallback_resources(topic)