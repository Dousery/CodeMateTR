from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
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
from agents.code_agent import CodeAIAgent
from agents.intelligent_job_agent import IntelligentJobAgent
from utils.code_formatter import code_indenter
from flask_sqlalchemy import SQLAlchemy
import json
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')

# Production settings
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# Production'da session ayarlarını düzenle
if os.getenv('FLASK_ENV') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    # Production'da session'ları kalıcı yap
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 saat
    app.config['SESSION_COOKIE_MAX_AGE'] = 86400  # 24 saat
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    # Session'ları server-side sakla
    app.config['SESSION_TYPE'] = 'filesystem'
else:
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 saat
    app.config['SESSION_COOKIE_MAX_AGE'] = 3600  # 1 saat
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# CORS configuration for production
FRONTEND_URL = 'https://codematetr.onrender.com'  # Render frontend adresin

# Production'da sadece frontend originine izin ver
if os.getenv('FLASK_ENV') == 'production':
    CORS_ORIGINS = [FRONTEND_URL]
else:
    CORS_ORIGINS = [FRONTEND_URL, 'http://localhost:3000', 'http://127.0.0.1:5173']

CORS(app, 
     origins=CORS_ORIGINS,
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Origin", "Accept", "Access-Control-Allow-Origin"],
     expose_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"])

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
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
app.config['SESSION_COOKIE_MAX_AGE'] = 3600  # 1 saat
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Her istekte session'ı yenile

# Tek bir db instance oluştur
db = SQLAlchemy(app)

# Session'ı initialize et
Session(app)

# Model sınıflarını burada tanımla
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # scrypt hash için daha uzun alan
    interest = db.Column(db.String(80), nullable=True)
    cv_analysis = db.Column(db.Text, nullable=True)  # CV analiz sonucu

    def set_password(self, password):
        # Daha kısa hash için method belirt
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

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
        try:
            # Veritabanı tablolarını güvenli bir şekilde oluştur
            db.create_all()
            print("Veritabanı tabloları başarıyla oluşturuldu.")
            
            # Migration: password_hash sütununu güncelle
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE "user" 
                        ALTER COLUMN password_hash TYPE VARCHAR(255)
                    """))
                    conn.commit()
                    print("✅ Database migration completed - password_hash column updated")
            except Exception as migration_error:
                print(f"⚠️ Migration note: {migration_error}")
                # Migration hatası kritik değil, devam et
                pass
                
        except Exception as e:
            print(f"Veritabanı tabloları zaten mevcut veya oluşturulamadı: {e}")
            # Hata durumunda devam et
            pass
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

# Güvenlik dekoratörü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: Session check - Session: {dict(session)}")
        if 'username' not in session:
            print(f"DEBUG: No username in session")
            return jsonify({'error': 'Giriş yapmalısınız.'}), 401
        
        # Kullanıcının hala veritabanında var olup olmadığını kontrol et
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            print(f"DEBUG: User not found in database: {session['username']}")
            session.clear()
            return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
        
        print(f"DEBUG: Login check passed for user: {session['username']}")
        return f(*args, **kwargs)
    return decorated_function

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
    
    # Şifre gücü kontrolü
    if len(password) < 5:
        return jsonify({'error': 'Şifre en az 5 karakter olmalıdır.'}), 400
    
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
    
    if not username or not password:
        return jsonify({'error': 'Kullanıcı adı ve şifre gerekli.'}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Geçersiz kullanıcı adı veya şifre.'}), 401
    
    # Session'ı kalıcı yap
    session.permanent = True
    session['username'] = username
    session['user_id'] = user.id
    
    # Session'ı hemen kaydet
    session.modified = True
    
    # Debug için session bilgilerini logla
    print(f"Login successful for user: {username}, session: {dict(session)}")
    
    return jsonify({
        'message': 'Giriş başarılı.',
        'username': username,
        'interest': user.interest
    })

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.modified = True
    return jsonify({'message': 'Çıkış başarılı.'})

@app.route('/session-status', methods=['GET'])
def session_status():
    """Session durumunu kontrol etmek için test endpoint'i"""
    return jsonify({
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session,
        'session_permanent': session.permanent,
        'session_modified': session.modified
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint'i"""
    import os
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'pid': os.getpid(),
        'flask_env': os.getenv('FLASK_ENV'),
        'database_connected': db.engine.pool.checkedin() > 0,
        'gemini_api_key': bool(os.getenv('GEMINI_API_KEY')),
        'jsearch_api_key': bool(os.getenv('JSEARCH_API_KEY'))
    })

@app.route('/debug/cv-test', methods=['POST'])
def debug_cv_test():
    """CV analizi test endpoint'i - debug için"""
    try:
        if 'cv_file' not in request.files:
            return jsonify({'error': 'CV dosyası bulunamadı'}), 400
        
        cv_file = request.files['cv_file']
        if cv_file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        # CV'yi kaydet
        filename = secure_filename(cv_file.filename)
        timestamp = int(time.time())
        unique_filename = f"debug_cv_{timestamp}.{filename.split('.')[-1]}"
        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        cv_file.save(cv_path)
        
        try:
            # PDF'den bytes oku
            with open(cv_path, 'rb') as file:
                pdf_bytes = file.read()
            
            print(f"DEBUG: PDF boyutu: {len(pdf_bytes)} bytes")
            print(f"DEBUG: Gemini API key mevcut: {bool(os.getenv('GEMINI_API_KEY'))}")
            print(f"DEBUG: JSearch API key mevcut: {bool(os.getenv('JSEARCH_API_KEY'))}")
            
            # Job agent'ı başlat
            job_agent = IntelligentJobAgent()
            
            # CV analizi yap
            print("DEBUG: CV analizi başlatılıyor...")
            cv_analysis = job_agent.analyze_cv_from_pdf_bytes(pdf_bytes)
            print(f"DEBUG: CV analizi sonucu: {cv_analysis}")
            
            # İş arama yap
            print("DEBUG: İş arama başlatılıyor...")
            print(f"DEBUG: CV analizi: {cv_analysis}")
            jobs = job_agent.search_jobs_with_jsearch(cv_analysis, max_results=5)
            print(f"DEBUG: Bulunan iş sayısı: {len(jobs)}")
            if jobs:
                print(f"DEBUG: İlk iş örneği: {jobs[0]}")
            else:
                print("DEBUG: Hiç iş bulunamadı!")
            
            return jsonify({
                'success': True,
                'cv_analysis': cv_analysis,
                'jobs': jobs,
                'pdf_size': len(pdf_bytes),
                'gemini_key_exists': bool(os.getenv('GEMINI_API_KEY')),
                'jsearch_key_exists': bool(os.getenv('JSEARCH_API_KEY'))
            })
            
        finally:
            # Geçici dosyayı temizle
            try:
                if os.path.exists(cv_path):
                    os.remove(cv_path)
            except:
                pass
    
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/set_interest', methods=['POST'])
@login_required
def set_interest():
    data = request.json
    interest = data.get('interest')
    if not interest:
        return jsonify({'error': 'İlgi alanı gerekli.'}), 400
    user = User.query.filter_by(username=session['username']).first()
    user.interest = interest
    db.session.commit()
    return jsonify({'message': 'İlgi alanı kaydedildi.'})

@app.route('/profile', methods=['GET'])
@login_required
def profile():
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
            daily_tests = UserActivity.query.filter(
                UserActivity.username == user.username,
                UserActivity.activity_type == 'test_completed',
                UserActivity.created_at >= date.replace(hour=0, minute=0, second=0),
                UserActivity.created_at < date.replace(hour=23, minute=59, second=59)
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
            
            # Türkçe gün isimleri
            day_names = {
                'Mon': 'Pzt',
                'Tue': 'Sal',
                'Wed': 'Çar',
                'Thu': 'Per',
                'Fri': 'Cum',
                'Sat': 'Cmt',
                'Sun': 'Paz'
            }
            
            day_name = day_names.get(date.strftime('%A')[:3], date.strftime('%A')[:3])
            
            daily_activity.append({
                'date': date_str,
                'day_name': day_name,
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
                'total_code_sessions': total_code_sessions,
                'total_code_points': total_code_points,
                'code_trend': code_trend,
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

@app.route('/test', methods=['GET'])
def test_page():
    """Test sayfası için basit endpoint"""
    return jsonify({
        'message': 'Test sayfası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })

@app.route('/code', methods=['GET'])
def code_page():
    """Kodlama odası sayfası için basit endpoint"""
    return jsonify({
        'message': 'Kodlama odası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })

@app.route('/auto-interview', methods=['GET'])
def auto_interview_page():
    """Otomatik mülakat odası sayfası için basit endpoint"""
    return jsonify({
        'message': 'Otomatik mülakat odası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })

@app.route('/smart-job-finder', methods=['GET'])
def smart_job_finder_page():
    """Akıllı iş bulma sayfası için basit endpoint"""
    return jsonify({
        'message': 'Akıllı iş bulma sayfası erişilebilir',
        'session_data': dict(session),
        'has_username': 'username' in session,
        'has_user_id': 'user_id' in session
    })

@app.route('/test_your_skill', methods=['POST'])
@login_required
def test_your_skill():
    print(f"DEBUG: test_your_skill called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
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
@login_required
def upload_cv():
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
@login_required
def interview_cv_based_question():
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
@login_required
def interview_personalized_questions():
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
@login_required
def interview_speech_question():
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
@login_required
def interview_cv_speech_question():
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
@login_required
def interview_speech_evaluation():
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
@login_required
def interview_simulation():
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
@login_required
def code_room():
    print(f"DEBUG: code_room called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    language = data.get('language', 'python')  # Varsayılan olarak python
    difficulty = data.get('difficulty', 'orta')  # Varsayılan olarak orta
    
    try:
        agent = CodeAIAgent(user.interest, language)
        coding_question = agent.generate_coding_question(difficulty)
        
        # Kodlama aktivitesi kaydet
        activity = UserActivity(
            username=user.username,
            activity_type='code_session',
            points_earned=10
        )
        db.session.add(activity)
        db.session.commit()
        
    except Exception as e:
        return jsonify({'error': f'Gemini API hatası: {str(e)}'}), 500
    return jsonify({
        'message': f'{user.interest} alanında kodlama sorusu oluşturuldu.',
        'coding_question': coding_question
    })

@app.route('/code_room/generate_solution', methods=['POST'])
@login_required
def code_room_generate_solution():
    print(f"DEBUG: code_room_generate_solution called by user: {session.get('username')}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    question = data.get('question')
    language = data.get('language', 'python')  # Varsayılan olarak python
    
    if not question:
        return jsonify({'error': 'Soru gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        solution = agent.generate_solution(question)
        return jsonify({
            'success': True,
            'solution': solution
        })
    except Exception as e:
        return jsonify({'error': f'Çözüm oluşturma hatası: {str(e)}'}), 500



# Test çözümü kaydı
@app.route('/test_your_skill/evaluate', methods=['POST'])
@login_required
def test_your_skill_evaluate():
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
    
    # Kaynak önerileri kaldırıldı
    resources = []
    web_resources = {}
    
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
    
    # Test aktivitesi kaydet
    activity = UserActivity(
        username=user.username,
        activity_type='test_completed',
        points_earned=20
    )
    db.session.add(activity)
    
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
@login_required
def code_room_evaluate():
    """Kodu değerlendirir ve puan verir"""
    user = User.query.filter_by(username=session['username']).first()
    if not user.interest:
        return jsonify({'error': 'İlgi alanı seçmelisiniz.'}), 400
    
    data = request.json
    question = data.get('question', '')
    user_code = data.get('user_code')
    use_execution = data.get('use_execution', False)
    language = data.get('language', 'python')
    
    if not user_code:
        return jsonify({'error': 'Kod gerekli.'}), 400
    
    try:
        agent = CodeAIAgent(user.interest, language)
        
        if use_execution:
            # Çalıştırarak değerlendir
            result = agent.evaluate_code_with_execution(user_code, question)
        else:
            # Sadece analiz yap
            evaluation_text = agent.evaluate_code(user_code, question)
            result = {
                "evaluation": evaluation_text,
                "execution_output": "",
                "code_suggestions": "",
                "has_errors": False,
                "corrected_code": "",
                "score": 0,
                "feedback": evaluation_text
            }
        
        # Kodlama değerlendirme aktivitesi kaydet
        activity = UserActivity(
            username=user.username,
            activity_type='code_evaluation',
            points_earned=15
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Değerlendirme hatası: {str(e)}'}), 500



@app.route('/code_room/run', methods=['POST'])
@login_required
def code_room_run():
    """Sadece kodu çalıştırır, değerlendirmez"""
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

@app.route('/code_room/run_simple', methods=['POST'])
@login_required
def code_room_run_simple():
    """Basit kod çalıştırma - sadece çalıştırır, analiz yapmaz"""
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
        
        # Sadece kod çalıştırma için basit prompt
        simple_prompt = f"""
        Bu kodu çalıştır ve sadece çıktıyı ver:
        
        ```{language}
        {user_code}
        ```
        
        Sadece çıktıyı göster, kod gösterme. Analiz yapma.
        """
        
        # execute_complex_code metodunu kullan ama sadece çalıştırma
        result = agent.execute_complex_code(simple_prompt, language)
        
        # Sadece çalıştırma sonucunu döndür
        simple_result = {
            'success': result['success'],
            'code': result['code'],
            'output': result['output'],
            'error': result['error']
        }
        
        return jsonify({
            'success': True,
            'result': simple_result
        })
        
    except Exception as e:
        return jsonify({'error': f'Kod çalıştırma hatası: {str(e)}'}), 500







@app.route('/code_room/suggest_resources', methods=['POST'])
@login_required
def code_room_suggest_resources():
    """Konuya göre kaynak önerileri"""
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

@app.route('/code_room/format_code', methods=['POST'])
@login_required
def code_room_format_code():
    """Kodu gelişmiş formatter ile formatlar"""
    # Session kontrolünü kaldır - formatlama için gerekli değil
    # if 'username' not in session:
    #     return jsonify({'error': 'Giriş yapmalısınız.'}), 401
    
    data = request.json
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if not code.strip():
        return jsonify({'error': 'Kod gerekli.'}), 400
    
    try:
        # Dil enum'una çevir
        language_map = {
            'python': 'PYTHON',
            'javascript': 'JAVASCRIPT', 
            'java': 'JAVA',
            'cpp': 'CPP'
        }
        
        from utils.code_formatter import Language
        lang_enum = getattr(Language, language_map.get(language, 'PYTHON'))
        
        # Kodu formatla
        formatted_code = code_indenter.indent_code(code, lang_enum)
        
        return jsonify({
            'success': True,
            'formatted_code': formatted_code,
            'language': language
        })
    except Exception as e:
        return jsonify({'error': f'Kod formatlanamadı: {str(e)}'}), 500









# Case Study çözümü kaydı

# Interview çözümü kaydı
@app.route('/interview_simulation/evaluate', methods=['POST'])
@login_required
def interview_simulation_evaluate():
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
@login_required
def change_password():
    data = request.json
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'error': 'Yeni şifre gerekli.'}), 400
    
    # Şifre gücü kontrolü
    if len(new_password) < 6:
        return jsonify({'error': 'Yeni şifre en az 6 karakter olmalıdır.'}), 400
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı.'}), 404
    
    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Şifre başarıyla değiştirildi.'})















@app.route('/')
def home():
    return jsonify({'message': 'CodeMateTR API is running!'})

@app.route('/test-session')
def test_session():
    return jsonify({
        'session': dict(session),
        'has_username': 'username' in session,
        'username': session.get('username', None)
    })





# ==================== OTOMATİK MÜLAKAT SİSTEMİ ====================

@app.route('/auto_interview/start', methods=['POST'])
@login_required
def start_auto_interview():
    """Otomatik mülakat başlatır"""
    print(f"DEBUG: start_auto_interview called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        print(f"DEBUG: User not found in database: {session.get('username')}")
        return jsonify({'error': 'Kullanıcı bulunamadı. Lütfen tekrar giriş yapın.'}), 401
    
    if not user.interest:
        print(f"DEBUG: User has no interest: {session.get('username')}")
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
            'question_index': 0,  # İlk soru, henüz cevap yok
            'total_questions': 5,  # Toplam soru sayısı
            'audio_url': audio_url
        })
        
    except Exception as e:
        return jsonify({'error': f'Mülakat başlatma hatası: {str(e)}'}), 500

@app.route('/auto_interview/submit_answer', methods=['POST'])
@login_required
def submit_auto_interview_answer():
    """Otomatik mülakat cevabını gönder ve sonraki soruyu al"""
    print(f"DEBUG: submit_auto_interview_answer called by user: {session.get('username')}")
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
        
        # 5 cevap tamamlandı mı kontrol et (5 soru, 5 cevap)
        if len(answers) >= 5:
            # Final değerlendirme üret
            agent = InterviewAIAgent(auto_session.interest)
            final_evaluation = agent.generate_final_evaluation(
                questions, 
                answers, 
                auto_session.conversation_context
            )
            
            # Session'ı tamamla
            auto_session.status = 'completed'
            auto_session.end_time = datetime.utcnow()
            auto_session.final_evaluation = final_evaluation
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'message': 'Mülakat tamamlandı!',
                'final_evaluation': final_evaluation,
                'total_questions': len(questions),
                'total_answers': len(answers),
                'session_duration': (auto_session.end_time - auto_session.start_time).total_seconds()
            })
        
        # Sonraki soru için index'i güncelle (cevaplanan soru sayısı)
        auto_session.current_question_index = len(answers)
        
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
        
        print(f"DEBUG: question_index={auto_session.current_question_index}, answers_count={len(answers)}, questions_count={len(questions)}")
        return jsonify({
            'status': 'continue',
            'question': next_question,
            'question_index': auto_session.current_question_index,  # Şu anki soru index'i
            'total_questions': 5,
            'audio_url': audio_url
        })
        
    except Exception as e:
        print(f"Auto interview submit answer error: {e}")
        return jsonify({'error': f'Cevap gönderme hatası: {str(e)}'}), 500

@app.route('/auto_interview/complete', methods=['POST'])
@login_required
def complete_auto_interview():
    print(f"DEBUG: complete_auto_interview called by user: {session.get('username')}")
    """Mülakatı tamamlar ve final değerlendirme üretir"""
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
@login_required
def get_auto_interview_status():
    print(f"DEBUG: get_auto_interview_status called by user: {session.get('username')}")
    """Aktif mülakat oturumunun durumunu döndürür"""
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
@login_required
def get_forum_posts():
    """İlgi alanına göre forum gönderilerini getirir"""
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
            'author': post.author_username,
            'post_type': post.post_type,
            'tags': json.loads(post.tags) if post.tags else [],
            'views': post.views,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
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
@login_required
def create_forum_post():
    """Yeni forum gönderisi oluşturur"""
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
            tags=json.dumps(tags)
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        # Forum post aktivitesi kaydet
        activity = UserActivity(
            username=session['username'],
            activity_type='forum_post',
            points_earned=5,
            related_post_id=new_post.id
        )
        db.session.add(activity)
        db.session.commit()
        
        return jsonify({
            'message': 'Gönderi başarıyla oluşturuldu.',
            'post_id': new_post.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Gönderi oluşturma hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>', methods=['GET'])
@login_required
def get_forum_post(post_id):
    """Tekil forum gönderisini getirir"""
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
                'author': reply.author_username,
                'likes_count': reply.likes_count,
                'user_liked': user_liked_reply,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'author': comment.author_username,
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
            'author': post.author_username,
            'author_username': post.author_username,
            'interest': post.interest,
            'post_type': post.post_type,
            'tags': json.loads(post.tags) if post.tags else [],
            'views': post.views,
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
            'is_solved': post.is_solved,
            'solved_by': post.solved_by,
            'solved_at': post.solved_at.strftime('%Y-%m-%d %H:%M') if post.solved_at else None,
            'user_liked': user_liked,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M')
        },
        'comments': comments_data
    })



@app.route('/forum/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_forum_post(post_id):
    """Forum gönderisini siler"""
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
@login_required
def create_forum_comment(post_id):
    """Forum gönderisine yorum ekler"""
    post = ForumPost.query.get_or_404(post_id)
    
    data = request.json
    content = data.get('content')
    parent_comment_id = data.get('parent_comment_id')
    
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
            parent_comment_id=parent_comment_id
        )
        
        db.session.add(new_comment)
        
        # Post'un yorum sayısını artır
        post.comments_count += 1
        
        # Forum comment aktivitesi kaydet
        activity = UserActivity(
            username=session['username'],
            activity_type='forum_comment',
            points_earned=3,
            related_post_id=post_id,
            related_comment_id=new_comment.id
        )
        db.session.add(activity)
        
        # Yorum notification'ı gönder (kendine gönderme)
        if post.author_username != session['username']:
            try:
                notification = ForumNotification(
                    username=post.author_username,
                    notification_type='comment',
                    title='Gönderinize yorum yapıldı!',
                    message=f'"{post.title}" gönderinize yeni bir yorum yapıldı.',
                    related_post_id=post_id,
                    related_comment_id=new_comment.id
                )
                db.session.add(notification)
            except Exception as e:
                print(f"Comment notification error: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': 'Yorum başarıyla eklendi.',
            'comment_id': new_comment.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Yorum ekleme hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_forum_post(post_id):
    """Forum gönderisini beğenir/beğenmekten vazgeçer"""
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
            
            # Beğeni notification'ı gönder (kendine gönderme)
            if post.author_username != session['username']:
                try:
                    notification = ForumNotification(
                        username=post.author_username,
                        notification_type='like',
                        title='Gönderiniz beğenildi!',
                        message=f'"{post.title}" gönderiniz beğenildi.',
                        related_post_id=post_id
                    )
                    db.session.add(notification)
                except Exception as e:
                    print(f"Like notification error: {e}")
        
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
@login_required
def like_forum_comment(comment_id):
    """Forum yorumunu beğenir/beğenmekten vazgeçer"""
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
            
            # Beğeni notification'ı gönder (kendine gönderme)
            if comment.author_username != session['username']:
                try:
                    notification = ForumNotification(
                        username=comment.author_username,
                        notification_type='like',
                        title='Yorumunuz beğenildi!',
                        message=f'Yorumunuz beğenildi.',
                        related_comment_id=comment_id
                    )
                    db.session.add(notification)
                except Exception as e:
                    print(f"Comment like notification error: {e}")
        
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
@login_required
def get_forum_stats():
    """Forum istatistiklerini getirir"""
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
@login_required
def get_notifications():
    """Kullanıcının bildirimlerini getirir"""
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
@login_required
def mark_notifications_read():
    """Tüm bildirimleri siler (geçmişi temizler)"""
    try:
        # Kullanıcının tüm bildirimlerini sil
        ForumNotification.query.filter_by(
            username=session['username']
        ).delete()
        
        db.session.commit()
        return jsonify({'message': 'Tüm bildirimler temizlendi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Tek bir bildirimi siler"""
    try:
        notification = ForumNotification.query.filter_by(
            id=notification_id,
            username=session['username']
        ).first()
        
        if not notification:
            return jsonify({'error': 'Bildirim bulunamadı.'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Bildirim silindi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/report', methods=['POST'])
@login_required
def report_content():
    """İçerik raporlar"""
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
@login_required
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
@login_required
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
@login_required
def mark_post_solved(post_id):
    """Gönderiyi çözüldü olarak işaretler"""
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
        if solved_by and solved_by != session['username']:  # Kendine notification gönderme
            try:
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
                print(f"Notification sent to {solved_by} for solution acceptance")
            except Exception as e:
                print(f"Notification error: {e}")
                db.session.rollback()
        
        return jsonify({'message': 'Gönderi çözüldü olarak işaretlendi.'})
        
    except Exception as e:
        return jsonify({'error': f'İşlem hatası: {str(e)}'}), 500

@app.route('/forum/posts/<int:post_id>/bounty', methods=['POST'])
@login_required
def add_bounty(post_id):
    """Gönderiye ödül puanı ekler"""
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
@login_required
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
@login_required
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
@login_required
def advanced_search():
    """Gelişmiş arama"""
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
@login_required
def get_forum_analytics():
    """Forum analitiklerini getirir"""
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
@login_required
def analyze_cv():
    """CV'yi Gemini AI ile analiz eder"""
    print(f"DEBUG: analyze_cv called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
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
        unique_filename = f"cv_{session['username']}_{timestamp}.{filename.split('.')[-1]}"
        cv_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        cv_file.save(cv_path)
        
        try:
            # PDF'den metin çıkarmak yerine direkt PDF bytes'ını gönder
            with open(cv_path, 'rb') as file:
                pdf_bytes = file.read()
            
            # Akıllı Job Agent'ı başlat
            job_agent = IntelligentJobAgent()
            
            # CV'yi direkt PDF bytes ile analiz et (Yeni yöntem!)
            print(f"CV PDF analiz ediliyor - Kullanıcı: {session['username']}")
            print(f"PDF boyutu: {len(pdf_bytes)} bytes")
            print(f"Gemini API key mevcut: {bool(os.getenv('GEMINI_API_KEY'))}")
            
            cv_analysis = job_agent.analyze_cv_from_pdf_bytes(pdf_bytes)
            print(f"CV analizi sonucu: {cv_analysis}")
            
            # CV analiz sonucunu veritabanına kaydet
            user = User.query.filter_by(username=session['username']).first()
            if user:
                user.cv_analysis = json.dumps(cv_analysis)
                db.session.commit()
                print(f"CV analiz sonucu veritabanına kaydedildi - Kullanıcı: {user.username}")
            else:
                print(f"Kullanıcı bulunamadı: {session['username']}")
            
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
@login_required
def search_jobs():
    """CV analizine göre iş ilanları arar ve eşleştirir"""
    print(f"DEBUG: search_jobs called by user: {session.get('username')}")
    print(f"DEBUG: Session data: {dict(session)}")
    
    try:
        data = request.json
        if not data or 'cv_analysis' not in data:
            return jsonify({'error': 'CV analizi verisi bulunamadı'}), 400
        
        cv_analysis = data['cv_analysis']
        location = data.get('location', 'Türkiye')
        max_jobs = data.get('max_jobs', 20)
        
        # Akıllı Job Agent'ı başlat
        job_agent = IntelligentJobAgent()
        
        # JSearch API ile iş ilanlarını ara
        print(f"JSearch API ile iş ilanları aranıyor - Kullanıcı: {session.get('username')}")
        jobs = job_agent.search_jobs_with_jsearch(
            cv_analysis=cv_analysis,
            max_results=max_jobs
        )
        
        if not jobs:
            return jsonify({
                'success': True,
                'message': 'Şu anda uygun iş ilanı bulunamadı. Daha sonra tekrar deneyin.',
                'jobs': [],
                'stats': {
                    'total_found': 0,
                    'matched': 0,
                    'search_areas': cv_analysis.get('uygun_iş_alanları', []),
                    'search_method': 'JSearch API'
                }
            })
        
        # İstatistikler
        stats = {
            'total_found': len(jobs),
            'matched': len(jobs),
            'search_areas': cv_analysis.get('uygun_iş_alanları', []),
            'avg_match_score': sum(job.get('score', 0) for job in jobs) / len(jobs) if jobs else 0,
            'search_method': 'JSearch API',
            'total_jobs': len(jobs)
        }
        
        return jsonify({
            'success': True,
            'jobs': jobs,
            'stats': stats
        })
    
    except Exception as e:
        print(f"İş arama hatası: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'İş arama sırasında hata: {str(e)}'}), 500

@app.route('/api/process-cv-file', methods=['POST'])
@login_required
def process_cv_file():
    """PDF CV dosyasını analiz eder ve uygun işleri bulur"""
    print(f"DEBUG: process_cv_file called by user: {session.get('username')}")
    
    try:
        if 'cv_file' not in request.files:
            return jsonify({'error': 'CV dosyası seçilmemiş.'}), 400
        
        file = request.files['cv_file']
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmemiş.'}), 400
        
        if file and allowed_file(file.filename):
            # CV'yi kaydet
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            unique_filename = f"cv_{session['username']}_{timestamp}.{filename.split('.')[-1]}"
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(cv_path)
            
            print(f"CV dosyası kaydedildi: {cv_path}")
            print(f"Dosya boyutu: {os.path.getsize(cv_path)} bytes")
            
            try:
                # PDF'yi bytes olarak oku
                with open(cv_path, 'rb') as f:
                    pdf_bytes = f.read()
                
                # IntelligentJobAgent'ı başlat
                print("IntelligentJobAgent başlatılıyor...")
                job_agent = IntelligentJobAgent()
                
                # CV analizi ve iş arama
                print(f"CV analizi ve JSearch API iş arama başlatılıyor - Kullanıcı: {session['username']}")
                result = job_agent.process_cv_and_find_jobs(pdf_bytes, max_results=20)
                
                print(f"İşlem sonucu: {result.get('success', False)}")
                print(f"CV analizi: {result.get('cv_analysis', {}).get('teknik_beceriler', [])}")
                print(f"Bulunan iş sayısı: {len(result.get('jobs', []))}")
                
                if result.get('success'):
                    # CV analiz sonucunu veritabanına kaydet
                    user = User.query.filter_by(username=session['username']).first()
                    if user:
                        user.cv_analysis = json.dumps(result['cv_analysis'])
                        db.session.commit()
                        print(f"CV analiz sonucu veritabanına kaydedildi - Kullanıcı: {user.username}")
                    
                    # Stats'a search_method ekle
                    stats = result.get('stats', {})
                    stats['search_method'] = 'JSearch API'
                    
                    # Sonucu döndür
                    return jsonify({
                        'success': True,
                        'cv_analysis': result['cv_analysis'],
                        'jobs': result['jobs'],
                        'stats': stats,
                        'cv_filename': unique_filename
                    })
                else:
                    error_msg = result.get('error', 'CV işleme başarısız')
                    print(f"CV işleme hatası: {error_msg}")
                    return jsonify({'error': error_msg}), 500
                    
            except Exception as e:
                print(f"CV işleme hatası: {e}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                return jsonify({'error': f'CV işleme sırasında hata: {str(e)}'}), 500
            
            finally:
                # Geçici dosyayı temizle
                try:
                    if os.path.exists(cv_path):
                        os.remove(cv_path)
                        print(f"Geçici dosya temizlendi: {cv_path}")
                except Exception as cleanup_error:
                    print(f"Dosya temizleme hatası: {cleanup_error}")
        else:
            return jsonify({'error': 'Geçersiz dosya formatı. Sadece PDF dosyaları kabul edilir.'}), 400
    
    except Exception as e:
        print(f"CV dosya işleme endpoint hatası: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Beklenmedik hata oluştu'}), 500

@app.route('/api/job-application-tips', methods=['POST'])
@login_required
def get_job_application_tips():
    print(f"DEBUG: get_job_application_tips called by user: {session.get('username')}")
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Production ortamında (Render) sadece veritabanını başlat
    init_app()
