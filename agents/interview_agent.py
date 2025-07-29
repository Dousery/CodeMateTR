import google.generativeai as genai
from google import genai as google_genai_new
from google.genai import types
import httpx
import base64
import io
from pathlib import Path
import wave
import tempfile
import os

class InterviewAIAgent:
    def __init__(self, interest):
        self.interest = interest
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.client = google_genai_new.Client()  # Yeni API için client

    def analyze_cv(self, cv_data, mime_type='application/pdf'):
        """
        CV'yi analiz eder ve kişinin becerilerine göre mülakat soruları hazırlar
        """
        try:
            prompt = """
            Bu CV'yi analiz et ve aşağıdaki bilgileri çıkar:
            1. Kişinin ana becerileri ve teknolojileri
            2. Deneyim seviyesi
            3. Güçlü ve zayıf olduğu alanlar
            4. Bu kişiye sorulabilecek uygun teknik mülakat soruları (3-5 tane)
            
            Analizi Türkçe olarak yap ve net bir şekilde kategorize et.
            """
            
            # Gemini ile dosya upload
            response = self.model.generate_content([
                {
                    "mime_type": mime_type,
                    "data": base64.b64encode(cv_data).decode()
                },
                prompt
            ])
            return response.text.strip()
        except Exception as e:
            return f"CV analizi sırasında hata oluştu: {str(e)}"

    def analyze_cv_from_url(self, cv_url):
        """
        URL'den CV'yi indirip analiz eder
        """
        try:
            cv_data = httpx.get(cv_url).content
            return self.analyze_cv(cv_data)
        except Exception as e:
            return f"CV indirme ve analizi sırasında hata oluştu: {str(e)}"

    def generate_cv_based_question(self, cv_analysis):
        """
        CV analizine göre özelleştirilmiş soru üretir
        """
        prompt = f"""
        Aşağıdaki CV analizi sonucuna göre uygun bir teknik mülakat sorusu sor:
        
        CV Analizi: {cv_analysis}
        
        Soruyu kişinin deneyim seviyesine uygun ve gerçekçi yap. Sadece soruyu ver, açıklama ekleme.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def generate_personalized_questions(self, cv_analysis, difficulty='orta'):
        """
        CV analizine göre kişiselleştirilmiş sorular üretir
        """
        prompt = f"""
        Aşağıdaki CV analizi sonucuna göre {difficulty} seviyede 5 teknik mülakat sorusu hazırla:
        
        CV Analizi: {cv_analysis}
        
        Soruları kişinin deneyimlerine göre özelleştir ve numaralı liste halinde sun.
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def evaluate_cv_answer(self, question, user_answer, cv_context):
        """
        CV bağlamında cevabı değerlendirir
        """
        prompt = f"""
        CV Bağlamı: {cv_context}
        Mülakat Sorusu: {question}
        Kullanıcı Cevabı: {user_answer}
        
        Bu cevabı kişinin CV'sindeki deneyim seviyesi göz önünde bulundurarak değerlendir:
        - Cevabın doğruluğu ve yeterliliği
        - Kişinin deneyim seviyesine uygunluğu
        - Geliştirmesi gereken alanlar
        - Öneriler ve kaynaklar
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

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

    def generate_speech_question(self, voice_name='Kore'):
        """
        Sesli mülakat sorusu üretir ve ses dosyası olarak döndürür
        """
        try:
            prompt = f"""
            {self.interest} alanında bir teknik mülakat sorusu sor. 
            Soru profesyonel ve samimi bir tonda sorulmalı.
            Mülakat yapan kişi gibi konuş ve soruyu net bir şekilde sor.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                )
            )
            
            # Ses verisini al
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # Geçici dosya oluştur
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            self._save_wave_file(temp_file.name, audio_data)
            
            # Metin versiyonunu da al
            text_response = self.model.generate_content(prompt)
            
            return {
                'audio_file': temp_file.name,
                'question_text': text_response.text.strip(),
                'audio_data': audio_data
            }
            
        except Exception as e:
            # Hata durumunda sadece metin döndür
            prompt = f"{self.interest} alanında bir teknik mülakat sorusu sor."
            response = self.model.generate_content(prompt)
            return {
                'audio_file': None,
                'question_text': response.text.strip(),
                'audio_data': None,
                'error': str(e)
            }

    def generate_cv_based_speech_question(self, cv_analysis, voice_name='Kore'):
        """
        CV analizine göre sesli soru üretir
        """
        try:
            prompt = f"""
            Aşağıdaki CV analizi sonucuna göre uygun bir teknik mülakat sorusu sor:
            
            CV Analizi: {cv_analysis}
            
            Soruyu kişinin deneyim seviyesine uygun ve gerçekçi yap. 
            Mülakat yapan kişi gibi profesyonel ve samimi bir tonda konuş.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                )
            )
            
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            self._save_wave_file(temp_file.name, audio_data)
            
            # Metin versiyonu
            text_response = self.model.generate_content(prompt)
            
            return {
                'audio_file': temp_file.name,
                'question_text': text_response.text.strip(),
                'audio_data': audio_data
            }
            
        except Exception as e:
            return self.generate_cv_based_question(cv_analysis)

    def generate_speech_feedback(self, question, user_answer, cv_context=None, voice_name='Enceladus'):
        """
        Kullanıcı cevabına sesli geri bildirim üretir
        """
        try:
            if cv_context:
                prompt = f"""
                CV Bağlamı: {cv_context}
                Mülakat Sorusu: {question}
                Kullanıcı Cevabı: {user_answer}
                
                Bu cevabı kişinin CV'sindeki deneyim seviyesi göz önünde bulundurarak değerlendir.
                Mülakat yapan kişi gibi yapıcı geri bildirim ver.
                Olumlu yönleri belirt, eksikleri kibarca söyle ve gelişim önerileri sun.
                """
            else:
                prompt = f"""
                Mülakat Sorusu: {question}
                Kullanıcı Cevabı: {user_answer}
                
                Bu cevabı değerlendir ve yapıcı geri bildirim ver.
                Mülakat yapan kişi gibi profesyonel ve destekleyici bir tonda konuş.
                """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                )
            )
            
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            self._save_wave_file(temp_file.name, audio_data)
            
            # Metin versiyonu
            if cv_context:
                text_response = self.evaluate_cv_answer(question, user_answer, cv_context)
            else:
                text_response = self.evaluate_answer(question, user_answer)
            
            return {
                'audio_file': temp_file.name,
                'feedback_text': text_response,
                'audio_data': audio_data
            }
            
        except Exception as e:
            if cv_context:
                text_feedback = self.evaluate_cv_answer(question, user_answer, cv_context)
            else:
                text_feedback = self.evaluate_answer(question, user_answer)
                
            return {
                'audio_file': None,
                'feedback_text': text_feedback,
                'audio_data': None,
                'error': str(e)
            }

    def evaluate_speech_answer(self, question, audio_file_path, additional_text="", cv_context=None, voice_name="Enceladus"):
        """
        Ses dosyasını transcript edip değerlendirir ve sesli geri bildirim üretir
        """
        try:
            # Önce ses dosyasını transcript et
            transcribed_text = self._transcribe_audio(audio_file_path)
            
            # Ek metin varsa birleştir
            if additional_text:
                user_answer = f"{transcribed_text}\n\nEk açıklama: {additional_text}"
            else:
                user_answer = transcribed_text
            
            # Sesli geri bildirim üret
            result = self.generate_speech_feedback(question, user_answer, cv_context, voice_name)
            result['transcribed_text'] = transcribed_text
            
            return result
            
        except Exception as e:
            # Transcript edilemezse sadece ek metni kullan
            if additional_text:
                result = self.generate_speech_feedback(question, additional_text, cv_context, voice_name)
                result['transcribed_text'] = f"Ses transcript edilemedi: {str(e)}"
                return result
            else:
                return {
                    'audio_file': None,
                    'feedback_text': f"Ses dosyası işlenemedi: {str(e)}",
                    'audio_data': None,
                    'transcribed_text': f"Transcript hatası: {str(e)}",
                    'error': str(e)
                }

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

    def suggest_resources(self, topic, num_resources=3):
        prompt = f"""
        {topic} konusunda kendini geliştirmek isteyen bir geliştiriciye {num_resources} adet kaliteli kaynak (YouTube videosu, Medium makalesi, blog, vs) öner. Sadece başlık ve link ver.
        """
        response = self.model.generate_content(prompt)
        resources = [line.strip() for line in response.text.split('\n') if line.strip()]
        return resources[:num_resources] 