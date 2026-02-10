"""
AI Recruit - Smart Job Application & Interview Automation System
Main Application Entry Point
"""
 
import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import extensions and models
from models import db, User
from config import config

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Azure App Service sets WEBSITE_HOSTNAME
    if os.environ.get('WEBSITE_HOSTNAME'):
        config_name = 'production'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Please log in to access this page.'  # type: ignore
    login_manager.login_message_category = 'info'  # type: ignore
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes import auth_bp, main_bp, company_bp, candidate_bp, interview_bp, api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(candidate_bp, url_prefix='/candidate')
    app.register_blueprint(interview_bp, url_prefix='/interview')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create upload directories
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
        
        # Create database tables
        db.create_all()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403
    
    # Context processors
    @app.context_processor
    def inject_globals():
        return {
            'app_name': 'AI Recruit',
            'current_year': 2025
        }
    
    # Register custom Jinja2 filters
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        """Parse JSON string to Python object"""
        import json
        if value is None or value == '':
            return {}
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from models import (User, Company, Candidate, Job, Application, 
                          Interview, InterviewQuestion, CandidateResult, ActivityLog)
        return {
            'db': db,
            'User': User,
            'Company': Company,
            'Candidate': Candidate,
            'Job': Job,
            'Application': Application,
            'Interview': Interview,
            'InterviewQuestion': InterviewQuestion,
            'CandidateResult': CandidateResult,
            'ActivityLog': ActivityLog
        }
    
    return app


def init_db():
    """Initialize the database with sample data"""
    from models import User, Company, Candidate, Job, Application, Interview, InterviewQuestion
    from werkzeug.security import generate_password_hash
    from datetime import datetime, timedelta
    
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()
        
        # ==================== COMPANY 1 ====================
        company_user = User(
            email='hr@techcorp.com',
            password_hash=generate_password_hash('password123'),
            role='Company'
        )
        db.session.add(company_user)
        db.session.commit()
        
        company = Company(
            user_id=company_user.user_id,
            company_name='TechCorp Solutions',
            industry='Technology',
            description='Leading software development company specializing in AI and ML solutions.',
            website='https://techcorp.com',
            location='San Francisco, CA'
        )
        db.session.add(company)
        db.session.commit()
        
        # ==================== COMPANY 2 ====================
        company_user2 = User(
            email='hr@innovate.pk',
            password_hash=generate_password_hash('password123'),
            role='Company'
        )
        db.session.add(company_user2)
        db.session.commit()
        
        company2 = Company(
            user_id=company_user2.user_id,
            company_name='Innovate Pakistan',
            industry='Software',
            description='Pakistan ki leading software house jo AI aur automation mein kaam karti hai.',
            website='https://innovate.pk',
            location='Lahore, Pakistan'
        )
        db.session.add(company2)
        db.session.commit()
        
        # ==================== COMPANY 3 (AI Solutions Karachi) ====================
        company_user3 = User(
            email='hr@aisolutions.pk',
            password_hash=generate_password_hash('password123'),
            role='Company'
        )
        db.session.add(company_user3)
        db.session.commit()
        
        company3 = Company(
            user_id=company_user3.user_id,
            company_name='AI Solutions Karachi',
            industry='Artificial Intelligence',
            description='AI Solutions is a leading Karachi-based company specializing in AI, Machine Learning, Deep Learning, and Generative AI solutions for enterprises.',
            website='https://aisolutions.pk',
            location='Karachi, Pakistan'
        )
        db.session.add(company3)
        db.session.commit()
        
        # ==================== JOBS ====================
        jobs = [
            Job(
                company_id=company.company_id,
                title='Senior Python Developer',
                description='We are looking for an experienced Python developer to join our team and work on cutting-edge AI projects.',
                requirements='5+ years Python experience, Flask/Django, SQL databases, REST APIs, Git',
                location='San Francisco, CA',
                job_type='Full-time',
                experience_required='5+ years',
                salary_range='$120,000 - $180,000',
                skills_required='Python, Flask, Django, SQL, REST APIs, Git'
            ),
            Job(
                company_id=company.company_id,
                title='Machine Learning Engineer',
                description='Join our ML team to develop and deploy machine learning models at scale.',
                requirements='3+ years ML experience, Python, TensorFlow/PyTorch, MLOps, Cloud platforms',
                location='Remote',
                job_type='Full-time',
                experience_required='3+ years',
                salary_range='$100,000 - $150,000',
                skills_required='Python, TensorFlow, PyTorch, MLOps, AWS/GCP'
            ),
            Job(
                company_id=company2.company_id,
                title='Full Stack Developer',
                description='Hum ek talented full stack developer dhundh rahe hain jo React aur Node.js mein expert ho.',
                requirements='2+ years experience, React, Node.js, MongoDB, REST APIs',
                location='Lahore, Pakistan',
                job_type='Full-time',
                experience_required='2+ years',
                salary_range='PKR 150,000 - 300,000',
                skills_required='React, Node.js, MongoDB, JavaScript, Git'
            ),
            Job(
                company_id=company2.company_id,
                title='Python Developer',
                description='Python developer ki zaroorat hai jo Django aur FastAPI mein kaam kar sake.',
                requirements='1+ years Python experience, Django/FastAPI, PostgreSQL',
                location='Remote (Pakistan)',
                job_type='Full-time',
                experience_required='1+ years',
                salary_range='PKR 100,000 - 200,000',
                skills_required='Python, Django, FastAPI, PostgreSQL, Git'
            ),
            # ==================== AI ENGINEER JOB (AI Solutions Karachi) ====================
            Job(
                company_id=company3.company_id,
                title='AI Engineer',
                overview='''We are seeking a skilled and motivated AI Engineer to design, develop, and deploy intelligent AI-driven solutions. The ideal candidate will work onsite with cross-functional teams to build scalable Machine Learning, Deep Learning, and Generative AI applications for real-world business use cases.''',
                description='''Key Responsibilities:

• Design, develop, and deploy AI & Machine Learning models
• Work on Deep Learning, NLP, Computer Vision, and Generative AI solutions
• Build and integrate LLM-based applications such as chatbots and AI agents
• Perform data preprocessing, feature engineering, and model evaluation
• Optimize model performance, scalability, and accuracy
• Integrate AI solutions with existing software systems
• Collaborate with product, data, and engineering teams''',
                requirements='''• Bachelor's degree in Artificial Intelligence, Computer Science, or related field
• Strong proficiency in Python
• Solid understanding of Machine Learning & Deep Learning algorithms
• Hands-on experience with TensorFlow, PyTorch, or Scikit-learn
• Knowledge of NLP, Computer Vision, or Generative AI
• Good problem-solving and analytical skills''',
                preferred_qualifications='''• Experience with LLMs, Prompt Engineering, and AI Agents
• Familiarity with LangChain, OpenAI APIs, or Azure AI
• Knowledge of MLOps tools (Docker, CI/CD, MLflow)
• Experience deploying AI models in production environments''',
                location='Karachi, Pakistan',
                job_type='Full-time',
                work_mode='Onsite',
                experience_required='2+ years',
                education_required='Bachelor\'s degree in AI, Computer Science, or related field',
                salary_min=150000,
                salary_max=250000,
                salary_currency='PKR',
                salary_range='PKR 150,000 - 250,000 per month',
                working_hours='9:00 AM – 6:00 PM',
                working_days='Monday to Friday',
                skills_required='Python, TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision, Deep Learning, Machine Learning, Generative AI, LLMs'
            ),
            # ==================== SOFTWARE ENGINEER JOB (AI Solutions Karachi) ====================
            Job(
                company_id=company3.company_id,
                title='Software Engineer',
                overview='''We are looking for a skilled and motivated Software Engineer to design, develop, and maintain high-quality software applications. The ideal candidate will work onsite with cross-functional teams to build scalable, secure, and efficient software solutions for real-world business needs.''',
                description='''Key Responsibilities:

• Design, develop, test, and maintain software applications
• Write clean, efficient, and reusable code
• Collaborate with UI/UX designers, QA, and product teams
• Debug, troubleshoot, and optimize application performance
• Develop and integrate APIs and backend services
• Ensure software quality through testing and code reviews
• Maintain documentation and follow best coding practices''',
                requirements='''• Bachelor's degree in Computer Science, Software Engineering, or related field
• Strong knowledge of programming languages (e.g., Python, Java, JavaScript, C++)
• Experience with web or software development frameworks
• Understanding of databases (SQL / NoSQL)
• Knowledge of RESTful APIs
• Strong problem-solving and analytical skills''',
                preferred_qualifications='''• Experience with frontend frameworks (React, Angular, Vue)
• Knowledge of backend frameworks (Django, Spring Boot, Node.js)
• Familiarity with Git, CI/CD pipelines
• Experience working in agile / scrum environments
• Basic understanding of cloud platforms (AWS, Azure)''',
                location='Karachi, Pakistan',
                job_type='Full-time',
                work_mode='Onsite',
                experience_required='1+ years',
                education_required='Bachelor\'s degree in Computer Science, Software Engineering, or related field',
                salary_min=120000,
                salary_max=220000,
                salary_currency='PKR',
                salary_range='PKR 120,000 - 220,000 per month',
                working_hours='9:00 AM – 6:00 PM',
                working_days='Monday to Friday',
                skills_required='Python, Java, JavaScript, C++, SQL, NoSQL, REST APIs, Git, React, Angular, Vue, Django, Node.js'
            )
        ]
        
        for job in jobs:
            db.session.add(job)
        db.session.commit()
        
        # ==================== CANDIDATE 1 ====================
        candidate_user = User(
            email='john@example.com',
            password_hash=generate_password_hash('password123'),
            role='Candidate'
        )
        db.session.add(candidate_user)
        db.session.commit()
        
        candidate = Candidate(
            user_id=candidate_user.user_id,
            full_name='John Doe',
            phone='+1-555-123-4567',
            skills='Python, Flask, Django, SQL, JavaScript, React, Git, Docker',
            experience_years=5,
            education='Bachelor of Science in Computer Science'
        )
        db.session.add(candidate)
        db.session.commit()
        
        # ==================== CANDIDATE 2 (Pakistani) ====================
        candidate_user2 = User(
            email='ali@gmail.com',
            password_hash=generate_password_hash('password123'),
            role='Candidate'
        )
        db.session.add(candidate_user2)
        db.session.commit()
        
        candidate2 = Candidate(
            user_id=candidate_user2.user_id,
            full_name='Ali Ahmed Khan',
            phone='+92-321-1234567',
            skills='Python, Django, React, JavaScript, PostgreSQL, Git, Docker, AWS',
            experience_years=3,
            education='BS Computer Science - FAST NUCES Lahore'
        )
        db.session.add(candidate2)
        db.session.commit()
        
        # ==================== CANDIDATE 3 ====================
        candidate_user3 = User(
            email='fatima@gmail.com',
            password_hash=generate_password_hash('password123'),
            role='Candidate'
        )
        db.session.add(candidate_user3)
        db.session.commit()
        
        candidate3 = Candidate(
            user_id=candidate_user3.user_id,
            full_name='Fatima Zahra',
            phone='+92-300-9876543',
            skills='React, Node.js, MongoDB, Express, TypeScript, Tailwind CSS',
            experience_years=2,
            education='BS Software Engineering - LUMS'
        )
        db.session.add(candidate3)
        db.session.commit()
        
        # ==================== APPLICATION + INTERVIEW WITH OTP ====================
        # Ali applied for Python Developer job at Innovate Pakistan
        python_job = Job.query.filter_by(title='Python Developer').first()
        
        if python_job is None:
            print("Error: Python Developer job not found!")
            return
        
        application = Application(
            job_id=python_job.job_id,
            candidate_id=candidate2.candidate_id,
            resume_path='uploads/resumes/sample_resume.pdf',
            cover_letter='Main ek passionate Python developer hoon aur is position ke liye best fit hoon.',
            ai_resume_score=85.5,
            status='Shortlisted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Create Interview with test Interview ID
        TEST_INTERVIEW_ID = 'INT-2025-TEST'  # Easy to remember Interview ID for testing
        TEST_OTP = 'TEST1234'  # Legacy OTP for backward compatibility
        
        interview = Interview(
            app_id=application.app_id,
            interview_code=TEST_INTERVIEW_ID,
            expires_at=datetime.utcnow() + timedelta(hours=48)
        )
        db.session.add(interview)
        db.session.commit()
        
        # Add sample interview questions (in English)
        questions = [
            {
                'question': 'Tell us about yourself and your professional background.',
                'type': 'General',
                'keywords': 'experience,background,skills,education,career',
                'difficulty': 'Easy'
            },
            {
                'question': 'What is the difference between a list and a tuple in Python?',
                'type': 'Technical',
                'keywords': 'list,tuple,mutable,immutable,performance',
                'difficulty': 'Easy'
            },
            {
                'question': 'Explain what Django ORM is and what are its benefits?',
                'type': 'Technical',
                'keywords': 'ORM,database,models,queries,abstraction',
                'difficulty': 'Medium'
            },
            {
                'question': 'Tell us about a challenging project you worked on and how you overcame the challenges.',
                'type': 'Behavioral',
                'keywords': 'challenge,solution,teamwork,problem-solving',
                'difficulty': 'Medium'
            },
            {
                'question': 'What best practices do you follow when designing REST APIs?',
                'type': 'Technical',
                'keywords': 'REST,HTTP,endpoints,status codes,versioning',
                'difficulty': 'Medium'
            },
            {
                'question': 'How do you handle disagreements with team members?',
                'type': 'Behavioral',
                'keywords': 'communication,teamwork,conflict,resolution',
                'difficulty': 'Easy'
            },
            {
                'question': 'Where do you see yourself in 5 years?',
                'type': 'General',
                'keywords': 'goals,growth,career,ambition,development',
                'difficulty': 'Easy'
            },
            {
                'question': 'What is your greatest strength and weakness?',
                'type': 'Behavioral',
                'keywords': 'self-awareness,improvement,skills,growth',
                'difficulty': 'Easy'
            },
            {
                'question': 'How do you stay updated with the latest technologies?',
                'type': 'General',
                'keywords': 'learning,courses,blogs,community,growth',
                'difficulty': 'Easy'
            },
            {
                'question': 'Do you have any questions for us about the role or company?',
                'type': 'General',
                'keywords': 'curiosity,interest,engagement,questions',
                'difficulty': 'Easy'
            }
        ]
        
        for i, q in enumerate(questions):
            question = InterviewQuestion(
                interview_id=interview.interview_id,
                question_text=q['question'],
                question_type=q['type'],
                expected_keywords=q['keywords'],
                difficulty=q['difficulty'],
                question_order=i + 1,
                time_limit_seconds=120
            )
            db.session.add(question)
        
        db.session.commit()
        
        # ==================== CANDIDATE 4 (Muhammad Muzammil Shah - AI Engineer Applicant) ====================
        candidate_user4 = User(
            email='muzammil.shah@gmail.com',
            password_hash=generate_password_hash('password123'),
            role='Candidate'
        )
        db.session.add(candidate_user4)
        db.session.commit()
        
        candidate4 = Candidate(
            user_id=candidate_user4.user_id,
            full_name='Muhammad Muzammil Shah',
            phone='+92-333-1234567',
            skills='Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision, LLMs, LangChain, OpenAI API, Scikit-learn, Pandas, NumPy, Flask, FastAPI, Docker, Git',
            experience_years=2,
            education='BS Artificial Intelligence - FAST NUCES Karachi'
        )
        db.session.add(candidate4)
        db.session.commit()
        
        # Muzammil applied for AI Engineer job at AI Solutions Karachi
        ai_job = Job.query.filter_by(title='AI Engineer').first()
        
        if ai_job is None:
            print("Error: AI Engineer job not found!")
            return
        
        application2 = Application(
            job_id=ai_job.job_id,
            candidate_id=candidate4.candidate_id,
            resume_path='uploads/resumes/20251225104530_05510138_AIML_Engineer_M_Muzammil_Shah.pdf',
            cover_letter='I am a passionate AI/ML Engineer with hands-on experience in Deep Learning, NLP, and Generative AI. I am excited to contribute to AI Solutions Karachi and build intelligent solutions.',
            ai_resume_score=92.5,
            status='Shortlisted'
        )
        db.session.add(application2)
        db.session.commit()
        
        # Create Interview for Muzammil with Interview ID
        MUZAMMIL_INTERVIEW_ID = 'INT-AI-2025-001'
        
        interview2 = Interview(
            app_id=application2.app_id,
            interview_code=MUZAMMIL_INTERVIEW_ID,
            expires_at=datetime.utcnow() + timedelta(hours=72)  # 3 days validity
        )
        db.session.add(interview2)
        db.session.commit()
        
        # Add AI Engineer specific interview questions (based on job description + resume)
        ai_questions = [
            {
                'question': 'What is the fundamental difference between Machine Learning and Deep Learning? Explain with a real-world example.',
                'type': 'Technical',
                'keywords': 'machine learning,deep learning,neural network,feature extraction,automatic,layers,representation',
                'difficulty': 'Medium'
            },
            {
                'question': 'Which framework do you prefer: TensorFlow or PyTorch, and why? Share your experience.',
                'type': 'Technical',
                'keywords': 'tensorflow,pytorch,dynamic graph,static graph,debugging,production,research,keras',
                'difficulty': 'Medium'
            },
            {
                'question': 'Have you worked on any NLP or Computer Vision project? Explain its architecture and challenges.',
                'type': 'Technical',
                'keywords': 'NLP,computer vision,CNN,transformer,BERT,GPT,tokenization,image classification,object detection',
                'difficulty': 'Hard'
            },
            {
                'question': 'What are Large Language Models (LLMs)? How do you use LangChain or OpenAI API to build a chatbot?',
                'type': 'Technical',
                'keywords': 'LLM,GPT,LangChain,OpenAI,prompt engineering,chain,agent,embedding,vector database,RAG',
                'difficulty': 'Hard'
            },
            {
                'question': 'During model training, how do you detect and solve the overfitting problem?',
                'type': 'Technical',
                'keywords': 'overfitting,regularization,dropout,early stopping,cross-validation,data augmentation,L1,L2',
                'difficulty': 'Medium'
            },
            {
                'question': 'Have you deployed any ML model in production? Describe your MLOps practices.',
                'type': 'Technical',
                'keywords': 'deployment,docker,flask,fastapi,MLflow,CI/CD,model versioning,monitoring,API,containerization',
                'difficulty': 'Medium'
            },
            {
                'question': 'Describe a challenging AI project you worked on. What problems did you face and how did you solve them?',
                'type': 'Behavioral',
                'keywords': 'challenge,problem solving,solution,debugging,optimization,teamwork,deadline',
                'difficulty': 'Medium'
            },
            {
                'question': 'What is your opinion on AI ethics and responsible AI? How do you detect bias in models?',
                'type': 'Behavioral',
                'keywords': 'ethics,bias,fairness,responsible AI,transparency,explainability,data privacy',
                'difficulty': 'Easy'
            }
        ]
        
        for i, q in enumerate(ai_questions):
            question = InterviewQuestion(
                interview_id=interview2.interview_id,
                question_text=q['question'],
                question_type=q['type'],
                expected_keywords=q['keywords'],
                difficulty=q['difficulty'],
                question_order=i + 1,
                time_limit_seconds=150  # 2.5 minutes for AI questions
            )
            db.session.add(question)
        
        db.session.commit()
        
        # ==================== PRINT SUMMARY ====================
        print("\n" + "="*70)
        print("   DATABASE INITIALIZED WITH SAMPLE DATA!")
        print("="*70)
        print("\n📋 COMPANY ACCOUNTS:")
        print("   1. hr@techcorp.com / password123 (TechCorp Solutions)")
        print("   2. hr@innovate.pk / password123 (Innovate Pakistan)")
        print("   3. hr@aisolutions.pk / password123 (AI Solutions Karachi)")
        print("\n👤 CANDIDATE ACCOUNTS:")
        print("   1. john@example.com / password123 (John Doe)")
        print("   2. ali@gmail.com / password123 (Ali Ahmed Khan)")
        print("   3. fatima@gmail.com / password123 (Fatima Zahra)")
        print("   4. muzammil.shah@gmail.com / password123 (Muhammad Muzammil Shah) [NEW!]")
        print("\n💼 JOBS POSTED:")
        print("   • Senior Python Developer - TechCorp Solutions")
        print("   • Machine Learning Engineer - TechCorp Solutions")
        print("   • Full Stack Developer - Innovate Pakistan")
        print("   • Python Developer - Innovate Pakistan")
        print("   • AI Engineer - AI Solutions Karachi")
        print("   • Software Engineer - AI Solutions Karachi")
        print("\n🎯 TEST INTERVIEW 1 (Python Developer):")
        print("   ╔══════════════════════════════════════════════════════════════╗")
        print("   ║  Interview ID: INT-2025-TEST                                 ║")
        print("   ║  Candidate Name: Ali Ahmed Khan                              ║")
        print("   ║  Position: Python Developer                                  ║")
        print("   ║  Company: Innovate Pakistan                                  ║")
        print("   ║  Questions: 5                                                ║")
        print("   ╚══════════════════════════════════════════════════════════════╝")
        print("\n🎯 TEST INTERVIEW 2 (AI Engineer) [NEW!]:")
        print("   ╔══════════════════════════════════════════════════════════════╗")
        print("   ║  Interview ID: INT-AI-2025-001                               ║")
        print("   ║  Candidate Name: Muhammad Muzammil Shah                      ║")
        print("   ║  Position: AI Engineer                                       ║")
        print("   ║  Company: AI Solutions Karachi                               ║")
        print("   ║  Questions: 8 (AI/ML Specific)                               ║")
        print("   ╚══════════════════════════════════════════════════════════════╝")
        print("\n🚀 Go to: http://localhost:5000/interview/verify")
        print("   Enter Interview ID + Candidate Name + Position to start!")
        print("="*70 + "\n")


# Run the application
# Expose 'app' at module level for Azure App Service / Gunicorn auto-detection
app = create_app()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_db()
    else:
        app.run(debug=True, host='0.0.0.0', port=5000)
