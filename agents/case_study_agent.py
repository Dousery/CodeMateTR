import google.generativeai as genai

class CaseStudyAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_case(self):
        prompt = f"""
        {self.interest} alanında iki geliştirici için bir case study senaryosu oluştur. Sadece case'i açıkla, başka açıklama ekleme.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip() 