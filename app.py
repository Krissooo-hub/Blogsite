import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# Configs
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Database Configuration (Fix: Handle external persistent PostgreSQL URL)
db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

# File Extensions
app.config['ALLOWED_IMAGE_EXTS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['ALLOWED_VIDEO_EXTS'] = {'mp4', 'webm', 'ogg', 'mov'}

db = SQLAlchemy(app)

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the dashboard.'

# --- DATABASE MODELS ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True, default='default_profile.jpg')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="CHRIST GABRIEL V. CELESTE")
    age = db.Column(db.String(20), default="20 YEARS OLD")
    email = db.Column(db.String(120), default="CYNATOPHER@EMAIL.COM")
    status = db.Column(db.String(50), default="SINGLE")
    graduated = db.Column(db.String(200), default="BACHELOR OF SCIENCE IN INFORMATION TECHNOLOGY")
    hobbies = db.Column(db.Text, default="")
    biography = db.Column(db.Text, default="")
    image_filename = db.Column(db.String(255), default="self.png")
    facebook_url = db.Column(db.String(255), nullable=True)
    instagram_url = db.Column(db.String(255), nullable=True)
    tiktok_url = db.Column(db.String(255), nullable=True)
    discord_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    about_text = db.Column(db.Text, nullable=True)
    about_image = db.Column(db.String(255), nullable=True)

class ProjectCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.Text, nullable=False)
    badge = db.Column(db.String(50), default="Featured")
    image_filename = db.Column(db.String(255), nullable=False)

class MediaUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    caption = db.Column(db.Text, nullable=True)
    badge = db.Column(db.String(50), default="Featured")
    filename = db.Column(db.String(255), nullable=True)
    media_type = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Interest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Initialize Database & Default Data
# --- AFTER ---
# Initialize Database & Default Data safely
with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(username='krissooo').first():
            hashed_pw = generate_password_hash('celeste')
            admin_user = User(username='krissooo', password_hash=hashed_pw)
            db.session.add(admin_user)
            db.session.commit()
        
        if not UserProfile.query.first():
            default_profile = UserProfile()
            db.session.add(default_profile)
            db.session.commit()
    except Exception as e:
        print(f"Database setup error: {e}")

# --- HELPER FUNCTIONS ---

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_IMAGE_EXTS']

def get_media_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in app.config['ALLOWED_IMAGE_EXTS']:
        return 'image'
    elif ext in app.config['ALLOWED_VIDEO_EXTS']:
        return 'video'
    return None

def save_file(file_obj, prefix=""):
    """Saves file to Cloudinary on production, or to disk locally."""
    if os.environ.get('CLOUDINARY_CLOUD_NAME'):
        res = cloudinary.uploader.upload(file_obj, resource_type="auto")
        return res.get('secure_url')
    elif not os.environ.get('VERCEL'):
        filename = secure_filename(prefix + file_obj.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_obj.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    return "default.jpg"

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- PUBLIC ROUTES ---

@app.route('/')
def home():
    cards = ProjectCard.query.order_by(ProjectCard.id.desc()).all()
    music_slides = Interest.query.filter_by(category='Music').order_by(Interest.id.desc()).all()
    games_slides = Interest.query.filter_by(category='Games').order_by(Interest.id.desc()).all()
    lifestyle_slides = Interest.query.filter_by(category='Lifestyle').order_by(Interest.id.desc()).all()
    user_profile = UserProfile.query.first()

    return render_template(
        'index.html', 
        cards=cards,
        music_slides=music_slides,
        games_slides=games_slides,
        lifestyle_slides=lifestyle_slides,
        user_profile=user_profile
    )

@app.route('/blog')
def blog():
    category = request.args.get('category', 'all')
    query = MediaUpload.query.order_by(MediaUpload.id.desc())
    
    if category == 'image':
        posts = query.filter_by(media_type='image').all()
    elif category == 'video':
        posts = query.filter_by(media_type='video').all()
    elif category == 'text':
        posts = query.filter(
            (MediaUpload.media_type == 'text') | 
            (MediaUpload.filename == 'none') | 
            (MediaUpload.filename == None)
        ).all()
    else:
        posts = query.all()
        
    user_profile = UserProfile.query.first()
    return render_template('blogpage.html', posts=posts, user_profile=user_profile, active_category=category)

@app.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog_post(post_id):
    post = MediaUpload.query.get_or_404(post_id)
    if post.filename and post.filename != 'none' and not post.filename.startswith('http'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/profile')
def profile():
    user_profile = UserProfile.query.first()
    return render_template('profile.html', user_profile=user_profile)

@app.route('/project')
def project():
    cards = ProjectCard.query.order_by(ProjectCard.id.desc()).all()
    return render_template('project.html', cards=cards)

# --- PROTECTED DASHBOARD ROUTES ---

@app.route('/dashboard')
@login_required
def dashboard():
    card_count = ProjectCard.query.count()
    interest_count = Interest.query.count()
    media_count = MediaUpload.query.count()
    user_profile = UserProfile.query.first()
    uploads = MediaUpload.query.order_by(MediaUpload.id.desc()).all()

    return render_template(
        'dashboard_main.html',
        card_count=card_count,
        interest_count=interest_count,
        media_count=media_count,
        user_profile=user_profile,
        uploads=uploads
    )

@app.route('/dashboard/cards')
@login_required
def dashboard_cards():
    cards = ProjectCard.query.order_by(ProjectCard.id.desc()).all()
    interests = Interest.query.order_by(Interest.id.desc()).all()
    return render_template('dashboard.html', cards=cards, interests=interests)

@app.route('/dashboard/post')
@login_required
def dashboard_post():
    uploads = MediaUpload.query.order_by(MediaUpload.id.desc()).all()
    return render_template('dashboard_post.html', uploads=uploads)

@app.route('/dashboard/profile')
@login_required
def dashboard_profile_page():
    user_profile = UserProfile.query.first()
    return render_template('dashboard_profile.html', user_profile=user_profile)

# --- DASHBOARD ACTION HANDLERS ---

@app.route('/dashboard/update-profile', methods=['POST'])
@login_required
def update_profile():
    profile_data = UserProfile.query.first()
    if not profile_data:
        profile_data = UserProfile()
        db.session.add(profile_data)

    profile_data.name = request.form.get('name', profile_data.name)
    profile_data.age = request.form.get('age', profile_data.age)
    profile_data.email = request.form.get('email', profile_data.email)
    profile_data.status = request.form.get('status', profile_data.status)
    profile_data.graduated = request.form.get('graduated', profile_data.graduated)
    profile_data.hobbies = request.form.get('hobbies', profile_data.hobbies)
    profile_data.biography = request.form.get('biography', profile_data.biography)
    
    profile_data.facebook_url = request.form.get('facebook_url', profile_data.facebook_url)
    profile_data.instagram_url = request.form.get('instagram_url', profile_data.instagram_url)
    profile_data.tiktok_url = request.form.get('tiktok_url', profile_data.tiktok_url)
    profile_data.discord_url = request.form.get('discord_url', profile_data.discord_url)
    profile_data.linkedin_url = request.form.get('linkedin_url', profile_data.linkedin_url)
    profile_data.about_text = request.form.get('about_text', profile_data.about_text)

    file = request.files.get('image')
    if file and allowed_image(file.filename):
        profile_data.image_filename = save_file(file, prefix="profile_")

    about_file = request.files.get('about_image')
    if about_file and allowed_image(about_file.filename):
        profile_data.about_image = save_file(about_file, prefix="about_")

    db.session.commit()
    flash('Profile updated successfully!')
    return redirect(url_for('dashboard_profile_page'))

@app.route('/dashboard/upload-card', methods=['POST'])
@login_required
def upload_card():
    title = request.form.get('title')
    caption = request.form.get('caption')
    badge = request.form.get('badge', 'Featured')
    file = request.files.get('image')

    if file and allowed_image(file.filename):
        filename = save_file(file)
        new_card = ProjectCard(title=title, caption=caption, badge=badge, image_filename=filename)
        db.session.add(new_card)
        db.session.commit()

    return redirect(url_for('dashboard_cards'))

@app.route('/dashboard/delete-card/<int:card_id>', methods=['POST'])
@login_required
def delete_card(card_id):
    card = db.get_or_404(ProjectCard, card_id)
    if card.image_filename and not card.image_filename.startswith('http'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], card.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(card)
    db.session.commit()
    return redirect(url_for('dashboard_cards'))

@app.route('/dashboard/upload-interest', methods=['POST'])
@login_required
def upload_interest():
    category = request.form.get('category')
    title = request.form.get('title')
    caption = request.form.get('caption')
    file = request.files.get('image')

    if file and allowed_image(file.filename):
        filename = save_file(file)
        new_interest = Interest(
            category=category,
            title=title,
            caption=caption,
            image_filename=filename
        )
        db.session.add(new_interest)
        db.session.commit()

    return redirect(url_for('dashboard_cards'))

@app.route('/dashboard/delete-interest/<int:interest_id>', methods=['POST'])
@login_required
def delete_interest(interest_id):
    item = db.get_or_404(Interest, interest_id)
    if item.image_filename and not item.image_filename.startswith('http'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], item.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('dashboard_cards'))

@app.route('/dashboard/post/upload', methods=['POST'])
@login_required
def upload_media():
    caption = request.form.get('caption', '')
    file = request.files.get('file')

    filename = "none"
    media_type = "text"

    if file and file.filename != '':
        detected_type = get_media_type(file.filename)
        if detected_type:
            media_type = detected_type
            filename = save_file(file)

    if caption or filename != "none":
        new_upload = MediaUpload(
            title="Status Update",
            caption=caption,
            badge="Post",
            filename=filename,
            media_type=media_type,
            created_at=datetime.utcnow()
        )
        db.session.add(new_upload)
        db.session.commit()
        flash('Media posted successfully!')

    return redirect(url_for('dashboard_post'))

@app.route('/dashboard/post/delete/<int:upload_id>', methods=['POST'])
@login_required
def delete_media(upload_id):
    upload = db.get_or_404(MediaUpload, upload_id)
    if upload.filename and upload.filename != 'none' and not upload.filename.startswith('http'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(upload)
    db.session.commit()
    flash('Post deleted successfully!')
    return redirect(url_for('dashboard_post'))

# Enable Vercel serverless execution
app_handler = app

if __name__ == '__main__':
    app.run(debug=True)