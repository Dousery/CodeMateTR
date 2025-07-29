import google.generativeai as genai
from google import genai as google_genai_new
from google.genai import types
import wave
import tempfile
import os
import base64
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class InterviewAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        # Configure the new client with API key
        try:
            self.client = google_genai_new.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Google GenAI client initialization error: {e}")
            # Fallback: Set environment variable
            os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
            try:
                self.client = google_genai_new.Client()
            except Exception as e2:
                print(f"Fallback client initialization error: {e2}")
                self.client = None

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
            Eğer conversation_context'te kullanıcı adı belirtilmişse (örneğin "Bu mülakat [ad] adlı kullanıcı ile yapılıyor"), 
            o adı kullanarak kişiselleştirilmiş sorular sor. Örneğin: "[Ad], bu konuda ne düşünüyorsun?" 
            veya "[Ad], bu durumda nasıl davranırdın?" gibi. Kullanıcı adını conversation_context'ten çıkar ve doğrudan kullan.
            Sadece soruyu ver, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            # Fallback soru
            return f"{self.interest} alanında çalışırken en büyük zorlukla nasıl karşılaştınız?"

    def generate_dynamic_speech_question(self, previous_questions=None, user_answers=None, conversation_context=None, voice_name='Kore'):
        """
        Kullanıcının önceki cevaplarına göre dinamik sesli soru üretir
        """
        try:
            question_text = self.generate_dynamic_question(previous_questions, user_answers, conversation_context)
            print(f"Generated question text: {question_text}")
            
            # TTS kotası aşıldığı için geçici olarak devre dışı
            print("TTS quota exceeded - returning text only")
            return {
                'audio_file': None,
                'question_text': question_text,
                'audio_data': None,
                'error': 'Sesli özellik geçici olarak devre dışı - API kotası aşıldı'
            }
            
        except Exception as e:
            print(f"General error in generate_dynamic_speech_question: {e}")
            import traceback
            traceback.print_exc()
            # Hata durumunda sadece metin döndür
            question_text = self.generate_dynamic_question(previous_questions, user_answers, conversation_context)
            return {
                'audio_file': None,
                'question_text': question_text,
                'audio_data': None,
                'error': f'Genel hata: {str(e)}'
            }

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
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Mülakat değerlendirmesi yapılamadı: {str(e)}"

    def generate_final_evaluation(self, questions, answers, conversation_summary=None):
        """
        Mülakat sonunda kapsamlı değerlendirme üretir
        """
        try:
            prompt = f"""
            {self.interest} alanında yapılan mülakatın genel değerlendirmesini yap:
            
            Sorular ve cevaplar:
            """
            for i, (q, a) in enumerate(zip(questions, answers)):
                prompt += f"\nSoru {i+1}: {q}\nCevap: {a}\n"
            
            if conversation_summary:
                prompt += f"\nMülakat özeti: {conversation_summary}"
            
            prompt += f"""
            
            Bu mülakatın kapsamlı değerlendirmesini yap:
            
            **Güçlü Yönler:**
            - Kullanıcının en iyi performans gösterdiği alanlar
            - Olumlu özellikler ve beceriler
            
            **Geliştirilmesi Gereken Alanlar:**
            - Eksiklikler ve zayıf noktalar
            - İyileştirme önerileri
            
            **Genel İzlenim:**
            - Mülakatın genel tonu ve atmosferi
            - Kullanıcının motivasyonu ve ilgisi
            
            **Öneriler:**
            - Kariyer gelişimi için öneriler
            - Öğrenme kaynakları ve yönlendirmeler
            
            **Puanlama (1-10):**
            - Genel performans: X/10
            - İletişim becerileri: X/10
            - Teknik bilgi: X/10
            - Problem çözme: X/10
            
            Yapıcı, destekleyici ve detaylı bir değerlendirme yap.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Genel değerlendirme yapılamadı: {str(e)}"

    def _transcribe_audio(self, audio_file_path):
        """
        Ses dosyasını metne dönüştürür (Gemini ile)
        """
        try:
            # Ses dosyasını oku
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Gemini ile transcript et
            prompt = """
            Bu ses dosyasındaki konuşmayı metne dönüştür. 
            Sadece konuşulan metni ver, başka açıklama ekleme.
            Türkçe konuşma var ise Türkçe olarak transcript et.
            """
            
            response = self.model.generate_content([
                {
                    "mime_type": "audio/webm",  # Frontend'den gelen format
                    "data": base64.b64encode(audio_data).decode()
                },
                prompt
            ])
            
            return response.text.strip()
            
        except Exception as e:
            # Gemini ile transcript edilemezse, basit placeholder
            return f"Ses transcript edildi ancak metin çıkarılamadı. Hata: {str(e)}"

    def _save_wave_file(self, filename, pcm_data, channels=1, rate=24000, sample_width=2):
        """
        PCM verisini wave dosyası olarak kaydeder
        """
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data) 