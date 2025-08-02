# Code Execution Integration with Google Generative AI

Bu dokümantasyon, `CodeAIAgent` sınıfına entegre edilen yeni Google Generative AI kod çalıştırma özelliklerini açıklar.

## 🚀 Yeni Özellikler

### 1. Gerçek Zamanlı Kod Çalıştırma
- Kullanıcı kodunu gerçek zamanlı olarak çalıştırır
- Hata yakalama ve raporlama
- Çıktı ve hata mesajlarını ayrı ayrı gösterir

### 2. Gelişmiş Değerlendirme
- Kod çalıştırma ile birlikte değerlendirme
- Otomatik puanlama sistemi
- Detaylı geri bildirim

### 3. Matematik Problem Çözme
- Karmaşık matematik problemlerini kod ile çözme
- Hesaplama sonuçlarını gösterme

### 4. Veri Analizi
- Veri analizi görevlerini kod ile gerçekleştirme
- İstatistiksel hesaplamalar

## 📦 Gereksinimler

```bash
pip install google-genai>=0.6.0
```

## 🔧 Kurulum

1. `.env` dosyanızda `GEMINI_API_KEY` değişkenini ayarlayın:
```env
GEMINI_API_KEY=your_api_key_here
```

2. `CodeAIAgent` sınıfını kullanmaya başlayın:
```python
from agents.code_agent import CodeAIAgent

agent = CodeAIAgent(interest="programming", language="python")
```

## 📚 Kullanım Örnekleri

### Temel Kod Çalıştırma

```python
# Basit kod çalıştırma
code = """
print("Hello, World!")
x = 5 + 3
print(f"5 + 3 = {x}")
"""

result = agent.run_code(code)
print(result['execution_output'])
print(f"Has Errors: {result['has_errors']}")
```

### Kod Değerlendirme ile Çalıştırma

```python
# Kod değerlendirme ve çalıştırma
question = "Write a function that calculates factorial"
user_code = """
def factorial(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
"""

result = agent.evaluate_code_with_execution(user_code, question)
print(f"Score: {result['score']}")
print(f"Evaluation: {result['evaluation']}")
print(f"Execution Output: {result['execution_output']}")
```

### Matematik Problem Çözme

```python
# Matematik problemi çözme
problem = "What is the sum of the first 50 prime numbers?"
result = agent.solve_math_problem(problem)

if result['success']:
    print(f"Code: {result['code']}")
    print(f"Result: {result['output']}")
else:
    print(f"Error: {result['error']}")
```

### Veri Analizi

```python
# Veri analizi
data_description = "A list of numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]"
result = agent.analyze_data(data_description, "statistical")

if result['success']:
    print(f"Analysis Code: {result['code']}")
    print(f"Analysis Results: {result['output']}")
```

### Karmaşık Kod Çalıştırma

```python
# Karmaşık kod çalıştırma
complex_prompt = """
Generate and run code to find all prime numbers between 1 and 100.
Then calculate the sum of these prime numbers.
"""

result = agent.execute_complex_code(complex_prompt)
print(f"Success: {result['success']}")
print(f"Generated Code: {result['code']}")
print(f"Output: {result['output']}")
```

## 🔍 API Değişiklikleri

### Eski API (google.generativeai)
```python
import google.generativeai as genai
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite')
response = model.generate_content(prompt)
```

### Yeni API (google.genai)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)
chat = client.chats.create(
    model="gemini-2.0-flash-exp",
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)]
    ),
)
response = chat.send_message(prompt)
```

## 🧪 Test Etme

Test scriptini çalıştırmak için:

```bash
python test_code_execution.py
```

Bu script şunları test eder:
- Temel kod çalıştırma
- Matematik problem çözme
- Veri analizi
- Kod değerlendirme
- Karmaşık kod çalıştırma

## ⚠️ Önemli Notlar

1. **API Kotası**: Google Generative AI API'sinin kotasına dikkat edin
2. **Model Sınırlamaları**: `gemini-2.0-flash-exp` modeli kod çalıştırma için gereklidir
3. **Güvenlik**: Kullanıcı kodunu güvenli bir şekilde çalıştırın
4. **Hata Yönetimi**: API hatalarını uygun şekilde yakalayın

## 🔄 Geriye Uyumluluk

Eski API kullanımı hala desteklenmektedir. Fallback model olarak `gemini-2.0-flash-lite` kullanılır:
- Kod çalıştırma gerektirmeyen işlemler için
- Eski kodlarla uyumluluk için

## 📈 Performans

- **Kod Çalıştırma**: Gerçek zamanlı
- **Değerlendirme**: Kod çalıştırma ile birlikte
- **Hata Yakalama**: Otomatik
- **Sonuç Formatı**: Yapılandırılmış JSON

## 🛠️ Sorun Giderme

### Yaygın Hatalar

1. **API Key Hatası**:
   ```
   ValueError: GEMINI_API_KEY environment variable is not set
   ```
   Çözüm: `.env` dosyasında API key'i ayarlayın

2. **Model Hatası**:
   ```
   Model not found: gemini-2.0-flash-exp
   ```
   Çözüm: Doğru model adını kullandığınızdan emin olun

3. **Kod Çalıştırma Hatası**:
   ```
   Code execution failed
   ```
   Çözüm: Kodun syntax'ını kontrol edin

### Debug Modu

Debug modunu etkinleştirmek için:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📞 Destek

Sorunlarınız için:
1. Test scriptini çalıştırın
2. API key'inizi kontrol edin
3. Model adlarını doğrulayın
4. Kod syntax'ını kontrol edin 