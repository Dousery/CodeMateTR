import google.generativeai as genai

class InterviewAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_question(self):
        prompt = f"""
        {self.interest} alanında bir teknik mülakat başlat. Sadece ilk soruyu sor ve başka açıklama ekleme.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def evaluate_answer(self, question, user_answer):
        prompt = f"""
        Aşağıdaki teknik mülakat sorusu ve kullanıcı cevabını değerlendir:
        Soru: {question}
        Cevap: {user_answer}
        - Cevabın doğruluğu ve eksikleri hakkında kısa bir değerlendirme yap.
        - Geliştirme için öneriler ver.
        - Son olarak, eksik veya yanlış varsa 2-3 kaynak öner (başlık ve link).
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def suggest_resources(self, topic, num_resources=3):
        prompt = f"""
        {topic} konusunda kendini geliştirmek isteyen bir geliştiriciye {num_resources} adet kaliteli kaynak (YouTube videosu, Medium makalesi, blog, vs) öner. Sadece başlık ve link ver.
        """
        response = self.model.generate_content(prompt)
        resources = [line.strip() for line in response.text.split('\n') if line.strip()]
        return resources[:num_resources] 