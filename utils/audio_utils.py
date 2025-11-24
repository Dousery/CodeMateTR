"""Audio utility functions for speech generation and handling."""
import wave
import tempfile
import os
from google.genai import types


def save_wave_file(filename, pcm_data, channels=1, rate=24000, sample_width=2):
    """
    Save PCM data as a wave file.
    
    Args:
        filename (str): Output filename
        pcm_data (bytes): PCM audio data
        channels (int): Number of audio channels (default: 1)
        rate (int): Sample rate in Hz (default: 24000)
        sample_width (int): Sample width in bytes (default: 2)
    """
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


def generate_speech_with_client(client, text, voice_name='Kore', model="gemini-2.5-flash-preview-tts"):
    """
    Generate speech audio from text using Gemini client.
    
    Args:
        client: Gemini client instance
        text (str): Text to convert to speech
        voice_name (str): Voice configuration name (default: 'Kore')
        model (str): Model to use for generation
        
    Returns:
        dict: Dictionary with audio_file path, audio_data, and text, or error info
    """
    if not client:
        return {
            'audio_file': None,
            'question_text': text,
            'audio_data': None,
            'error': 'Sesli özellik kullanılamıyor - client başlatılamadı'
        }
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=text,
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
        save_wave_file(temp_file.name, audio_data)
        
        return {
            'audio_file': temp_file.name,
            'question_text': text,
            'audio_data': audio_data
        }
    except Exception as audio_error:
        print(f"Audio generation error: {audio_error}")
        return {
            'audio_file': None,
            'question_text': text,
            'audio_data': None,
            'error': f'Ses üretilemedi: {str(audio_error)}'
        }


def create_audio_response(text, client=None, voice_name='Kore'):
    """
    Create a speech audio response from text, with fallback to text-only.
    
    Args:
        text (str): Text to convert to speech
        client: Gemini client instance (optional)
        voice_name (str): Voice configuration name
        
    Returns:
        dict: Audio response dictionary with text and optional audio
    """
    if client:
        return generate_speech_with_client(client, text, voice_name)
    else:
        return {
            'audio_file': None,
            'question_text': text,
            'audio_data': None,
            'error': 'Sesli özellik kullanılamıyor'
        }
