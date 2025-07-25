from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai
from dotenv import load_dotenv
import os
from agents.test_agent import TestAIAgent
from agents.interview_agent import InterviewAIAgent
from agents.case_study_agent import CaseStudyAIAgent
from agents.code_agent import CodeAIAgent
from flask_sqlalchemy import SQLAlchemy
from models.user import db, User
from models.history import UserHistory

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Geliştirme için, prod'da değiştirilmeli
CORS(app, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///btk_project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Geçici bellek içi veri saklama
users = {}  # username: {password_hash, interest}

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Kullanıcı zaten mevcut.'}), 400
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    session['username'] = username
    return jsonify({'message': 'Kayıt başarılı.'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre.'}), 401
    session['username'] = username
    return jsonify({'message': 'Giriş başarılı.'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Çıkış başarılı.'})

@app.route('/set_interest', methods=['POST'])
def set_interest():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    data = request.json
    interest = data.get('interest')
    if not interest:
        return jsonify({'error': 'İlgi alanı gerekli.'}), 400
    user = User.query.filter_by(username=session['username']).first()
    user.interest = interest
    db.session.commit()
    return jsonify({'message': 'İlgi alanı kaydedildi.'})

@app.route('/profile', methods=['GET'])
def profile():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    return jsonify({
        'username': user.username,
        'interest': user.interest
    })

@app.route('/test_your_skill', methods=['POST'])
def test_your_skill():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    try:
        agent = TestAIAgent(user.interest)
        questions = agent.generate_questions()
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    for q in questions:
        q.pop('answer', None)
    return jsonify({'questions': questions})

@app.route('/interview_simulation', methods=['POST'])
def interview_simulation():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    try:
        agent = InterviewAIAgent(user.interest)
        question = agent.generate_question()
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    return jsonify({
        'message': f'{user.interest} alanında mülakat başlatıldı.',
        'question': question
    })

@app.route('/case_study_room', methods=['POST'])
def case_study_room():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    try:
        agent = CaseStudyAIAgent(user.interest)
        case = agent.generate_case()
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    return jsonify({
        'message': f'{user.interest} alanında case study başlatıldı.',
        'case': case
    })

@app.route('/code_room', methods=['POST'])
def code_room():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    try:
        agent = CodeAIAgent(user.interest)
        coding_question = agent.generate_coding_question()
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    return jsonify({
        'message': f'{user.interest} alanında kodlama sorusu oluşturuldu.',
        'coding_question': coding_question
    })

@app.route('/user_history', methods=['GET'])
def user_history():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    history = UserHistory.query.filter_by(username=session['username']).order_by(UserHistory.created_at.desc()).all()
    return jsonify([
        {
            'activity_type': h.activity_type,
            'detail': h.detail,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M')
        } for h in history
    ])

# Test çözümü kaydı
@app.route('/test_your_skill/evaluate', methods=['POST'])
def test_your_skill_evaluate():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    data = request.json
    user_answers = data.get('user_answers')
    questions = data.get('questions')
    if not user_answers or not questions:
        return jsonify({'error': 'Cevaplar ve sorular gerekli.'}), 400
    agent = TestAIAgent(user.interest)
    results = agent.evaluate_answers(user_answers, questions)
    wrong_topics = [r['question'] for r in results if not r['is_correct']]
    resources = []
    if wrong_topics:
        resources = agent.suggest_resources(wrong_topics[0])
    # Geçmişe kaydet
    detail = f"{sum(r['is_correct'] for r in results)}/{len(results)} doğru. İlgi alanı: {user.interest}"
    history = UserHistory(username=user.username, activity_type='test', detail=detail)
    db.session.add(history)
    db.session.commit()
    return jsonify({'results': results, 'resources': resources})

# Code Room çözümü kaydı
@app.route('/code_room/evaluate', methods=['POST'])
def code_room_evaluate():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    data = request.json
    user_code = data.get('user_code')
    question = data.get('question')
    if not user_code or not question:
        return jsonify({'error': 'Kod ve soru gerekli.'}), 400
    agent = CodeAIAgent(user.interest)
    evaluation = agent.evaluate_code(user_code, question)
    # Geçmişe kaydet
    detail = f"Kodlama sorusu: {question[:60]}..."
    history = UserHistory(username=user.username, activity_type='code', detail=detail)
    db.session.add(history)
    db.session.commit()
    return jsonify({'evaluation': evaluation})

# Case Study çözümü kaydı
@app.route('/case_study_room/evaluate', methods=['POST'])
def case_study_room_evaluate():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    data = request.json
    case = data.get('case')
    user_solution = data.get('user_solution')
    if not case or not user_solution:
        return jsonify({'error': 'Case ve çözüm gerekli.'}), 400
    agent = CaseStudyAIAgent(user.interest)
    try:
        evaluation = agent.evaluate_case_solution(case, user_solution)
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    # Geçmişe kaydet
    detail = f"Case: {case[:60]}..."
    history = UserHistory(username=user.username, activity_type='case', detail=detail)
    db.session.add(history)
    db.session.commit()
    return jsonify({'evaluation': evaluation})

# Interview çözümü kaydı
@app.route('/interview_simulation/evaluate', methods=['POST'])
def interview_simulation_evaluate():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    data = request.json
    question = data.get('question')
    user_answer = data.get('user_answer')
    if not question or not user_answer:
        return jsonify({'error': 'Soru ve cevap gerekli.'}), 400
    agent = InterviewAIAgent(user.interest)
    try:
        evaluation = agent.evaluate_answer(question, user_answer)
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    # Geçmişe kaydet
    detail = f"Mülakat sorusu: {question[:60]}..."
    history = UserHistory(username=user.username, activity_type='interview', detail=detail)
    db.session.add(history)
    db.session.commit()
    return jsonify({'evaluation': evaluation})

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return jsonify({'error': 'Mevcut ve yeni şifre gerekli.'}), 400
    user = User.query.filter_by(username=session['username']).first()
    if not user or not user.check_password(old_password):
        return jsonify({'error': 'Mevcut şifre yanlış.'}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Şifre başarıyla değiştirildi.'})

if __name__ == '__main__':
    app.run(debug=True)
