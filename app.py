from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import json
import shutil
import tempfile
import PyPDF2
import pdfplumber
from datetime import datetime, timedelta
from agents.test_agent import TestAIAgent
from agents.interview_agent import InterviewAIAgent
from agents.case_study_agent import CaseStudyAIAgent
from agents.code_agent import CodeAIAgent
from agents.intelligent_job_agent import IntelligentJobAgent
from flask_sqlalchemy import SQLAlchemy
import threading
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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Upload klasörünü oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# İzin verilen dosya uzantıları
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

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
    cv_analysis = db.Column(db.Text, nullable=True)  # CV analiz sonucu

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Forum sistemi için yeni modeller
class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_username = db.Column(db.String(80), nullable=False)
    interest = db.Column(db.String(80), nullable=False)
    post_type = db.Column(db.String(20), default='discussion')  # discussion, question, resource, announcement
    tags = db.Column(db.Text, nullable=True)  # JSON string
    views = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_solved = db.Column(db.Boolean, default=False)  # Soru çözüldü mü?
    solved_by = db.Column(db.String(80), nullable=True)  # Kim çözdü?
    solved_at = db.Column(db.DateTime, nullable=True)
    bounty_points = db.Column(db.Integer, default=0)  # Ödül puanları
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    author_username = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('forum_comment.id'), nullable=True)  # Nested comments
    likes_count = db.Column(db.Integer, default=0)
    is_anonymous = db.Column(db.Boolean, default=False)
    is_solution = db.Column(db.Boolean, default=False)  # Bu yorum çözüm mü?
    is_accepted = db.Column(db.Boolean, default=False)  # Çözüm kabul edildi mi?
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ForumLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('forum_comment.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Yeni gelişmiş modeller
class ForumNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # like, comment, mention, solution_accepted
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('forum_comment.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_username = db.Column(db.String(80), nullable=False)
    reported_username = db.Column(db.String(80), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('forum_comment.id'), nullable=True)
    reason = db.Column(db.String(100), nullable=False)  # spam, inappropriate, duplicate, other
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved, dismissed
    moderator_username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)  # expert, helper, creator, moderator
    badge_name = db.Column(db.String(100), nullable=False)
    badge_description = db.Column(db.Text, nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class ForumTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # post_created, comment_added, post_liked, etc.
    points_earned = db.Column(db.Integer, default=0)
    related_post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('forum_comment.id'), nullable=True)
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

# Otomatik mülakat oturumları için database tablosu
class AutoInterviewSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    interest = db.Column(db.String(80), nullable=False)
    questions = db.Column(db.Text, nullable=True)  # JSON string - sorular listesi
    answers = db.Column(db.Text, nullable=True)  # JSON string - cevaplar listesi
    current_question_index = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    conversation_context = db.Column(db.Text, nullable=True)  # Mülakat bağlamı
    final_evaluation = db.Column(db.Text, nullable=True)  # Final değerlendirme

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """CV dosyasından metin çıkarır"""
    try:
        if file_path.lower().endswith('.pdf'):
            # PDF okuma
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    return "PDF okuma kütüphanesi bulunamadı"
        
        elif file_path.lower().endswith('.docx'):
            # DOCX okuma
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                return "DOCX okuma kütüphanesi bulunamadı"
        
        elif file_path.lower().endswith('.doc'):
            # DOC dosyaları için - basit metin döndür
            return "DOC dosyası algılandı - içerik okunamadı (DOCX formatını tercih edin)"
        
        else:
            return "Desteklenmeyen dosya formatı"
            
    except Exception as e:
        return f"Dosya okuma hatası: {str(e)}"

def get_file_mimetype(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return 'application/pdf'
    elif ext in ['doc', 'docx']:
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    return 'application/octet-stream'

# Uygulama context'i oluşturulduktan sonra test session'larını temizle
def init_app():
    with app.app_context():
        # Veritabanı tablolarını oluştur (eğer yoksa)
        try:
            db.create_all()
            print("✅ Veritabanı tabloları kontrol edildi ve oluşturuldu!")
        except Exception as e:
            print(f"❌ Veritabanı oluşturma hatası: {e}")
        
        # Eski test session'larını temizle
        expired_sessions = TestSession.query.filter_by(status='active').all()
        for test_session in expired_sessions:
            session_age = (datetime.utcnow() - test_session.start_time).total_seconds()
            if session_age > test_session.duration:
                test_session.status = 'expired'
        db.session.commit()
        print(f"🧹 {len([s for s in expired_sessions if s.status == 'expired'])} süresi dolmuş test session'ı temizlendi")

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
    
    
    # Kullanıcı login olduğunda eski session'larını temizle (artık sadece test session'ları)
    
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
    
    try:
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            # Kullanıcı bulunamadıysa session'ı temizle
            print(f"WARNING: User not found in database: {session['username']}")
            session.clear()
            return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
        
        # Test istatistikleri
        test_performances = TestPerformance.query.filter_by(username=user.username).all()
        total_tests = len(test_performances)
        avg_score = sum(p.success_rate for p in test_performances) / total_tests if total_tests > 0 else 0
        
        # Son 5 test performansı
        recent_tests = TestPerformance.query.filter_by(username=user.username)\
            .order_by(TestPerformance.created_at.desc()).limit(5).all()
        
        test_trend = []
        for test in recent_tests:
            test_trend.append({
                'date': test.created_at.strftime('%Y-%m-%d'),
                'score': test.success_rate,
                'interest': test.interest
            })
        
        # Forum aktiviteleri
        forum_posts = ForumPost.query.filter_by(author_username=user.username).count()
        forum_comments = ForumComment.query.filter_by(author_username=user.username).count()
        
        # Kodlama odası aktiviteleri
        code_activities = UserActivity.query.filter(
            UserActivity.username == user.username,
            UserActivity.activity_type.like('code%')
        ).all()
        
        total_code_sessions = len(code_activities)
        total_code_points = sum(activity.points_earned for activity in code_activities)
        
        # Son 5 kodlama aktivitesi
        recent_code_activities = UserActivity.query.filter(
            UserActivity.username == user.username,
            UserActivity.activity_type.like('code%')
        ).order_by(UserActivity.created_at.desc()).limit(5).all()
        
        code_trend = []
        for activity in recent_code_activities:
            code_trend.append({
                'date': activity.created_at.strftime('%Y-%m-%d'),
                'type': activity.activity_type,
                'points': activity.points_earned
            })
        
        # Forum puanları
        forum_activities = UserActivity.query.filter_by(username=user.username).all()
        total_forum_points = sum(activity.points_earned for activity in forum_activities)
        
        # Beceri seviyesi analizi
        skill_level = "Başlangıç"
        if avg_score >= 80:
            skill_level = "İleri"
        elif avg_score >= 60:
            skill_level = "Orta"
        elif avg_score >= 40:
            skill_level = "Gelişen"
        
        # CV analizi durumu
        has_cv = bool(user.cv_analysis)
        
        # Başarı rozetleri hesaplama
        achievements = []
        
        # Test rozetleri
        if total_tests >= 10:
            achievements.append({"name": "Test Uzmanı", "icon": "quiz", "description": "10+ test tamamladı"})
        if avg_score >= 90:
            achievements.append({"name": "Mükemmeliyetçi", "icon": "star", "description": "90%+ ortalama"})
        if total_tests >= 1:
            achievements.append({"name": "İlk Adım", "icon": "flag", "description": "İlk testi tamamladı"})
            
        # Kodlama odası rozetleri
        if total_code_sessions >= 10:
            achievements.append({"name": "Kod Savaşçısı", "icon": "code", "description": "10+ kodlama oturumu"})
        if total_code_points >= 200:
            achievements.append({"name": "Algoritma Ustası", "icon": "psychology", "description": "200+ kodlama puanı"})
        if total_code_sessions >= 1:
            achievements.append({"name": "İlk Kod", "icon": "code", "description": "İlk kodlama oturumu"})
            
        # Forum rozetleri
        if forum_posts >= 5:
            achievements.append({"name": "Aktif Üye", "icon": "forum", "description": "5+ forum gönderisi"})
        if total_forum_points >= 100:
            achievements.append({"name": "Forum Kahramanı", "icon": "trophy", "description": "100+ forum puanı"})
            
        # CV rozeti
        if has_cv:
            achievements.append({"name": "Hazırlıklı", "icon": "work", "description": "CV analizi tamamlandı"})
        
        # Günlük aktivite (son 7 gün)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        daily_activity = []
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # O günkü test sayısı
            daily_tests = TestPerformance.query.filter(
                TestPerformance.username == user.username,
                TestPerformance.created_at >= date.replace(hour=0, minute=0, second=0),
                TestPerformance.created_at < date.replace(hour=23, minute=59, second=59)
            ).count()
            
            # O günkü forum aktivitesi
            daily_forum = UserActivity.query.filter(
                UserActivity.username == user.username,
                UserActivity.activity_type.in_(['forum_post', 'forum_comment']),
                UserActivity.created_at >= date.replace(hour=0, minute=0, second=0),
                UserActivity.created_at < date.replace(hour=23, minute=59, second=59)
            ).count()
            
            # O günkü kodlama aktivitesi
            daily_code = UserActivity.query.filter(
                UserActivity.username == user.username,
                UserActivity.activity_type == 'code_session',
                UserActivity.created_at >= date.replace(hour=0, minute=0, second=0),
                UserActivity.created_at < date.replace(hour=23, minute=59, second=59)
            ).count()
            
            daily_activity.append({
                'date': date_str,
                'day_name': date.strftime('%A')[:3],
                'tests': daily_tests,
                'forum_activity': daily_forum,
                'code_activity': daily_code,
                'total_activity': daily_tests + daily_forum + daily_code
            })
        
        return jsonify({
            'username': user.username,
            'interest': user.interest,
            'stats': {
                'total_tests': total_tests,
                'average_score': round(avg_score, 1),
                'skill_level': skill_level,
                'forum_posts': forum_posts,
                'forum_comments': forum_comments,
                'forum_points': total_forum_points,
                'has_cv': has_cv,
                'test_trend': test_trend,
                'achievements': achievements,
                'daily_activity': daily_activity
            }
        })
    except Exception as e:
        print(f"ERROR in profile endpoint: {str(e)}")
        # Veritabanı hatası durumunda session'ı temizleme, sadece hata döndür
        return jsonify({'error': 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.'}), 500

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

@app.route('/upload_cv', methods=['POST'])
def upload_cv():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    if 'cv_file' not in request.files:
        return jsonify({'error': 'CV dosyası seçilmemiş.'}), 400
    
    file = request.files['cv_file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmemiş.'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Dosyayı bellekte oku
            cv_data = file.read()
            mime_type = get_file_mimetype(file.filename)
            
            # CV'yi analiz et
            user = User.query.filter_by(username=session['username']).first()
            agent = InterviewAIAgent(user.interest)
            cv_analysis = agent.analyze_cv(cv_data, mime_type)
            
            # Analizi veritabanına kaydet
            user.cv_analysis = cv_analysis
            db.session.commit()
            
            return jsonify({
                'message': 'CV başarıyla yüklendi ve analiz edildi.',
                'analysis': cv_analysis
            })
            
        except Exception as e:
            return jsonify({'error': f'CV analizi sırasında hata: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Geçersiz dosya formatı. PDF, DOC veya DOCX dosyası yükleyiniz.'}), 400

@app.route('/interview_cv_based_question', methods=['POST'])
def interview_cv_based_question():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.cv_analysis:
        return jsonify({'error': 'Önce CV yüklemelisiniz.'}), 400
    
    try:
        agent = InterviewAIAgent(user.interest)
        question = agent.generate_cv_based_question(user.cv_analysis)
        
        return jsonify({
            'message': 'CV\'nize özel mülakat sorusu hazırlandı.',
            'question': question,
            'cv_analysis': user.cv_analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Soru oluşturma hatası: {str(e)}'}), 500

@app.route('/interview_personalized_questions', methods=['POST'])
def interview_personalized_questions():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.cv_analysis:
        return jsonify({'error': 'Önce CV yüklemelisiniz.'}), 400
    
    data = request.get_json()
    difficulty = data.get('difficulty', 'orta')
    
    try:
        agent = InterviewAIAgent(user.interest)
        questions = agent.generate_personalized_questions(user.cv_analysis, difficulty)
        
        return jsonify({
            'message': f'{difficulty} seviyede kişiselleştirilmiş sorular hazırlandı.',
            'questions': questions,
            'difficulty': difficulty
        })
        
    except Exception as e:
        return jsonify({'error': f'Sorular oluşturma hatası: {str(e)}'}), 500

@app.route('/interview_speech_question', methods=['POST'])
def interview_speech_question():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.get_json() or {}
    voice_name = data.get('voice_name', 'Kore')
    
    try:
        agent = InterviewAIAgent(user.interest)
        result = agent.generate_dynamic_speech_question(voice_name=voice_name)
        
        if result.get('audio_file'):
            # Ses dosyasını static klasörüne taşı
            audio_filename = f"interview_question_{session['username']}_{int(time.time())}.wav"
            audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # Dosyayı kopyala
            import shutil
            shutil.move(result['audio_file'], audio_path)
            
            return jsonify({
                'question': result['question_text'],
                'audio_url': f'/static/audio/{audio_filename}',
                'has_audio': True
            })
        else:
            return jsonify({
                'question': result['question_text'],
                'audio_url': None,
                'has_audio': False,
                'error': result.get('error')
            })
            
    except Exception as e:
        return jsonify({'error': f'Sesli soru oluşturma hatası: {str(e)}'}), 500

@app.route('/interview_cv_speech_question', methods=['POST'])
def interview_cv_speech_question():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.cv_analysis:
        return jsonify({'error': 'Önce CV yüklemelisiniz.'}), 400
    
    data = request.get_json() or {}
    voice_name = data.get('voice_name', 'Kore')
    
    try:
        agent = InterviewAIAgent(user.interest)
        result = agent.generate_cv_based_speech_question(user.cv_analysis, voice_name)
        
        if result.get('audio_file'):
            audio_filename = f"cv_question_{session['username']}_{int(time.time())}.wav"
            audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            import shutil
            shutil.move(result['audio_file'], audio_path)
            
            return jsonify({
                'question': result['question_text'],
                'audio_url': f'/static/audio/{audio_filename}',
                'has_audio': True
            })
        else:
            return jsonify({
                'question': result['question_text'],
                'audio_url': None,
                'has_audio': False,
                'error': result.get('error')
            })
            
    except Exception as e:
        return jsonify({'error': f'CV tabanlı sesli soru hatası: {str(e)}'}), 500

@app.route('/interview_speech_evaluation', methods=['POST'])
def interview_speech_evaluation():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    # Ses dosyası yükleme desteği
    if 'audio' in request.files:
        # FormData ile ses dosyası geldi
        audio_file = request.files['audio']
        question = request.form.get('question')
        voice_name = request.form.get('voice_name', 'Enceladus')
        additional_text = request.form.get('additional_text', '')
        
        if not question:
            return jsonify({'error': 'Soru gerekli.'}), 400
        
        # Ses dosyasını geçici olarak kaydet
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio_path = temp_audio.name
        
        try:
            agent = InterviewAIAgent(user.interest)
            cv_context = user.cv_analysis if user.cv_analysis else None
            
            # Ses dosyasını transcript et ve değerlendir
            result = agent.evaluate_speech_answer(question, temp_audio_path, additional_text, cv_context, voice_name)
            
            # Geçici dosyayı sil
            os.unlink(temp_audio_path)
            
            if result.get('audio_file'):
                audio_filename = f"feedback_{session['username']}_{int(time.time())}.wav"
                audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                import shutil
                shutil.move(result['audio_file'], audio_path)
                
                return jsonify({
                    'evaluation': result['feedback_text'],
                    'audio_url': f'/static/audio/{audio_filename}',
                    'has_audio': True,
                    'has_cv_context': bool(user.cv_analysis),
                    'transcribed_text': result.get('transcribed_text', '')
                })
            else:
                return jsonify({
                    'evaluation': result['feedback_text'],
                    'audio_url': None,
                    'has_audio': False,
                    'has_cv_context': bool(user.cv_analysis),
                    'transcribed_text': result.get('transcribed_text', ''),
                    'error': result.get('error')
                })
                
        except Exception as e:
            print(f"Speech evaluation error: {e}")
            # Geçici dosyayı sil
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            return jsonify({'error': f'Ses değerlendirme hatası: {str(e)}'}), 500
    
    else:
        # JSON formatında metin cevap
        data = request.json
        question = data.get('question')
        user_answer = data.get('user_answer')
        voice_name = data.get('voice_name', 'Enceladus')
        
        if not question or not user_answer:
            return jsonify({'error': 'Soru ve cevap gerekli.'}), 400
        
        try:
            agent = InterviewAIAgent(user.interest)
            cv_context = user.cv_analysis if user.cv_analysis else None
            
            result = agent.generate_speech_feedback(question, user_answer, cv_context, voice_name)
            
            if result.get('audio_file'):
                audio_filename = f"feedback_{session['username']}_{int(time.time())}.wav"
                audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
                os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                
                import shutil
                shutil.move(result['audio_file'], audio_path)
                
                return jsonify({
                    'evaluation': result['feedback_text'],
                    'audio_url': f'/static/audio/{audio_filename}',
                    'has_audio': True,
                    'has_cv_context': bool(user.cv_analysis)
                })
            else:
                return jsonify({
                    'evaluation': result['feedback_text'],
                    'audio_url': None,
                    'has_audio': False,
                    'has_cv_context': bool(user.cv_analysis),
                    'error': result.get('error')
                })
                
        except Exception as e:
            print(f"Text evaluation error: {e}")
            return jsonify({'error': f'Sesli değerlendirme hatası: {str(e)}'}), 500

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

@app.route('/code_room/generate_solution', methods=['POST'])
def code_room_generate_solution():
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Soru gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest)
        solution = agent.generate_solution(question)
        return jsonify({
            'success': True,
            'solution': solution
        })
    except Exception as e:
        return jsonify({'error': f'Çözüm oluşturma hatası: {str(e)}'}), 500

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
    return jsonify({'evaluation': evaluation})

@app.route('/code_room/run', methods=['POST'])
def code_room_run():
    """Sadece kodu çalıştırır, değerlendirmez"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    user_code = data.get('user_code')
    language = data.get('language', 'python')
    
    if not user_code:
        return jsonify({'error': 'Kod gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        result = agent.run_code(user_code)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': f'Kod çalıştırma hatası: {str(e)}'}), 500

@app.route('/code_room/debug', methods=['POST'])
def code_room_debug():
    """Hatalı kodu debug eder"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    code_with_error = data.get('code')
    language = data.get('language', 'python')
    
    if not code_with_error:
        return jsonify({'error': 'Hatalı kod gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        debug_result = agent.debug_code(code_with_error)
        return jsonify({
            'success': True,
            'debug_result': debug_result
        })
    except Exception as e:
        return jsonify({'error': f'Debug hatası: {str(e)}'}), 500

@app.route('/code_room/analyze_complexity', methods=['POST'])
def code_room_analyze_complexity():
    """Kod karmaşıklığını analiz eder"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    code = data.get('code')
    language = data.get('language', 'python')
    
    if not code:
        return jsonify({'error': 'Analiz edilecek kod gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        analysis = agent.analyze_algorithm_complexity(code)
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': f'Karmaşıklık analizi hatası: {str(e)}'}), 500

@app.route('/code_room/suggest_resources', methods=['POST'])
def code_room_suggest_resources():
    """Konuya göre kaynak önerileri"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    topic = data.get('topic')
    language = data.get('language', 'python')
    num_resources = data.get('num_resources', 3)
    
    if not topic:
        return jsonify({'error': 'Konu gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        resources = agent.suggest_resources(topic, num_resources)
        return jsonify({
            'success': True,
            'resources': resources
        })
    except Exception as e:
        return jsonify({'error': f'Kaynak önerisi hatası: {str(e)}'}), 500

@app.route('/code_room/evaluate_with_execution', methods=['POST'])
def code_room_evaluate_with_execution():
    """Kodu çalıştırarak değerlendirir ve puan verir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    user_code = data.get('user_code')
    question = data.get('question')
    language = data.get('language', 'python')
    
    if not user_code or not question:
        return jsonify({'error': 'Kod ve soru gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        result = agent.evaluate_code_with_execution(user_code, question)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': f'Değerlendirme hatası: {str(e)}'}), 500

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
        # CV analizi varsa, CV bağlamında değerlendirme yap
        if user.cv_analysis:
            evaluation = agent.evaluate_cv_answer(question, user_answer, user.cv_analysis)
        else:
            # CV yoksa normal değerlendirme
            evaluation = agent.evaluate_answer(question, user_answer)
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    
    # Geçmişe kaydet
    
    return jsonify({
        'evaluation': evaluation,
        'has_cv_context': bool(user.cv_analysis)
    })

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

@app.route('/')
def home():
    return jsonify({'message': 'BTK Project API is running!'})

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

@app.route('/debug/clear_auto_interview_sessions', methods=['POST'])
def clear_auto_interview_sessions():
    """Kullanıcının otomatik mülakat oturumlarını temizler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    username = session['username']
    
    try:
        # Kullanıcının tüm aktif otomatik mülakat oturumlarını bul ve sil
        active_sessions = AutoInterviewSession.query.filter_by(
            username=username,
            status='active'
        ).all()
        
        for interview_session in active_sessions:
            interview_session.status = 'cancelled'
            interview_session.end_time = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'{username} kullanıcısının {len(active_sessions)} aktif otomatik mülakat oturumu temizlendi.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Oturum temizleme hatası: {str(e)}'}), 500

# ==================== OTOMATİK MÜLAKAT SİSTEMİ ====================

@app.route('/auto_interview/start', methods=['POST'])
def start_auto_interview():
    """Otomatik mülakat başlatır"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    try:
        # Request data'sını al
        data = request.get_json() or {}
        
        # Kullanıcının aktif mülakat oturumu var mı kontrol et
        existing_session = AutoInterviewSession.query.filter_by(
            username=user.username,
            status='active'
        ).first()
        
        if existing_session:
            return jsonify({'error': 'Aktif bir mülakat oturumunuz zaten var.'}), 400
        
        # Yeni mülakat oturumu oluştur
        session_id = f"auto_interview_{int(time.time())}_{user.username}"
        agent = InterviewAIAgent(user.interest)
        
        # Conversation context'i kullanıcının nickname'i ile oluştur
        conversation_context = f"Kullanıcının nickname: {user.username}"
        
        # İlk sesli soruyu üret
        voice_name = data.get('voice_name', 'Kore')
        result = agent.generate_dynamic_speech_question(
            previous_questions=None, 
            user_answers=None, 
            conversation_context=conversation_context, 
            voice_name=voice_name
        )
        
        first_question = result['question_text']
        audio_url = None
        
        if result.get('audio_file'):
            # Ses dosyasını static klasörüne taşı
            audio_filename = f"auto_interview_{session['username']}_{int(time.time())}.wav"
            audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # Dosyayı kopyala
            import shutil
            shutil.move(result['audio_file'], audio_path)
            audio_url = f'/static/audio/{audio_filename}'
        
        auto_session = AutoInterviewSession(
            session_id=session_id,
            username=user.username,
            interest=user.interest,
            questions=json.dumps([first_question]),
            answers=json.dumps([]),
            current_question_index=0,
            conversation_context=conversation_context
        )
        db.session.add(auto_session)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'question': first_question,
            'question_index': 0,
            'total_questions': 5,  # Toplam soru sayısı
            'audio_url': audio_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Mülakat başlatma hatası: {str(e)}'}), 500

@app.route('/auto_interview/submit_answer', methods=['POST'])
def submit_auto_interview_answer():
    """Otomatik mülakat cevabını gönder ve sonraki soruyu al"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    # Hem JSON hem de form data formatını destekle
    if request.is_json:
        data = request.json
        session_id = data.get('session_id')
        answer = data.get('answer')
        voice_name = data.get('voice_name', 'Kore')
        audio_file = None
    else:
        data = request.form.to_dict()
        # Form data'dan değerleri al
        session_id = data.get('session_id')
        answer = data.get('answer')
        voice_name = data.get('voice_name', 'Kore')
        audio_file = request.files.get('audio')
    
    if not session_id:
        return jsonify({'error': 'Session ID gerekli.'}), 400
    
    # Ses dosyası varsa transcript et, yoksa metin cevabı kullan
    if audio_file:
        try:
            # Önce session'ı bul
            auto_session = AutoInterviewSession.query.filter_by(
                session_id=session_id,
                username=session['username'],
                status='active'
            ).first()
            
            if not auto_session:
                return jsonify({'error': 'Geçersiz mülakat oturumu.'}), 400
            
            # Ses dosyasını geçici olarak kaydet
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
                audio_file.save(temp_audio.name)
                temp_audio_path = temp_audio.name
            
            # Ses dosyasını transcript et
            agent = InterviewAIAgent(auto_session.interest)
            transcribed_text = agent._transcribe_audio(temp_audio_path)
            
            # Geçici dosyayı sil
            os.unlink(temp_audio_path)
            
            # Transcript edilen metni cevap olarak kullan
            answer = transcribed_text
        except Exception as e:
            print(f"Audio transcription error: {e}")
            return jsonify({'error': f'Ses dosyası işlenemedi: {str(e)}'}), 500
    
    if not answer:
        return jsonify({'error': 'Cevap gerekli.'}), 400
    
    try:
        # Mülakat oturumunu bul (eğer henüz bulunmadıysa)
        if 'auto_session' not in locals():
            auto_session = AutoInterviewSession.query.filter_by(
                session_id=session_id,
                username=session['username'],
                status='active'
            ).first()
            
            if not auto_session:
                return jsonify({'error': 'Geçersiz mülakat oturumu.'}), 400
        
        # Cevabı kaydet
        questions = json.loads(auto_session.questions) if auto_session.questions else []
        answers = json.loads(auto_session.answers) if auto_session.answers else []
        answers.append(answer)
        
        auto_session.answers = json.dumps(answers)
        auto_session.current_question_index += 1
        
        # 5 soru tamamlandı mı kontrol et
        if auto_session.current_question_index >= 5:
            auto_session.status = 'completed'
            auto_session.end_time = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'message': 'Mülakat tamamlandı!'
            })
        
        # Sonraki sesli soruyu üret
        agent = InterviewAIAgent(auto_session.interest)
        
        # Dinamik sesli soru üret ve ses dosyası oluştur
        result = agent.generate_dynamic_speech_question(questions, answers, auto_session.conversation_context, voice_name)
        next_question = result['question_text']
        audio_url = None
        
        if result.get('audio_file'):
            # Ses dosyasını static klasörüne taşı
            audio_filename = f"auto_interview_{session['username']}_{int(time.time())}.wav"
            audio_path = os.path.join(app.static_folder, 'audio', audio_filename)
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            # Dosyayı kopyala
            import shutil
            shutil.move(result['audio_file'], audio_path)
            audio_url = f'/static/audio/{audio_filename}'
        
        questions.append(next_question)
        auto_session.questions = json.dumps(questions)
        db.session.commit()
        
        return jsonify({
            'status': 'continue',
            'question': next_question,
            'question_index': auto_session.current_question_index,
            'total_questions': 5,
            'audio_url': audio_url
        })
        
    except Exception as e:
        print(f"Auto interview submit answer error: {e}")
        return jsonify({'error': f'Cevap gönderme hatası: {str(e)}'}), 500

@app.route('/auto_interview/complete', methods=['POST'])
def complete_auto_interview():
    """Mülakatı tamamlar ve final değerlendirme üretir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'Session ID gerekli.'}), 400
    
    try:
        # Session'ı bul
        interview_session = AutoInterviewSession.query.filter_by(
            session_id=session_id,
            username=session['username'],
            status='active'
        ).first()
        
        if not interview_session:
            return jsonify({'error': 'Aktif mülakat oturumu bulunamadı.'}), 404
        
        # Final değerlendirme üret
        questions = json.loads(interview_session.questions or '[]')
        answers = json.loads(interview_session.answers or '[]')
        
        agent = InterviewAIAgent(interview_session.interest)
        final_evaluation = agent.generate_final_evaluation(
            questions, 
            answers, 
            interview_session.conversation_context
        )
        
        # Session'ı tamamla
        interview_session.status = 'completed'
        interview_session.end_time = datetime.now()
        interview_session.final_evaluation = final_evaluation
        
        # Geçmişe kaydet
        detail = f"Otomatik mülakat tamamlandı - {len(questions)} soru"
        
        return jsonify({
            'final_evaluation': final_evaluation,
            'total_questions': len(questions),
            'total_answers': len(answers),
            'session_duration': (interview_session.end_time - interview_session.start_time).total_seconds()
        })
        
    except Exception as e:
        return jsonify({'error': f'Mülakat tamamlama hatası: {str(e)}'}), 500

@app.route('/auto_interview/status', methods=['GET'])
def get_auto_interview_status():
    """Aktif mülakat oturumunun durumunu döndürür"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    try:
        interview_session = AutoInterviewSession.query.filter_by(
            username=session['username'],
            status='active'
        ).first()
        
        if not interview_session:
            return jsonify({'has_active_session': False})
        
        questions = json.loads(interview_session.questions or '[]')
        answers = json.loads(interview_session.answers or '[]')
        
        return jsonify({
            'has_active_session': True,
            'session_id': interview_session.session_id,
            'interest': interview_session.interest,
            'current_question_index': interview_session.current_question_index,
            'total_questions': len(questions),
            'total_answers': len(answers),
            'start_time': interview_session.start_time.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Durum kontrolü hatası: {str(e)}'}), 500

# ==================== FORUM SİSTEMİ ====================

@app.route('/forum/posts', methods=['GET'])
def get_forum_posts():
    """İlgi alanına göre forum gönderilerini getirir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    try:
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            print(f"WARNING: User not found in forum posts: {session['username']}")
            return jsonify({'error': 'Kullanıcı bulunamadı.'}), 404
        
        if not user.interest:
            return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    except Exception as e:
        print(f"ERROR in forum posts endpoint: {str(e)}")
        return jsonify({'error': 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.'}), 500
    
    # Query parametreleri
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    post_type = request.args.get('type', 'all')
    sort_by = request.args.get('sort', 'latest')  # latest, popular, most_commented
    search = request.args.get('search', '')
    
    # Base query - kullanıcının ilgi alanına göre
    query = ForumPost.query.filter_by(interest=user.interest)
    
    # Post type filtresi
    if post_type != 'all':
        query = query.filter_by(post_type=post_type)
    
    # Arama filtresi
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                ForumPost.title.ilike(search_term),
                ForumPost.content.ilike(search_term)
            )
        )
    
    # Sıralama
    if sort_by == 'popular':
        query = query.order_by(ForumPost.likes_count.desc(), ForumPost.views.desc())
    elif sort_by == 'most_commented':
        query = query.order_by(ForumPost.comments_count.desc())
    else:  # latest
        query = query.order_by(ForumPost.created_at.desc())
    
    # Sayfalama
    posts = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Sonuçları formatla
    posts_data = []
    for post in posts.items:
        # Kullanıcının bu postu beğenip beğenmediğini kontrol et
        user_liked = ForumLike.query.filter_by(
            username=session['username'],
            post_id=post.id
        ).first() is not None
        
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
            'author': 'Anonim' if post.is_anonymous else post.author_username,
            'post_type': post.post_type,
            'tags': json.loads(post.tags) if post.tags else [],
            'views': post.views,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'is_pinned': post.is_pinned,
            'is_solved': post.is_solved,
            'solved_by': post.solved_by,
            'solved_at': post.solved_at.strftime('%Y-%m-%d %H:%M') if post.solved_at else None,
            'user_liked': user_liked,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({
        'posts': posts_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': posts.total,
            'pages': posts.pages,
            'has_next': posts.has_next,
            'has_prev': posts.has_prev
        }
    })

@app.route('/forum/posts', methods=['POST'])
def create_forum_post():
    """Yeni forum gönderisi oluşturur"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı.'}), 404
    
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    post_type = data.get('post_type', 'discussion')
    tags = data.get('tags', [])
    is_anonymous = data.get('is_anonymous', False)
    
    if not title or not content:
        return jsonify({'error': 'Başlık ve içerik gerekli.'}), 400
    
    # İçerik uzunluğu kontrolü
    if len(title) > 200:
        return jsonify({'error': 'Başlık 200 karakterden uzun olamaz.'}), 400
    
    if len(content) > 10000:
        return jsonify({'error': 'İçerik 10000 karakterden uzun olamaz.'}), 400
    
    try:
        new_post = ForumPost(
            title=title,
            content=content,
            author_username=session['username'],
            interest=user.interest,
            post_type=post_type,
            tags=json.dumps(tags),
            is_anonymous=is_anonymous
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            'message': 'Gönderi başarıyla oluşturuldu.',
            'post_id': new_post.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Gönderi oluşturma hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>', methods=['GET'])
def get_forum_post(post_id):
    """Tekil forum gönderisini getirir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    post = ForumPost.query.get_or_404(post_id)
    
    # Görüntüleme sayısını artır
    post.views += 1
    db.session.commit()
    
    # Kullanıcının bu postu beğenip beğenmediğini kontrol et
    user_liked = ForumLike.query.filter_by(
        username=session['username'],
        post_id=post.id
    ).first() is not None
    
    # Yorumları getir
    comments = ForumComment.query.filter_by(
        post_id=post.id,
        parent_comment_id=None  # Sadece ana yorumlar
    ).order_by(ForumComment.created_at.asc()).all()
    
    comments_data = []
    for comment in comments:
        # Alt yorumları getir
        replies = ForumComment.query.filter_by(
            parent_comment_id=comment.id
        ).order_by(ForumComment.created_at.asc()).all()
        
        # Kullanıcının bu yorumu beğenip beğenmediğini kontrol et
        user_liked_comment = ForumLike.query.filter_by(
            username=session['username'],
            comment_id=comment.id
        ).first() is not None
        
        replies_data = []
        for reply in replies:
            user_liked_reply = ForumLike.query.filter_by(
                username=session['username'],
                comment_id=reply.id
            ).first() is not None
            
            replies_data.append({
                'id': reply.id,
                'content': reply.content,
                'author': 'Anonim' if reply.is_anonymous else reply.author_username,
                'likes_count': reply.likes_count,
                'user_liked': user_liked_reply,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'author': 'Anonim' if comment.is_anonymous else comment.author_username,
            'likes_count': comment.likes_count,
            'user_liked': user_liked_comment,
            'is_solution': comment.is_solution,
            'is_accepted': comment.is_accepted,
            'replies': replies_data,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({
        'post': {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': 'Anonim' if post.is_anonymous else post.author_username,
            'author_username': post.author_username,
            'interest': post.interest,
            'post_type': post.post_type,
            'tags': json.loads(post.tags) if post.tags else [],
            'views': post.views,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'is_pinned': post.is_pinned,
            'is_solved': post.is_solved,
            'solved_by': post.solved_by,
            'solved_at': post.solved_at.strftime('%Y-%m-%d %H:%M') if post.solved_at else None,
            'user_liked': user_liked,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M')
        },
        'comments': comments_data
    })

@app.route('/forum/posts/<int:post_id>', methods=['PUT'])
def update_forum_post(post_id):
    """Forum gönderisini günceller"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    post = ForumPost.query.get_or_404(post_id)
    
    # Sadece yazar düzenleyebilir
    if post.author_username != session['username']:
        return jsonify({'error': 'Bu gönderiyi düzenleme yetkiniz yok.'}), 403
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags', [])
    
    if not title or not content:
        return jsonify({'error': 'Başlık ve içerik gerekli.'}), 400
    
    try:
        post.title = title
        post.content = content
        post.tags = json.dumps(tags)
        post.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Gönderi başarıyla güncellendi.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Güncelleme hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>', methods=['DELETE'])
def delete_forum_post(post_id):
    """Forum gönderisini siler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    post = ForumPost.query.get_or_404(post_id)
    
    # Sadece yazar silebilir
    if post.author_username != session['username']:
        return jsonify({'error': 'Bu gönderiyi silme yetkiniz yok.'}), 403
    
    try:
        # İlişkili yorumları ve beğenileri sil
        ForumComment.query.filter_by(post_id=post_id).delete()
        ForumLike.query.filter_by(post_id=post_id).delete()
        
        # Postu sil
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({'message': 'Gönderi başarıyla silindi.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Silme hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/comments', methods=['POST'])
def create_forum_comment(post_id):
    """Forum gönderisine yorum ekler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    post = ForumPost.query.get_or_404(post_id)
    
    data = request.json
    content = data.get('content')
    parent_comment_id = data.get('parent_comment_id')
    is_anonymous = data.get('is_anonymous', False)
    
    if not content:
        return jsonify({'error': 'Yorum içeriği gerekli.'}), 400
    
    if len(content) > 2000:
        return jsonify({'error': 'Yorum 2000 karakterden uzun olamaz.'}), 400
    
    # Parent comment kontrolü
    if parent_comment_id:
        parent_comment = ForumComment.query.get(parent_comment_id)
        if not parent_comment or parent_comment.post_id != post_id:
            return jsonify({'error': 'Geçersiz parent yorum.'}), 400
    
    try:
        new_comment = ForumComment(
            post_id=post_id,
            author_username=session['username'],
            content=content,
            parent_comment_id=parent_comment_id,
            is_anonymous=is_anonymous
        )
        
        db.session.add(new_comment)
        
        # Post'un yorum sayısını artır
        post.comments_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Yorum başarıyla eklendi.',
            'comment_id': new_comment.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Yorum ekleme hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/like', methods=['POST'])
def like_forum_post(post_id):
    """Forum gönderisini beğenir/beğenmekten vazgeçer"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    post = ForumPost.query.get_or_404(post_id)
    
    existing_like = ForumLike.query.filter_by(
        username=session['username'],
        post_id=post_id
    ).first()
    
    try:
        if existing_like:
            # Beğeniyi kaldır
            db.session.delete(existing_like)
            post.likes_count -= 1
            action = 'unliked'
        else:
            # Beğeni ekle
            new_like = ForumLike(
                username=session['username'],
                post_id=post_id
            )
            db.session.add(new_like)
            post.likes_count += 1
            action = 'liked'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Gönderi {action}.',
            'likes_count': post.likes_count,
            'user_liked': action == 'liked'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Beğeni işlemi hatası: {str(e)}'}), 500

@app.route('/forum/comments/<int:comment_id>/like', methods=['POST'])
def like_forum_comment(comment_id):
    """Forum yorumunu beğenir/beğenmekten vazgeçer"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    comment = ForumComment.query.get_or_404(comment_id)
    
    existing_like = ForumLike.query.filter_by(
        username=session['username'],
        comment_id=comment_id
    ).first()
    
    try:
        if existing_like:
            # Beğeniyi kaldır
            db.session.delete(existing_like)
            comment.likes_count -= 1
            action = 'unliked'
        else:
            # Beğeni ekle
            new_like = ForumLike(
                username=session['username'],
                comment_id=comment_id
            )
            db.session.add(new_like)
            comment.likes_count += 1
            action = 'liked'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Yorum {action}.',
            'likes_count': comment.likes_count,
            'user_liked': action == 'liked'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Beğeni işlemi hatası: {str(e)}'}), 500

@app.route('/forum/stats', methods=['GET'])
def get_forum_stats():
    """Forum istatistiklerini getirir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı.'}), 404
    
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    try:
        # Kullanıcının ilgi alanındaki istatistikler
        total_posts = ForumPost.query.filter_by(interest=user.interest).count()
        total_comments = ForumComment.query.join(ForumPost).filter(
            ForumPost.interest == user.interest
        ).count()
        
        # Kullanıcının kendi istatistikleri
        user_posts = ForumPost.query.filter_by(
            author_username=session['username'],
            interest=user.interest
        ).count()
        
        user_comments = ForumComment.query.join(ForumPost).filter(
            ForumComment.author_username == session['username'],
            ForumPost.interest == user.interest
        ).count()
        
        # En popüler gönderiler
        popular_posts = ForumPost.query.filter_by(interest=user.interest)\
            .order_by(ForumPost.likes_count.desc(), ForumPost.views.desc())\
            .limit(5).all()
        
        popular_posts_data = []
        for post in popular_posts:
            popular_posts_data.append({
                'id': post.id,
                'title': post.title,
                'likes_count': post.likes_count,
                'views': post.views,
                'comments_count': post.comments_count
            })
        
        return jsonify({
            'interest': user.interest,
            'total_posts': total_posts,
            'total_comments': total_comments,
            'user_posts': user_posts,
            'user_comments': user_comments,
            'popular_posts': popular_posts_data
        })
        
    except Exception as e:
        return jsonify({'error': f'İstatistik hatası: {str(e)}'}), 500

# ==================== GELİŞMİŞ FORUM ÖZELLİKLERİ ====================

@app.route('/forum/notifications', methods=['GET'])
def get_notifications():
    """Kullanıcının bildirimlerini getirir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    try:
        notifications = ForumNotification.query.filter_by(
            username=session['username']
        ).order_by(ForumNotification.created_at.desc()).limit(20).all()
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'type': notif.notification_type,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'related_post_id': notif.related_post_id,
                'related_comment_id': notif.related_comment_id,
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({'notifications': notifications_data})
        
    except Exception as e:
        return jsonify({'error': f'Bildirim hatası: {str(e)}'}), 500

@app.route('/forum/notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    """Bildirimleri okundu olarak işaretler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    try:
        ForumNotification.query.filter_by(
            username=session['username'],
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        return jsonify({'message': 'Bildirimler okundu olarak işaretlendi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/report', methods=['POST'])
def report_content():
    """İçerik raporlar"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    reported_username = data.get('reported_username')
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    reason = data.get('reason')
    description = data.get('description')
    
    if not reported_username or not reason:
        return jsonify({'error': 'Gerekli alanlar eksik.'}), 400
    
    try:
        new_report = ForumReport(
            reporter_username=session['username'],
            reported_username=reported_username,
            post_id=post_id,
            comment_id=comment_id,
            reason=reason,
            description=description
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        return jsonify({'message': 'Rapor başarıyla gönderildi.'})
        
    except Exception as e:
        return jsonify({'error': f'Rapor hatası: {str(e)}'}), 500

@app.route('/forum/badges/<username>', methods=['GET'])
def get_user_badges(username):
    """Kullanıcının rozetlerini getirir"""
    try:
        badges = UserBadge.query.filter_by(username=username).all()
        
        badges_data = []
        for badge in badges:
            badges_data.append({
                'id': badge.id,
                'type': badge.badge_type,
                'name': badge.badge_name,
                'description': badge.badge_description,
                'earned_at': badge.earned_at.strftime('%Y-%m-%d')
            })
        
        return jsonify({'badges': badges_data})
        
    except Exception as e:
        return jsonify({'error': f'Rozet hatası: {str(e)}'}), 500

@app.route('/forum/tags', methods=['GET'])
def get_popular_tags():
    """Popüler etiketleri getirir"""
    try:
        tags = ForumTag.query.order_by(ForumTag.usage_count.desc()).limit(20).all()
        
        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'description': tag.description,
                'usage_count': tag.usage_count
            })
        
        return jsonify({'tags': tags_data})
        
    except Exception as e:
        return jsonify({'error': f'Etiket hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/solve', methods=['POST'])
def mark_post_solved(post_id):
    """Gönderiyi çözüldü olarak işaretler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    solved_by = data.get('solved_by')
    comment_id = data.get('comment_id')
    
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        # Sadece gönderi sahibi çözüldü olarak işaretleyebilir
        if post.author_username != session['username']:
            return jsonify({'error': 'Bu işlemi yapma yetkiniz yok.'}), 403
        
        post.is_solved = True
        post.solved_by = solved_by
        post.solved_at = datetime.utcnow()
        
        # Çözüm yorumunu kabul et
        if comment_id:
            comment = ForumComment.query.get(comment_id)
            if comment:
                comment.is_solution = True
                comment.is_accepted = True
        
        db.session.commit()
        
        # Bildirim gönder
        if solved_by:
            notification = ForumNotification(
                username=solved_by,
                notification_type='solution_accepted',
                title='Çözümünüz kabul edildi!',
                message=f'"{post.title}" gönderisindeki çözümünüz kabul edildi.',
                related_post_id=post_id,
                related_comment_id=comment_id
            )
            db.session.add(notification)
            db.session.commit()
        
        return jsonify({'message': 'Gönderi çözüldü olarak işaretlendi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/bounty', methods=['POST'])
def add_bounty(post_id):
    """Gönderiye ödül puanı ekler"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    points = data.get('points', 0)
    
    if points <= 0:
        return jsonify({'error': 'Geçersiz puan miktarı.'}), 400
    
    try:
        post = ForumPost.query.get_or_404(post_id)
        
        # Sadece gönderi sahibi ödül ekleyebilir
        if post.author_username != session['username']:
            return jsonify({'error': 'Bu işlemi yapma yetkiniz yok.'}), 403
        
        post.bounty_points += points
        db.session.commit()
        
        return jsonify({'message': f'{points} puan ödül eklendi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/activity/<username>', methods=['GET'])
def get_user_activity(username):
    """Kullanıcının aktivite geçmişini getirir"""
    try:
        activities = UserActivity.query.filter_by(username=username)\
            .order_by(UserActivity.created_at.desc()).limit(50).all()
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'type': activity.activity_type,
                'points_earned': activity.points_earned,
                'related_post_id': activity.related_post_id,
                'related_comment_id': activity.related_comment_id,
                'created_at': activity.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({'activities': activities_data})
        
    except Exception as e:
        return jsonify({'error': f'Aktivite hatası: {str(e)}'}), 500

@app.route('/forum/leaderboard', methods=['GET'])
def get_leaderboard():
    """Liderlik tablosunu getirir - En iyi çözüm seçilen 3 kullanıcı"""
    try:
        # En iyi çözüm seçilen kullanıcıları hesapla
        solution_leaders = db.session.query(
            ForumComment.author_username,
            db.func.count(ForumComment.id).label('solution_count')
        ).filter(
            ForumComment.is_solution == True
        ).group_by(
            ForumComment.author_username
        ).order_by(
            db.func.count(ForumComment.id).desc()
        ).limit(3).all()
        
        leaderboard_data = []
        for i, (username, solution_count) in enumerate(solution_leaders, 1):
            # Kullanıcının toplam aktivite puanlarını da hesapla
            total_points = db.session.query(
                db.func.sum(UserActivity.points_earned)
            ).filter(
                UserActivity.username == username
            ).scalar() or 0
            
            leaderboard_data.append({
                'rank': i,
                'username': username,
                'solution_count': solution_count,
                'total_points': total_points,
                'avatar': username[0].upper() if username else 'U'  # İlk harf avatar olarak
            })
        
        return jsonify({'leaderboard': leaderboard_data})
        
    except Exception as e:
        return jsonify({'error': f'Liderlik tablosu hatası: {str(e)}'}), 500

@app.route('/forum/search/advanced', methods=['GET'])
def advanced_search():
    """Gelişmiş arama"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    # Query parametreleri
    query = request.args.get('q', '')
    author = request.args.get('author', '')
    tags = request.args.get('tags', '').split(',') if request.args.get('tags') else []
    post_type = request.args.get('type', '')

    solved_only = request.args.get('solved_only', 'false').lower() == 'true'
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    try:
        # Base query
        search_query = ForumPost.query.filter_by(interest=user.interest)
        
        # Arama terimi
        if query:
            search_term = f"%{query}%"
            search_query = search_query.filter(
                db.or_(
                    ForumPost.title.ilike(search_term),
                    ForumPost.content.ilike(search_term)
                )
            )
        
        # Yazar filtresi
        if author:
            search_query = search_query.filter(ForumPost.author_username.ilike(f"%{author}%"))
        
        # Gönderi türü
        if post_type:
            search_query = search_query.filter(ForumPost.post_type == post_type)
        

        
        # Çözülmüş sadece
        if solved_only:
            search_query = search_query.filter(ForumPost.is_solved == True)
        
        # Tarih aralığı
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                search_query = search_query.filter(ForumPost.created_at >= from_date)
            except:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                search_query = search_query.filter(ForumPost.created_at <= to_date)
            except:
                pass
        
        # Etiketler
        if tags and tags[0]:
            for tag in tags:
                if tag.strip():
                    search_query = search_query.filter(ForumPost.tags.contains(tag.strip()))
        
        # Sonuçları sırala
        search_query = search_query.order_by(ForumPost.created_at.desc())
        
        # Sayfalama
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        results = search_query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Sonuçları formatla
        posts_data = []
        for post in results.items:
            user_liked = ForumLike.query.filter_by(
                username=session['username'],
                post_id=post.id
            ).first() is not None
            
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'author': post.author_username,
                'post_type': post.post_type,
                'tags': json.loads(post.tags) if post.tags else [],
                'views': post.views,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'is_solved': post.is_solved,

                'bounty_points': post.bounty_points,
                'user_liked': user_liked,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'posts': posts_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': results.total,
                'pages': results.pages,
                'has_next': results.has_next,
                'has_prev': results.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Arama hatası: {str(e)}'}), 500

@app.route('/forum/analytics', methods=['GET'])
def get_forum_analytics():
    """Forum analitiklerini getirir"""
    if 'username' not in session:
        return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    try:
        # Son 30 günün istatistikleri
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        # Gönderi istatistikleri
        total_posts = ForumPost.query.filter_by(interest=user.interest).count()
        recent_posts = ForumPost.query.filter(
            ForumPost.interest == user.interest,
            ForumPost.created_at >= thirty_days_ago
        ).count()
        
        # Yorum istatistikleri
        total_comments = ForumComment.query.join(ForumPost).filter(
            ForumPost.interest == user.interest
        ).count()
        recent_comments = ForumComment.query.join(ForumPost).filter(
            ForumPost.interest == user.interest,
            ForumComment.created_at >= thirty_days_ago
        ).count()
        
        # Çözülen sorular
        solved_questions = ForumPost.query.filter(
            ForumPost.interest == user.interest,
            ForumPost.post_type == 'question',
            ForumPost.is_solved == True
        ).count()
        
        # En aktif kullanıcılar
        active_users = db.session.query(
            ForumPost.author_username,
            db.func.count(ForumPost.id).label('post_count')
        ).filter(
            ForumPost.interest == user.interest,
            ForumPost.created_at >= thirty_days_ago
        ).group_by(ForumPost.author_username)\
         .order_by(db.func.count(ForumPost.id).desc())\
         .limit(5).all()
        
        active_users_data = []
        for username, count in active_users:
            active_users_data.append({
                'username': username,
                'post_count': count
            })
        
        # Popüler etiketler
        popular_tags = ForumTag.query.order_by(ForumTag.usage_count.desc()).limit(10).all()
        tags_data = []
        for tag in popular_tags:
            tags_data.append({
                'name': tag.name,
                'usage_count': tag.usage_count
            })
        
        return jsonify({
            'total_posts': total_posts,
            'recent_posts': recent_posts,
            'total_comments': total_comments,
            'recent_comments': recent_comments,
            'solved_questions': solved_questions,
            'active_users': active_users_data,
            'popular_tags': tags_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Analitik hatası: {str(e)}'}), 500

# ============================================
# İş Arama ve CV Analizi Endpoints (Yeni)
# ============================================

@app.route('/api/analyze-cv', methods=['POST'])
def analyze_cv():
    """CV'yi Gemini AI ile analiz eder"""
    try:
        # Kullanıcı girişi kontrolü (geçici olarak devre dışı - debug için)
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        
        # Test için user_id ata
        user_id = session.get('user_id', 'test_user')
        
        # CV dosyasını kontrol et
        if 'cv_file' not in request.files:
            return jsonify({'error': 'CV dosyası bulunamadı'}), 400
        
        cv_file = request.files['cv_file']
        if cv_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if not cv_file or not allowed_file(cv_file.filename):
            return jsonify({'error': 'Geçersiz dosya formatı. PDF destekleniyor.'}), 400
        
        # CV'yi kaydet
        filename = secure_filename(cv_file.filename)
        timestamp = int(time.time())
        unique_filename = f"cv_{user_id}_{timestamp}.{filename.split('.')[-1]}"
        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        cv_file.save(cv_path)
        
        try:
            # PDF'den metin çıkarmak yerine direkt PDF bytes'ını gönder
            with open(cv_path, 'rb') as file:
                pdf_bytes = file.read()
            
            # Akıllı Job Agent'ı başlat
            job_agent = IntelligentJobAgent()
            
            # CV'yi direkt PDF bytes ile analiz et (Yeni yöntem!)
            print(f"CV PDF analiz ediliyor - Kullanıcı: {user_id}")
            cv_analysis = job_agent.analyze_cv_from_pdf_bytes(pdf_bytes)
            
            # Sonucu döndür
            return jsonify({
                'success': True,
                'cv_analysis': cv_analysis,
                'cv_filename': unique_filename
            })
            
        except Exception as e:
            print(f"CV analiz hatası: {e}")
            return jsonify({'error': f'CV analizi sırasında hata: {str(e)}'}), 500
        
        finally:
            # Geçici dosyayı temizle
            try:
                if os.path.exists(cv_path):
                    os.remove(cv_path)
            except:
                pass
    
    except Exception as e:
        print(f"CV analiz endpoint hatası: {e}")
        return jsonify({'error': 'Beklenmedik hata oluştu'}), 500

@app.route('/api/search-jobs', methods=['POST'])
def search_jobs():
    """CV analizine göre iş ilanları arar ve eşleştirir"""
    try:
        # Kullanıcı girişi kontrolü (geçici olarak devre dışı - debug için)
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        
        data = request.json
        if not data or 'cv_analysis' not in data:
            return jsonify({'error': 'CV analizi verisi bulunamadı'}), 400
        
        cv_analysis = data['cv_analysis']
        location = data.get('location', 'Türkiye')
        max_jobs = data.get('max_jobs', 20)
        
        # Akıllı Job Agent'ı başlat
        job_agent = IntelligentJobAgent()
        
        # 1. İş ilanlarını scrape et
        print(f"İş ilanları aranıyor - Kullanıcı: test_user")
        job_areas = cv_analysis.get('uygun_iş_alanları', ['Software Developer'])
        jobs = job_agent.scrape_linkedin_jobs(
            job_areas=job_areas,
            location=location,
            max_per_search=max_jobs // len(job_areas) if job_areas else 10
        )
        
        if not jobs:
            return jsonify({
                'success': True,
                'message': 'Şu anda uygun iş ilanı bulunamadı. Daha sonra tekrar deneyin.',
                'jobs': [],
                'stats': {
                    'total_found': 0,
                    'matched': 0,
                    'search_areas': job_areas
                }
            })
        
        # 2. CV ile işleri eşleştir
        print(f"CV-İş eşleştirmesi yapılıyor...")
        matched_jobs = job_agent.match_cv_with_jobs(cv_analysis, jobs)
        
        # 3. İstatistikler
        stats = {
            'total_found': len(jobs),
            'matched': len(matched_jobs),
            'search_areas': job_areas,
            'avg_match_score': sum(job.get('score', 0) for job in matched_jobs) / len(matched_jobs) if matched_jobs else 0
        }
        
        return jsonify({
            'success': True,
            'jobs': matched_jobs,
            'stats': stats
        })
    
    except Exception as e:
        print(f"İş arama hatası: {e}")
        return jsonify({'error': f'İş arama sırasında hata: {str(e)}'}), 500

@app.route('/api/job-application-tips', methods=['POST'])
def get_job_application_tips():
    """Belirli bir iş için başvuru önerileri verir"""
    try:
        # Kullanıcı girişi kontrolü (geçici olarak devre dışı - debug için)
        # if 'user_id' not in session:
        #     return jsonify({'error': 'Giriş yapmanız gerekiyor'}), 401
        
        data = request.json
        if not data or 'cv_analysis' not in data or 'job' not in data:
            return jsonify({'error': 'CV analizi ve iş verisi gerekli'}), 400
        
        cv_analysis = data['cv_analysis']
        job = data['job']
        
        # Akıllı Job Agent'ı başlat
        job_agent = IntelligentJobAgent()
        
        # Başvuru önerilerini oluştur
        tips = job_agent.generate_job_application_tips(cv_analysis, job)
        
        return jsonify({
            'success': True,
            'tips': tips
        })
    
    except Exception as e:
        print(f"Başvuru önerileri hatası: {e}")
        return jsonify({'error': f'Başvuru önerileri oluşturulurken hata: {str(e)}'}), 500

def extract_text_from_pdf(file_path):
    """PDF dosyasından metin çıkarır"""
    text = ""
    try:
        # PyPDF2 ile dene
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Eğer PyPDF2 başarısızsa pdfplumber ile dene
        if not text.strip():
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
    
    except Exception as e:
        print(f"PDF metin çıkarma hatası: {e}")
        return ""
    
    return text.strip()

if __name__ == '__main__':
    init_app()  # Database'i başlat ve session'ları yükle
    app.run(debug=True)
