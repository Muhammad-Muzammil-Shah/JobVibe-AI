"""
Flask Routes and Authentication for AI Job Application System
"""
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
import os
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from models import db, User, Company, Candidate, Job, Application, Interview, InterviewQuestion, CandidateResult, ActivityLog, Notification
from ai_engine import AIEngine, ResumeParser

# Import independent analyzer modules
from resume_analyzer import analyze_resume
from video_processor import process_interview_video
from answer_analyzer import evaluate_knowledge
from communication_analyzer import analyze_communication
from confidence_analyzer import analyze_confidence

# Create Blueprints
auth_bp = Blueprint('auth', __name__)
main_bp = Blueprint('main', __name__)
company_bp = Blueprint('company', __name__, url_prefix='/company')
candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidate')
interview_bp = Blueprint('interview', __name__, url_prefix='/interview')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Utility Functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'doc', 'docx'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_uploaded_file(file, folder_type='resumes'):
    """Save uploaded file and return path"""
    if folder_type == 'resumes':
        upload_folder = current_app.config.get('RESUME_FOLDER', 'uploads/resumes')
    else:
        upload_folder = current_app.config.get('VIDEO_FOLDER', 'uploads/videos')
    
    os.makedirs(upload_folder, exist_ok=True)
    
    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}_{filename}"
    filepath = os.path.join(upload_folder, unique_filename)
    file.save(filepath)
    return filepath


def company_required(f):
    """Decorator to require company role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Company':
            flash('Access denied. Company account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def candidate_required(f):
    """Decorator to require candidate role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Candidate':
            flash('Access denied. Candidate account required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def log_activity(action, entity_type=None, entity_id=None, details=None):
    """Log user activity"""
    try:
        log = ActivityLog(
            user_id=current_user.user_id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Logging error: {e}")


# ==================== AUTH ROUTES ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.main_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        
        # Validation
        if not all([email, password, role]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('auth/register.html')
        
        if role not in ['Company', 'Candidate']:
            flash('Invalid role selected.', 'danger')
            return render_template('auth/register.html')
        
        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')
        
        # Create user
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user_id
        
        # Create profile based on role
        if role == 'Company':
            company_name = request.form.get('company_name', '')
            industry = request.form.get('industry', '')
            company = Company(
                user_id=user.user_id,
                company_name=company_name,
                industry=industry
            )
            db.session.add(company)
        else:
            full_name = request.form.get('full_name', '')
            candidate = Candidate(
                user_id=user.user_id,
                full_name=full_name
            )
            db.session.add(candidate)
        
        db.session.commit()
        log_activity('User registered', 'User', user.user_id)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.main_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember', False))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Account is deactivated. Contact support.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            log_activity('User logged in', 'User', user.user_id)
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.main_dashboard'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    log_activity('User logged out', 'User', current_user.user_id)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


# ==================== SEPARATE AUTH ROUTES ====================

@auth_bp.route('/company/login', methods=['GET', 'POST'])
def company_login():
    """HR/Company Login"""
    if current_user.is_authenticated:
        if current_user.role == 'Company':
            return redirect(url_for('company.company_dashboard'))
        return redirect(url_for('candidate.candidate_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember', False))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role != 'Company':
                flash('This account is registered as a Candidate. Please use Candidate Login.', 'warning')
                return redirect(url_for('auth.candidate_login'))
            
            login_user(user, remember=remember)
            log_activity('Company User logged in', 'User', user.user_id)
            return redirect(url_for('company.company_dashboard'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/company/login.html')


@auth_bp.route('/company/register', methods=['GET', 'POST'])
def company_register():
    """Company Registration"""
    if current_user.is_authenticated:
        return redirect(url_for('company.company_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = 'Company'
        
        # Validation checks
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/company/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/company/register.html')
            
        # Create user
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create Company profile
        company = Company(
            user_id=user.user_id,
            company_name=request.form.get('company_name', ''),
            industry=request.form.get('industry', '')
        )
        db.session.add(company)
        db.session.commit()
        
        log_activity('New Company registered', 'Company', company.company_id)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.company_login'))
        
    return render_template('auth/company/register.html')


@auth_bp.route('/candidate/login', methods=['GET', 'POST'])
def candidate_login():
    """Candidate Login"""
    if current_user.is_authenticated:
        if current_user.role == 'Candidate':
            return redirect(url_for('candidate.candidate_dashboard'))
        return redirect(url_for('company.company_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember', False))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.role != 'Candidate':
                flash('This account is registered as a Company. Please use HR Login.', 'warning')
                return redirect(url_for('auth.company_login'))
            
            login_user(user, remember=remember)
            log_activity('Candidate logged in', 'User', user.user_id)
            return redirect(url_for('candidate.candidate_dashboard'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/candidate/login.html')


@auth_bp.route('/candidate/register', methods=['GET', 'POST'])
def candidate_register():
    """Candidate Registration"""
    if current_user.is_authenticated:
        return redirect(url_for('candidate.candidate_dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = 'Candidate'
        
        # Validation checks
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/candidate/register.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/candidate/register.html')
            
        # Create user
        user = User(email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        # Create Candidate profile
        candidate = Candidate(
            user_id=user.user_id,
            full_name=request.form.get('full_name', '')
        )
        db.session.add(candidate)
        db.session.commit()
        
        log_activity('New Candidate registered', 'Candidate', candidate.candidate_id)
        flash('Registration successful! Please login to your portal.', 'success')
        return redirect(url_for('auth.candidate_login'))
        
    return render_template('auth/candidate/register.html')


# ==================== MAIN ROUTES ====================

@main_bp.route('/')
def index():
    """Homepage"""
    # Get featured jobs
    featured_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(6).all()
    
    # Stats
    stats = {
        'total_jobs': Job.query.filter_by(is_active=True).count(),
        'total_companies': Company.query.count(),
        'total_candidates': Candidate.query.count()
    }
    
    return render_template('main/index.html', featured_jobs=featured_jobs, stats=stats)


@main_bp.route('/dashboard')
@login_required
def main_dashboard():
    """Redirect to role-specific dashboard"""
    if current_user.role == 'Company':
        return redirect(url_for('company.company_dashboard'))
    else:
        return redirect(url_for('candidate.candidate_dashboard'))


@main_bp.route('/jobs')
def main_jobs():
    """Browse all jobs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    job_type = request.args.get('job_type', '')
    
    query = Job.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(
            (Job.title.ilike(f'%{search}%')) | 
            (Job.description.ilike(f'%{search}%')) |
            (Job.skills_required.ilike(f'%{search}%'))
        )
    
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    
    if job_type:
        query = query.filter_by(job_type=job_type)
    
    jobs = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=10)
    
    return render_template('main/jobs.html', jobs=jobs, search=search, location=location, job_type=job_type)


@main_bp.route('/job/<int:job_id>')
def job_detail(job_id):
    """Job detail page"""
    job = Job.query.get_or_404(job_id)
    
    # Check if current user has already applied
    has_applied = False
    if current_user.is_authenticated and current_user.role == 'Candidate':
        has_applied = Application.query.filter_by(
            job_id=job_id, 
            candidate_id=current_user.candidate.candidate_id
        ).first() is not None
    
    return render_template('main/job_detail.html', job=job, has_applied=has_applied)


# ==================== COMPANY ROUTES ====================

@company_bp.route('/dashboard')
@login_required
@company_required
def company_dashboard():
    """Company dashboard"""
    company = current_user.company
    
    # Get stats
    total_jobs = company.jobs.count()
    active_jobs = company.jobs.filter_by(is_active=True).count()
    
    # Get recent applications
    recent_applications = Application.query.join(Job).filter(
        Job.company_id == company.company_id
    ).order_by(Application.applied_at.desc()).limit(10).all()
    
    # Application stats
    total_applications = Application.query.join(Job).filter(
        Job.company_id == company.company_id
    ).count()
    
    shortlisted = Application.query.join(Job).filter(
        Job.company_id == company.company_id,
        Application.status == 'Shortlisted'
    ).count()
    
    return render_template('company/dashboard.html', 
        company=company,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        shortlisted=shortlisted,
        recent_applications=recent_applications
    )


@company_bp.route('/dashboard/bulk-interview', methods=['POST'])
@login_required
@company_required
def dashboard_bulk_interview():
    """
    Send interview invitations from dashboard.
    This route handles bulk interview creation with AI-generated questions
    based on each candidate's resume and the specific job description.
    """
    company = current_user.company
    
    # Get selected application IDs from form
    selected_app_ids = request.form.getlist('selected_applications')
    
    if not selected_app_ids:
        flash('Please select at least one candidate.', 'warning')
        return redirect(url_for('company.company_dashboard'))
    
    success_count = 0
    error_count = 0
    interview_results = []
    
    for app_id in selected_app_ids:
        try:
            application = Application.query.get(int(app_id))
            
            if not application:
                error_count += 1
                continue
            
            # Verify this application belongs to company's job
            if application.job.company_id != company.company_id:
                error_count += 1
                continue
            
            # Skip if already has interview
            if application.interview:
                continue
            
            job = application.job
            
            # Update status to Interview
            application.status = 'Interview'
            
            # Extract resume text for question generation
            resume_text = ""
            if application.resume_path and application.resume_path != "no_resume_uploaded":
                from ai_engine import ResumeParser
                resume_text = ResumeParser.extract_text_from_pdf(application.resume_path)
            
            # Create interview with 1 week validity
            interview_code = Interview.generate_interview_code()
            otp_code = Interview.generate_otp()
            expires_at = datetime.utcnow() + timedelta(days=7)
            
            interview = Interview(
                app_id=application.app_id,
                interview_code=interview_code,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(interview)
            db.session.flush()
            
            # Generate AI interview questions using Grok API
            ai_engine = AIEngine(current_app.config.get('GROQ_API_KEY'))
            num_questions = current_app.config.get('QUESTIONS_PER_INTERVIEW', 10)
            
            # Build comprehensive job context for question generation
            job_context = f"""
📋 JOB TITLE: {job.title}

📝 JOB DESCRIPTION:
{job.description or 'Not specified'}

✅ REQUIREMENTS:
{job.requirements or 'Not specified'}

💼 RESPONSIBILITIES:
{job.responsibilities or 'Not specified'}

🛠️ SKILLS REQUIRED:
{job.skills_required or 'Not specified'}

📚 EDUCATION REQUIRED:
{job.education_required or 'Not specified'}

⏰ EXPERIENCE REQUIRED:
{job.experience_required or 'Not specified'}
"""
            
            # Generate questions using candidate's resume + job description
            questions = ai_engine.prepare_interview(
                resume_text,
                job_context,
                job.requirements or '',
                num_questions
            )
            
            # Save questions to database
            for i, q in enumerate(questions):
                question = InterviewQuestion(
                    interview_id=interview.interview_id,
                    question_text=q.get('question', ''),
                    question_type=q.get('type', 'Technical'),
                    expected_keywords=','.join(q.get('expected_keywords', [])),
                    difficulty=q.get('difficulty', 'Medium'),
                    question_order=i + 1,
                    time_limit_seconds=current_app.config.get('MAX_ANSWER_TIME_SECONDS', 120)
                )
                db.session.add(question)
            
            # Create notification for candidate
            notification = Notification(
                user_id=application.candidate.user_id,
                notification_type='interview_invite',
                title=f'🎉 Interview Invitation: {job.title}',
                message=f'Congratulations! You have been shortlisted for an interview for the {job.title} position at {company.company_name}. Your Interview ID is: {interview_code}. This invitation is valid for 7 days.',
                related_entity_type='Interview',
                related_entity_id=interview.interview_id,
                interview_code=interview_code,
                expires_at=expires_at
            )
            db.session.add(notification)
            
            interview_results.append({
                'candidate': application.candidate.full_name,
                'job': job.title,
                'code': interview_code,
                'questions_generated': len(questions)
            })
            success_count += 1
            
            log_activity(f'Sent interview invitation from dashboard', 'Application', application.app_id, 
                        details=f'Interview Code: {interview_code}, Questions: {len(questions)}')
            
        except Exception as e:
            print(f"Error processing application {app_id}: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            error_count += 1
            continue
    
    db.session.commit()
    
    if success_count > 0:
        flash(f'✅ Successfully sent interview invitations to {success_count} candidate(s)! AI-generated questions based on resume & job description.', 'success')
    
    if error_count > 0:
        flash(f'⚠️ {error_count} candidate(s) could not be processed.', 'warning')
    
    return redirect(url_for('company.company_dashboard'))


@company_bp.route('/jobs')
@login_required
@company_required
def jobs():
    """List company's jobs"""
    jobs = current_user.company.jobs.order_by(Job.created_at.desc()).all()
    return render_template('company/jobs.html', jobs=jobs)


@company_bp.route('/job/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_job():
    """Create new job posting"""
    if request.method == 'POST':
        # Build salary range display string
        salary_min = request.form.get('salary_min')
        salary_max = request.form.get('salary_max')
        salary_currency = request.form.get('salary_currency', 'PKR')
        
        salary_range = None
        if salary_min and salary_max:
            salary_range = f"{salary_currency} {int(salary_min):,} - {int(salary_max):,} per month"
        
        # Build description from overview + description
        overview = request.form.get('overview', '').strip()
        description = request.form.get('description', '').strip()
        full_description = overview
        if description:
            full_description = f"{overview}\n\n{description}" if overview else description
        
        job = Job(
            company_id=current_user.company.company_id,
            title=request.form.get('title'),
            overview=overview,
            description=full_description or request.form.get('responsibilities', ''),
            requirements=request.form.get('requirements'),
            preferred_qualifications=request.form.get('preferred_qualifications'),
            responsibilities=request.form.get('responsibilities'),
            location=request.form.get('location'),
            work_mode=request.form.get('work_mode', 'Onsite'),
            job_type=request.form.get('job_type', 'Full-time'),
            experience_required=request.form.get('experience_required'),
            education_required=request.form.get('education_required'),
            salary_min=int(salary_min) if salary_min else None,
            salary_max=int(salary_max) if salary_max else None,
            salary_currency=salary_currency,
            salary_range=salary_range,
            working_hours=request.form.get('working_hours'),
            working_days=request.form.get('working_days'),
            skills_required=request.form.get('skills_required'),
            is_active=request.form.get('is_active', '1') == '1'
        )
        
        deadline = request.form.get('deadline')
        if deadline:
            job.deadline = datetime.strptime(deadline, '%Y-%m-%d')
        
        db.session.add(job)
        db.session.commit()
        
        log_activity('Created job posting', 'Job', job.job_id)
        flash('Job posted successfully! 🎉', 'success')
        return redirect(url_for('company.jobs'))
    
    return render_template('company/create_job.html')


@company_bp.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_job(job_id):
    """Edit job posting"""
    job = Job.query.get_or_404(job_id)
    
    # Verify ownership
    if job.company_id != current_user.company.company_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.jobs'))
    
    if request.method == 'POST':
        # Build salary range display string
        salary_min = request.form.get('salary_min')
        salary_max = request.form.get('salary_max')
        salary_currency = request.form.get('salary_currency', 'PKR')
        
        salary_range = None
        if salary_min and salary_max:
            salary_range = f"{salary_currency} {int(salary_min):,} - {int(salary_max):,} per month"
        
        # Build description from overview + description
        overview = request.form.get('overview', '').strip()
        description = request.form.get('description', '').strip()
        full_description = overview
        if description:
            full_description = f"{overview}\n\n{description}" if overview else description
        
        job.title = request.form.get('title')
        job.overview = overview
        job.description = full_description or request.form.get('responsibilities', '')
        job.requirements = request.form.get('requirements')
        job.preferred_qualifications = request.form.get('preferred_qualifications')
        job.responsibilities = request.form.get('responsibilities')
        job.location = request.form.get('location')
        job.work_mode = request.form.get('work_mode', 'Onsite')
        job.job_type = request.form.get('job_type')
        job.experience_required = request.form.get('experience_required')
        job.education_required = request.form.get('education_required')
        job.salary_min = int(salary_min) if salary_min else None
        job.salary_max = int(salary_max) if salary_max else None
        job.salary_currency = salary_currency
        job.salary_range = salary_range
        job.working_hours = request.form.get('working_hours')
        job.working_days = request.form.get('working_days')
        job.skills_required = request.form.get('skills_required')
        job.is_active = request.form.get('is_active') == '1'
        
        deadline = request.form.get('deadline')
        if deadline:
            job.deadline = datetime.strptime(deadline, '%Y-%m-%d')
        else:
            job.deadline = None
        
        db.session.commit()
        log_activity('Updated job posting', 'Job', job.job_id)
        flash('Job updated successfully! ✅', 'success')
        return redirect(url_for('company.jobs'))
    
    return render_template('company/edit_job.html', job=job)


@company_bp.route('/job/<int:job_id>/applications')
@login_required
@company_required
def job_applications(job_id):
    """View applications for a job"""
    job = Job.query.get_or_404(job_id)
    
    if job.company_id != current_user.company.company_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.jobs'))
    
    status_filter = request.args.get('status', '')
    
    query = job.applications
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    applications = query.order_by(Application.ai_resume_score.desc()).all()
    
    return render_template('company/applications.html', job=job, applications=applications, status_filter=status_filter)


@company_bp.route('/application/<int:app_id>')
@login_required
@company_required
def company_view_application(app_id):
    """View application details"""
    application = Application.query.get_or_404(app_id)
    
    if application.job.company_id != current_user.company.company_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.company_dashboard'))
    
    # Get interview results if available
    result = None
    if application.interview and application.interview.result:
        result = application.interview.result
    
    return render_template('company/view_application.html', application=application, result=result)


@company_bp.route('/application/<int:app_id>/decision', methods=['POST'])
@login_required
@company_required
def make_decision(app_id):
    """Make HR decision on application"""
    application = Application.query.get_or_404(app_id)
    
    if application.job.company_id != current_user.company.company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    decision = request.form.get('decision')
    notes = request.form.get('notes', '')
    
    if application.interview and application.interview.result:
        result = application.interview.result
        result.hr_decision = decision
        result.hr_notes = notes
        result.decided_at = datetime.utcnow()
        result.decided_by = current_user.user_id
        
        # Update application status
        if decision == 'Selected':
            application.status = 'Hired'
        elif decision == 'Rejected':
            application.status = 'Rejected'
        
        db.session.commit()
        log_activity(f'Made HR decision: {decision}', 'Application', app_id)
        flash(f'Decision recorded: {decision}', 'success')
    else:
        flash('No interview results to make decision on.', 'warning')
    
    return redirect(url_for('company.company_view_application', app_id=app_id))


@company_bp.route('/analytics')
@login_required
@company_required
def analytics():
    """Company analytics dashboard"""
    company = current_user.company
    
    # Get all applications for company's jobs
    applications = Application.query.join(Job).filter(
        Job.company_id == company.company_id
    ).all()
    
    # Calculate analytics
    analytics = {
        'total_applications': len(applications),
        'avg_resume_score': sum(a.ai_resume_score for a in applications) / len(applications) if applications else 0,
        'status_breakdown': {},
        'jobs_performance': []
    }
    
    # Status breakdown
    for app in applications:
        analytics['status_breakdown'][app.status] = analytics['status_breakdown'].get(app.status, 0) + 1
    
    # Job performance
    for job in company.jobs:
        job_apps = job.applications.all()
        analytics['jobs_performance'].append({
            'title': job.title,
            'applications': len(job_apps),
            'avg_score': sum(a.ai_resume_score for a in job_apps) / len(job_apps) if job_apps else 0,
            'shortlisted': sum(1 for a in job_apps if a.status == 'Shortlisted')
        })
    
    return render_template('company/analytics.html', analytics=analytics)


@company_bp.route('/job/<int:job_id>/bulk-shortlist', methods=['POST'])
@login_required
@company_required
def bulk_shortlist(job_id):
    """
    Bulk shortlist candidates and call for interview.
    HR selects multiple candidates using checkboxes and clicks 'Call for Interview'.
    """
    job = Job.query.get_or_404(job_id)
    
    # Verify ownership
    if job.company_id != current_user.company.company_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.jobs'))
    
    # Get selected application IDs from form
    selected_app_ids = request.form.getlist('selected_applications')
    
    if not selected_app_ids:
        flash('Please select at least one candidate.', 'warning')
        return redirect(url_for('company.job_applications', job_id=job_id))
    
    shortlisted_count = 0
    interview_codes = []
    
    for app_id in selected_app_ids:
        try:
            application = Application.query.get(int(app_id))
            
            if not application or application.job_id != job_id:
                continue
            
            # Skip if already has interview
            if application.interview:
                continue
            
            # Update status to Interview
            application.status = 'Interview'
            
            # Extract resume text for question generation
            resume_text = ""
            if application.resume_path and application.resume_path != "no_resume_uploaded":
                from ai_engine import ResumeParser
                resume_text = ResumeParser.extract_text_from_pdf(application.resume_path)
            
            # Create interview with 1 week validity
            interview_code = Interview.generate_interview_code()
            otp_code = Interview.generate_otp()  # Generate unique OTP for legacy compatibility
            expires_at = datetime.utcnow() + timedelta(days=7)  # 1 week validity as per requirements
            
            interview = Interview(
                app_id=application.app_id,
                interview_code=interview_code,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(interview)
            db.session.flush()
            
            # Generate AI interview questions
            ai_engine = AIEngine(current_app.config.get('GROQ_API_KEY'))
            num_questions = current_app.config.get('QUESTIONS_PER_INTERVIEW', 10)
            
            # Build comprehensive job context for question generation
            job_context = f"""
📋 JOB DESCRIPTION:
{job.description or ''}

✅ REQUIREMENTS:
{job.requirements or ''}

💼 RESPONSIBILITIES:
{job.responsibilities or ''}

🛠️ SKILLS REQUIRED:
{job.skills_required or ''}
"""
            
            questions = ai_engine.prepare_interview(
                resume_text,
                job_context,
                job.requirements or '',
                num_questions
            )
            
            # Save questions to database
            for i, q in enumerate(questions):
                question = InterviewQuestion(
                    interview_id=interview.interview_id,
                    question_text=q.get('question', ''),
                    question_type=q.get('type', 'Technical'),
                    expected_keywords=','.join(q.get('expected_keywords', [])),
                    difficulty=q.get('difficulty', 'Medium'),
                    question_order=i + 1,
                    time_limit_seconds=current_app.config.get('MAX_ANSWER_TIME_SECONDS', 120)
                )
                db.session.add(question)
            
            # Create notification for candidate
            notification = Notification(
                user_id=application.candidate.user_id,
                notification_type='interview_invite',
                title=f'🎉 Interview Invitation: {job.title}',
                message=f'Congratulations! You have been shortlisted for an interview for the {job.title} position at {job.company.company_name}. Your Interview ID is: {interview_code}. This invitation is valid for 7 days.',
                related_entity_type='Interview',
                related_entity_id=interview.interview_id,
                interview_code=interview_code,
                expires_at=expires_at
            )
            db.session.add(notification)
            
            interview_codes.append({
                'candidate': application.candidate.full_name,
                'code': interview_code
            })
            shortlisted_count += 1
            
            log_activity(f'Shortlisted for interview', 'Application', application.app_id, 
                        details=f'Interview Code: {interview_code}')
            
        except Exception as e:
            print(f"Error shortlisting application {app_id}: {e}")
            continue
    
    db.session.commit()
    
    if shortlisted_count > 0:
        flash(f'✅ Successfully called {shortlisted_count} candidate(s) for interview!', 'success')
    else:
        flash('No new candidates were shortlisted. They may already have pending interviews.', 'warning')
    
    return redirect(url_for('company.job_applications', job_id=job_id))


@company_bp.route('/job/<int:job_id>/calculate-percentiles', methods=['POST'])
@login_required
@company_required
def calculate_percentiles(job_id):
    """Calculate and update percentile rankings for all applicants of a job"""
    job = Job.query.get_or_404(job_id)
    
    if job.company_id != current_user.company.company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get all completed interviews with results for this job
    applications = Application.query.filter_by(job_id=job_id).all()
    
    # Collect all overall scores
    all_scores = []
    results_to_update = []
    
    for app in applications:
        if app.interview and app.interview.result:
            result = app.interview.result
            all_scores.append(result.overall_score)
            results_to_update.append(result)
    
    # Calculate percentiles using simple calculation
    def calculate_percentile(score, all_scores):
        """Calculate percentile rank for a score"""
        if not all_scores or len(all_scores) == 0:
            return 0
        count_below = sum(1 for s in all_scores if s < score)
        return round((count_below / len(all_scores)) * 100, 2)
    
    for result in results_to_update:
        percentile = calculate_percentile(result.overall_score, all_scores)
        result.overall_percentile = percentile
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'updated': len(results_to_update),
        'message': f'Percentiles calculated for {len(results_to_update)} candidates'
    })


@company_bp.route('/job/<int:job_id>/reject-unselected', methods=['POST'])
@login_required
@company_required
def reject_unselected(job_id):
    """Reject all candidates who have not been selected for interview (status: Applied)"""
    job = Job.query.get_or_404(job_id)
    
    if job.company_id != current_user.company.company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Find all applications with status 'Applied' (not yet called for interview)
    applications_to_reject = Application.query.filter_by(
        job_id=job_id,
        status='Applied'
    ).all()
    
    rejected_count = 0
    for app in applications_to_reject:
        # Only reject if no interview exists
        if not app.interview:
            app.status = 'Rejected'
            rejected_count += 1
            log_activity('Application rejected (bulk)', 'Application', app.app_id,
                        details=f'Rejected by HR bulk action')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rejected': rejected_count,
        'message': f'Successfully rejected {rejected_count} candidates who were not selected for interview.'
    })


# ==================== CANDIDATE ROUTES ====================


@candidate_bp.route('/dashboard')
@login_required
@candidate_required
def candidate_dashboard():
    """Candidate dashboard"""
    candidate = current_user.candidate
    
    # Get applications
    applications = candidate.applications.order_by(Application.applied_at.desc()).all()
    
    # Get unread notifications (interview invitations)
    notifications = Notification.query.filter_by(
        user_id=current_user.user_id,
        is_read=False
    ).order_by(Notification.created_at.desc()).all()
    
    # Get all notifications for display
    all_notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get stats
    stats = {
        'total_applications': len(applications),
        'shortlisted': sum(1 for a in applications if a.status == 'Shortlisted'),
        'interviews_pending': sum(1 for a in applications if a.interview and not a.interview.is_completed),
        'avg_resume_score': sum(a.ai_resume_score for a in applications) / len(applications) if applications else 0,
        'unread_notifications': len(notifications)
    }
    
    return render_template('candidate/dashboard.html', 
        candidate=candidate, 
        applications=applications,
        stats=stats,
        notifications=all_notifications,
        unread_count=len(notifications)
    )


@candidate_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@candidate_required
def profile():
    """Update candidate profile"""
    candidate = current_user.candidate
    
    if request.method == 'POST':
        candidate.full_name = request.form.get('full_name')
        candidate.phone = request.form.get('phone')
        candidate.linkedin_url = request.form.get('linkedin_url')
        candidate.portfolio_url = request.form.get('portfolio_url')
        candidate.skills = request.form.get('skills')
        candidate.experience_years = request.form.get('experience_years', type=int)
        candidate.education = request.form.get('education')
        candidate.bio = request.form.get('bio')
        
        # Handle resume upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filepath = save_uploaded_file(file, 'resumes')
                candidate.default_resume_path = filepath
        
        db.session.commit()
        log_activity('Updated profile', 'Candidate', candidate.candidate_id)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('candidate.profile'))
    
    return render_template('candidate/profile.html', candidate=candidate)


@candidate_bp.route('/notifications')
@login_required
@candidate_required
def notifications():
    """View all notifications"""
    all_notifications = Notification.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('candidate/notifications.html', notifications=all_notifications)


@candidate_bp.route('/notification/<int:notification_id>/read', methods=['POST'])
@login_required
@candidate_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})


@candidate_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@candidate_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.user_id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    
    return redirect(url_for('candidate.candidate_dashboard'))


@candidate_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
@candidate_required
def apply(job_id):
    """Apply for a job"""
    job = Job.query.get_or_404(job_id)
    candidate = current_user.candidate
    
    # Check if already applied
    existing = Application.query.filter_by(
        job_id=job_id, 
        candidate_id=candidate.candidate_id
    ).first()
    
    if existing:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('main.job_detail', job_id=job_id))
    
    if request.method == 'POST':
        print(f"🔍 DEBUG: Apply POST received for job {job_id}")
        print(f"🔍 DEBUG: Candidate ID: {candidate.candidate_id}, Name: {candidate.full_name}")
        
        # Handle resume - NOW OPTIONAL
        resume_path = None
        if 'resume' in request.files and request.files['resume'].filename:
            file = request.files['resume']
            print(f"🔍 DEBUG: Resume file uploaded: {file.filename}")
            if allowed_file(file.filename):
                resume_path = save_uploaded_file(file, 'resumes')
                print(f"🔍 DEBUG: Resume saved to: {resume_path}")
        
        if not resume_path:
            resume_path = candidate.default_resume_path
            print(f"🔍 DEBUG: Using default resume: {resume_path}")
        
        # Resume is now optional - use placeholder if none
        if not resume_path:
            resume_path = "no_resume_uploaded"
            print("⚠️ DEBUG: No resume - using placeholder")
        
        try:
            # === AI RESUME SCORING (Using Independent Module with GROQ) ===
            ai_score = 50.0  # Default score if no resume
            resume_analysis = {}
            
            if resume_path and resume_path != "no_resume_uploaded":
                print(f"🤖 AI: Analyzing resume using GROQ-powered resume_analyzer...")
                try:
                    # Build job data with 4 key sections for AI analysis
                    # 📋 Job Description, ✅ Requirements, 💼 Responsibilities, 🛠️ Skills Required
                    job_data = {
                        'description': job.description or "",
                        'requirements': job.requirements or "",
                        'responsibilities': job.responsibilities or "",
                        'skills_required': job.skills_required or ""
                    }
                    
                    # Use AI-powered analysis with job context
                    result = analyze_resume(
                        resume_path,
                        job_data=job_data,
                        api_key=current_app.config.get('GROQ_API_KEY')
                    )
                    
                    if result['status'] == 'success':
                        ai_score = result['score']
                        resume_analysis = result['analysis']
                        print(f"✅ AI Resume Score: {ai_score}%")
                        if resume_analysis.get('ai_powered'):
                            print(f"   🤖 AI-Powered Analysis")
                            print(f"   - Matched Skills: {len(resume_analysis.get('matched_skills', []))}")
                            print(f"   - Missing Skills: {len(resume_analysis.get('missing_skills', []))}")
                            print(f"   - Recommendation: {resume_analysis.get('recommendation', 'N/A')[:60]}...")
                        else:
                            print(f"   📊 Fallback TF-IDF Analysis")
                            print(f"   - Matched Skills: {len(resume_analysis.get('matched_skills', []))}")
                    else:
                        print(f"⚠️ Resume analysis failed: {result.get('error')}")
                        ai_score = 55.0
                except Exception as e:
                    print(f"⚠️ AI scoring error: {e}, using default score")
                    ai_score = 55.0
            else:
                print("⚠️ No resume provided, using minimum score")
                ai_score = 40.0
            
            # Create application - NO interview yet (HR will select candidates)
            print(f"✅ DEBUG: Creating application with AI Score: {ai_score}%")
            application = Application(
                job_id=job_id,
                candidate_id=candidate.candidate_id,
                resume_path=resume_path,
                cover_letter=request.form.get('cover_letter', ''),
                status='Applied',  # Pending HR review - NOT auto-shortlisted
                ai_resume_score=round(ai_score, 1),  # AI calculated score
                resume_analysis=json.dumps(resume_analysis) if resume_analysis else None
            )
            db.session.add(application)
            db.session.flush()
            print(f"✅ DEBUG: Application created with ID: {application.app_id}")
            
            # NOTE: Interview is NOT created here anymore
            # HR will use "Call for Interview" button to assign interview IDs to selected candidates
            
            db.session.commit()
            log_activity('Applied for job', 'Application', application.app_id)
            
            flash(f'✅ Application submitted successfully! Please wait for HR to review your application.', 'success')
            return redirect(url_for('candidate.candidate_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR: {e}")
            flash(f'Error submitting application. Please try again.', 'danger')
            return render_template('candidate/apply.html', job=job)
    
    return render_template('candidate/apply.html', job=job)


def create_interview_for_application(application, resume_text, job):
    """Create interview and generate questions for shortlisted candidate"""
    try:
        # Create interview with unique Interview Code
        interview_code = Interview.generate_interview_code()
        otp_code = Interview.generate_otp()  # Generate unique OTP for legacy compatibility
        
        interview = Interview(
            app_id=application.app_id,
            interview_code=interview_code,
            otp_code=otp_code,
            expires_at=datetime.utcnow() + timedelta(days=7)  # 7-day validity
        )
        db.session.add(interview)
        db.session.flush()
        
        # Generate questions using AI
        ai_engine = AIEngine(current_app.config.get('GROQ_API_KEY'))
        num_questions = current_app.config.get('QUESTIONS_PER_INTERVIEW', 10)
        
        # Build comprehensive job context for question generation
        job_context = f"""
📋 JOB DESCRIPTION:
{job.description or ''}

✅ REQUIREMENTS:
{job.requirements or ''}

💼 RESPONSIBILITIES:
{job.responsibilities or ''}

🛠️ SKILLS REQUIRED:
{job.skills_required or ''}
"""
        
        questions = ai_engine.prepare_interview(
            resume_text, 
            job_context, 
            job.requirements or '',
            num_questions
        )
        
        # Save questions
        for i, q in enumerate(questions):
            question = InterviewQuestion(
                interview_id=interview.interview_id,
                question_text=q.get('question', ''),
                question_type=q.get('type', 'Technical'),
                expected_keywords=','.join(q.get('expected_keywords', [])),
                difficulty=q.get('difficulty', 'Medium'),
                question_order=i + 1,
                time_limit_seconds=current_app.config.get('MAX_ANSWER_TIME_SECONDS', 120)
            )
            db.session.add(question)
        
        db.session.commit()
        print(f"✅ Interview created! Code: {interview.interview_code} | Candidate: {application.candidate.full_name} | Position: {job.title}")
        return interview
        
    except Exception as e:
        print(f"Interview creation error: {e}")
        db.session.rollback()
        return None


@candidate_bp.route('/application/<int:app_id>')
@login_required
@candidate_required
def candidate_view_application(app_id):
    """View application status and details"""
    application = Application.query.get_or_404(app_id)
    
    if application.candidate_id != current_user.candidate.candidate_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('candidate.candidate_dashboard'))
    
    return render_template('candidate/view_application.html', application=application)


# ==================== INTERVIEW ROUTES ====================

@interview_bp.route('/verify', methods=['GET', 'POST'])
def verify_otp():
    """Verify Interview ID + Candidate Name + Position to start interview"""
    if request.method == 'POST':
        interview_code = request.form.get('interview_code', '').strip().upper()
        candidate_name = request.form.get('candidate_name', '').strip()
        position = request.form.get('position', '').strip().lower()
        
        # Find interview by code
        interview = Interview.query.filter_by(interview_code=interview_code).first()
        
        # Also check legacy otp_code field for backward compatibility
        if not interview:
            flash('Invalid Interview ID. Please check your email for the correct ID.', 'danger')
            return render_template('interview/verify.html')
        
        # Verify candidate name matches (flexible matching)
        application = interview.application
        actual_name = application.candidate.full_name.lower().strip()
        entered_name = candidate_name.lower().strip()
        
        # Check if names match (either substring or significant word overlap)
        actual_words = set(actual_name.split())
        entered_words = set(entered_name.split())
        common_words = actual_words & entered_words
        
        # Match if: substring match OR at least one significant word matches (length > 2)
        significant_match = any(len(w) > 2 for w in common_words)
        substring_match = entered_name in actual_name or actual_name in entered_name
        
        if not substring_match and not significant_match:
            flash('Candidate name does not match our records.', 'danger')
            return render_template('interview/verify.html')
        
        # Verify position matches
        actual_position = application.job.title.lower()
        if position not in actual_position and actual_position not in position:
            flash('Position does not match the job you applied for.', 'danger')
            return render_template('interview/verify.html')
        
        if interview.is_expired:
            flash('This interview link has expired. Please contact the company.', 'danger')
            return render_template('interview/verify.html')
        
        if interview.is_completed:
            flash('This interview has already been completed.', 'warning')
            return render_template('interview/verify.html')
        
        # All verified - Store interview ID in session
        session['interview_id'] = interview.interview_id
        session['verified_candidate'] = application.candidate.full_name
        return redirect(url_for('interview.start'))
    
    return render_template('interview/verify.html')


@interview_bp.route('/start')
def start():
    """Start interview after OTP verification"""
    interview_id = session.get('interview_id')
    
    if not interview_id:
        flash('Please verify your OTP first.', 'warning')
        return redirect(url_for('interview.verify_otp'))
    
    interview = Interview.query.get_or_404(interview_id)
    
    if interview.is_completed:
        return redirect(url_for('interview.completed', interview_id=interview_id))
    
    # Get candidate and job info
    application = interview.application
    candidate = application.candidate
    job = application.job
    
    # Get questions - generate if none exist
    questions = interview.questions.order_by(InterviewQuestion.question_order).all()
    
    if not questions:
        # Generate questions using AI
        try:
            from ai_engine import ai_engine
            # Read resume for context
            resume_text = ""
            if application.resume_path and os.path.exists(application.resume_path):
                resume_text = ai_engine.resume_scorer.parse_resume(application.resume_path)
            
            # Generate 10 questions as per requirements
            generated_questions = ai_engine.generate_interview_questions(
                job_title=job.title,
                job_description=job.description or job.overview or '',
                job_requirements=job.requirements or '',
                resume_text=resume_text,
                num_questions=10
            )
            
            # Save questions to database
            for i, q in enumerate(generated_questions):
                question = InterviewQuestion(
                    interview_id=interview.interview_id,
                    question_text=q.get('question', q) if isinstance(q, dict) else str(q),
                    question_type=q.get('type', 'Technical') if isinstance(q, dict) else 'Technical',
                    expected_keywords=q.get('keywords', '') if isinstance(q, dict) else '',
                    difficulty=q.get('difficulty', 'Medium') if isinstance(q, dict) else 'Medium',
                    question_order=i + 1
                )
                db.session.add(question)
            
            db.session.commit()
            questions = interview.questions.order_by(InterviewQuestion.question_order).all()
            print(f"✅ Generated {len(questions)} interview questions for Interview {interview.interview_code}")
        except Exception as e:
            print(f"❌ Error generating questions: {e}")
            # Create fallback questions
            fallback_questions = [
                "Tell me about yourself and your background.",
                f"Why are you interested in the {job.title} position?",
                "What relevant experience do you have for this role?",
                "Describe a challenging project you've worked on.",
                "How do you handle tight deadlines and pressure?",
                "What are your greatest strengths?",
                "Where do you see yourself in 5 years?",
                "Why should we hire you for this position?",
                "Do you have any questions about the role or company?",
                "Is there anything else you'd like us to know about you?"
            ]
            for i, q_text in enumerate(fallback_questions):
                question = InterviewQuestion(
                    interview_id=interview.interview_id,
                    question_text=q_text,
                    question_type='Behavioral' if i < 5 else 'General',
                    question_order=i + 1
                )
                db.session.add(question)
            db.session.commit()
            questions = interview.questions.order_by(InterviewQuestion.question_order).all()
    
    return render_template('interview/start.html', 
        interview=interview,
        candidate=candidate,
        job=job,
        questions=questions,
        total_questions=len(questions)
    )


@interview_bp.route('/room/<int:interview_id>')
def room(interview_id):
    """Interview room with camera and questions"""
    interview = Interview.query.get_or_404(interview_id)
    
    # Verify session
    if session.get('interview_id') != interview_id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('interview.verify_otp'))
    
    if interview.is_completed:
        return redirect(url_for('interview.completed', interview_id=interview_id))
    
    # Mark as started
    if not interview.started_at:
        interview.started_at = datetime.utcnow()
        db.session.commit()
    
    questions = interview.questions.order_by(InterviewQuestion.question_order).all()
    current_index = interview.current_question_index
    
    return render_template('interview/room.html',
        interview=interview,
        questions=questions,
        current_index=current_index,
        current_question=questions[current_index] if current_index < len(questions) else None
    )


@interview_bp.route('/completed/<int:interview_id>')
def completed(interview_id):
    """Interview completed page"""
    interview = Interview.query.get_or_404(interview_id)
    return render_template('interview/completed.html', interview=interview)


# ==================== API ROUTES ====================

@api_bp.route('/upload-answer', methods=['POST'])
def upload_answer():
    """Handle video answer upload - supports both single video and per-question"""
    interview_id = request.form.get('interview_id', type=int)
    is_complete_video = request.form.get('is_complete_video', 'false') == 'true'
    
    if not interview_id:
        return jsonify({'error': 'Missing interview_id'}), 400
    
    interview = Interview.query.get_or_404(interview_id)
    
    # Handle video file
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    video_file = request.files['video']
    if video_file.filename:
        # Save video
        upload_folder = current_app.config.get('VIDEO_FOLDER', 'uploads/videos')
        os.makedirs(upload_folder, exist_ok=True)
        
        if is_complete_video:
            # Single video for entire interview
            filename = f"interview_{interview_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.webm"
            filepath = os.path.join(upload_folder, filename)
            video_file.save(filepath)
            
            # Store in interview record
            interview.video_path = filepath
            interview.is_completed = True
            interview.completed_at = datetime.utcnow()
            
            # Mark all questions as answered
            for q in interview.questions.all():
                if not q.answered_at:
                    q.answered_at = datetime.utcnow()
            
            # Trigger analysis
            process_interview_analysis(interview_id)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'is_completed': True
            })
        else:
            # Legacy: per-question video
            question_id = request.form.get('question_id', type=int)
            if not question_id:
                return jsonify({'error': 'Missing question_id'}), 400
            
            question = InterviewQuestion.query.get_or_404(question_id)
            
            if question.interview_id != interview_id:
                return jsonify({'error': 'Invalid question'}), 400
            
            filename = f"answer_{interview_id}_{question_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.webm"
            filepath = os.path.join(upload_folder, filename)
            video_file.save(filepath)
            
            question.answer_video_path = filepath
            question.answered_at = datetime.utcnow()
            
            interview.current_question_index += 1
            
            total_questions = interview.questions.count()
            if interview.current_question_index >= total_questions:
                interview.is_completed = True
                interview.completed_at = datetime.utcnow()
                process_interview_analysis(interview_id)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'next_question': interview.current_question_index,
                'is_completed': interview.is_completed
            })
    
    return jsonify({'error': 'Invalid video file'}), 400


def process_interview_analysis(interview_id):
    """
    Process interview analysis using INDEPENDENT MODULES (all 4 pillars)
    
    Each module is independent and produces its own score:
    - Pillar 1: Resume Match (resume_analyzer.py) - Already calculated at application
    - Pillar 2: Confidence (confidence_analyzer.py) - Video analysis
    - Pillar 3: Communication (communication_analyzer.py) - Speech analysis
    - Pillar 4: Knowledge (answer_analyzer.py) - Answer evaluation
    
    Workflow:
    1. Process video → extract audio → get transcript (video_processor.py)
    2. Analyze video for confidence (confidence_analyzer.py)
    3. Analyze transcript for communication (communication_analyzer.py)
    4. Evaluate answers for knowledge (answer_analyzer.py)
    5. Store all results in database
    """
    try:
        interview = Interview.query.get(interview_id)
        if not interview:
            print(f"❌ Interview {interview_id} not found")
            return {'error': 'Interview not found'}
        
        application = interview.application
        job = application.job
        
        print(f"\n{'='*70}")
        print(f"🎯 STARTING MODULAR INTERVIEW ANALYSIS")
        print(f"   Interview ID: {interview_id}")
        print(f"   Candidate: {application.candidate.full_name}")
        print(f"   Job: {job.title}")
        print(f"{'='*70}")
        
        # Get all questions for this interview
        questions = list(interview.questions)
        print(f"📋 Total Questions: {len(questions)}")
        
        # Initialize result variables
        resume_score = application.ai_resume_score or 0
        confidence_score = 0
        communication_score = 0
        knowledge_score = 0
        transcript = ""
        video_duration = 0
        
        # Analysis detail storage
        confidence_detail = {}
        communication_detail = {}
        knowledge_detail = {}
        
        # Check for interview video
        video_path = interview.video_path
        
        if not video_path or not os.path.exists(video_path):
            print(f"\n⚠️ No interview video found at: {video_path}")
            print("   Setting default scores...")
            confidence_score = 0
            communication_score = 0
            knowledge_score = 0
        else:
            print(f"\n🎬 Video found: {video_path}")
            file_size = os.path.getsize(video_path) / (1024 * 1024)
            print(f"   File size: {file_size:.2f} MB")
            
            # ================================================================
            # MODULE 1: VIDEO PROCESSOR - Extract transcript
            # ================================================================
            print(f"\n{'='*50}")
            print("📹 MODULE 1: VIDEO PROCESSOR")
            print(f"{'='*50}")
            
            try:
                video_result = process_interview_video(video_path, keep_audio=False)
                
                if video_result['status'] == 'success':
                    transcript = video_result['transcript']
                    video_duration = video_result.get('video_duration', 0)
                    print(f"   ✅ Transcript extracted: {len(transcript)} characters")
                    print(f"   ✅ Video duration: {video_duration:.1f} seconds")
                else:
                    print(f"   ❌ Video processing failed: {video_result.get('error')}")
                    transcript = ""
                    
            except Exception as e:
                print(f"   ❌ Video processing error: {e}")
                transcript = ""
            
            # ================================================================
            # MODULE 2: CONFIDENCE ANALYZER - Analyze video
            # ================================================================
            print(f"\n{'='*50}")
            print("😊 MODULE 2: CONFIDENCE ANALYZER")
            print(f"{'='*50}")
            
            try:
                conf_result = analyze_confidence(video_path, sample_rate=30)
                
                if conf_result['status'] == 'success':
                    confidence_score = conf_result['score']
                    confidence_detail = {
                        'face_presence': conf_result.get('face_presence', 0),
                        'eye_contact': conf_result.get('eye_contact', 0),
                        'emotion_breakdown': conf_result.get('emotion_breakdown', {}),
                        'raw_analysis': conf_result.get('analysis_detail', '')
                    }
                    print(f"   ✅ Confidence Score: {confidence_score}%")
                else:
                    print(f"   ❌ Confidence analysis failed: {conf_result.get('error')}")
                    confidence_score = 0
                    confidence_detail = {'error': conf_result.get('error')}
                    
            except Exception as e:
                print(f"   ❌ Confidence analysis error: {e}")
                confidence_score = 0
                confidence_detail = {'error': str(e)}
            
            # ================================================================
            # MODULE 3: COMMUNICATION ANALYZER - Analyze speech
            # ================================================================
            print(f"\n{'='*50}")
            print("🎙️ MODULE 3: COMMUNICATION ANALYZER")
            print(f"{'='*50}")
            
            if transcript and len(transcript) > 20:
                try:
                    comm_result = analyze_communication(transcript, video_duration)
                    
                    if comm_result['status'] == 'success':
                        communication_score = comm_result['score']
                        communication_detail = {
                            'clarity': comm_result.get('clarity', {}),
                            'vocabulary': comm_result.get('vocabulary', {}),
                            'fluency': comm_result.get('fluency', {}),
                            'readability': comm_result.get('readability', {}),
                            'raw_analysis': comm_result.get('analysis_detail', '')
                        }
                        print(f"   ✅ Communication Score: {communication_score}%")
                    else:
                        print(f"   ❌ Communication analysis failed: {comm_result.get('error')}")
                        communication_score = 0
                        communication_detail = {'error': comm_result.get('error')}
                        
                except Exception as e:
                    print(f"   ❌ Communication analysis error: {e}")
                    communication_score = 0
                    communication_detail = {'error': str(e)}
            else:
                print("   ⚠️ No transcript available for communication analysis")
                communication_score = 0
                communication_detail = {'error': 'No transcript available'}
            
            # ================================================================
            # MODULE 4: ANSWER/KNOWLEDGE ANALYZER - Evaluate answers
            # ================================================================
            print(f"\n{'='*50}")
            print("💡 MODULE 4: KNOWLEDGE ANALYZER")
            print(f"{'='*50}")
            
            if transcript and len(transcript) > 20 and questions:
                try:
                    # Prepare questions for analyzer
                    question_list = [
                        {
                            'question_text': q.question_text,
                            'expected_keywords': q.expected_keywords or ''
                        }
                        for q in questions
                    ]
                    
                    knowledge_result = evaluate_knowledge(
                        question_list, 
                        transcript,
                        current_app.config.get('GROQ_API_KEY')
                    )
                    
                    if knowledge_result['status'] == 'success':
                        knowledge_score = knowledge_result['score']
                        knowledge_detail = {
                            'individual_scores': knowledge_result.get('individual_scores', []),
                            'raw_analysis': knowledge_result.get('analysis_detail', '')
                        }
                        
                        # Update individual question scores
                        for i, q in enumerate(questions):
                            if i < len(knowledge_result.get('individual_scores', [])):
                                q.answer_transcript = transcript
                                q.answer_score = knowledge_result['individual_scores'][i].get('score', 0)
                        
                        print(f"   ✅ Knowledge Score: {knowledge_score}%")
                    else:
                        print(f"   ❌ Knowledge analysis failed: {knowledge_result.get('error')}")
                        knowledge_score = 0
                        knowledge_detail = {'error': knowledge_result.get('error')}
                        
                except Exception as e:
                    print(f"   ❌ Knowledge analysis error: {e}")
                    knowledge_score = 0
                    knowledge_detail = {'error': str(e)}
            else:
                print("   ⚠️ No transcript or questions for knowledge analysis")
                knowledge_score = 0
                knowledge_detail = {'error': 'No transcript or questions available'}
        
        # ================================================================
        # STORE RESULTS IN DATABASE
        # ================================================================
        print(f"\n{'='*50}")
        print("💾 STORING RESULTS")
        print(f"{'='*50}")
        
        # IMPORTANT: If no meaningful speech was detected, scores should remain 0
        # Do NOT apply minimum scores as it gives false positives
        # Only apply minimum if there was actual content analyzed
        
        # Check if transcript has meaningful content (at least 50 chars of actual words)
        has_meaningful_speech = transcript and len(transcript.strip()) >= 50
        
        # If no meaningful speech, all speech-based scores should be 0
        if not has_meaningful_speech:
            print("   ⚠️ No meaningful speech detected - setting speech scores to 0")
            communication_score = 0
            knowledge_score = 0
        
        # Round all scores
        resume_score = round(resume_score, 2)
        confidence_score = round(confidence_score, 2)
        communication_score = round(communication_score, 2)
        knowledge_score = round(knowledge_score, 2)
        
        print(f"   📄 Resume Score: {resume_score}%")
        print(f"   😊 Confidence Score: {confidence_score}%")
        print(f"   🎙️ Communication Score: {communication_score}%")
        print(f"   💡 Knowledge Score: {knowledge_score}%")
        
        # Check if result already exists
        existing_result = CandidateResult.query.filter_by(interview_id=interview_id).first()
        
        if existing_result:
            # Update existing result
            existing_result.resume_score = resume_score
            existing_result.confidence_score = confidence_score
            existing_result.communication_score = communication_score
            existing_result.knowledge_score = knowledge_score
            existing_result.confidence_analysis_detail = json.dumps(confidence_detail)
            existing_result.communication_analysis_detail = json.dumps(communication_detail)
            existing_result.knowledge_analysis_detail = json.dumps(knowledge_detail)
            result = existing_result
        else:
            # Create new result
            result = CandidateResult(
                interview_id=interview_id,
                resume_score=resume_score,
                confidence_score=confidence_score,
                communication_score=communication_score,
                knowledge_score=knowledge_score
            )
            result.confidence_analysis_detail = json.dumps(confidence_detail)
            result.communication_analysis_detail = json.dumps(communication_detail)
            result.knowledge_analysis_detail = json.dumps(knowledge_detail)
            db.session.add(result)
        
        # Calculate overall score with weights
        weights = {
            'resume': current_app.config.get('WEIGHT_RESUME', 0.25),
            'confidence': current_app.config.get('WEIGHT_CONFIDENCE', 0.20),
            'communication': current_app.config.get('WEIGHT_COMMUNICATION', 0.25),
            'knowledge': current_app.config.get('WEIGHT_KNOWLEDGE', 0.30)
        }
        result.calculate_overall_score(weights)
        
        # Update interview status
        interview.is_analyzed = True
        application.status = 'Interview'
        
        db.session.commit()
        
        print(f"\n{'='*70}")
        print(f"✅ MODULAR ANALYSIS COMPLETE!")
        print(f"   Overall Score: {result.overall_score}%")
        print(f"{'='*70}\n")
        
        return {
            'success': True,
            'resume_score': resume_score,
            'confidence_score': confidence_score,
            'communication_score': communication_score,
            'knowledge_score': knowledge_score,
            'overall_score': result.overall_score
        }
        
    except Exception as e:
        print(f"\n❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()


@api_bp.route('/job/<int:job_id>/stats')
@login_required
@company_required
def job_stats(job_id):
    """Get job statistics (AJAX)"""
    job = Job.query.get_or_404(job_id)
    
    if job.company_id != current_user.company.company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    applications = job.applications.all()
    
    stats = {
        'total': len(applications),
        'applied': sum(1 for a in applications if a.status == 'Applied'),
        'screening': sum(1 for a in applications if a.status == 'Screening'),
        'shortlisted': sum(1 for a in applications if a.status == 'Shortlisted'),
        'interview': sum(1 for a in applications if a.status == 'Interview'),
        'hired': sum(1 for a in applications if a.status == 'Hired'),
        'rejected': sum(1 for a in applications if a.status == 'Rejected'),
        'avg_score': sum(a.ai_resume_score for a in applications) / len(applications) if applications else 0
    }
    
    return jsonify(stats)


@api_bp.route('/candidate/<int:candidate_id>/results')
@login_required
@company_required
def candidate_results(candidate_id):
    """Get candidate interview results"""
    candidate = Candidate.query.get_or_404(candidate_id)
    
    # Find application for current company's jobs
    application = Application.query.join(Job).filter(
        Application.candidate_id == candidate_id,
        Job.company_id == current_user.company.company_id
    ).first()
    
    if not application or not application.interview or not application.interview.result:
        return jsonify({'error': 'No results found'}), 404
    
    result = application.interview.result
    
    return jsonify({
        'candidate_name': candidate.full_name,
        'job_title': application.job.title,
        'resume_score': result.resume_score,
        'confidence_score': result.confidence_score,
        'communication_score': result.communication_score,
        'knowledge_score': result.knowledge_score,
        'overall_score': result.overall_score,
        'hr_decision': result.hr_decision
    })
