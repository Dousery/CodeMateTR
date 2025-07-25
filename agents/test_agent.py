import google.generativeai as genai

class TestAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_questions(self, num_questions=10):
        prompt = f"""
        {self.interest} alanında geliştiriciler için {num_questions} adet çoktan seçmeli sınav sorusu üret. Her soru için 4 şık (A, B, C, D) ve doğru cevabı belirt. Format:
        Soru: ...\nA) ...\nB) ...\nC) ...\nD) ...\nCevap: ...
        """
        response = self.model.generate_content(prompt)
        questions = []
        current = {}
        for line in response.text.split('\n'):
            if line.startswith('Soru:'):
                if current:
                    questions.append(current)
                current = {'question': line[6:].strip(), 'options': [], 'answer': ''}
            elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                current['options'].append(line[3:].strip())
            elif line.startswith('Cevap:'):
                current['answer'] = line[7:].strip()
        if current:
            questions.append(current)
        return questions[:num_questions]

    def evaluate_answers(self, user_answers, questions):
        # user_answers: ["A", "B", ...], questions: [{question, options, answer}, ...]
        results = []
        for idx, (user_ans, q) in enumerate(zip(user_answers, questions)):
            correct = (user_ans == q['answer'])
            results.append({
                'question': q['question'],
                'user_answer': user_ans,
                'correct_answer': q['answer'],
                'is_correct': correct
            })
        return results

    def suggest_resources(self, topic, num_resources=3):
        prompt = f"""
        {topic} konusunda temel kavramları ve eksikleri öğrenmek isteyen bir geliştiriciye {num_resources} adet kaliteli kaynak (YouTube videosu, Medium makalesi, blog, vs) öner. Sadece başlık ve link ver.
        """
        response = self.model.generate_content(prompt)
        # Basitçe satır satır ayır
        resources = [line.strip() for line in response.text.split('\n') if line.strip()]
        return resources[:num_resources] 