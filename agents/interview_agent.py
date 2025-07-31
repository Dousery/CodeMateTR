import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

class InterviewAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_question(self):
        """Basit mülakat sorusu üretir"""
        try:
            prompt = f"""
            {self.interest} alanında genel bir mülakat sorusu sor. Teknik kod soruları sorma, 
            kişinin deneyimi, motivasyonu, hedefleri, problem çözme yaklaşımı, 
            takım çalışması, liderlik, öğrenme isteği gibi konularda sorular sor.
            
            Soruyu doğal ve samimi bir şekilde sor, mülakat yapan kişi gibi konuş.
            Sadece soruyu ver, başka açıklama ekleme.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"{self.interest} alanında çalışma motivasyonunuz nedir?"

    def generate_dynamic_question(self, previous_questions=None, user_answers=None, conversation_context=None):
        """
        Kullanıcının önceki cevaplarına göre dinamik soru üretir
        """
        try:
            context_prompt = ""
            if previous_questions and user_answers:
                context_prompt = f"""
                Önceki sorular ve cevaplar:
                """
                for i, (q, a) in enumerate(zip(previous_questions, user_answers)):
                    context_prompt += f"\nSoru {i+1}: {q}\nCevap: {a}\n"
                context_prompt += "\nBu cevaplara göre uygun bir sonraki soru sor."
            
            if conversation_context:
                context_prompt += f"\n\nMülakat bağlamı: {conversation_context}"
            
            prompt = f"""
            {self.interest} alanında genel bir mülakat yapıyorsun. Teknik kod soruları sorma, 
            kişinin deneyimi, motivasyonu, hedefleri, problem çözme yaklaşımı, 
            takım çalışması, liderlik, öğrenme isteği gibi konularda sorular sor.
            
            {context_prompt}
            
            Soruyu doğal ve samimi bir şekilde sor, mülakat yapan kişi gibi konuş.
<<<<<<< HEAD
            Eğer conversation_context'te kullanıcı adı belirtilmişse (örneğin "Bu mülakat [ad] adlı kullanıcı ile yapılıyor"), 
            o adı kullanarak kişiselleştirilmiş sorular sor. Örneğin: "[Ad], bu konuda ne düşünüyorsun?" 
            veya "[Ad], bu durumda nasıl davranırdın?" gibi. Kullanıcı adını conversation_context'ten çıkar ve doğrudan kullan.
=======
>>>>>>> 1d3fffa0c7b15f58865a39bc0a06a2a39e3b075d
            Sadece soruyu ver, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            # Fallback soru
            return f"{self.interest} alanında çalışırken en büyük zorlukla nasıl karşılaştınız?"

    def generate_cv_based_question(self, cv_analysis):
        """CV analizi temelinde kişiselleştirilmiş soru üretir"""
        try:
            prompt = f"""
            Aşağıdaki CV analizi temelinde {self.interest} alanında bir mülakat sorusu hazırla:
            
            CV Analizi:
            {cv_analysis}
            
            Kişinin deneyimine ve becerilerine göre kişiselleştirilmiş bir soru sor.
            Teknik detaylara girmeden, deneyim, motivasyon, hedefler konularında sor.
            Sadece soruyu ver, başka açıklama ekleme.
            """
<<<<<<< HEAD
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return self.generate_question()

    def evaluate_conversation_progress(self, questions, answers):
        """
        Mülakat ilerlemesini değerlendirir ve sonraki adım önerisi verir
        """
        try:
            # Eğer henüz cevap yoksa, mülakatın başladığını belirt
            if not answers:
                return f"{self.interest} alanında mülakat başladı. İlk soruya cevap verildikten sonra detaylı değerlendirme yapılacak."
            
            if not self.client:
                return f"{self.interest} alanında mülakat devam ediyor. API bağlantısı olmadığı için detaylı değerlendirme yapılamıyor."
            
            prompt = f"""
            {self.interest} alanında yapılan mülakatın ilerlemesini değerlendir:
            
            Sorular ve cevaplar:
            """
            for i, (q, a) in enumerate(zip(questions, answers)):
                prompt += f"\nSoru {i+1}: {q}\nCevap: {a}\n"
            
            prompt += f"""
            
            Bu mülakatın durumunu değerlendir:
            1. Hangi alanlar daha detaylı sorulmalı?
            2. Kullanıcının güçlü yanları neler?
            3. Hangi konularda daha fazla bilgi alınmalı?
            4. Mülakatın genel tonu nasıl?
            5. Sonraki soru için öneriler
            
            Kısa ve öz bir değerlendirme yap. Maksimum 3-4 cümle.
            """
            
=======
>>>>>>> 1d3fffa0c7b15f58865a39bc0a06a2a39e3b075d
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return self.generate_question()

    def evaluate_answer(self, question, user_answer):
        """Kullanıcının cevabını değerlendirir"""
        try:
            prompt = f"""
            Mülakat sorusu: {question}
            Kullanıcının cevabı: {user_answer}
            
            Bu cevabı değerlendir ve geri bildirim ver:
            1. Cevabın güçlü yanları
            2. Geliştirilmesi gereken alanlar
            3. Genel puan (1-10)
            4. Yapıcı öneriler
            
            Objektif ve yapıcı bir değerlendirme yap.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return "Değerlendirme şu anda yapılamıyor. Lütfen tekrar deneyin."

    def evaluate_cv_answer(self, question, user_answer, cv_analysis):
        """CV bağlamında kullanıcının cevabını değerlendirir"""
        try:
            prompt = f"""
            CV Analizi: {cv_analysis}
            Mülakat sorusu: {question}
            Kullanıcının cevabı: {user_answer}
            
            Bu cevabı CV bilgileri ışığında değerlendir:
            1. Cevabın CV ile tutarlılığı
            2. Deneyimine uygun derinlik
            3. Güçlü yanları
            4. Geliştirilmesi gereken alanlar
            5. Genel puan (1-10)
            6. Yapıcı öneriler
            
            Kişiselleştirilmiş ve yapıcı bir değerlendirme yap.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return self.evaluate_answer(question, user_answer)

    def generate_personalized_questions(self, cv_analysis, difficulty='orta'):
        """CV analizine göre kişiselleştirilmiş sorular üretir"""
        try:
            prompt = f"""
            CV analizi: {cv_analysis}
            Zorluk seviyesi: {difficulty}
            Alan: {self.interest}
            
            Bu kişi için {difficulty} seviyede 5 mülakat sorusu hazırla.
            Kişinin deneyimi ve becerilerine göre özelleştir.
            Teknik kod soruları değil, deneyim, motivasyon, problem çözme, 
            takım çalışması konularında sorular sor.
            
            Her soruyu ayrı satırda ver, numaralandır.
            """
            response = self.model.generate_content(prompt)
            questions = response.text.strip().split('\n')
            return [q.strip() for q in questions if q.strip()]
        except Exception as e:
            return [
                f"{self.interest} alanındaki deneyiminizden bahseder misiniz?",
                "Kendinizi nasıl motive ediyorsunuz?",
                "Takım çalışmasında hangi role daha uygunsunuz?",
                "Karşılaştığınız en büyük teknik zorluk neydi?",
                "Gelecek hedefleriniz nelerdir?"
            ]