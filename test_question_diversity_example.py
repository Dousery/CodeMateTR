#!/usr/bin/env python3
"""
Test Agent Soru Çeşitliliği Örneği
Bu dosya, güncellenmiş TestAIAgent'ın nasıl kullanılacağını gösterir.
"""

from agents.test_agent import TestAIAgent
import uuid
from datetime import datetime

def main():
    # Test agent'ı oluştur
    interest = "Data Science"
    agent = TestAIAgent(interest)
    
    print(f"=== {interest} Test Agent Soru Çeşitliliği Demo ===\n")
    
    # Örnek kullanıcı ID'leri
    user_id_1 = "user_123"
    user_id_2 = "user_456"
    
    # İlk kullanıcı için test
    print("1. İlk kullanıcı için test soruları üretiliyor...")
    session_id_1 = str(uuid.uuid4())
    questions_1 = agent.generate_questions(
        num_questions=5, 
        difficulty='mixed', 
        user_id=user_id_1, 
        session_id=session_id_1
    )
    
    print(f"   Üretilen soru sayısı: {len(questions_1)}")
    for i, q in enumerate(questions_1, 1):
        print(f"   Soru {i}: {q['question'][:50]}... (Kategori: {q['category']}, Zorluk: {q['difficulty']})")
    
    print("\n" + "="*60 + "\n")
    
    # Aynı kullanıcı için ikinci test (farklı seans)
    print("2. Aynı kullanıcı için ikinci test (farklı seans)...")
    session_id_1b = str(uuid.uuid4())
    questions_1b = agent.generate_questions(
        num_questions=5, 
        difficulty='mixed', 
        user_id=user_id_1, 
        session_id=session_id_1b
    )
    
    print(f"   Üretilen soru sayısı: {len(questions_1b)}")
    for i, q in enumerate(questions_1b, 1):
        print(f"   Soru {i}: {q['question'][:50]}... (Kategori: {q['category']}, Zorluk: {q['difficulty']})")
    
    # Aynı soruların tekrarlanıp tekrarlanmadığını kontrol et
    questions_1_texts = [q['question'] for q in questions_1]
    questions_1b_texts = [q['question'] for q in questions_1b]
    
    repeated_questions = set(questions_1_texts) & set(questions_1b_texts)
    print(f"\n   Tekrarlanan soru sayısı: {len(repeated_questions)}")
    
    print("\n" + "="*60 + "\n")
    
    # İkinci kullanıcı için test
    print("3. İkinci kullanıcı için test soruları üretiliyor...")
    session_id_2 = str(uuid.uuid4())
    questions_2 = agent.generate_questions(
        num_questions=5, 
        difficulty='mixed', 
        user_id=user_id_2, 
        session_id=session_id_2
    )
    
    print(f"   Üretilen soru sayısı: {len(questions_2)}")
    for i, q in enumerate(questions_2, 1):
        print(f"   Soru {i}: {q['question'][:50]}... (Kategori: {q['category']}, Zorluk: {q['difficulty']})")
    
    print("\n" + "="*60 + "\n")
    
    # Adaptif soru üretimi demo
    print("4. Adaptif soru üretimi demo...")
    
    # Önceki performans simülasyonu
    previous_performance = {
        'success_rate': 65,
        'weak_areas': [
            {'category': 'Machine Learning', 'success_rate': 40},
            {'category': 'Data Analysis', 'success_rate': 55}
        ]
    }
    
    adaptive_questions = agent.generate_adaptive_questions(
        user_id=user_id_1,
        session_id=str(uuid.uuid4()),
        previous_performance=previous_performance,
        num_questions=5
    )
    
    print(f"   Adaptif soru sayısı: {len(adaptive_questions)}")
    for i, q in enumerate(adaptive_questions, 1):
        print(f"   Soru {i}: {q['question'][:50]}... (Kategori: {q['category']}, Zorluk: {q['difficulty']})")
    
    print("\n" + "="*60 + "\n")
    
    # İstatistikler
    print("5. Soru havuzu ve kullanıcı istatistikleri...")
    
    # Genel istatistikler
    general_stats = agent.get_question_statistics()
    print(f"   Toplam soru havuzu: {general_stats['total_questions_in_pool']}")
    print(f"   Kategoriler: {list(general_stats['pool_categories'].keys())}")
    print(f"   Zorluk seviyeleri: {list(general_stats['pool_difficulties'].keys())}")
    
    # Kullanıcı 1 istatistikleri
    user1_stats = agent.get_question_statistics(user_id_1)
    if user1_stats['user_history']:
        print(f"\n   Kullanıcı 1 toplam cevaplanan soru: {user1_stats['user_history']['total_questions_answered']}")
        print(f"   Kullanıcı 1 seans sayısı: {len(user1_stats['user_history']['questions_by_session'])}")
    
    print("\n" + "="*60 + "\n")
    
    # Soru havuzunu yenileme demo
    print("6. Soru havuzu yenileme demo...")
    refresh_result = agent.refresh_question_pool(force_refresh=True)
    print(f"   Havuz yenilendi: {refresh_result}")
    
    # Yenileme sonrası istatistikler
    new_stats = agent.get_question_statistics()
    print(f"   Yeni toplam soru sayısı: {new_stats['total_questions_in_pool']}")
    
    print("\n" + "="*60 + "\n")
    
    print("Demo tamamlandı! ✅")
    print("\nÖnemli özellikler:")
    print("• Her kullanıcı için benzersiz soru geçmişi takibi")
    print("• Farklı seanslarda aynı soruların tekrarlanmasını önleme")
    print("• Çeşitli kategorilerden dengeli soru seçimi")
    print("• Performansa göre adaptif soru üretimi")
    print("• Otomatik soru havuzu yönetimi")

if __name__ == "__main__":
    main()
