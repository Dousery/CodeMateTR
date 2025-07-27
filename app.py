from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import os
from agents.test_agent import TestAIAgent
from agents.interview_agent import InterviewAIAgent
from agents.case_study_agent import CaseStudyAIAgent
from agents.code_agent import CodeAIAgent
from flask_sqlalchemy import SQLAlchemy
import threading
import time
from datetime import datetime, timedelta
import json

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'  # Geliştirme için, prod'da değiştirilmeli

# CORS ayarlarını daha spesifik yap
CORS(app, 
     origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"])

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///btk_project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session ayarları
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 saat
app.config['SESSION_COOKIE_SECURE'] = False  # Development için
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Tek bir db instance oluştur
db = SQLAlchemy(app)

# Model sınıflarını burada tanımla
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    interest = db.Column(db.String(80), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    activity_type = db.Column(db.String(32), nullable=False)  # test, code, case, interview
    detail = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    interest = db.Column(db.String(80), nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    success_rate = db.Column(db.Float, nullable=False)
    skill_level = db.Column(db.String(20), nullable=False)
    time_taken = db.Column(db.Integer, nullable=False)  # saniye cinsinden
    difficulty = db.Column(db.String(20), nullable=False)
    weak_areas = db.Column(db.Text, nullable=True)  # JSON string
    strong_areas = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# Geçici bellek içi veri saklama
users = {}  # username: {password_hash, interest}

# Case Study eşleştirme sistemi
case_study_queue = {}  # interest: [usernames]
active_case_sessions = {}  # session_id: {users: [], case: {}, start_time: datetime, duration: 30, messages: [], audio_messages: []}

# Session persistence için database tablosu
class CaseSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    users = db.Column(db.Text, nullable=False)  # JSON string
    case_data = db.Column(db.Text, nullable=False)  # JSON string
    status = db.Column(db.String(20), default='active')  # active, completed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    messages = db.Column(db.Text, nullable=True)  # JSON string
    audio_messages = db.Column(db.Text, nullable=True)  # JSON string
    evaluations = db.Column(db.Text, nullable=True)  # JSON string

# Test session'ları için database tablosu
class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    questions = db.Column(db.Text, nullable=False)  # JSON string
    difficulty = db.Column(db.String(20), nullable=False)
    num_questions = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # saniye
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, completed, expired

# Database'den session'ları yükle
def load_sessions_from_db():
    with app.app_context():
        try:
            sessions = CaseSession.query.filter_by(status='active').all()
            for session_db in sessions:
                session_data = {
                    'users': json.loads(session_db.users),
                    'case': json.loads(session_db.case_data),
                    'start_time': session_db.start_time,
                    'duration': 30,
                    'messages': json.loads(session_db.messages) if session_db.messages else [],
                    'audio_messages': json.loads(session_db.audio_messages) if session_db.audio_messages else [],
                    'status': session_db.status
                }
                active_case_sessions[session_db.session_id] = session_data
            print(f"Database'den {len(sessions)} aktif session yüklendi.")
        except Exception as e:
            print(f"Session yükleme hatası: {e}")

# Uygulama context'i oluşturulduktan sonra session'ları yükle
def init_app():
    with app.app_context():
        db.create_all()
        load_sessions_from_db()
        # Eski test session'larını temizle
        expired_sessions = TestSession.query.filter_by(status='active').all()
        for test_session in expired_sessions:
            session_age = (datetime.utcnow() - test_session.start_time).total_seconds()
            if session_age > test_session.duration:
                test_session.status = 'expired'
        db.session.commit()
        print(f"Cleaned {len([s for s in expired_sessions if s.status == 'expired'])} expired test sessions")

# Session yüklemeyi app başladığında değil, route çağrıldığında yap
# load_sessions_from_db()

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    interest = data.get('interest')
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli.'}), 400
    if not interest:
        return jsonify({'error': 'İlgi alanı gerekli.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Kullanıcı zaten mevcut.'}), 400
    user = User(username=username, interest=interest)
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
    
    # Kullanıcı login olduğunda eski session'larını temizle
    # Kullanıcıyı tüm kuyruklardan çıkar
    for interest in case_study_queue:
        if username in case_study_queue[interest]:
            case_study_queue[interest].remove(username)
    
    # Kullanıcıyı tüm aktif session'lardan çıkar
    for session_id, session_data in list(active_case_sessions.items()):
        if username in session_data['users']:
            session_data['users'].remove(username)
            # Eğer session'da başka kullanıcı kalmadıysa session'ı sil
            if not session_data['users']:
                del active_case_sessions[session_id]
    
    session['username'] = username
    return jsonify({'message': 'Giriş başarılı.'})

@app.route('/logout', methods=['POST'])
def logout():
    if 'username' in session:
        username = session['username']
        
        # Kullanıcıyı tüm case study kuyruklarından çıkar
        for interest in case_study_queue:
            if username in case_study_queue[interest]:
                case_study_queue[interest].remove(username)
        
        # Kullanıcının aktif session'larını tamamla
        for session_id, session_data in list(active_case_sessions.items()):
            if username in session_data['users'] and session_data['status'] == 'active':
                # Session'ı completed olarak işaretle
                session_data['status'] = 'completed'
                session_data['end_time'] = datetime.now()
                
                # Kullanıcıyı session'dan çıkar
                session_data['users'].remove(username)
                
                # Eğer session'da başka kullanıcı kalmadıysa session'ı sil
                if not session_data['users']:
                    del active_case_sessions[session_id]
    
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
    
    data = request.json
    num_questions = data.get('num_questions', 10)
    difficulty = data.get('difficulty', 'mixed')
    
    try:
        agent = TestAIAgent(user.interest)
        questions = agent.generate_questions(num_questions, difficulty)
        
        # Test sessionu oluştur
        test_session_id = f"test_{int(time.time())}_{user.username}"
        
        # Eski session'ları temizle (30 dakikadan eski olanlar)
        old_sessions = TestSession.query.filter(
            TestSession.username == user.username,
            TestSession.status == 'active'
        ).all()
        
        for old_session in old_sessions:
            session_age = (datetime.utcnow() - old_session.start_time).total_seconds()
            if session_age > 1800:  # 30 dakika
                old_session.status = 'expired'
        
        # Yeni test session'ını database'e kaydet
        test_session = TestSession(
            session_id=test_session_id,
            username=user.username,
            questions=json.dumps(questions),
            difficulty=difficulty,
            num_questions=num_questions,
            duration=30 * 60  # 30 dakika
        )
        db.session.add(test_session)
        db.session.commit()
        
        print(f"Test session created and saved to DB: {test_session_id}")
        
        # Sorulardan doğru cevapları çıkar (frontend'e gönderme)
        questions_for_frontend = []
        for q in questions:
            question_copy = q.copy()
            question_copy.pop('correct_answer', None)  # Doğru cevabı gizle
            question_copy.pop('explanation', None)     # Açıklamayı gizle
            questions_for_frontend.append(question_copy)
        
        return jsonify({
            'questions': questions_for_frontend,
            'test_session_id': test_session_id,
            'duration': 30 * 60,  # 30 dakika
            'total_questions': len(questions_for_frontend)
        })
        
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500

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
    
    username = session['username']
    interest = user.interest
    
    # Kullanıcının aktif session'da olup olmadığını kontrol et
    for session_id, session_data in active_case_sessions.items():
        if username in session_data['users'] and session_data['status'] == 'active':
            return jsonify({'error': 'Zaten aktif bir case study session\'ınız var.'}), 400
    
    # Kullanıcıyı kuyruğa ekle
    if interest not in case_study_queue:
        case_study_queue[interest] = []
    
    # Kullanıcı zaten kuyrukta mı kontrol et
    if username in case_study_queue[interest]:
        return jsonify({'status': 'waiting', 'message': 'Eşleşme bekleniyor...'})
    
    case_study_queue[interest].append(username)
    
    # Eşleşme kontrolü
    if len(case_study_queue[interest]) >= 2:
        # İki kullanıcıyı eşleştir
        user1, user2 = case_study_queue[interest][:2]
        case_study_queue[interest] = case_study_queue[interest][2:]  # Kuyruktan çıkar
        
        # Case study oluştur
        try:
            agent = CaseStudyAIAgent(interest)
            case = agent.generate_case()
            
            # Session oluştur
            session_id = f"case_{int(time.time())}"
            active_case_sessions[session_id] = {
                'users': [user1, user2],
                'case': case,
                'start_time': datetime.now(),
                'duration': 30,  # 30 dakika
                'solutions': {},
                'messages': [],
                'audio_messages': [],
                'status': 'active'
            }
            
            return jsonify({
                'status': 'matched',
                'session_id': session_id,
                'case': case,
                'partner': user2 if username == user1 else user1,
                'start_time': datetime.now().isoformat(),
                'duration': 30
            })
            
        except Exception as e:
            # Hata durumunda kullanıcıları kuyruğa geri ekle
            case_study_queue[interest].extend([user1, user2])
            return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    
    return jsonify({'status': 'waiting', 'message': 'Eşleşme bekleniyor...'})

@app.route('/case_study_room/check_match', methods=['GET'])
def check_case_match():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    interest = user.interest
    
    # Aktif session'da mı kontrol et
    for session_id, session_data in list(active_case_sessions.items()):
        if username in session_data['users'] and session_data['status'] == 'active':
            return jsonify({
                'status': 'matched',
                'session_id': session_id,
                'case': session_data['case'],
                'partner': next(u for u in session_data['users'] if u != username),
                'start_time': session_data['start_time'].isoformat(),
                'duration': session_data['duration']
            })
        elif username in session_data['users'] and session_data['status'] == 'completed':
            # Completed session'da kullanıcı varsa, onu temizle
            session_data['users'].remove(username)
            # Eğer session'da başka kullanıcı kalmadıysa session'ı sil
            if not session_data['users']:
                del active_case_sessions[session_id]
    
    # Kuyrukta mı kontrol et
    if interest in case_study_queue and username in case_study_queue[interest]:
        return jsonify({'status': 'waiting', 'message': 'Eşleşme bekleniyor...'})
    
    return jsonify({'status': 'not_found'})

@app.route('/case_study_room/submit_solution', methods=['POST'])
def submit_case_solution():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    solution = data.get('solution')
    
    if not session_id or not solution:
        return jsonify({'error': 'Session ID ve çözüm gerekli.'}), 400
    
    if session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    # Çözümü kaydet
    if 'solutions' not in session_data:
        session_data['solutions'] = {}
    session_data['solutions'][username] = solution
    
    return jsonify({'message': 'Çözüm kaydedildi.'})

@app.route('/case_study_room/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    message = data.get('message')
    
    if not session_id or not message:
        return jsonify({'error': 'Session ID ve mesaj gerekli.'}), 400
    
    if session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    # Mesajı kaydet
    message_data = {
        'username': username,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'type': 'text'
    }
    session_data['messages'].append(message_data)
    
    return jsonify({'message': 'Mesaj gönderildi.'})



@app.route('/case_study_room/send_audio', methods=['POST'])
def send_audio():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    session_id = request.form.get('session_id')
    audio_text = request.form.get('audio_text')
    
    if not session_id or not audio_text:
        return jsonify({'error': 'Session ID ve ses metni gerekli.'}), 400
    
    if session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    # Ses dosyasını kaydet
    audio_url = None
    if 'audio_file' in request.files:
        audio_file = request.files['audio_file']
        if audio_file.filename:
            # Ses dosyaları için klasör oluştur
            audio_dir = os.path.join(app.root_path, 'static', 'audio')
            os.makedirs(audio_dir, exist_ok=True)
            
            # Dosya adını güvenli hale getir
            filename = secure_filename(f"{session_id}_{username}_{int(time.time())}.webm")
            filepath = os.path.join(audio_dir, filename)
            
            # Dosyayı kaydet
            audio_file.save(filepath)
            audio_url = f"/static/audio/{filename}"
    
    # Ses mesajını kaydet
    audio_message_data = {
        'username': username,
        'audio_text': audio_text,
        'audio_url': audio_url,
        'timestamp': datetime.now().isoformat(),
        'type': 'audio'
    }
    session_data['audio_messages'].append(audio_message_data)
    
    return jsonify({'message': 'Ses mesajı gönderildi.'})

@app.route('/case_study_room/get_messages', methods=['GET'])
def get_messages():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.args
    session_id = data.get('session_id')
    
    if not session_id or session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    # Tüm mesajları birleştir ve sırala
    all_messages = session_data['messages'] + session_data['audio_messages']
    all_messages.sort(key=lambda x: x['timestamp'])
    
    return jsonify({'messages': all_messages})

@app.route('/case_study_room/complete_session', methods=['POST'])
def complete_session():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        # Yeni bir session oluştur
        session_id = f"case_{int(time.time())}"
        active_case_sessions[session_id] = {
            'users': [session['username']],
            'case': {}, # Case bilgisi henüz alınmadı
            'start_time': datetime.now(),
            'duration': 30,
            'solutions': {},
            'messages': [],
            'audio_messages': [],
            'status': 'active'
        }
        # Yeni session'ı veritabanına kaydet
        new_session_db = CaseSession(
            session_id=session_id,
            users=json.dumps([session['username']]),
            case_data=json.dumps({}),
            status='active'
        )
        db.session.add(new_session_db)
        db.session.commit()
    elif session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    # Oturumu hemen tamamla (tek kullanıcı basınca)
    session_data['status'] = 'completed'
    session_data['end_time'] = datetime.now()

    agent = CaseStudyAIAgent(session_data['case'].get('interest', 'general'))
    evaluations = {}

    # Tüm mesajları birleştir
    all_messages = session_data['messages'] + session_data['audio_messages']
    all_messages.sort(key=lambda x: x['timestamp'])
    conversation_text = ""
    for msg in all_messages:
        if msg['type'] == 'audio':
            conversation_text += f"{msg['username']}: {msg['audio_text']}\n"
        else:
            conversation_text += f"{msg['username']}: {msg['message']}\n"

    # Her kullanıcı için ayrı ayrı değerlendirme yap
    for user in session_data['users']:
        try:
            # Birleşik performans değerlendirmesi (hem çözüm hem mesajlaşma)
            unified_evaluation = agent.evaluate_unified_performance(session_data['case'], conversation_text, user)
            
            evaluations[user] = {
                'unified_evaluation': unified_evaluation
            }
            
        except Exception as e:
            evaluations[user] = {
                'unified_evaluation': {'error': str(e)}
            }

    # Geçmişe kaydet
    for user in session_data['users']:
        detail = f"Case study tamamlandı: {len(all_messages)} mesaj. Partner: {next(u for u in session_data['users'] if u != user)}"
        history = UserHistory(username=user, activity_type='case_conversation', detail=detail)
        db.session.add(history)

    session_data['evaluations'] = evaluations
    db.session.commit()
    
    # Session tamamlandıktan sonra kullanıcıları kuyruktan temizle
    # Interest'i case data'dan al
    case_interest = session_data['case'].get('interest', 'general')
    for user in session_data['users']:
        if case_interest in case_study_queue and user in case_study_queue[case_interest]:
            case_study_queue[case_interest].remove(user)
    
    return jsonify({'message': 'Oturum tamamlandı.'})

@app.route('/case_study_room/get_result', methods=['GET'])
def get_case_result():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.args
    session_id = data.get('session_id')
    
    if not session_id or session_id not in active_case_sessions:
        return jsonify({'error': 'Geçersiz session.'}), 400
    
    session_data = active_case_sessions[session_id]
    username = session['username']
    
    if username not in session_data['users']:
        return jsonify({'error': 'Bu session\'a erişim izniniz yok.'}), 403
    
    if session_data['status'] != 'completed':
        return jsonify({'status': 'not_completed'})
    
    return jsonify({
        'status': 'completed',
        'evaluation': session_data['evaluations'].get(username, {}),
        'partner_evaluation': session_data['evaluations'].get(
            next(u for u in session_data['users'] if u != username), {}
        ),
        'case': session_data['case'],
        'partner': next(u for u in session_data['users'] if u != username),
        'messages': session_data['messages'],
        'audio_messages': session_data['audio_messages']
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

@app.route('/user_test_stats', methods=['GET'])
def user_test_stats():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    username = session['username']
    
    # Son test performansları
    recent_tests = TestPerformance.query.filter_by(username=username)\
        .order_by(TestPerformance.created_at.desc()).limit(10).all()
    
    # Genel istatistikler
    all_tests = TestPerformance.query.filter_by(username=username).all()
    
    if not all_tests:
        return jsonify({
            'total_tests': 0,
            'average_score': 0,
            'best_score': 0,
            'current_level': 'Henüz test alınmadı',
            'improvement_trend': 'Veri yok',
            'recent_tests': []
        })
    
    # İstatistikleri hesapla
    total_tests = len(all_tests)
    average_score = sum(test.success_rate for test in all_tests) / total_tests
    best_score = max(test.success_rate for test in all_tests)
    current_level = recent_tests[0].skill_level if recent_tests else 'Bilinmiyor'
    
    # Gelişim trendi (son 5 test)
    if len(recent_tests) >= 2:
        recent_scores = [test.success_rate for test in recent_tests[:5]]
        recent_scores.reverse()  # Chronological order
        
        if len(recent_scores) >= 2:
            trend_diff = recent_scores[-1] - recent_scores[0]
            if trend_diff > 5:
                improvement_trend = 'Yükseliş'
            elif trend_diff < -5:
                improvement_trend = 'Düşüş'
            else:
                improvement_trend = 'Stabil'
        else:
            improvement_trend = 'Yeterli veri yok'
    else:
        improvement_trend = 'Yeterli veri yok'
    
    # Son testleri formatla
    recent_tests_data = []
    for test in recent_tests:
        recent_tests_data.append({
            'date': test.created_at.strftime('%Y-%m-%d %H:%M'),
            'score': test.success_rate,
            'level': test.skill_level,
            'questions': f"{test.correct_answers}/{test.total_questions}",
            'time': f"{test.time_taken // 60}dk {test.time_taken % 60}sn",
            'difficulty': test.difficulty,
            'interest': test.interest
        })
    
    return jsonify({
        'total_tests': total_tests,
        'average_score': round(average_score, 1),
        'best_score': round(best_score, 1),
        'current_level': current_level,
        'improvement_trend': improvement_trend,
        'recent_tests': recent_tests_data
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
    test_session_id = data.get('test_session_id')
    
    if not user_answers or not test_session_id:
        return jsonify({'error': 'Cevaplar ve test session ID gerekli.'}), 400
    
    # Test session'ını database'den al
    test_session = TestSession.query.filter_by(
        session_id=test_session_id,
        username=user.username,
        status='active'
    ).first()
    
    if not test_session:
        print(f"Test session not found in DB: {test_session_id}")
        return jsonify({'error': 'Geçersiz test session.'}), 400
    
    # Session süre aşımı kontrolü
    session_age = (datetime.utcnow() - test_session.start_time).total_seconds()
    if session_age > test_session.duration:
        test_session.status = 'expired'
        db.session.commit()
        return jsonify({'error': 'Test süresi aşıldı.'}), 400
    
    # Soruları JSON'dan yükle
    questions = json.loads(test_session.questions)
    time_taken = session_age
    
    # Test değerlendirmesi
    agent = TestAIAgent(user.interest)
    evaluation_result = agent.evaluate_answers(user_answers, questions, time_taken)
    
    # Summary'yi al
    summary = evaluation_result['summary']
    
    # Zayıf olunan konular için kaynak önerileri
    resources = []
    web_resources = {}
    if evaluation_result['weak_areas']:
        weak_topic = evaluation_result['weak_areas'][0]['category']
        resources = agent.suggest_resources(weak_topic)
        # Web search ile YouTube ve website önerileri
        web_resources = agent.search_web_resources(weak_topic)
    
    # Test performansını veritabanına kaydet
    test_performance = TestPerformance(
        username=user.username,
        interest=user.interest,
        total_questions=summary['total_questions'],
        correct_answers=summary['correct_answers'],
        success_rate=summary['success_rate'],
        skill_level=summary['skill_level'],
        time_taken=int(time_taken),
        difficulty=test_session.difficulty,
        weak_areas=json.dumps(evaluation_result['weak_areas']),
        strong_areas=json.dumps(evaluation_result['strong_areas'])
    )
    db.session.add(test_performance)
    detail = (f"{summary['correct_answers']}/{summary['total_questions']} doğru "
             f"({summary['success_rate']}%) - Seviye: {summary['skill_level']} - "
             f"Süre: {int(time_taken//60)}dk {int(time_taken%60)}sn")
    
    history = UserHistory(
        username=user.username, 
        activity_type='test', 
        detail=detail
    )
    db.session.add(history)
    db.session.commit()
    
    # Test session'ını tamamlandı olarak işaretle
    test_session.status = 'completed'
    db.session.commit()
    
    print(f"Test session completed: {test_session_id}")
    
    return jsonify({
        'evaluation': evaluation_result,
        'resources': resources,
        'web_resources': web_resources,
        'time_taken': {
            'total_seconds': int(time_taken),
            'minutes': int(time_taken // 60),
            'seconds': int(time_taken % 60)
        }
    })

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

@app.route('/debug/session/<session_id>', methods=['GET'])
def debug_session(session_id):
    if session_id not in active_case_sessions:
        return jsonify({'error': 'Session bulunamadı'})
    
    session_data = active_case_sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'users': session_data['users'],
        'status': session_data['status'],
        'messages_count': len(session_data['messages']),
        'audio_messages_count': len(session_data['audio_messages']),
        'has_evaluations': 'evaluations' in session_data,
        'evaluations': session_data.get('evaluations', {}),
        'case': session_data['case']
    })

@app.route('/debug/queue', methods=['GET'])
def debug_queue():
    return jsonify({
        'case_study_queue': case_study_queue,
        'active_sessions': {k: {'users': v['users'], 'status': v['status']} for k, v in active_case_sessions.items()}
    })

@app.route('/debug/force_match', methods=['POST'])
def force_match():
    data = request.json
    interest = data.get('interest', 'Data Science')

    if interest in case_study_queue and len(case_study_queue[interest]) >= 2:
        user1, user2 = case_study_queue[interest][:2]
        case_study_queue[interest] = case_study_queue[interest][2:]

        # Basit case study oluştur (API olmadan)
        case = {
            "title": f"{interest} Case Study",
            "description": f"Bu bir {interest} alanında test case study'sidir. Lütfen bu senaryoyu çözün.",
            "requirements": ["Çözümü tamamlayın"],
            "constraints": ["30 dakika süre"],
            "evaluation_criteria": ["Çözüm kalitesi", "Analiz derinliği"],
            "interest": interest
        }

        session_id = f"case_{int(time.time())}"
        active_case_sessions[session_id] = {
            'users': [user1, user2],
            'case': case,
            'start_time': datetime.now(),
            'duration': 30,
            'solutions': {},
            'messages': [],
            'audio_messages': [],
            'status': 'active'
        }

        return jsonify({
            'status': 'success',
            'message': f'{user1} ve {user2} eşleştirildi',
            'session_id': session_id
        })

    return jsonify({'status': 'error', 'message': 'Eşleştirilecek kullanıcı yok'})

@app.route('/debug/clear_sessions', methods=['POST'])
def clear_sessions():
    global active_case_sessions, case_study_queue
    active_case_sessions.clear()
    case_study_queue.clear()
    return jsonify({'status': 'success', 'message': 'Tüm sessionlar temizlendi'})

@app.route('/case_study_room/leave_queue', methods=['POST'])
def leave_queue():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    interest = user.interest
    
    # Kullanıcıyı kuyruktan çıkar
    if interest in case_study_queue and username in case_study_queue[interest]:
        case_study_queue[interest].remove(username)
    
    # Kullanıcıyı aktif session'lardan çıkar
    for session_id, session_data in list(active_case_sessions.items()):
        if username in session_data['users']:
            session_data['users'].remove(username)
            # Eğer session'da başka kullanıcı kalmadıysa session'ı sil
            if not session_data['users']:
                del active_case_sessions[session_id]
    
    return jsonify({'message': 'Tüm session\'lardan çıkarıldınız.'})

@app.route('/debug/test_case_generation', methods=['POST'])
def test_case_generation():
    data = request.json
    interest = data.get('interest', 'Data Science')
    
    try:
        agent = CaseStudyAIAgent(interest)
        case = agent.generate_case()
        return jsonify({
            'status': 'success',
            'case': case,
            'message': 'Case generation başarılı'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Case generation hatası'
        })

@app.route('/debug/clear_user_sessions', methods=['POST'])
def clear_user_sessions():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    username = session['username']
    
    # Kullanıcıyı tüm kuyruklardan çıkar
    for interest in case_study_queue:
        if username in case_study_queue[interest]:
            case_study_queue[interest].remove(username)
    
    # Kullanıcıyı tüm session'lardan çıkar
    for session_id, session_data in list(active_case_sessions.items()):
        if username in session_data['users']:
            session_data['users'].remove(username)
            # Eğer session'da başka kullanıcı kalmadıysa session'ı sil
            if not session_data['users']:
                del active_case_sessions[session_id]
    
    return jsonify({'message': f'{username} kullanıcısının tüm session\'ları temizlendi.'})

if __name__ == '__main__':
    init_app()  # Database'i başlat ve session'ları yükle
    app.run(debug=True)
