"""
Seed Database Script
Adds 5 companies, 5 candidates, and sample jobs to the database.
Run: python seed_database.py
"""
from app import create_app
from models import db, User, Company, Candidate, Job, Application, Interview, InterviewQuestion
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os

def seed():
    # Use production config if USE_AZURE_SQL is set, otherwise development
    config_name = 'production' if os.environ.get('USE_AZURE_SQL', 'false').lower() == 'true' else 'development'
    app = create_app(config_name)
    
    with app.app_context():
        print("\n" + "="*60)
        print("   SEEDING DATABASE...")
        print("="*60)
        print(f"   Config: {config_name}")
        print(f"   DB: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        # Create tables if not exists
        db.create_all()
        
        # Check if data already exists
        existing_users = User.query.count()
        if existing_users > 0:
            print(f"\n   WARNING: Database already has {existing_users} users!")
            choice = input("   Drop all data and re-seed? (yes/no): ").strip().lower()
            if choice != 'yes':
                print("   Cancelled.")
                return
            db.drop_all()
            db.create_all()
            print("   Tables dropped and recreated.")
        
        # ============================================================
        #                    5 COMPANY ACCOUNTS
        # ============================================================
        companies_data = [
            {
                'email': 'hr1@company.com',
                'password': 'Hr@123451',
                'name': 'TechCorp Solutions',
                'industry': 'Technology',
                'description': 'Leading software development company specializing in AI and ML solutions for enterprise clients worldwide.',
                'website': 'https://techcorp.com',
                'location': 'San Francisco, USA'
            },
            {
                'email': 'hr2@company.com',
                'password': 'Hr@123452',
                'name': 'Innovate Pakistan',
                'industry': 'Software Development',
                'description': 'Pakistan ki leading software house jo AI, automation aur cloud solutions mein specialized hai.',
                'website': 'https://innovate.pk',
                'location': 'Lahore, Pakistan'
            },
            {
                'email': 'hr3@company.com',
                'password': 'Hr@123453',
                'name': 'AI Solutions Karachi',
                'industry': 'Artificial Intelligence',
                'description': 'AI Solutions is a Karachi-based company specializing in AI, Machine Learning, Deep Learning, and Generative AI solutions for enterprises.',
                'website': 'https://aisolutions.pk',
                'location': 'Karachi, Pakistan'
            },
            {
                'email': 'hr4@company.com',
                'password': 'Hr@123454',
                'name': 'DevHive Technologies',
                'industry': 'Cloud & DevOps',
                'description': 'DevHive provides cloud infrastructure, DevOps consulting, and scalable SaaS products for startups and enterprises across MENA region.',
                'website': 'https://devhive.io',
                'location': 'Dubai, UAE'
            },
            {
                'email': 'hr5@company.com',
                'password': 'Hr@123455',
                'name': 'NexGen Labs',
                'industry': 'FinTech',
                'description': 'NexGen Labs is a fast-growing fintech startup building digital payment solutions and blockchain-based platforms for South Asian markets.',
                'website': 'https://nexgenlabs.pk',
                'location': 'Islamabad, Pakistan'
            }
        ]
        
        company_objects = []
        for c in companies_data:
            user = User(
                email=c['email'],
                password_hash=generate_password_hash(c['password']),
                role='Company'
            )
            db.session.add(user)
            db.session.flush()
            
            company = Company(
                user_id=user.user_id,
                company_name=c['name'],
                industry=c['industry'],
                description=c['description'],
                website=c['website'],
                location=c['location']
            )
            db.session.add(company)
            db.session.flush()
            company_objects.append(company)
            print(f"   + Company: {c['name']} ({c['email']})")
        
        db.session.commit()
        
        # ============================================================
        #                    5 CANDIDATE ACCOUNTS
        # ============================================================
        candidates_data = [
            {
                'email': 'candidate1@gmail.com',
                'password': 'Cand@123451',
                'name': 'Ali Ahmed Khan',
                'phone': '+92-321-1234567',
                'skills': 'Python, Django, React, JavaScript, PostgreSQL, Git, Docker, AWS',
                'experience': 3,
                'education': 'BS Computer Science - FAST NUCES Lahore'
            },
            {
                'email': 'candidate2@gmail.com',
                'password': 'Cand@123452',
                'name': 'Fatima Zahra',
                'phone': '+92-300-9876543',
                'skills': 'React, Node.js, MongoDB, Express, TypeScript, Tailwind CSS, Next.js',
                'experience': 2,
                'education': 'BS Software Engineering - LUMS'
            },
            {
                'email': 'candidate3@gmail.com',
                'password': 'Cand@123453',
                'name': 'Muhammad Muzammil Shah',
                'phone': '+92-333-1234567',
                'skills': 'Python, TensorFlow, PyTorch, Machine Learning, Deep Learning, NLP, Computer Vision, LLMs, LangChain',
                'experience': 2,
                'education': 'BS Artificial Intelligence - FAST NUCES Karachi'
            },
            {
                'email': 'candidate4@gmail.com',
                'password': 'Cand@123454',
                'name': 'Sarah Ahmed',
                'phone': '+92-312-5556789',
                'skills': 'Java, Spring Boot, Microservices, Kubernetes, Docker, AWS, CI/CD, PostgreSQL',
                'experience': 4,
                'education': 'MS Computer Science - NUST Islamabad'
            },
            {
                'email': 'candidate5@gmail.com',
                'password': 'Cand@123455',
                'name': 'Usman Malik',
                'phone': '+92-345-7891234',
                'skills': 'Flutter, Dart, Firebase, Swift, Kotlin, React Native, REST APIs, Git',
                'experience': 3,
                'education': 'BS Computer Science - COMSATS Islamabad'
            }
        ]
        
        candidate_objects = []
        for c in candidates_data:
            user = User(
                email=c['email'],
                password_hash=generate_password_hash(c['password']),
                role='Candidate'
            )
            db.session.add(user)
            db.session.flush()
            
            candidate = Candidate(
                user_id=user.user_id,
                full_name=c['name'],
                phone=c['phone'],
                skills=c['skills'],
                experience_years=c['experience'],
                education=c['education']
            )
            db.session.add(candidate)
            db.session.flush()
            candidate_objects.append(candidate)
            print(f"   + Candidate: {c['name']} ({c['email']})")
        
        db.session.commit()
        
        # ============================================================
        #              JOBS (2 per company = 10 total)
        # ============================================================
        jobs_data = [
            # ---- TechCorp Solutions ----
            {
                'company_idx': 0,
                'title': 'Senior Python Developer',
                'description': 'We are looking for an experienced Python developer to join our team and work on cutting-edge AI projects.',
                'requirements': '5+ years Python experience, Flask/Django, SQL databases, REST APIs, Git',
                'location': 'San Francisco, USA',
                'job_type': 'Full-time',
                'experience_required': '5+ years',
                'salary_range': '$120,000 - $180,000',
                'skills_required': 'Python, Flask, Django, SQL, REST APIs, Git, Docker'
            },
            {
                'company_idx': 0,
                'title': 'Machine Learning Engineer',
                'description': 'Join our ML team to develop and deploy machine learning models at scale.',
                'requirements': '3+ years ML experience, Python, TensorFlow/PyTorch, MLOps',
                'location': 'Remote',
                'job_type': 'Full-time',
                'experience_required': '3+ years',
                'salary_range': '$100,000 - $150,000',
                'skills_required': 'Python, TensorFlow, PyTorch, MLOps, AWS/GCP'
            },
            # ---- Innovate Pakistan ----
            {
                'company_idx': 1,
                'title': 'Full Stack Developer',
                'description': 'We need a talented full stack developer expert in React and Node.js to build modern web applications.',
                'requirements': '2+ years experience, React, Node.js, MongoDB, REST APIs',
                'location': 'Lahore, Pakistan',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'PKR 150,000 - 300,000',
                'skills_required': 'React, Node.js, MongoDB, JavaScript, Git'
            },
            {
                'company_idx': 1,
                'title': 'Python Developer',
                'description': 'Python developer needed who can work with Django and FastAPI for backend services.',
                'requirements': '1+ years Python experience, Django/FastAPI, PostgreSQL',
                'location': 'Remote (Pakistan)',
                'job_type': 'Full-time',
                'experience_required': '1+ years',
                'salary_range': 'PKR 100,000 - 200,000',
                'skills_required': 'Python, Django, FastAPI, PostgreSQL, Git'
            },
            # ---- AI Solutions Karachi ----
            {
                'company_idx': 2,
                'title': 'AI Engineer',
                'description': 'Design, develop, and deploy AI & Machine Learning models. Work on Deep Learning, NLP, Computer Vision, and Generative AI solutions.',
                'requirements': "Bachelor's in AI/CS, Python, TensorFlow/PyTorch, NLP or Computer Vision experience",
                'location': 'Karachi, Pakistan',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'PKR 150,000 - 250,000',
                'skills_required': 'Python, TensorFlow, PyTorch, NLP, Computer Vision, Deep Learning, LLMs'
            },
            {
                'company_idx': 2,
                'title': 'Data Scientist',
                'description': 'Analyze large datasets, build predictive models, and create data-driven insights for business decisions.',
                'requirements': '2+ years experience, Python, SQL, Statistics, Machine Learning',
                'location': 'Karachi, Pakistan',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'PKR 120,000 - 220,000',
                'skills_required': 'Python, Pandas, SQL, Scikit-learn, Tableau, Statistics'
            },
            # ---- DevHive Technologies ----
            {
                'company_idx': 3,
                'title': 'DevOps Engineer',
                'description': 'Manage cloud infrastructure, CI/CD pipelines, and ensure high availability of our SaaS products.',
                'requirements': '3+ years DevOps experience, AWS/Azure, Docker, Kubernetes, Terraform',
                'location': 'Dubai, UAE',
                'job_type': 'Full-time',
                'experience_required': '3+ years',
                'salary_range': 'AED 15,000 - 25,000',
                'skills_required': 'AWS, Azure, Docker, Kubernetes, Terraform, CI/CD, Linux'
            },
            {
                'company_idx': 3,
                'title': 'Backend Developer (Go/Python)',
                'description': 'Build high-performance backend microservices using Go and Python for our cloud platform.',
                'requirements': '2+ years backend development, Go or Python, gRPC, PostgreSQL',
                'location': 'Dubai, UAE (Hybrid)',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'AED 12,000 - 20,000',
                'skills_required': 'Go, Python, gRPC, PostgreSQL, Redis, Docker, Microservices'
            },
            # ---- NexGen Labs ----
            {
                'company_idx': 4,
                'title': 'Mobile App Developer (Flutter)',
                'description': 'Build and maintain cross-platform mobile apps for our digital payment solutions using Flutter.',
                'requirements': '2+ years Flutter/Dart, Firebase, REST APIs, State Management',
                'location': 'Islamabad, Pakistan',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'PKR 130,000 - 250,000',
                'skills_required': 'Flutter, Dart, Firebase, REST APIs, Git, Provider/Riverpod'
            },
            {
                'company_idx': 4,
                'title': 'Blockchain Developer',
                'description': 'Develop smart contracts and blockchain-based solutions for our fintech platform.',
                'requirements': '2+ years blockchain experience, Solidity, Web3.js, Ethereum/Polygon',
                'location': 'Islamabad, Pakistan (Hybrid)',
                'job_type': 'Full-time',
                'experience_required': '2+ years',
                'salary_range': 'PKR 200,000 - 400,000',
                'skills_required': 'Solidity, Web3.js, Ethereum, Smart Contracts, Node.js, TypeScript'
            }
        ]
        
        job_objects = []
        for j in jobs_data:
            company = company_objects[j['company_idx']]
            job = Job(
                company_id=company.company_id,
                title=j['title'],
                description=j['description'],
                requirements=j['requirements'],
                location=j['location'],
                job_type=j['job_type'],
                experience_required=j['experience_required'],
                salary_range=j['salary_range'],
                skills_required=j['skills_required']
            )
            db.session.add(job)
            db.session.flush()
            job_objects.append(job)
            print(f"   + Job: {j['title']} @ {company.company_name}")
        
        db.session.commit()
        
        # ============================================================
        #          SAMPLE APPLICATIONS + INTERVIEWS
        # ============================================================
        # Ali applied for Python Developer @ Innovate Pakistan
        app1 = Application(
            job_id=job_objects[3].job_id,  # Python Developer
            candidate_id=candidate_objects[0].candidate_id,  # Ali
            resume_path='uploads/resumes/sample_resume.pdf',
            cover_letter='I am a passionate Python developer and best fit for this position.',
            ai_resume_score=85.5,
            status='Shortlisted'
        )
        db.session.add(app1)
        db.session.flush()
        
        interview1 = Interview(
            app_id=app1.app_id,
            interview_code='INT-2025-TEST',
            expires_at=datetime.utcnow() + timedelta(hours=72)
        )
        db.session.add(interview1)
        db.session.flush()
        
        # Add questions for Ali's interview
        ali_questions = [
            ('Tell us about yourself and your professional background.', 'General', 'experience,background,skills', 'Easy'),
            ('What is the difference between a list and a tuple in Python?', 'Technical', 'list,tuple,mutable,immutable', 'Easy'),
            ('Explain what Django ORM is and its benefits.', 'Technical', 'ORM,database,models,queries', 'Medium'),
            ('Tell us about a challenging project you worked on.', 'Behavioral', 'challenge,solution,teamwork', 'Medium'),
            ('What best practices do you follow for REST APIs?', 'Technical', 'REST,HTTP,endpoints,status codes', 'Medium'),
        ]
        for i, (text, qtype, keywords, diff) in enumerate(ali_questions):
            db.session.add(InterviewQuestion(
                interview_id=interview1.interview_id,
                question_text=text, question_type=qtype,
                expected_keywords=keywords, difficulty=diff,
                question_order=i+1, time_limit_seconds=120
            ))
        
        # Muzammil applied for AI Engineer @ AI Solutions Karachi
        app2 = Application(
            job_id=job_objects[4].job_id,  # AI Engineer
            candidate_id=candidate_objects[2].candidate_id,  # Muzammil
            resume_path='uploads/resumes/muzammil_resume.pdf',
            cover_letter='I am a passionate AI/ML Engineer with hands-on experience in Deep Learning, NLP, and Generative AI.',
            ai_resume_score=92.5,
            status='Shortlisted'
        )
        db.session.add(app2)
        db.session.flush()
        
        interview2 = Interview(
            app_id=app2.app_id,
            interview_code='INT-AI-2025-001',
            expires_at=datetime.utcnow() + timedelta(hours=72)
        )
        db.session.add(interview2)
        db.session.flush()
        
        # Add questions for Muzammil's interview
        ai_questions = [
            ('What is the difference between Machine Learning and Deep Learning?', 'Technical', 'machine learning,deep learning,neural network,layers', 'Medium'),
            ('Which framework do you prefer: TensorFlow or PyTorch, and why?', 'Technical', 'tensorflow,pytorch,dynamic graph,production', 'Medium'),
            ('Have you worked on any NLP or Computer Vision project? Explain.', 'Technical', 'NLP,computer vision,CNN,transformer,BERT', 'Hard'),
            ('What are LLMs? How do you use LangChain or OpenAI API?', 'Technical', 'LLM,GPT,LangChain,OpenAI,RAG', 'Hard'),
            ('How do you detect and solve overfitting?', 'Technical', 'overfitting,regularization,dropout,cross-validation', 'Medium'),
            ('Have you deployed any ML model in production?', 'Technical', 'deployment,docker,flask,MLflow,CI/CD', 'Medium'),
            ('Describe a challenging AI project you worked on.', 'Behavioral', 'challenge,problem solving,solution', 'Medium'),
            ('What is your opinion on AI ethics and bias?', 'Behavioral', 'ethics,bias,fairness,responsible AI', 'Easy'),
        ]
        for i, (text, qtype, keywords, diff) in enumerate(ai_questions):
            db.session.add(InterviewQuestion(
                interview_id=interview2.interview_id,
                question_text=text, question_type=qtype,
                expected_keywords=keywords, difficulty=diff,
                question_order=i+1, time_limit_seconds=150
            ))
        
        db.session.commit()
        
        # ============================================================
        #                    PRINT SUMMARY
        # ============================================================
        print("\n" + "="*60)
        print("   DATABASE SEEDED SUCCESSFULLY!")
        print("="*60)
        print("\n   COMPANY ACCOUNTS:")
        for c in companies_data:
            print(f"   - {c['email']} / {c['password']} ({c['name']})")
        print("\n   CANDIDATE ACCOUNTS:")
        for c in candidates_data:
            print(f"   - {c['email']} / {c['password']} ({c['name']})")
        print(f"\n   JOBS POSTED: {len(jobs_data)}")
        print(f"   INTERVIEWS READY: 2")
        print("\n   TEST INTERVIEWS:")
        print("   +--------------------------+----------------------+")
        print("   | Interview ID             | Candidate            |")
        print("   +--------------------------+----------------------+")
        print("   | INT-2025-TEST            | Ali Ahmed Khan       |")
        print("   | INT-AI-2025-001          | M. Muzammil Shah     |")
        print("   +--------------------------+----------------------+")
        print("\n   Go to: /interview/verify")
        print("="*60 + "\n")


if __name__ == '__main__':
    seed()
