import google.generativeai as genai

class CodeAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_coding_question(self):
        prompt = f"""
        {self.interest} alanında bir kodlama sorusu üret. Sadece soruyu döndür, başka açıklama ekleme.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def evaluate_code(self, user_code, question):
        prompt = f"""
        Kullanıcıdan gelen kodu değerlendir:
        Soru: {question}
        Kod:
        {user_code}
        Kodun doğruluğu, verimliliği ve okunabilirliği hakkında kısa bir değerlendirme yap. Geliştirme için öneriler ver. Son olarak, eksik veya yanlış varsa 2-3 kaynak öner (başlık ve link).
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