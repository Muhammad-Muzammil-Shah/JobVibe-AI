# 🎯 AI Recruit - Smart Job Application & Interview Automation System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/AI-Groq%20LLama3-orange.svg" alt="AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

> 🚀 A fully functional AI-powered recruitment portal that automates the entire hiring process including Job Posting, Resume Screening, Smart Question Generation, Video Interviewing, and Real-Time Multi-Model Assessment.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [Detailed Installation](#-detailed-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Demo Accounts](#-demo-accounts)
- [Project Structure](#-project-structure)
- [How It Works](#-how-it-works)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Features

### 👔 For Companies/HR
| Feature | Description |
|---------|-------------|
| 📝 Job Management | Create, edit, and manage job postings |
| 🤖 AI Resume Screening | Automatic resume analysis and scoring using NLP |
| 💡 Smart Question Generation | AI-generated interview questions based on JD and resume |
| 🎥 Video Interview Analysis | Automated analysis of candidate video responses |
| 📊 4-Pillar Evaluation | Resume Match, Confidence, Communication, Knowledge |
| 📈 Analytics Dashboard | Insights into hiring metrics and candidate performance |

### 👤 For Candidates
| Feature | Description |
|---------|-------------|
| 🔍 Job Search | Browse and filter job opportunities |
| 📄 Easy Application | Upload resume and apply with one click |
| 🎤 AI-Powered Interviews | Secure video interviews with OTP verification |
| ✅ Real-time Feedback | View application status and interview results |

---

## 🛠 Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      TECH STACK                              │
├─────────────────────────────────────────────────────────────┤
│  Backend      │  Python Flask with Blueprints Architecture  │
│  Frontend     │  HTML5, CSS3, Jinja2, Bootstrap 5          │
│  Database     │  SQLite / Azure SQL with SQLAlchemy ORM    │
│  AI/ML        │  Groq API (Llama 3.3), OpenCV, MediaPipe   │
│  Speech       │  OpenAI Whisper for Speech-to-Text          │
│  NLP          │  TF-IDF & Cosine Similarity                 │
│  Auth         │  Flask-Login with Role-based Access         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

| Requirement | Version | Download Link |
|-------------|---------|---------------|
| Python | 3.8 - 3.12 | [python.org](https://www.python.org/downloads/) |
| Git | Latest | [git-scm.com](https://git-scm.com/downloads) |
| pip | Latest | Comes with Python |
| FFmpeg | Latest | [ffmpeg.org](https://ffmpeg.org/download.html) |

### 🔑 Required API Keys

| Service | Purpose | Get API Key |
|---------|---------|-------------|
| Groq API | AI Question Generation & Analysis | [console.groq.com](https://console.groq.com/) |

### 💻 Hardware Requirements

- ✅ Webcam (for video interviews)
- ✅ Microphone (for audio recording)
- ✅ Minimum 8GB RAM recommended
- ✅ 5GB free disk space

---

## ⚡ Quick Start Guide

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/AI-Interview-System.git
cd AI-Interview-System

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file and add your API key
echo GROQ_API_KEY=your_groq_api_key_here > .env

# 6. Run the application
python app.py

# 7. Open browser: http://localhost:5000
```

---

## 📦 Detailed Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/AI-Interview-System.git
cd AI-Interview-System
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⚠️ **Note:** If you face issues with MediaPipe, ensure you're using Python 3.8-3.12

### Step 4: Install FFmpeg (Required for Audio Processing)

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# OR download from https://ffmpeg.org/download.html and add to PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Step 5: Create Environment File

Create a `.env` file in the root directory:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this
FLASK_ENV=development

# Groq API Configuration (Required)
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration (Optional - defaults to SQLite)
USE_AZURE_SQL=false

# Azure SQL Configuration (Only if USE_AZURE_SQL=true)
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=recruitment_db
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password
```

### Step 6: Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up / Login
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key to your `.env` file

---

## ⚙️ Configuration

### Key Settings in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `SHORTLIST_THRESHOLD` | 70 | Minimum resume score (%) to shortlist |
| `QUESTIONS_PER_INTERVIEW` | 10 | Number of AI-generated questions |
| `GROQ_MODEL` | llama-3.3-70b-versatile | AI model for analysis |
| `MAX_CONTENT_LENGTH` | 50MB | Maximum file upload size |

### Customize Settings:

```python
# In config.py
SHORTLIST_THRESHOLD = 60  # Lower threshold for more candidates
QUESTIONS_PER_INTERVIEW = 5  # Fewer questions for shorter interviews
```

---

## 🏃 Running the Application

### Development Mode

```bash
# Make sure virtual environment is activated
python app.py
```

The server will start at: **http://localhost:5000**

### Production Mode

```bash
# Using Gunicorn (Linux/macOS)
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# Using Waitress (Windows)
pip install waitress
waitress-serve --port=5000 app:create_app
```

---

## 🔐 Demo Accounts

### HR/Company Accounts

| # | Email | Password |
|---|-------|----------|
| 1 | hr1@company.com | Hr@123451 |
| 2 | hr2@company.com | Hr@123452 |
| 3 | hr3@company.com | Hr@123453 |
| 4 | hr4@company.com | Hr@123454 |
| 5 | hr5@company.com | Hr@123455 |

### Candidate Accounts

| # | Email | Password |
|---|-------|----------|
| 1 | candidate1@gmail.com | Cand@123451 |
| 2 | candidate2@gmail.com | Cand@123452 |
| 3 | candidate3@gmail.com | Cand@123453 |
| 4 | candidate4@gmail.com | Cand@123454 |
| 5 | candidate5@gmail.com | Cand@123455 |

> 📝 You can also register new accounts through the application!

---

## 📁 Project Structure

```
AI-Interview-System/
│
├── 📄 app.py                    # Main application entry point
├── 📄 config.py                 # Configuration settings
├── 📄 models.py                 # SQLAlchemy database models
├── 📄 routes.py                 # Flask routes and blueprints
├── 📄 ai_engine.py              # AI/ML processing module
├── 📄 answer_analyzer.py        # Answer evaluation logic
├── 📄 communication_analyzer.py # Speech analysis
├── 📄 confidence_analyzer.py    # Facial confidence detection
├── 📄 resume_analyzer.py        # Resume parsing & matching
├── 📄 video_processor.py        # Video processing utilities
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env                      # Environment variables (create this)
│
├── 📁 static/
│   ├── 📁 css/
│   │   └── style.css           # Custom styles
│   └── 📁 js/
│       └── main.js             # JavaScript utilities
│
├── 📁 templates/
│   ├── base.html               # Base template
│   ├── 📁 auth/                # Authentication pages
│   ├── 📁 main/                # Public pages
│   ├── 📁 company/             # HR dashboard
│   ├── 📁 candidate/           # Candidate dashboard
│   ├── 📁 interview/           # Interview room
│   └── 📁 errors/              # Error pages
│
├── 📁 uploads/
│   ├── 📁 resumes/             # Uploaded resumes
│   └── 📁 videos/              # Recorded interviews
│
├── 📁 instance/
│   └── recruitment.db          # SQLite database (auto-generated)
│
└── 📁 migrations/              # Database migrations
```

---

## 🎯 How It Works

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RECRUITMENT WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

1️⃣ COMPANY POSTS JOB
   └─→ Job Description stored in database

2️⃣ CANDIDATE APPLIES
   └─→ Resume uploaded and parsed (PDF/DOCX)

3️⃣ AI SCREENS RESUME
   └─→ TF-IDF + Cosine Similarity calculates match score

4️⃣ IF SCORE ≥ 70%
   ├─→ Status = "Shortlisted"
   ├─→ OTP generated & sent
   └─→ 10 AI questions generated

5️⃣ CANDIDATE VERIFIES OTP
   └─→ Enters video interview room

6️⃣ VIDEO INTERVIEW
   └─→ Records responses for each question

7️⃣ 4-PILLAR AI ANALYSIS
   ├─→ 📄 Pillar 1: Resume Match (NLP)
   ├─→ 😊 Pillar 2: Confidence (Face + Eye tracking)
   ├─→ 🗣️ Pillar 3: Communication (Speech analysis)
   └─→ 🧠 Pillar 4: Knowledge (Answer evaluation)

8️⃣ HR DECISION
   └─→ Accept / Reject / Hold with AI recommendations
```

### 4-Pillar Evaluation System

| Pillar | Technology | What It Measures |
|--------|------------|------------------|
| 📄 Resume Match | TF-IDF, Cosine Similarity | Skills alignment with JD |
| 😊 Confidence | OpenCV, MediaPipe | Eye contact, facial expressions |
| 🗣️ Communication | Whisper, TextStat | Clarity, fluency, grammar |
| 🧠 Knowledge | Groq LLama 3 | Technical accuracy, depth |

---

## 🔑 API Reference

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-answer` | POST | Upload video answer |
| `/api/job/<id>/stats` | GET | Get job statistics |
| `/api/candidate/<id>/results` | GET | Get candidate results |

### Example API Usage

```python
import requests

# Get job statistics
response = requests.get('http://localhost:5000/api/job/1/stats')
print(response.json())
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

<details>
<summary><b>❌ ModuleNotFoundError: No module named 'xxx'</b></summary>

```bash
# Make sure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```
</details>

<details>
<summary><b>❌ MediaPipe installation fails</b></summary>

```bash
# MediaPipe requires Python 3.8-3.12
# Check your Python version
python --version

# If using Python 3.13+, create new venv with Python 3.12
py -3.12 -m venv venv
```
</details>

<details>
<summary><b>❌ FFmpeg not found error</b></summary>

```bash
# Windows - Add FFmpeg to PATH or install via:
choco install ffmpeg

# Verify installation
ffmpeg -version
```
</details>

<details>
<summary><b>❌ Groq API error</b></summary>

1. Verify API key in `.env` file
2. Check API key is valid at [console.groq.com](https://console.groq.com/)
3. Ensure you have API credits available
</details>

<details>
<summary><b>❌ Camera/Microphone not working</b></summary>

1. Allow browser permissions for camera/microphone
2. Check if another application is using the camera
3. Try a different browser (Chrome recommended)
</details>

<details>
<summary><b>❌ Database errors</b></summary>

```bash
# Delete existing database and recreate
del instance\recruitment.db  # Windows
rm instance/recruitment.db   # macOS/Linux

# Restart application
python app.py
```
</details>

---

## 🔒 Security Features

- ✅ Password hashing with Werkzeug
- ✅ Session-based authentication
- ✅ Role-based access control (HR/Candidate)
- ✅ OTP verification for interviews
- ✅ CSRF protection
- ✅ Secure file upload validation
- ✅ SQL injection prevention (SQLAlchemy ORM)

---

## 📊 Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                    DATABASE TABLES (3NF)                     │
├─────────────────────────────────────────────────────────────┤
│  1. User              │  Authentication & roles              │
│  2. Company           │  Company profiles                    │
│  3. Candidate         │  Candidate profiles                  │
│  4. Job               │  Job postings                        │
│  5. Application       │  Applications with AI scores         │
│  6. Interview         │  Interview sessions with OTP         │
│  7. InterviewQuestion │  AI-generated questions              │
│  8. CandidateResult   │  4-pillar analysis results           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Groq](https://groq.com/) - AI inference API
- [MediaPipe](https://mediapipe.dev/) - Face detection
- [OpenAI Whisper](https://openai.com/whisper) - Speech recognition
- [Bootstrap](https://getbootstrap.com/) - UI components
- [Flask](https://flask.palletsprojects.com/) - Web framework

---

## 📞 Support

If you have any questions or need help:

- 📧 Create an issue on GitHub
- ⭐ Star this repo if you found it helpful!

---

<p align="center">
  Made with ❤️ for AI-Powered Recruitment
</p>
