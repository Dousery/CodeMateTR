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
            Eğer conversation_context'te "Kullanıcının nickname: [nickname]" formatında bir bilgi varsa, 
            o nickname'i kullanarak kişiselleştirilmiş sorular sor. Örneğin: "[Nickname], bu konuda ne düşünüyorsun?" 
            veya "[Nickname], bu durumda nasıl davranırdın?" gibi.
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
            
            # Sesli özellik aktifse ses üret
            if self.client:
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash-preview-tts",
                        contents=question_text,
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
                    
                    return {
                        'audio_file': temp_file.name,
                        'question_text': question_text,
                        'audio_data': audio_data
                    }
                except Exception as audio_error:
                    print(f"Audio generation error: {audio_error}")
                    return {
                        'audio_file': None,
                        'question_text': question_text,
                        'audio_data': None,
                        'error': f'Ses üretilemedi: {str(audio_error)}'
                    }
            else:
                return {
                    'audio_file': None,
                    'question_text': question_text,
                    'audio_data': None,
                    'error': 'Sesli özellik kullanılamıyor'
                }
            
        except Exception as e:
            # Hata durumunda sadece metin döndür
            question_text = self.generate_dynamic_question(previous_questions, user_answers, conversation_context)
            return {
                'audio_file': None,
                'question_text': question_text,
                'audio_data': None,
                'error': str(e)
            }

    def generate_cv_based_question(self, cv_analysis):
        """
        CV analizine göre soru üretir
        """
        try:
            prompt = f"""
            Aşağıdaki CV analizi sonucuna göre uygun bir teknik mülakat sorusu sor:
            
            CV Analizi: {cv_analysis}
            
            Soruyu kişinin deneyim seviyesine uygun ve gerçekçi yap. 
            Sadece soruyu ver, başka açıklama ekleme.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"{self.interest} alanında deneyiminiz hakkında ne söyleyebilirsiniz?"

    def generate_cv_based_speech_question(self, cv_analysis, voice_name='Kore'):
        """
        CV analizine göre sesli soru üretir
        """
        try:
            question_text = self.generate_cv_based_question(cv_analysis)
            
            # Sesli özellik aktifse ses üret
            if self.client:
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash-preview-tts",
                        contents=question_text,
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
                    
                    return {
                        'audio_file': temp_file.name,
                        'question_text': question_text,
                        'audio_data': audio_data
                    }
                except Exception as audio_error:
                    print(f"Audio generation error: {audio_error}")
                    return {
                        'audio_file': None,
                        'question_text': question_text,
                        'audio_data': None,
                        'error': f'Ses üretilemedi: {str(audio_error)}'
                    }
            else:
                return {
                    'audio_file': None,
                    'question_text': question_text,
                    'audio_data': None,
                    'error': 'Sesli özellik kullanılamıyor'
                }
            
        except Exception as e:
            # Hata durumunda sadece metin döndür
            question_text = self.generate_cv_based_question(cv_analysis)
            return {
                'audio_file': None,
                'question_text': question_text,
                'audio_data': None,
                'error': str(e)
            }

    def generate_personalized_questions(self, cv_analysis, difficulty='medium'):
        """
        CV analizine göre kişiselleştirilmiş sorular üretir
        """
        try:
            prompt = f"""
            Aşağıdaki CV analizi sonucuna göre {difficulty} zorluk seviyesinde 5 adet mülakat sorusu üret:
            
            CV Analizi:
            {cv_analysis}
            
            Soruları şu kategorilerde dağıt:
            - Teknik bilgi ve deneyim
            - Problem çözme yaklaşımı
            - Takım çalışması ve iletişim
            - Kariyer hedefleri ve motivasyon
            - Öğrenme ve gelişim
            
            Her soru için:
            - Soru metni
            - Beklenen cevap anahtarları
            - Zorluk seviyesi
            
            JSON formatında döndür.
            """
            
            response = self.model.generate_content(prompt)
            # JSON parse etmeye çalış, başarısız olursa basit liste döndür
            try:
                import json
                questions = json.loads(response.text)
                return questions
            except:
                # Basit format döndür
                questions = []
                lines = response.text.strip().split('\n')
                current_question = {}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Soru') or line.startswith('Q'):
                        if current_question:
                            questions.append(current_question)
                        current_question = {'question': line}
                    elif line and current_question:
                        if 'question' in current_question:
                            current_question['question'] += ' ' + line
                
                if current_question:
                    questions.append(current_question)
                
                return questions[:5]  # Maksimum 5 soru
            
        except Exception as e:
            # Fallback sorular
            return [
                {'question': f'{self.interest} alanında deneyiminiz hakkında ne söyleyebilirsiniz?'},
                {'question': 'En büyük teknik zorlukla nasıl karşılaştınız?'},
                {'question': 'Takım çalışmasında nasıl bir rol üstlenirsiniz?'},
                {'question': 'Kariyer hedefleriniz nelerdir?'},
                {'question': 'Yeni teknolojileri nasıl öğrenirsiniz?'}
            ]

    def generate_speech_feedback(self, question, user_answer, cv_context=None, voice_name='Enceladus'):
        """
        Kullanıcı cevabına sesli geri bildirim üretir
        """
        try:
            # Önce metin geri bildirimi üret
            if cv_context:
                text_feedback = self.evaluate_cv_answer(question, user_answer, cv_context)
            else:
                text_feedback = self.evaluate_answer(question, user_answer)
            
            # Sonra bu geri bildirimi sesli hale getir
            if not self.client:
                raise Exception("Sesli özellik kullanılamıyor - client başlatılamadı")
                
            speech_prompt = f"""
            Şu mülakat geri bildirimini profesyonel ve destekleyici bir tonda oku:
            
            "{text_feedback}"
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=speech_prompt,
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
            
            return {
                'audio_file': temp_file.name,
                'feedback_text': text_feedback,
                'audio_data': audio_data
            }
            
        except Exception as e:
            print(f"Speech feedback generation error: {e}")
            # Hata durumunda sadece metin geri bildirim döndür
            try:
                if cv_context:
                    text_feedback = self.evaluate_cv_answer(question, user_answer, cv_context)
                else:
                    text_feedback = self.evaluate_answer(question, user_answer)
            except Exception as eval_error:
                print(f"Text feedback generation error: {eval_error}")
                text_feedback = f"Cevap değerlendirilemedi: {str(eval_error)}"
                
            return {
                'audio_file': None,
                'feedback_text': text_feedback,
                'audio_data': None,
                'error': f'Sesli geri bildirim üretilemedi: {str(e)}'
            }

    def evaluate_answer(self, question, user_answer):
        """
        Kullanıcı cevabını değerlendirir
        """
        try:
            prompt = f"""
            Mülakat sorusu: {question}
            Kullanıcı cevabı: {user_answer}
            
            Bu cevabı değerlendir ve yapıcı geri bildirim ver:
            1. Cevabın güçlü yanları
            2. Geliştirilebilir alanlar
            3. Öneriler
            
            Kısa ve destekleyici bir değerlendirme yap.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Cevap değerlendirilemedi: {str(e)}"

    def evaluate_cv_answer(self, question, user_answer, cv_context):
        """
        CV bağlamında kullanıcı cevabını değerlendirir
        """
        try:
            prompt = f"""
            CV Analizi: {cv_context}
            Mülakat sorusu: {question}
            Kullanıcı cevabı: {user_answer}
            
            Bu cevabı CV bağlamında değerlendir:
            1. Cevap CV ile tutarlı mı?
            2. Deneyim seviyesine uygun mu?
            3. Güçlü yanlar ve geliştirme alanları
            4. Öneriler
            
            Kısa ve yapıcı bir değerlendirme yap.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"CV bağlamında değerlendirme yapılamadı: {str(e)}"

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
            print(f"Speech answer evaluation error: {e}")
            # Transcript edilemezse sadece ek metni kullan
            try:
                if additional_text:
                    result = self.generate_speech_feedback(question, additional_text, cv_context, voice_name)
                    result['transcribed_text'] = f"Ses transcript edilemedi: {str(e)}"
                    return result
                else:
                    return {
                        'audio_file': None,
                        'feedback_text': f"Ses değerlendirilemedi: {str(e)}",
                        'audio_data': None,
                        'transcribed_text': f"Ses transcript edilemedi: {str(e)}",
                        'error': f'Sesli cevap değerlendirilemedi: {str(e)}'
                    }
            except Exception as feedback_error:
                print(f"Feedback generation error: {feedback_error}")
                return {
                    'audio_file': None,
                    'feedback_text': f"Ses değerlendirilemedi: {str(e)}",
                    'audio_data': None,
                    'transcribed_text': f"Ses transcript edilemedi: {str(e)}",
                    'error': f'Sesli cevap değerlendirilemedi: {str(e)}. Geri bildirim hatası: {str(feedback_error)}'
                }

    def evaluate_conversation_progress(self, questions, answers):
        """
        Mülakat ilerlemesini değerlendirir ve sonraki adım önerisi verir
        """
        try:
            # Eğer henüz cevap yoksa, mülakatın başladığını belirt
            if not answers:
                return f"{self.interest} alanında mülakat başladı. İlk soruya cevap verildikten sonra detaylı değerlendirme yapılacak."
            
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
            
            Bu mülakatın kapsamlı değerlendirmesini yap. Temiz ve düzenli bir format kullan:
            
            Güçlü Yönler:
            - Kullanıcının en iyi performans gösterdiği alanlar
            - Olumlu özellikler ve beceriler
            
            Geliştirilmesi Gereken Alanlar:
            - Eksiklikler ve zayıf noktalar
            - İyileştirme önerileri
            
            Genel İzlenim:
            - Mülakatın genel tonu ve atmosferi
            - Kullanıcının motivasyonu ve ilgisi
            
            Öneriler:
            - Kariyer gelişimi için öneriler
            - Öğrenme kaynakları ve yönlendirmeler
            
            Puanlama (1-10):
            - Genel performans: X/10
            - İletişim becerileri: X/10
            - Teknik bilgi: X/10
            - Problem çözme: X/10
            
            Yapıcı, destekleyici ve detaylı bir değerlendirme yap. Gereksiz işaretler (*) kullanma, temiz markdown formatında yaz.
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
            print(f"Transcribing audio file: {audio_file_path}")
            
            # Ses dosyasını oku
            with open(audio_file_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Dosya boyutu kontrolü
            if len(audio_data) == 0:
                return "Ses dosyası boş veya okunamadı."
            
            file_size_mb = len(audio_data) / (1024 * 1024)
            print(f"Audio file size for transcription: {file_size_mb:.2f} MB")
            
            if file_size_mb > 20:  # 20MB limit for transcription
                return "Ses dosyası transcript için çok büyük. Daha kısa kayıt yapın."
            
            # Gemini ile transcript et - daha kısa ve odaklı prompt
            prompt = "Bu ses dosyasındaki konuşmayı metne dönüştür. Sadece konuşulan metni ver."
            
            # Farklı MIME type'ları dene - hızlı failover
            mime_types = ["audio/webm", "audio/wav", "audio/mpeg"]
            
            for i, mime_type in enumerate(mime_types):
                try:
                    print(f"Trying transcription with MIME type: {mime_type} (attempt {i+1})")
                    
                    response = self.model.generate_content([
                        {
                            "mime_type": mime_type,
                            "data": base64.b64encode(audio_data).decode()
                        },
                        prompt
                    ])
                    
                    result = response.text.strip()
                    if result and not result.lower().startswith('hata') and len(result) > 3:
                        print(f"Transcription successful with {mime_type}")
                        return result
                except Exception as e:
                    print(f"MIME type {mime_type} failed: {e}")
                    if i == len(mime_types) - 1:  # Son deneme
                        break
                    continue
            
            # Hiçbir MIME type başarılı olmadıysa
            return "Ses transcript edilemedi. Lütfen daha net konuşun veya metin ile cevap verin."
            
        except FileNotFoundError:
            print(f"Audio file not found: {audio_file_path}")
            return "Ses dosyası bulunamadı."
        except Exception as e:
            print(f"Transcription error: {e}")
            print(f"Audio file path: {audio_file_path}")
            return f"Ses transcript hatası: {str(e)}. Manuel cevap yazabilirsiniz."

    def _save_wave_file(self, filename, pcm_data, channels=1, rate=24000, sample_width=2):
        """
        PCM verisini wave dosyası olarak kaydeder
        """
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)

    def analyze_cv(self, cv_data, mime_type):
        """
        CV dosyasını analiz eder
        """
        try:
            # CV metnini çıkar
            cv_text = extract_text_from_file(cv_data, mime_type)
            
            # CV analizi yap
            prompt = f"""
            Aşağıdaki CV'yi analiz et ve şu bilgileri çıkar:
            
            CV:
            {cv_text}
            
            Analiz sonucunu şu formatta ver:
            
            **Kişisel Bilgiler:**
            - Ad Soyad:
            - E-posta:
            - Telefon:
            - Konum:
            
            **Eğitim:**
            - Derece ve okul bilgileri
            
            **İş Deneyimi:**
            - Şirket adları ve pozisyonlar
            - Çalışma süreleri
            - Sorumluluklar ve başarılar
            
            **Teknik Beceriler:**
            - Programlama dilleri
            - Teknolojiler
            - Araçlar ve platformlar
            
            **Projeler:**
            - Önemli projeler ve açıklamaları
            
            **Sertifikalar:**
            - Varsa sertifika bilgileri
            
            **Dil Becerileri:**
            - Bildiği diller ve seviyeleri
            
            **Genel Değerlendirme:**
            - Deneyim seviyesi
            - Güçlü yanlar
            - Geliştirilebilir alanlar
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"CV analizi yapılamadı: {str(e)}"

def extract_text_from_file(file_data, mime_type):
    """
    Dosya verisinden metin çıkarır
    """
    try:
        if mime_type == 'application/pdf':
            # PDF işleme
            import PyPDF2
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            # Word dosyası işleme
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_data))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        else:
            # Diğer dosya türleri için basit text decode
            return file_data.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Dosya okuma hatası: {str(e)}" 