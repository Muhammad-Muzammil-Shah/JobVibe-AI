# pyright: reportArgumentType=false
# pyright: reportCallIssue=false
# pyright: reportIncompatibleMethodOverride=false
"""
Database Models for AI Job Application System
Normalized to 3NF with SQLAlchemy ORM
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

db = SQLAlchemy()


class User(UserMixin, db.Model):  # type: ignore
    """Base user model for authentication"""
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'Company' or 'Candidate'
    active = db.Column(db.Boolean, default=True)  # Renamed from is_active to avoid UserMixin conflict
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='user', uselist=False, cascade='all, delete-orphan')
    candidate = db.relationship('Candidate', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, email: str = '', password_hash: str = '', role: str = '', **kwargs: Any) -> None:
        super().__init__(email=email, password_hash=password_hash, role=role, **kwargs)
    
    @property
    def is_active(self) -> bool:
        """Override UserMixin's is_active to use our 'active' column"""
        return self.active  # type: ignore
    
    def get_id(self) -> str:
        return str(self.user_id)
    
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self) -> str:
        return f'<User {self.email}>'


class Company(db.Model):  # type: ignore
    """Company profile linked to user"""
    __tablename__ = 'companies'
    
    company_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    logo_path = db.Column(db.String(300))
    location = db.Column(db.String(200))
    employee_count = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, user_id: int = 0, company_name: str = '', industry: Optional[str] = None, 
                 description: Optional[str] = None, website: Optional[str] = None, 
                 location: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(user_id=user_id, company_name=company_name, industry=industry,
                        description=description, website=website, location=location, **kwargs)
    
    def __repr__(self) -> str:
        return f'<Company {self.company_name}>'


class Candidate(db.Model):  # type: ignore
    """Candidate profile linked to user"""
    __tablename__ = 'candidates'
    
    candidate_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    default_resume_path = db.Column(db.String(300))
    linkedin_url = db.Column(db.String(200))
    portfolio_url = db.Column(db.String(200))
    skills = db.Column(db.Text)  # Comma-separated skills
    experience_years = db.Column(db.Integer, default=0)
    education = db.Column(db.Text)
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, user_id: int = 0, full_name: str = '', phone: Optional[str] = None,
                 skills: Optional[str] = None, experience_years: int = 0, 
                 education: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(user_id=user_id, full_name=full_name, phone=phone,
                        skills=skills, experience_years=experience_years, education=education, **kwargs)
    
    def __repr__(self) -> str:
        return f'<Candidate {self.full_name}>'


class Job(db.Model):  # type: ignore
    """Job postings by companies"""
    __tablename__ = 'jobs'
    
    job_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.company_id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    overview = db.Column(db.Text)  # Job Overview/Summary
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)  # Required Skills & Qualifications
    preferred_qualifications = db.Column(db.Text)  # Preferred/Nice to have
    responsibilities = db.Column(db.Text)
    location = db.Column(db.String(200))
    work_mode = db.Column(db.String(20), default='Onsite')  # Onsite, Remote, Hybrid
    job_type = db.Column(db.String(20), default='Full-time')  # Full-time, Part-time, Contract, Internship
    experience_required = db.Column(db.String(50))
    education_required = db.Column(db.String(200))  # Education requirement
    salary_min = db.Column(db.Integer)  # Minimum salary
    salary_max = db.Column(db.Integer)  # Maximum salary
    salary_currency = db.Column(db.String(10), default='PKR')  # PKR, USD, etc.
    salary_range = db.Column(db.String(100))  # Display string
    working_hours = db.Column(db.String(100))  # e.g., "9:00 AM - 6:00 PM"
    working_days = db.Column(db.String(100))  # e.g., "Monday to Friday"
    skills_required = db.Column(db.Text)  # Comma-separated skills
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, company_id: int = 0, title: str = '', description: str = '',
                 requirements: str = '', location: Optional[str] = None, job_type: str = 'Full-time',
                 experience_required: Optional[str] = None, salary_range: Optional[str] = None,
                 skills_required: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(company_id=company_id, title=title, description=description,
                        requirements=requirements, location=location, job_type=job_type,
                        experience_required=experience_required, salary_range=salary_range,
                        skills_required=skills_required, **kwargs)
    
    @property
    def application_count(self) -> int:
        return self.applications.count()
    
    @property
    def salary_display(self) -> str:
        """Format salary for display"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,} - {self.salary_max:,}"
        elif self.salary_range:
            return self.salary_range
        return "Negotiable"
    
    def __repr__(self) -> str:
        return f'<Job {self.title}>'


class Application(db.Model):  # type: ignore
    """Job applications by candidates"""
    __tablename__ = 'applications'
    
    app_id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.job_id', ondelete='CASCADE'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.candidate_id', ondelete='CASCADE'), nullable=False)
    resume_path = db.Column(db.String(300), nullable=False)
    cover_letter = db.Column(db.Text)
    ai_resume_score = db.Column(db.Float, default=0.0)
    resume_analysis = db.Column(db.Text)  # JSON string with detailed analysis
    status = db.Column(db.String(20), default='Applied')  # Applied, Screening, Shortlisted, Interview, Rejected, Hired
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interview = db.relationship('Interview', backref='application', uselist=False, cascade='all, delete-orphan')
    
    # Unique constraint: one application per candidate per job
    __table_args__ = (db.UniqueConstraint('job_id', 'candidate_id', name='unique_job_candidate'),)
    
    def __init__(self, job_id: int = 0, candidate_id: int = 0, resume_path: str = '',
                 cover_letter: Optional[str] = None, ai_resume_score: float = 0.0,
                 status: str = 'Applied', **kwargs: Any) -> None:
        super().__init__(job_id=job_id, candidate_id=candidate_id, resume_path=resume_path,
                        cover_letter=cover_letter, ai_resume_score=ai_resume_score,
                        status=status, **kwargs)
    
    def __repr__(self) -> str:
        return f'<Application {self.app_id}>'


class Interview(db.Model):  # type: ignore
    """Interview sessions for shortlisted candidates"""
    __tablename__ = 'interviews'
    
    interview_id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('applications.app_id', ondelete='CASCADE'), unique=True, nullable=False)
    interview_code = db.Column(db.String(15), unique=True, nullable=False, index=True)  # Unique Interview ID like INT-2024-001
    otp_code = db.Column(db.String(10), unique=True, nullable=True, index=True)  # Legacy field, kept for compatibility
    video_url = db.Column(db.String(300))
    video_path = db.Column(db.String(300))  # Path to single recorded video for entire interview
    is_completed = db.Column(db.Boolean, default=False)
    is_analyzed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    current_question_index = db.Column(db.Integer, default=0)
    
    # Relationships
    questions = db.relationship('InterviewQuestion', backref='interview', lazy='dynamic', cascade='all, delete-orphan', order_by='InterviewQuestion.question_order')
    result = db.relationship('CandidateResult', backref='interview', uselist=False, cascade='all, delete-orphan')
    
    @staticmethod
    def generate_interview_code() -> str:
        """Generate a unique Interview ID like INT-2025-XXXX"""
        year = datetime.utcnow().year
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        return f"INT-{year}-{random_part}"
    
    @staticmethod
    def generate_otp(length: int = 8) -> str:
        """Generate a unique OTP code (legacy)"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def __init__(self, app_id: int = 0, interview_code: str = '', otp_code: str = '', 
                 expires_at: Optional[datetime] = None, **kwargs: Any) -> None:
        super().__init__(app_id=app_id, interview_code=interview_code, otp_code=otp_code, expires_at=expires_at, **kwargs)
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def __repr__(self) -> str:
        return f'<Interview {self.interview_id}>'


class InterviewQuestion(db.Model):  # type: ignore
    """AI-generated questions for each interview"""
    __tablename__ = 'interview_questions'
    
    question_id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.interview_id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='Technical')  # Technical, Behavioral, Situational, General
    expected_keywords = db.Column(db.Text)  # Comma-separated keywords for evaluation
    difficulty = db.Column(db.String(10), default='Medium')  # Easy, Medium, Hard
    question_order = db.Column(db.Integer, nullable=False)
    time_limit_seconds = db.Column(db.Integer, default=120)
    
    # Answer storage
    answer_video_path = db.Column(db.String(300))
    answer_transcript = db.Column(db.Text)
    answer_score = db.Column(db.Float)
    answered_at = db.Column(db.DateTime)
    
    def __init__(self, interview_id: int = 0, question_text: str = '', question_type: str = 'Technical',
                 expected_keywords: Optional[str] = None, difficulty: str = 'Medium',
                 question_order: int = 1, time_limit_seconds: int = 120, **kwargs: Any) -> None:
        super().__init__(interview_id=interview_id, question_text=question_text,
                        question_type=question_type, expected_keywords=expected_keywords,
                        difficulty=difficulty, question_order=question_order,
                        time_limit_seconds=time_limit_seconds, **kwargs)
    
    def __repr__(self) -> str:
        return f'<Question {self.question_id}>'


class CandidateResult(db.Model):  # type: ignore
    """Final analysis results for each interview"""
    __tablename__ = 'candidate_results'
    
    result_id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.interview_id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # The 4 Pillars of Analysis
    resume_score = db.Column(db.Float, default=0.0)  # Pillar 1: Resume Match (NLP)
    confidence_score = db.Column(db.Float, default=0.0)  # Pillar 2: Face Analysis (OpenCV)
    communication_score = db.Column(db.Float, default=0.0)  # Pillar 3: Voice Analysis (Whisper)
    knowledge_score = db.Column(db.Float, default=0.0)  # Pillar 4: Answer Quality (LLM)
    
    # Detailed breakdown (JSON)
    resume_analysis_detail = db.Column(db.Text)
    confidence_analysis_detail = db.Column(db.Text)
    communication_analysis_detail = db.Column(db.Text)
    knowledge_analysis_detail = db.Column(db.Text)
    
    # Final scores
    overall_score = db.Column(db.Float, default=0.0)
    overall_percentile = db.Column(db.Float, default=0.0)
    
    # HR Decision
    hr_decision = db.Column(db.String(20), default='Pending')  # Pending, Selected, Rejected, On-Hold
    hr_notes = db.Column(db.Text)
    decided_at = db.Column(db.DateTime)
    decided_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_overall_score(self, weights: Optional[dict] = None) -> float:
        """Calculate weighted overall score from 4 pillars"""
        if weights is None:
            weights = {
                'resume': 0.25,
                'confidence': 0.20,
                'communication': 0.25,
                'knowledge': 0.30
            }
        
        self.overall_score = (
            self.resume_score * weights['resume'] +
            self.confidence_score * weights['confidence'] +
            self.communication_score * weights['communication'] +
            self.knowledge_score * weights['knowledge']
        )
        return self.overall_score
    
    def __repr__(self) -> str:
        return f'<Result {self.result_id} - Score: {self.overall_score}>'


class ActivityLog(db.Model):
    """System activity logging for audit trail"""
    __tablename__ = 'activity_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # Job, Application, Interview, etc.
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Log {self.action} at {self.created_at}>'


class Notification(db.Model):
    """Notifications for candidates (interview invites, status updates)"""
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    notification_type = db.Column(db.String(30), nullable=False)  # interview_invite, status_update, reminder, system
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Link to related entities
    related_entity_type = db.Column(db.String(50))  # Application, Interview, Job
    related_entity_id = db.Column(db.Integer)
    
    # Interview-specific fields
    interview_code = db.Column(db.String(15))  # For quick reference
    expires_at = db.Column(db.DateTime)  # Interview validity window
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def __init__(self, user_id: int = 0, notification_type: str = 'system', 
                 title: str = '', message: str = '', related_entity_type: Optional[str] = None,
                 related_entity_id: Optional[int] = None, interview_code: Optional[str] = None,
                 expires_at: Optional[datetime] = None, **kwargs: Any) -> None:
        super().__init__(user_id=user_id, notification_type=notification_type,
                        title=title, message=message, related_entity_type=related_entity_type,
                        related_entity_id=related_entity_id, interview_code=interview_code,
                        expires_at=expires_at, **kwargs)
    
    def mark_as_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        """Check if interview invitation has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    @property
    def days_remaining(self) -> int:
        """Get days remaining for interview validity"""
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    def __repr__(self) -> str:
        return f'<Notification {self.notification_id}: {self.title}>'


# Helper function to initialize database
def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
