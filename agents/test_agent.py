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
        
        # Zayıf ve güçlü alanları belirle
        weak_areas = self._identify_weak_areas(results)
        strong_areas = self._identify_strong_areas(results)
        
        # Zayıf alanlar için kaynak önerileri ekle
        weak_topics = [area['category'] for area in weak_areas]
        suggested_resources = self.suggest_resources(weak_topics, num_resources=8) if weak_topics else []
        
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
            'weak_areas': weak_areas,
            'strong_areas': strong_areas,
            'suggested_resources': suggested_resources  # Dinamik kaynak önerileri
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

    def suggest_resources(self, topics, num_resources=8):
        """Birden fazla zayıf konu için dinamik kaynak önerisi - kişiselleştirilmiş"""
        all_resources = []
        
        # Eğer topics bir string ise, listeye çevir
        if isinstance(topics, str):
            topics = [topics]
        
        # Her zayıf konu için kaynak öner
        for topic in topics[:3]:  # En fazla 3 zayıf konu
            topic_resources = self._get_comprehensive_topic_resources(topic)
            
            # Topic adını ekle
            for resource in topic_resources:
                resource['related_topic'] = topic
                resource['priority'] = self._calculate_topic_priority(topic)
            
            all_resources.extend(topic_resources)
        
        # Kaynakları çeşitlendir ve filtrele
        diversified_resources = self._diversify_resource_types(all_resources)
        
        # Prioritye göre sırala
        diversified_resources.sort(key=lambda x: x.get('priority', 0.5), reverse=True)
        
        return diversified_resources[:num_resources]
    
    def _get_comprehensive_topic_resources(self, topic):
        """Bir konu için kapsamlı kaynak listesi - Video, site, kurs karışımı"""
        
        # Önce gerçek URL'leri al
        real_resources = self._get_real_topic_urls(topic)
        
        # Topic'e özel YouTube ve web kaynakları ekle
        dynamic_resources = self._generate_dynamic_topic_resources(topic)
        
        # Kaynakları birleştir
        all_resources = real_resources + dynamic_resources
        
        # Her kaynağa skor ekle
        for resource in all_resources:
            resource['relevance_score'] = self._calculate_resource_relevance(resource, topic)
        
        return all_resources
    
    def _generate_dynamic_topic_resources(self, topic):
        """Topic'e özel dinamik kaynak üretimi"""
        
        # Alan-spesifik YouTube kanal önerileri
        youtube_channels = {
            'Data Science': ['3Blue1Brown', 'StatQuest', 'Krish Naik', 'Data School', 'Sentdex'],
            'Web Development': ['Traversy Media', 'The Net Ninja', 'Academind', 'Web Dev Simplified', 'Kevin Powell'],
            'AI': ['Two Minute Papers', 'Lex Fridman', 'DeepLearningAI', 'AI Explained', '3Blue1Brown'],
            'Mobile': ['Flutter', 'Coding with Tea', 'Code with Andrea', 'Flutter Explained'],
            'Cyber Security': ['The Cyber Mentor', 'Null Byte', 'LiveOverflow', 'IppSec', 'Professor Messer']
        }
        
        # Alan-spesifik site önerileri
        recommended_sites = {
            'Data Science': ['Kaggle', 'Towards Data Science', 'Analytics Vidhya', 'DataCamp'],
            'Web Development': ['MDN Web Docs', 'CSS-Tricks', 'Dev.to', 'Smashing Magazine'],
            'AI': ['Papers with Code', 'Distill.pub', 'OpenAI Blog', 'Google AI Blog'],
            'Mobile': ['Flutter.dev', 'Android Developers', 'Ray Wenderlich', 'Medium Mobile Dev'],
            'Cyber Security': ['OWASP', 'Krebs on Security', 'TryHackMe', 'HackerOne']
        }
        
        dynamic_resources = []
        
        # YouTube video önerileri
        channels = youtube_channels.get(self.interest, ['freeCodeCamp', 'Programming with Mosh'])
        for i, channel in enumerate(channels[:2]):
            search_query = f"{topic} {self.interest} {channel}".replace(' ', '+')
            dynamic_resources.append({
                'title': f'{topic} Öğretimi - {channel}',
                'url': f'https://www.youtube.com/results?search_query={search_query}',
                'type': 'YouTube Video',
                'description': f'{channel} kanalından {topic} konulu videolar',
                'level': 'Orta' if i == 0 else 'Başlangıç',
                'source': 'YouTube',
                'estimated_duration': '15-45 dakika'
            })
        
        # Web sitesi önerileri
        sites = recommended_sites.get(self.interest, ['Stack Overflow', 'GitHub'])
        for i, site in enumerate(sites[:2]):
            search_query = f"{topic} {self.interest}".replace(' ', '+')
            dynamic_resources.append({
                'title': f'{topic} - {site} Kaynakları',
                'url': f'https://www.google.com/search?q=site:{site.lower().replace(" ", "")}.com+{search_query}',
                'type': 'Web Sitesi',
                'description': f'{site} üzerinde {topic} hakkında makaleler',
                'level': 'Tüm Seviyeler',
                'source': 'Web',
                'content_type': 'Makale/Tutorial'
            })
        
        # Özel alan kaynaklarına göre ek öneriler
        if self.interest == 'Data Science':
            dynamic_resources.append({
                'title': f'{topic} - Kaggle Datasets',
                'url': f'https://www.kaggle.com/search?q={topic.replace(" ", "+")}',
                'type': 'Dataset',
                'description': f'{topic} ile ilgili veri setleri',
                'level': 'Orta',
                'source': 'Kaggle',
                'content_type': 'Pratik Veri'
            })
        
        elif self.interest == 'Web Development':
            dynamic_resources.append({
                'title': f'{topic} - CodePen Examples',
                'url': f'https://codepen.io/search/pens?q={topic.replace(" ", "+")}',
                'type': 'Kod Örneği',
                'description': f'{topic} ile ilgili canlı kod örnekleri',
                'level': 'Orta',
                'source': 'CodePen',
                'content_type': 'İnteraktif Demo'
            })
        
        elif self.interest == 'AI':
            dynamic_resources.append({
                'title': f'{topic} - Papers with Code',
                'url': f'https://paperswithcode.com/search?q={topic.replace(" ", "+")}',
                'type': 'Araştırma',
                'description': f'{topic} konusunda akademik makaleler ve kod',
                'level': 'İleri',
                'source': 'Academia',
                'content_type': 'Araştırma Makalesi'
            })
        
        return dynamic_resources
    
    def _calculate_topic_priority(self, topic):
        """Topic'in öğrenme önceliğini hesapla"""
        
        # Temel konular daha yüksek öncelik
        fundamental_topics = {
            'Data Science': ['python', 'pandas', 'data analysis', 'statistics'],
            'Web Development': ['html', 'css', 'javascript', 'dom'],
            'AI': ['machine learning', 'algorithms', 'data structures'],
            'Mobile': ['flutter', 'dart', 'android', 'ui/ux'],
            'Cyber Security': ['networking', 'cryptography', 'security fundamentals']
        }
        
        topic_lower = topic.lower()
        fundamentals = fundamental_topics.get(self.interest, [])
        
        # Temel konu mu kontrol et
        for fundamental in fundamentals:
            if fundamental in topic_lower or topic_lower in fundamental:
                return 0.9  # Yüksek öncelik
        
        return 0.6  # Normal öncelik
    
    def _calculate_resource_relevance(self, resource, topic):
        """Kaynağın topic ile ilgisini hesapla"""
        
        title = resource.get('title', '').lower()
        description = resource.get('description', '').lower()
        resource_type = resource.get('type', '').lower()
        
        score = 0.0
        
        # Topic adı geçiyor mu
        if topic.lower() in title:
            score += 0.4
        if topic.lower() in description:
            score += 0.3
        
        # Alan adı geçiyor mu
        if self.interest.lower() in title:
            score += 0.2
        if self.interest.lower() in description:
            score += 0.1
        
        # Kaynak türü bonusu
        type_bonuses = {
            'video': 0.15,
            'youtube': 0.15,
            'tutorial': 0.10,
            'doküman': 0.08,
            'kurs': 0.12,
            'interactive': 0.10
        }
        
        for type_key, bonus in type_bonuses.items():
            if type_key in resource_type:
                score += bonus
                break
        
        return min(score, 1.0)
    
    def _diversify_resource_types(self, resources):
        """Kaynak türlerini çeşitlendir"""
        
        type_counts = {}
        diversified = []
        max_per_type = 3  # Her türden en fazla 3 kaynak
        
        # Önce relevance score'a göre sırala
        sorted_resources = sorted(resources, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        for resource in sorted_resources:
            resource_type = resource.get('type', 'Diğer')
            
            if type_counts.get(resource_type, 0) < max_per_type:
                diversified.append(resource)
                type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
        
        return diversified
    
    def _get_real_topic_urls(self, topic):
        """Konuya göre gerçek URL'leri döndür - Dinamik ve çeşitli kaynaklar"""
        topic_lower = topic.lower()
        
        # Kapsamlı alan-spesifik URL eşlemeleri
        url_mappings = {
            'Data Science': {
                'python': [
                    {'title': 'Python.org Resmi Dokümanları', 'url': 'https://docs.python.org/3/', 'type': 'Doküman', 'description': 'Python resmi dokümanları', 'level': 'Tüm Seviyeler'},
                    {'title': 'Python Temelları - YouTube', 'url': 'https://www.youtube.com/watch?v=kqtD5dpn9C8', 'type': 'Video', 'description': 'Python programlama temelleri', 'level': 'Başlangıç'},
                    {'title': 'Real Python Tutorials', 'url': 'https://realpython.com/', 'type': 'Tutorial', 'description': 'Kapsamlı Python öğrenme kaynağı', 'level': 'Orta'},
                    {'title': 'Python for Everybody Course', 'url': 'https://www.coursera.org/specializations/python', 'type': 'Kurs', 'description': 'Coursera Python kursu', 'level': 'Başlangıç'},
                    {'title': 'Corey Schafer Python Tutorials', 'url': 'https://www.youtube.com/user/schafer5', 'type': 'YouTube Kanal', 'description': 'Kaliteli Python video serisi', 'level': 'Orta'}
                ],
                'pandas': [
                    {'title': 'Pandas Resmi Dokümanları', 'url': 'https://pandas.pydata.org/docs/', 'type': 'Doküman', 'description': 'Pandas kütüphanesi resmi rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'Pandas Tutorial - Keith Galli', 'url': 'https://www.youtube.com/watch?v=vmEHCJofslg', 'type': 'Video', 'description': 'Kapsamlı Pandas öğretimi', 'level': 'Başlangıç'},
                    {'title': 'Pandas Tutorial - W3Schools', 'url': 'https://www.w3schools.com/python/pandas/', 'type': 'Tutorial', 'description': 'Adım adım pandas öğrenin', 'level': 'Başlangıç'},
                    {'title': '10 Minutes to Pandas', 'url': 'https://pandas.pydata.org/docs/user_guide/10min.html', 'type': 'Quick Start', 'description': 'Pandas hızlı başlangıç rehberi', 'level': 'Başlangıç'},
                    {'title': 'Data School Pandas', 'url': 'https://www.youtube.com/playlist?list=PL5-da3qGB5ICCsgW1MxlZ0Hq8LL5U3u9y', 'type': 'Video Serisi', 'description': 'Pandas video dersleri', 'level': 'Orta'}
                ],
                'data analysis': [
                    {'title': 'Kaggle Learn Data Analysis', 'url': 'https://www.kaggle.com/learn/data-analysis', 'type': 'Kurs', 'description': 'Ücretsiz veri analizi kursu', 'level': 'Orta'},
                    {'title': 'Data Analysis with Python - FreeCodeCamp', 'url': 'https://www.freecodecamp.org/learn/data-analysis-with-python/', 'type': 'Kurs', 'description': 'Python ile veri analizi', 'level': 'Başlangıç'},
                    {'title': 'Towards Data Science Blog', 'url': 'https://towardsdatascience.com/', 'type': 'Blog', 'description': 'Data science makaleleri', 'level': 'Tüm Seviyeler'},
                    {'title': 'Data Analysis Full Course - YouTube', 'url': 'https://www.youtube.com/watch?v=r-uOLxNrNk8', 'type': 'Video', 'description': 'Kapsamlı veri analizi eğitimi', 'level': 'Başlangıç'},
                    {'title': 'Sentdex Python Programming', 'url': 'https://www.youtube.com/user/sentdex', 'type': 'YouTube Kanal', 'description': 'Python ve veri analizi videoları', 'level': 'Orta'}
                ],
                'machine learning': [
                    {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/', 'type': 'Doküman', 'description': 'ML kütüphanesi rehberi', 'level': 'Orta'},
                    {'title': 'Machine Learning Explained - YouTube', 'url': 'https://www.youtube.com/watch?v=ukzFI9rgwfU', 'type': 'Video', 'description': 'ML kavramları açıklaması', 'level': 'Başlangıç'},
                    {'title': 'Machine Learning Mastery', 'url': 'https://machinelearningmastery.com/', 'type': 'Blog', 'description': 'Pratik ML teknikleri', 'level': 'Tüm Seviyeler'},
                    {'title': '3Blue1Brown Neural Networks', 'url': 'https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi', 'type': 'Video Serisi', 'description': 'Görsel neural network açıklamaları', 'level': 'Orta'}
                ]
            },
            'Web Development': {
                'javascript': [
                    {'title': 'MDN JavaScript Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide', 'type': 'Doküman', 'description': 'JavaScript resmi rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'JavaScript.info', 'url': 'https://javascript.info/', 'type': 'Tutorial', 'description': 'Modern JavaScript öğrenme rehberi', 'level': 'Başlangıç'},
                    {'title': 'JavaScript Crash Course - Traversy Media', 'url': 'https://www.youtube.com/watch?v=hdI2bqOjy3c', 'type': 'Video', 'description': 'JavaScript temelleri', 'level': 'Başlangıç'},
                    {'title': 'FreeCodeCamp JavaScript', 'url': 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/', 'type': 'Kurs', 'description': 'Ücretsiz JavaScript kursu', 'level': 'Başlangıç'},
                    {'title': 'Wes Bos JavaScript30', 'url': 'https://javascript30.com/', 'type': 'Challenge', 'description': '30 günde JavaScript projesi', 'level': 'Orta'},
                    {'title': 'Fun Fun Function', 'url': 'https://www.youtube.com/channel/UCO1cgjhGzsSYb1rsB4bFe4Q', 'type': 'YouTube Kanal', 'description': 'Eğlenceli JavaScript videoları', 'level': 'Orta'}
                ],
                'react': [
                    {'title': 'React Resmi Dokümanları', 'url': 'https://react.dev/', 'type': 'Doküman', 'description': 'React resmi öğrenme kaynağı', 'level': 'Tüm Seviyeler'},
                    {'title': 'React Course for Beginners - freeCodeCamp', 'url': 'https://www.youtube.com/watch?v=bMknfKXIFA8', 'type': 'Video', 'description': 'Kapsamlı React kursu', 'level': 'Başlangıç'},
                    {'title': 'React Tutorial - W3Schools', 'url': 'https://www.w3schools.com/react/', 'type': 'Tutorial', 'description': 'Adım adım React öğrenin', 'level': 'Başlangıç'},
                    {'title': 'React Course - Scrimba', 'url': 'https://scrimba.com/learn/learnreact', 'type': 'Kurs', 'description': 'İnteraktif React kursu', 'level': 'Orta'},
                    {'title': 'Academind React Series', 'url': 'https://www.youtube.com/playlist?list=PL55RiY5tL51oyA8euSROLjMFZbXaV7skS', 'type': 'Video Serisi', 'description': 'Detaylı React eğitimi', 'level': 'Orta'}
                ],
                'html': [
                    {'title': 'MDN HTML Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/HTML', 'type': 'Doküman', 'description': 'HTML resmi rehberi', 'level': 'Başlangıç'},
                    {'title': 'HTML Tutorial - W3Schools', 'url': 'https://www.w3schools.com/html/', 'type': 'Tutorial', 'description': 'Kapsamlı HTML öğrenme kaynağı', 'level': 'Başlangıç'},
                    {'title': 'HTML Crash Course - Traversy Media', 'url': 'https://www.youtube.com/watch?v=UB1O30fR-EE', 'type': 'Video', 'description': 'HTML temel eğitimi', 'level': 'Başlangıç'},
                    {'title': 'HTML Crash Course - FreeCodeCamp', 'url': 'https://www.freecodecamp.org/learn/responsive-web-design/', 'type': 'Kurs', 'description': 'HTML ve CSS öğrenin', 'level': 'Başlangıç'},
                    {'title': 'Kevin Powell CSS', 'url': 'https://www.youtube.com/kepowob', 'type': 'YouTube Kanal', 'description': 'HTML ve CSS uzmanı', 'level': 'Orta'}
                ],
                'css': [
                    {'title': 'MDN CSS Guide', 'url': 'https://developer.mozilla.org/en-US/docs/Web/CSS', 'type': 'Doküman', 'description': 'CSS resmi rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'CSS-Tricks', 'url': 'https://css-tricks.com/', 'type': 'Blog', 'description': 'CSS ipuçları ve teknikleri', 'level': 'Orta'},
                    {'title': 'CSS Tutorial - Net Ninja', 'url': 'https://www.youtube.com/playlist?list=PL4cUxeGkcC9gQeDH6xYhmO-db2mhoTSrT', 'type': 'Video Serisi', 'description': 'CSS video dersleri', 'level': 'Başlangıç'},
                    {'title': 'Flexbox Froggy', 'url': 'https://flexboxfroggy.com/', 'type': 'Oyun', 'description': 'Flexbox öğrenme oyunu', 'level': 'Başlangıç'},
                    {'title': 'CSS Grid Garden', 'url': 'https://cssgridgarden.com/', 'type': 'Oyun', 'description': 'CSS Grid öğrenme oyunu', 'level': 'Orta'}
                ],
                'node.js': [
                    {'title': 'Node.js Resmi Dokümanları', 'url': 'https://nodejs.org/en/docs/', 'type': 'Doküman', 'description': 'Node.js resmi rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'Node.js Crash Course - Traversy Media', 'url': 'https://www.youtube.com/watch?v=fBNz5xF-Kx4', 'type': 'Video', 'description': 'Node.js temelleri', 'level': 'Başlangıç'},
                    {'title': 'Learn Node.js - Codecademy', 'url': 'https://www.codecademy.com/learn/learn-node-js', 'type': 'Kurs', 'description': 'İnteraktif Node.js kursu', 'level': 'Başlangıç'},
                    {'title': 'Academind Node.js Course', 'url': 'https://www.youtube.com/playlist?list=PL55RiY5tL51oGJorjEgl6NVeDbx_fO5jR', 'type': 'Video Serisi', 'description': 'Kapsamlı Node.js eğitimi', 'level': 'Orta'}
                ]
            },
            'AI': {
                'machine learning': [
                    {'title': 'Machine Learning Course - Coursera', 'url': 'https://www.coursera.org/learn/machine-learning', 'type': 'Kurs', 'description': 'Andrew Ng ML kursu', 'level': 'Orta'},
                    {'title': 'Scikit-learn Documentation', 'url': 'https://scikit-learn.org/stable/', 'type': 'Doküman', 'description': 'ML kütüphanesi rehberi', 'level': 'Orta'},
                    {'title': 'Machine Learning Explained - Zach Star', 'url': 'https://www.youtube.com/watch?v=ukzFI9rgwfU', 'type': 'Video', 'description': 'ML kavramları açıklaması', 'level': 'Başlangıç'},
                    {'title': 'Machine Learning Mastery', 'url': 'https://machinelearningmastery.com/', 'type': 'Blog', 'description': 'Pratik ML teknikleri', 'level': 'Tüm Seviyeler'},
                    {'title': 'StatQuest with Josh Starmer', 'url': 'https://www.youtube.com/user/joshstarmer', 'type': 'YouTube Kanal', 'description': 'ML istatistik açıklamaları', 'level': 'Orta'}
                ],
                'tensorflow': [
                    {'title': 'TensorFlow Resmi Dokümanları', 'url': 'https://www.tensorflow.org/learn', 'type': 'Doküman', 'description': 'TensorFlow öğrenme rehberi', 'level': 'Orta'},
                    {'title': 'TensorFlow in Practice - Coursera', 'url': 'https://www.coursera.org/specializations/tensorflow-in-practice', 'type': 'Kurs', 'description': 'Pratik TensorFlow kursu', 'level': 'İleri'},
                    {'title': 'TensorFlow 2.0 Complete Course - freeCodeCamp', 'url': 'https://www.youtube.com/watch?v=tPYj3fFJGjk', 'type': 'Video', 'description': 'TensorFlow tam kursu', 'level': 'Orta'},
                    {'title': 'TensorFlow Tutorials', 'url': 'https://www.tensorflow.org/tutorials', 'type': 'Tutorial', 'description': 'Adım adım TensorFlow', 'level': 'Orta'},
                    {'title': 'Krish Naik Deep Learning', 'url': 'https://www.youtube.com/user/krishnaik06', 'type': 'YouTube Kanal', 'description': 'ML ve DL Türkçe içerik', 'level': 'Başlangıç'}
                ],
                'deep learning': [
                    {'title': 'Deep Learning Specialization', 'url': 'https://www.coursera.org/specializations/deep-learning', 'type': 'Kurs', 'description': 'Andrew Ng Deep Learning kursu', 'level': 'İleri'},
                    {'title': 'Deep Learning Book', 'url': 'https://www.deeplearningbook.org/', 'type': 'Kitap', 'description': 'Ücretsiz deep learning kitabı', 'level': 'İleri'},
                    {'title': '3Blue1Brown Neural Networks', 'url': 'https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi', 'type': 'Video Serisi', 'description': 'Görsel neural network açıklamaları', 'level': 'Orta'},
                    {'title': 'PyTorch Tutorials', 'url': 'https://pytorch.org/tutorials/', 'type': 'Tutorial', 'description': 'PyTorch ile deep learning', 'level': 'Orta'},
                    {'title': 'Two Minute Papers', 'url': 'https://www.youtube.com/user/keeroyz', 'type': 'YouTube Kanal', 'description': 'AI araştırma özetleri', 'level': 'İleri'}
                ],
                'neural networks': [
                    {'title': 'Neural Networks and Deep Learning - Coursera', 'url': 'https://www.coursera.org/learn/neural-networks-deep-learning', 'type': 'Kurs', 'description': 'Neural network temelleri', 'level': 'Orta'},
                    {'title': 'Neural Networks from Scratch - Sentdex', 'url': 'https://www.youtube.com/playlist?list=PLQVvvaa0QuDcjD5BAw2DxE6OF2tius3V3', 'type': 'Video Serisi', 'description': 'Sıfırdan neural network', 'level': 'İleri'},
                    {'title': 'Distill.pub', 'url': 'https://distill.pub/', 'type': 'Blog', 'description': 'Görsel ML açıklamaları', 'level': 'İleri'},
                    {'title': 'Neural Network Playground', 'url': 'https://playground.tensorflow.org/', 'type': 'İnteraktif', 'description': 'Neural network simülasyonu', 'level': 'Başlangıç'}
                ]
            },
            'Mobile': {
                'flutter': [
                    {'title': 'Flutter Resmi Dokümanları', 'url': 'https://docs.flutter.dev/', 'type': 'Doküman', 'description': 'Flutter resmi rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'Flutter Codelab', 'url': 'https://codelabs.developers.google.com/codelabs/first-flutter-app-pt1', 'type': 'Tutorial', 'description': 'İlk Flutter uygulamanız', 'level': 'Başlangıç'},
                    {'title': 'Flutter Course - freeCodeCamp', 'url': 'https://www.youtube.com/watch?v=pTJJsmejUOQ', 'type': 'Video', 'description': 'Kapsamlı Flutter kursu', 'level': 'Başlangıç'},
                    {'title': 'Flutter Course - Udemy', 'url': 'https://www.udemy.com/topic/flutter/', 'type': 'Kurs', 'description': 'Flutter kursları', 'level': 'Tüm Seviyeler'},
                    {'title': 'Flutter Official Channel', 'url': 'https://www.youtube.com/c/flutterdev', 'type': 'YouTube Kanal', 'description': 'Flutter resmi videoları', 'level': 'Tüm Seviyeler'}
                ],
                'android': [
                    {'title': 'Android Developer Guides', 'url': 'https://developer.android.com/guide', 'type': 'Doküman', 'description': 'Android geliştirme rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'Android Codelabs', 'url': 'https://codelabs.developers.google.com/?cat=android', 'type': 'Tutorial', 'description': 'Uygulamalı Android öğrenme', 'level': 'Orta'},
                    {'title': 'Android Development - Coding in Flow', 'url': 'https://www.youtube.com/c/CodinginFlow', 'type': 'YouTube Kanal', 'description': 'Android programlama videoları', 'level': 'Başlangıç'},
                    {'title': 'Kotlin for Android', 'url': 'https://kotlinlang.org/docs/android-overview.html', 'type': 'Doküman', 'description': 'Android için Kotlin', 'level': 'Orta'},
                    {'title': 'Android Development Course - Udacity', 'url': 'https://www.udacity.com/course/android-basics-nanodegree-by-google--nd803', 'type': 'Kurs', 'description': 'Google Android kursu', 'level': 'Başlangıç'}
                ],
                'ios': [
                    {'title': 'Apple Developer Documentation', 'url': 'https://developer.apple.com/documentation/', 'type': 'Doküman', 'description': 'iOS geliştirme rehberi', 'level': 'Tüm Seviyeler'},
                    {'title': 'Swift Programming Tutorial - Code with Chris', 'url': 'https://www.youtube.com/c/CodeWithChris', 'type': 'YouTube Kanal', 'description': 'Swift ve iOS videoları', 'level': 'Başlangıç'},
                    {'title': 'iOS & Swift - The Complete iOS App Development Bootcamp', 'url': 'https://www.udemy.com/course/ios-13-app-development-bootcamp/', 'type': 'Kurs', 'description': 'Kapsamlı iOS kursu', 'level': 'Başlangıç'},
                    {'title': 'Hacking with Swift', 'url': 'https://www.hackingwithswift.com/', 'type': 'Tutorial', 'description': 'Swift öğrenme kaynağı', 'level': 'Orta'}
                ]
            },
            'Cyber Security': {
                'penetration testing': [
                    {'title': 'OWASP Testing Guide', 'url': 'https://owasp.org/www-project-web-security-testing-guide/', 'type': 'Doküman', 'description': 'Web güvenlik test rehberi', 'level': 'İleri'},
                    {'title': 'TryHackMe', 'url': 'https://tryhackme.com/', 'type': 'Platform', 'description': 'Siber güvenlik öğrenme platformu', 'level': 'Tüm Seviyeler'},
                    {'title': 'Penetration Testing Course - freeCodeCamp', 'url': 'https://www.youtube.com/watch?v=3Kq1MIfTWCE', 'type': 'Video', 'description': 'Penetrasyon testi kursu', 'level': 'Orta'},
                    {'title': 'Hack The Box', 'url': 'https://www.hackthebox.com/', 'type': 'Platform', 'description': 'Penetrasyon testi pratiği', 'level': 'İleri'},
                    {'title': 'The Cyber Mentor', 'url': 'https://www.youtube.com/c/TheCyberMentor', 'type': 'YouTube Kanal', 'description': 'Ethical hacking videoları', 'level': 'Orta'}
                ],
                'cybersecurity': [
                    {'title': 'NIST Cybersecurity Framework', 'url': 'https://www.nist.gov/cyberframework', 'type': 'Doküman', 'description': 'Siber güvenlik çerçevesi', 'level': 'İleri'},
                    {'title': 'Cybrary', 'url': 'https://www.cybrary.it/', 'type': 'Platform', 'description': 'Ücretsiz siber güvenlik kursları', 'level': 'Tüm Seviyeler'},
                    {'title': 'Cybersecurity Full Course - Edureka', 'url': 'https://www.youtube.com/watch?v=inWWhr5tnEA', 'type': 'Video', 'description': 'Kapsamlı güvenlik kursu', 'level': 'Başlangıç'},
                    {'title': 'SANS Training', 'url': 'https://www.sans.org/', 'type': 'Kurs', 'description': 'Profesyonel güvenlik eğitimleri', 'level': 'İleri'},
                    {'title': 'Professor Messer', 'url': 'https://www.youtube.com/c/professormesser', 'type': 'YouTube Kanal', 'description': 'IT güvenlik videoları', 'level': 'Başlangıç'}
                ],
                'ethical hacking': [
                    {'title': 'Kali Linux Tutorials', 'url': 'https://www.kali.org/docs/', 'type': 'Doküman', 'description': 'Kali Linux kullanım rehberi', 'level': 'Orta'},
                    {'title': 'Ethical Hacking Course - EC-Council', 'url': 'https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/', 'type': 'Sertifika', 'description': 'CEH sertifika programı', 'level': 'İleri'},
                    {'title': 'Null Byte', 'url': 'https://www.youtube.com/c/NullByteWHT', 'type': 'YouTube Kanal', 'description': 'Ethical hacking teknikleri', 'level': 'Orta'},
                    {'title': 'OverTheWire Wargames', 'url': 'https://overthewire.org/wargames/', 'type': 'Challenge', 'description': 'Güvenlik challenge\'ları', 'level': 'Orta'}
                ]
            }
        }
        
        # Kullanıcının alanına göre dinamik kaynak seçimi
        resources = []
        if self.interest in url_mappings:
            area_mappings = url_mappings[self.interest]
            
            # 1. Önce topic'e tam uyumlu kaynakları bul
            for key, urls in area_mappings.items():
                if key in topic_lower or topic_lower in key:
                    resources.extend(urls)
                    break
            
            # 2. Tam eşleşme yoksa, kısmi eşleşme ara
            if not resources:
                for key, urls in area_mappings.items():
                    if any(word in topic_lower for word in key.split()) or any(word in key for word in topic_lower.split()):
                        resources.extend(urls[:3])  # İlk 3 kaynağı al
                        break
            
            # 3. Hâlâ kaynak yoksa, alanın genel kaynaklarını ekle
            if not resources and area_mappings:
                # İlk kategoriden 2 kaynak al
                first_category = next(iter(area_mappings.values()))
                resources.extend(first_category[:2])
        
        return resources
    
    def _generate_ai_resources(self, topic, num_needed):
        """AI ile ek kaynak önerileri oluştur"""
        prompt = f"""
        {topic} konusunda {self.interest} alanında çalışan bir geliştirici için {num_needed} adet gerçek URL önerisi yap.
        
        Sadece şu formatta JSON yanıt ver:
        [
            {{
                "title": "Kaynak başlığı",
                "url": "https://gerçek-site.com/path",
                "type": "Doküman/Tutorial/Kurs/Blog", 
                "description": "Kısa açıklama",
                "level": "Başlangıç/Orta/İleri"
            }}
        ]
        
        Sadece JSON formatında yanıt ver, başka açıklama ekleme.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            # Fallback
            return [
                {
                    'title': f'{topic} öğrenme kaynağı',
                    'url': f'https://www.google.com/search?q={topic.replace(" ", "+")}+{self.interest.replace(" ", "+")}',
                    'type': 'Arama',
                    'description': f'{topic} hakkında arama sonuçları',
                    'level': 'Tüm Seviyeler'
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