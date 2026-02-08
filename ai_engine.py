"""
AI Engine Module for Smart Job Application System
Handles: Resume Parsing, Scoring, Question Generation, and Answer Analysis
"""
import os
import re
import json
import fitz  # PyMuPDF
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Download NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt_tab')


class ResumeParser:
    """Extract and analyze text from resume PDFs"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """Extract text content from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                page_text = page.get_text()
                if isinstance(page_text, str):
                    text += page_text
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""
    
    @staticmethod
    def extract_email(text):
        """Extract email from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    @staticmethod
    def extract_phone(text):
        """Extract phone number from text"""
        phone_pattern = r'[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else None
    
    @staticmethod
    def extract_skills(text, skill_keywords=None):
        """Extract skills from resume text"""
        if skill_keywords is None:
            skill_keywords = [
                'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'nosql', 'mongodb',
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'linux',
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp',
                'data analysis', 'data science', 'excel', 'power bi', 'tableau',
                'html', 'css', 'rest api', 'graphql', 'agile', 'scrum', 'jira',
                'communication', 'leadership', 'teamwork', 'problem solving'
            ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        return found_skills
    
    @staticmethod
    def extract_experience_years(text):
        """Estimate years of experience from resume"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:in|with)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        return 0
    
    @staticmethod
    def extract_education(text):
        """Extract education information"""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'mba', 'b.tech', 'm.tech',
            'b.sc', 'm.sc', 'b.e', 'm.e', 'bca', 'mca', 'diploma'
        ]
        
        text_lower = text.lower()
        found_education = []
        for edu in education_keywords:
            if edu in text_lower:
                found_education.append(edu.upper())
        return found_education


class ResumeScorer:
    """Score resumes against job descriptions using NLP"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    
    def calculate_similarity(self, resume_text, job_description):
        """Calculate cosine similarity between resume and JD"""
        try:
            documents = [resume_text, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])  # type: ignore
            return float(similarity[0][0])
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def calculate_percentile(self, score, all_scores):
        """
        Calculate percentile ranking of a score among all applicants.
        
        Args:
            score: The candidate's score
            all_scores: List of all applicant scores for the same job
        
        Returns:
            Percentile ranking (0-100)
        """
        if not all_scores or len(all_scores) == 0:
            return 100.0  # Only applicant
        
        if len(all_scores) == 1:
            return 100.0  # Only applicant
        
        # Count how many scores are below the current score
        below_count = sum(1 for s in all_scores if s < score)
        equal_count = sum(1 for s in all_scores if s == score)
        
        # Percentile formula: (B + 0.5 * E) / N * 100
        # B = number of scores below, E = number of equal scores, N = total
        percentile = ((below_count + 0.5 * equal_count) / len(all_scores)) * 100
        
        return round(percentile, 1)
    
    def extract_keywords(self, text, top_n=20):
        """Extract top keywords from text"""
        try:
            stop_words = set(stopwords.words('english'))
            words = word_tokenize(text.lower())
            words = [w for w in words if w.isalnum() and w not in stop_words and len(w) > 2]
            
            # Frequency-based extraction
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:top_n]]
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def keyword_match_score(self, resume_text, job_requirements):
        """Score based on keyword matching"""
        job_keywords = self.extract_keywords(job_requirements)
        resume_lower = resume_text.lower()
        
        matched = sum(1 for kw in job_keywords if kw in resume_lower)
        return (matched / len(job_keywords)) * 100 if job_keywords else 0
    
    def score_resume(self, resume_text, job_description, job_requirements):
        """Generate comprehensive resume score"""
        # Combine JD and requirements
        full_job_text = f"{job_description} {job_requirements}"
        
        # Calculate different scores
        similarity_score = self.calculate_similarity(resume_text, full_job_text) * 100
        keyword_score = self.keyword_match_score(resume_text, job_requirements)
        
        # Extract info
        parser = ResumeParser()
        skills = parser.extract_skills(resume_text)
        experience = parser.extract_experience_years(resume_text)
        education = parser.extract_education(resume_text)
        
        # Skill bonus
        skill_score = min(len(skills) * 5, 30)  # Max 30 points for skills
        
        # Experience bonus (max 20 points)
        exp_score = min(experience * 4, 20)
        
        # Weighted final score
        final_score = (
            similarity_score * 0.35 +
            keyword_score * 0.35 +
            skill_score +
            exp_score
        )
        
        # Normalize to 0-100
        final_score = min(max(final_score, 0), 100)
        
        analysis = {
            'similarity_score': round(similarity_score, 2),
            'keyword_match_score': round(keyword_score, 2),
            'skills_found': skills,
            'experience_years': experience,
            'education': education,
            'final_score': round(final_score, 2)
        }
        
        return round(final_score, 2), json.dumps(analysis)


class GroqAIEngine:
    """Interface with Groq API for LLM-powered features"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        self.client = Groq(api_key=self.api_key) if self.api_key else None
        # Using llama-3.3-70b-versatile (latest model as of 2026)
        # Old model llama3-70b-8192 was decommissioned
        self.model = 'llama-3.3-70b-versatile'
    
    def _make_request(self, system_prompt, user_prompt, max_tokens=2000, temperature=0.7):
        """Make a request to Groq API"""
        if not self.client:
            raise ValueError("Groq API key not configured")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            raise
    
    def generate_interview_questions(self, resume_text, job_description, job_requirements, num_questions=10):
        """Generate tailored interview questions based on resume and job description"""
        
        system_prompt = """You are a Senior Technical Interviewer with 15+ years of experience in hiring for top tech companies. Your job is to create HIGHLY TARGETED interview questions that:

1. Test the candidate's ACTUAL skills from their resume
2. Verify claims made in the resume
3. Assess fit for THIS SPECIFIC job role
4. Identify gaps between resume and job requirements

🎯 QUESTION GENERATION RULES:

1. TECHNICAL QUESTIONS (50%):
   - Ask about specific technologies mentioned in BOTH resume AND job requirements
   - Create scenario-based coding/design questions
   - Test depth of knowledge, not just surface familiarity
   - Include questions about projects mentioned in resume

2. BEHAVIORAL QUESTIONS (25%):
   - Use STAR format (Situation, Task, Action, Result)
   - Focus on skills required for the job
   - Ask about real experiences from their resume

3. SITUATIONAL QUESTIONS (25%):
   - Create realistic job scenarios they would face
   - Test problem-solving abilities
   - Assess decision-making skills

⚠️ IMPORTANT:
- Questions must be SPECIFIC, not generic
- Reference actual technologies from job requirements
- If resume mentions a project, ask about it specifically
- Difficulty should match job level (Junior/Mid/Senior)
- Each question must have clear expected_keywords for evaluation"""

        user_prompt = f"""Create exactly {num_questions} interview questions for this candidate and job.

📄 CANDIDATE'S RESUME:
{resume_text[:4000]}

📋 JOB DESCRIPTION:
{job_description}

✅ JOB REQUIREMENTS:
{job_requirements}

Generate questions in this EXACT JSON format:
{{
    "questions": [
        {{
            "question": "Specific interview question here",
            "type": "Technical|Behavioral|Situational|General",
            "difficulty": "Easy|Medium|Hard",
            "expected_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
            "evaluation_criteria": "What makes a good answer - be specific"
        }}
    ]
}}

DISTRIBUTION:
- {int(num_questions * 0.5)} Technical questions (test actual skills)
- {int(num_questions * 0.25)} Behavioral questions (STAR format)
- {int(num_questions * 0.25)} Situational questions (job scenarios)

REMEMBER:
- Questions must be RELEVANT to both resume and job
- Include 4-6 expected_keywords for each question
- Technical questions should test skills from job requirements
- Behavioral questions should use "Tell me about a time when..."
- Situational questions should use "How would you handle..."

Return ONLY valid JSON, no additional text."""

        try:
            response = self._make_request(system_prompt, user_prompt, max_tokens=4000)
            
            # Parse JSON from response
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    questions_data = json.loads(json_match.group())
                    return questions_data.get('questions', [])
            return []
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            return self._generate_fallback_questions(num_questions)
        except Exception as e:
            print(f"Question Generation Error: {e}")
            return self._generate_fallback_questions(num_questions)
    
    def _generate_fallback_questions(self, num_questions):
        """Generate generic questions if API fails"""
        fallback = [
            {"question": "Tell me about yourself and your professional background.", "type": "General", "difficulty": "Easy", "expected_keywords": ["experience", "skills", "background"]},
            {"question": "What are your greatest strengths relevant to this position?", "type": "Behavioral", "difficulty": "Easy", "expected_keywords": ["strength", "skill", "ability"]},
            {"question": "Describe a challenging project you've worked on.", "type": "Behavioral", "difficulty": "Medium", "expected_keywords": ["challenge", "solution", "outcome"]},
            {"question": "How do you stay updated with the latest industry trends?", "type": "General", "difficulty": "Easy", "expected_keywords": ["learning", "trends", "development"]},
            {"question": "Describe a time when you had to work under pressure.", "type": "Situational", "difficulty": "Medium", "expected_keywords": ["pressure", "deadline", "manage"]},
            {"question": "What technical skills make you suitable for this role?", "type": "Technical", "difficulty": "Medium", "expected_keywords": ["skills", "experience", "proficiency"]},
            {"question": "How do you approach problem-solving in your work?", "type": "Situational", "difficulty": "Medium", "expected_keywords": ["analyze", "solution", "approach"]},
            {"question": "Describe your experience with team collaboration.", "type": "Behavioral", "difficulty": "Easy", "expected_keywords": ["team", "collaboration", "communication"]},
            {"question": "What are your career goals for the next 5 years?", "type": "General", "difficulty": "Easy", "expected_keywords": ["goals", "growth", "career"]},
            {"question": "Do you have any questions about the role or company?", "type": "General", "difficulty": "Easy", "expected_keywords": ["questions", "curiosity", "interest"]}
        ]
        return fallback[:num_questions]
    
    def analyze_answer(self, question, answer_transcript, expected_keywords):
        """Analyze candidate's answer for knowledge score"""
        
        if not answer_transcript or len(answer_transcript.strip()) < 10:
            return {
                'score': 0,
                'feedback': 'No meaningful answer provided',
                'keywords_matched': [],
                'keywords_missed': expected_keywords.split(',') if isinstance(expected_keywords, str) else expected_keywords
            }
        
        system_prompt = """You are an expert interview evaluator. 
        Analyze the candidate's answer for relevance, depth, and quality.
        Be fair but thorough in your assessment."""
        
        user_prompt = f"""Evaluate this interview answer:

QUESTION: {question}

CANDIDATE'S ANSWER: {answer_transcript}

EXPECTED KEYWORDS/CONCEPTS: {expected_keywords}

Provide evaluation in JSON format:
{{
    "score": <0-100 integer>,
    "feedback": "Brief constructive feedback",
    "keywords_matched": ["list", "of", "matched", "keywords"],
    "keywords_missed": ["list", "of", "missed", "keywords"],
    "strengths": ["strength1", "strength2"],
    "improvements": ["area1", "area2"]
}}

Scoring criteria:
- 90-100: Exceptional answer with deep insight
- 70-89: Good answer covering key points
- 50-69: Adequate but lacking depth
- 30-49: Partial answer, missed key points
- 0-29: Poor or irrelevant answer

Return ONLY valid JSON."""

        try:
            response = self._make_request(system_prompt, user_prompt, max_tokens=1000)
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"Answer Analysis Error: {e}")
        
        # Fallback: Simple keyword matching
        keywords = expected_keywords.split(',') if isinstance(expected_keywords, str) else expected_keywords
        answer_lower = answer_transcript.lower()
        matched = [kw.strip() for kw in keywords if kw.strip().lower() in answer_lower]
        missed = [kw.strip() for kw in keywords if kw.strip().lower() not in answer_lower]
        score = (len(matched) / len(keywords)) * 100 if keywords else 50
        
        return {
            'score': round(score),
            'feedback': 'Automated keyword-based evaluation',
            'keywords_matched': matched,
            'keywords_missed': missed
        }
    
    def generate_resume_feedback(self, resume_text, job_description):
        """Generate AI feedback on resume-job fit"""
        
        system_prompt = """You are a career counselor and resume expert.
        Provide actionable feedback to improve resume-job alignment."""
        
        user_prompt = f"""Analyze this resume against the job description:

RESUME:
{resume_text[:2500]}

JOB DESCRIPTION:
{job_description[:1500]}

Provide feedback in JSON format:
{{
    "match_percentage": <0-100>,
    "strengths": ["strength1", "strength2", "strength3"],
    "gaps": ["gap1", "gap2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "summary": "Brief 2-3 sentence summary"
}}

Return ONLY valid JSON."""

        try:
            response = self._make_request(system_prompt, user_prompt, max_tokens=1000)
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"Resume Feedback Error: {e}")
        
        return {
            "match_percentage": 50,
            "strengths": ["Unable to analyze"],
            "gaps": ["Unable to analyze"],
            "recommendations": ["Please try again"],
            "summary": "Automated analysis unavailable"
        }
    
    def generate_evaluation_summary(self, resume_score, confidence_score, communication_score, 
                                     knowledge_score, overall_score, candidate_name, job_title):
        """
        Generate an AI-powered evaluation summary for HR based on all pillar scores.
        
        Args:
            resume_score: Resume matching score (0-100)
            confidence_score: Video confidence score (0-100)
            communication_score: Communication/voice score (0-100)
            knowledge_score: Answer knowledge score (0-100)
            overall_score: Weighted overall score (0-100)
            candidate_name: Name of the candidate
            job_title: Job position applied for
        
        Returns:
            dict with summary, recommendation, and strengths/weaknesses
        """
        
        system_prompt = """You are an expert HR analyst providing interview evaluation summaries.
        Be concise, professional, and actionable in your assessment."""
        
        user_prompt = f"""Generate a brief HR evaluation summary for a candidate interview.

CANDIDATE: {candidate_name}
POSITION: {job_title}

SCORES (out of 100):
- Resume Match: {resume_score:.1f}%
- Confidence Level: {confidence_score:.1f}%
- Communication Skills: {communication_score:.1f}%
- Technical Knowledge: {knowledge_score:.1f}%
- OVERALL SCORE: {overall_score:.1f}%

Provide evaluation in JSON format:
{{
    "summary": "2-3 sentence professional summary for HR reviewing this candidate",
    "recommendation": "Strong Hire|Hire|Consider|On Hold|Do Not Hire",
    "top_strengths": ["strength1", "strength2"],
    "areas_of_concern": ["concern1", "concern2"],
    "interview_highlights": "1 sentence about notable interview performance"
}}

Be balanced and fair. Consider that:
- 80+ is excellent
- 70-79 is good
- 60-69 is average
- Below 60 needs attention

Return ONLY valid JSON."""

        try:
            response = self._make_request(system_prompt, user_prompt, max_tokens=800)
            if response:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            print(f"Evaluation Summary Error: {e}")
        
        # Fallback summary based on scores
        if overall_score >= 80:
            recommendation = "Strong Hire"
            summary = f"{candidate_name} demonstrated excellent performance across all evaluation criteria for the {job_title} position."
        elif overall_score >= 70:
            recommendation = "Hire"
            summary = f"{candidate_name} showed strong qualifications and performed well in the interview for {job_title}."
        elif overall_score >= 60:
            recommendation = "Consider"
            summary = f"{candidate_name} met basic requirements for {job_title} but may need additional evaluation."
        else:
            recommendation = "On Hold"
            summary = f"{candidate_name} showed potential but scored below expectations for the {job_title} role."
        
        return {
            "summary": summary,
            "recommendation": recommendation,
            "top_strengths": self._identify_strengths(resume_score, confidence_score, communication_score, knowledge_score),
            "areas_of_concern": self._identify_concerns(resume_score, confidence_score, communication_score, knowledge_score),
            "interview_highlights": "Automated evaluation - manual review recommended."
        }
    
    def _identify_strengths(self, resume, confidence, communication, knowledge):
        """Identify top strengths based on scores"""
        scores = {
            "Resume alignment with job requirements": resume,
            "Interview confidence and presence": confidence,
            "Communication clarity": communication,
            "Technical knowledge depth": knowledge
        }
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [name for name, score in sorted_scores[:2] if score >= 60]
    
    def _identify_concerns(self, resume, confidence, communication, knowledge):
        """Identify areas of concern based on scores"""
        scores = {
            "Resume-job fit": resume,
            "Confidence during interview": confidence,
            "Communication skills": communication,
            "Technical knowledge": knowledge
        }
        sorted_scores = sorted(scores.items(), key=lambda x: x[1])
        return [name for name, score in sorted_scores[:2] if score < 60]


class AIEngine:
    """Main AI Engine combining all components"""
    
    def __init__(self, groq_api_key=None):
        self.parser = ResumeParser()
        self.scorer = ResumeScorer()
        self.groq = GroqAIEngine(groq_api_key)
    
    def process_application(self, resume_path, job_description, job_requirements):
        """Process a job application - extract, score, and analyze resume"""
        
        # Extract resume text
        resume_text = self.parser.extract_text_from_pdf(resume_path)
        if not resume_text:
            return {
                'success': False,
                'error': 'Could not extract text from resume',
                'score': 0
            }
        
        # Score resume
        score, analysis_json = self.scorer.score_resume(resume_text, job_description, job_requirements)
        analysis = json.loads(analysis_json)
        
        return {
            'success': True,
            'resume_text': resume_text,
            'score': score,
            'analysis': analysis,
            'should_shortlist': score >= 70
        }
    
    def prepare_interview(self, resume_text, job_description, job_requirements, num_questions=10):
        """Prepare interview by generating questions"""
        questions = self.groq.generate_interview_questions(
            resume_text, job_description, job_requirements, num_questions
        )
        return questions
    
    def evaluate_interview_answer(self, question, transcript, expected_keywords):
        """Evaluate a single interview answer"""
        return self.groq.analyze_answer(question, transcript, expected_keywords)


# Utility function for testing
def test_ai_engine():
    """Test the AI engine components"""
    engine = AIEngine()
    
    # Test resume scoring
    sample_resume = """
    John Doe
    Software Engineer with 5 years of experience
    Skills: Python, JavaScript, React, Node.js, SQL, AWS
    Education: B.Tech in Computer Science
    Experience: Built scalable web applications, Led team of 5 developers
    """
    
    sample_jd = """
    We are looking for a Senior Software Engineer with experience in
    Python, JavaScript, and cloud technologies. Must have experience
    building web applications and working in agile teams.
    """
    
    sample_requirements = """
    - 3+ years experience in Python
    - Experience with React or Angular
    - Knowledge of AWS or GCP
    - Strong communication skills
    """
    
    score, analysis = engine.scorer.score_resume(sample_resume, sample_jd, sample_requirements)
    print(f"Resume Score: {score}")
    print(f"Analysis: {analysis}")


if __name__ == "__main__":
    test_ai_engine()
