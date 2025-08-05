import google.generativeai as genai
from google.genai import types
import json
import re


class TopicAnalysisAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Configure the client for grounding tool
        try:
            self.client = genai.Client()
            self.grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            self.config = types.GenerateContentConfig(
                tools=[self.grounding_tool]
            )
            self.use_grounding = True
        except Exception as e:
            print(f"Grounding tool not available: {e}")
            self.use_grounding = False

    def analyze_wrong_questions(self, wrong_questions):
        """
        Analyze wrong questions to identify topics and provide resource recommendations
        """
        if not wrong_questions:
            return {
                'message': 'Tebrikler! Tüm soruları doğru yanıtladınız.',
                'topic_analysis': [],
                'recommended_resources': []
            }
        
        topic_analysis = []
        all_resources = []
        
        for wrong_q in wrong_questions:
            # Analyze the question to identify the topic
            topic_info = self._analyze_question_topic(wrong_q)
            
            # Get resources for this specific topic
            topic_resources = self._get_topic_resources(topic_info['topic'], wrong_q)
            
            topic_analysis.append({
                'question_id': wrong_q.get('question_id', 0),
                'question_preview': wrong_q.get('question', '')[:100] + "..." if len(wrong_q.get('question', '')) > 100 else wrong_q.get('question', ''),
                'identified_topic': topic_info['topic'],
                'topic_confidence': topic_info['confidence'],
                'difficulty': wrong_q.get('difficulty', 'intermediate'),
                'explanation': wrong_q.get('explanation', ''),
                'your_answer': wrong_q.get('user_answer', ''),
                'correct_answer': wrong_q.get('correct_answer', ''),
                'topic_description': topic_info['description'],
                'learning_resources': topic_resources
            })
            
            all_resources.extend(topic_resources)
        
        # Group by topic and identify priority topics
        grouped_analysis = self._group_by_topic(topic_analysis)
        priority_topics = self._identify_priority_topics(topic_analysis)
        
        return {
            'message': f'{len(wrong_questions)} soru yanlış yanıtlandı. Her yanlış soru için özel öğrenme kaynakları:',
            'total_wrong_questions': len(wrong_questions),
            'individual_question_analysis': topic_analysis,
            'grouped_by_topic': grouped_analysis,
            'priority_topics': priority_topics,
            'all_recommended_resources': self._deduplicate_resources(all_resources)
        }
    
    def _analyze_question_topic(self, question_data):
        """
        Analyze a question to identify the specific topic using AI
        """
        prompt = f"""
        Aşağıdaki soruyu analiz ederek {self.interest} alanında hangi konuya ait olduğunu belirle:
        
        Soru: {question_data.get('question', '')}
        Açıklama: {question_data.get('explanation', '')}
        Zorluk: {question_data.get('difficulty', 'intermediate')}
        
        Lütfen şu bilgileri JSON formatında döndür:
        {{
            "topic": "konu_adı",
            "confidence": 0.85,
            "description": "Konunun kısa açıklaması",
            "keywords": ["anahtar", "kelimeler"],
            "subtopics": ["alt_konular"],
            "learning_path": "öğrenme_yolu"
        }}
        
        Sadece JSON formatında yanıt ver, başka açıklama ekleme.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx]
                topic_info = json.loads(json_text)
                
                # Ensure required fields
                topic_info.setdefault('topic', 'Genel Konular')
                topic_info.setdefault('confidence', 0.7)
                topic_info.setdefault('description', f'{self.interest} alanında genel konular')
                topic_info.setdefault('keywords', [])
                topic_info.setdefault('subtopics', [])
                topic_info.setdefault('learning_path', 'Temel öğrenme yolu')
                
                return topic_info
            else:
                return self._fallback_topic_analysis(question_data)
                
        except Exception as e:
            print(f"Topic analysis error: {e}")
            return self._fallback_topic_analysis(question_data)
    
    def _fallback_topic_analysis(self, question_data):
        """
        Fallback topic analysis when AI fails
        """
        question_lower = question_data.get('question', '').lower()
        
        # Simple keyword-based topic detection
        topic_keywords = {
            'Data Science': {
                'python': ['python', 'pandas', 'numpy', 'matplotlib', 'seaborn'],
                'machine learning': ['machine learning', 'ml', 'model', 'training', 'prediction'],
                'statistics': ['statistics', 'mean', 'median', 'correlation', 'regression'],
                'data analysis': ['data analysis', 'dataframe', 'csv', 'visualization'],
                'deep learning': ['deep learning', 'neural network', 'tensorflow', 'pytorch']
            },
            'Web Development': {
                'javascript': ['javascript', 'js', 'function', 'variable', 'dom'],
                'html': ['html', 'tag', 'element', 'attribute'],
                'css': ['css', 'style', 'selector', 'flexbox', 'grid'],
                'react': ['react', 'component', 'jsx', 'state', 'props'],
                'node.js': ['node', 'server', 'npm', 'express', 'backend']
            },
            'AI': {
                'machine learning': ['machine learning', 'ml', 'algorithm', 'model'],
                'deep learning': ['deep learning', 'neural network', 'tensorflow'],
                'natural language processing': ['nlp', 'text', 'language', 'tokenization'],
                'computer vision': ['image', 'vision', 'opencv', 'detection']
            }
        }
        
        if self.interest in topic_keywords:
            for topic, keywords in topic_keywords[self.interest].items():
                for keyword in keywords:
                    if keyword in question_lower:
                        return {
                            'topic': topic,
                            'confidence': 0.8,
                            'description': f'{topic} konusu',
                            'keywords': [keyword],
                            'subtopics': [],
                            'learning_path': f'{topic} öğrenme yolu'
                        }
        
        return {
            'topic': 'Genel Konular',
            'confidence': 0.5,
            'description': f'{self.interest} alanında genel konular',
            'keywords': [],
            'subtopics': [],
            'learning_path': 'Temel öğrenme yolu'
        }
    
    def _get_topic_resources(self, topic, question_data):
        """
        Get learning resources for a specific topic using grounding tool
        """
        if self.use_grounding:
            return self._get_grounded_resources(topic, question_data)
        else:
            return self._get_fallback_resources(topic, question_data)
    
    def _get_grounded_resources(self, topic, question_data):
        """
        Get resources using Google's grounding tool
        """
        try:
            search_query = f"{self.interest} {topic} tutorial learning resources"
            
            # Use grounding tool to search for resources
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Find the best learning resources for {topic} in {self.interest}. Include tutorials, courses, documentation, and practice materials. Return as JSON with title, url, type, description, and level.",
                config=self.config,
            )
            
            # Parse the response
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            if '```json' in response_text:
                json_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_text = response_text.split('```')[1].strip()
            else:
                json_text = response_text
            
            try:
                resources = json.loads(json_text)
                if isinstance(resources, list):
                    return resources[:5]  # Limit to 5 resources
                else:
                    return self._get_fallback_resources(topic, question_data)
            except json.JSONDecodeError:
                return self._get_fallback_resources(topic, question_data)
                
        except Exception as e:
            print(f"Grounding tool error: {e}")
            return self._get_fallback_resources(topic, question_data)
    
    def _get_fallback_resources(self, topic, question_data):
        """
        Fallback resource generation when grounding tool is not available
        """
        resources = []
        
        # YouTube videos
        youtube_query = f"{self.interest} {topic} tutorial".replace(' ', '+')
        resources.append({
            'title': f'{topic} Öğrenme Videosu',
            'url': f'https://www.youtube.com/results?search_query={youtube_query}',
            'type': 'Video Tutorial',
            'description': f'{topic} konusunu öğrenmek için video rehberi',
            'level': question_data.get('difficulty', 'intermediate'),
            'source': 'YouTube',
            'estimated_time': '15-30 dakika'
        })
        
        # Documentation
        doc_query = f"{self.interest} {topic} documentation".replace(' ', '+')
        resources.append({
            'title': f'{topic} Dokümantasyonu',
            'url': f'https://www.google.com/search?q={doc_query}',
            'type': 'Documentation',
            'description': f'{topic} için resmi dokümantasyon',
            'level': 'all',
            'source': 'Web',
            'estimated_time': '30-45 dakika'
        })
        
        # Practice examples
        practice_query = f"{self.interest} {topic} examples practice".replace(' ', '+')
        resources.append({
            'title': f'{topic} Pratik Örnekleri',
            'url': f'https://www.google.com/search?q={practice_query}',
            'type': 'Practice Examples',
            'description': f'{topic} ile ilgili pratik örnekler',
            'level': question_data.get('difficulty', 'intermediate'),
            'source': 'Web',
            'estimated_time': '45-60 dakika'
        })
        
        # Course
        course_query = f"{self.interest} {topic} course".replace(' ', '+')
        resources.append({
            'title': f'{topic} Kursu',
            'url': f'https://www.google.com/search?q={course_query}',
            'type': 'Course',
            'description': f'{topic} konusunda kapsamlı kurs',
            'level': 'beginner',
            'source': 'Web',
            'estimated_time': '2-4 saat'
        })
        
        return resources
    
    def _group_by_topic(self, topic_analysis):
        """
        Group wrong questions by topic
        """
        topic_groups = {}
        
        for analysis in topic_analysis:
            topic = analysis['identified_topic']
            
            if topic not in topic_groups:
                topic_groups[topic] = {
                    'topic': topic,
                    'wrong_question_count': 0,
                    'questions': [],
                    'combined_resources': [],
                    'priority_level': 'medium',
                    'average_confidence': 0,
                    'difficulties': []
                }
            
            topic_groups[topic]['wrong_question_count'] += 1
            topic_groups[topic]['questions'].append({
                'id': analysis['question_id'],
                'preview': analysis['question_preview'],
                'difficulty': analysis['difficulty'],
                'confidence': analysis['topic_confidence']
            })
            
            topic_groups[topic]['difficulties'].append(analysis['difficulty'])
            
            # Combine resources (remove duplicates)
            for resource in analysis['learning_resources']:
                if not any(r.get('title') == resource.get('title') for r in topic_groups[topic]['combined_resources']):
                    topic_groups[topic]['combined_resources'].append(resource)
        
        # Calculate average confidence and set priority
        for topic_data in topic_groups.values():
            confidences = [q['confidence'] for q in topic_data['questions']]
            topic_data['average_confidence'] = sum(confidences) / len(confidences)
            
            wrong_count = topic_data['wrong_question_count']
            if wrong_count >= 3:
                topic_data['priority_level'] = 'high'
            elif wrong_count >= 2:
                topic_data['priority_level'] = 'medium'
            else:
                topic_data['priority_level'] = 'low'
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        sorted_groups = dict(sorted(
            topic_groups.items(), 
            key=lambda x: priority_order[x[1]['priority_level']], 
            reverse=True
        ))
        
        return sorted_groups
    
    def _identify_priority_topics(self, topic_analysis):
        """
        Identify priority topics based on wrong questions
        """
        topic_counts = {}
        topic_confidences = {}
        
        for analysis in topic_analysis:
            topic = analysis['identified_topic']
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            if topic not in topic_confidences:
                topic_confidences[topic] = []
            topic_confidences[topic].append(analysis['topic_confidence'])
        
        priority_topics = []
        for topic, count in topic_counts.items():
            avg_confidence = sum(topic_confidences[topic]) / len(topic_confidences[topic])
            priority_level = 'high' if count >= 3 else 'medium' if count >= 2 else 'low'
            
            priority_topics.append({
                'topic': topic,
                'wrong_count': count,
                'priority': priority_level,
                'confidence': round(avg_confidence, 2),
                'recommendation': self._get_topic_learning_recommendation(topic, count, avg_confidence)
            })
        
        # Sort by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        priority_topics.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['confidence']), reverse=True)
        
        return priority_topics
    
    def _get_topic_learning_recommendation(self, topic, wrong_count, confidence):
        """
        Generate learning recommendation for a topic
        """
        if wrong_count >= 3:
            return f"{topic} konusunda temel eksiklikleriniz var. Bu konuyu baştan öğrenmenizi öneririz."
        elif wrong_count >= 2:
            return f"{topic} konusunda ek pratik yapmanız gerekiyor. Örnekler üzerinde çalışın."
        else:
            return f"{topic} konusunda küçük bir eksiklik. Kısa bir tekrar yeterli olacaktır."
    
    def _deduplicate_resources(self, resources):
        """
        Remove duplicate resources based on title
        """
        seen_titles = set()
        unique_resources = []
        
        for resource in resources:
            title = resource.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_resources.append(resource)
        
        return unique_resources[:10]  # Limit to 10 unique resources 