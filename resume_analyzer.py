# pyright: reportArgumentType=false
# pyright: reportOptionalSubscript=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnboundVariable=false
# type: ignore
"""
Resume Match Module (Pillar 1) - GROQ AI Enhanced
Analyze candidate's resume against comprehensive job description
Uses GROQ LLM for intelligent HR-style evaluation
Output: Resume Match percentage with detailed breakdown
"""
import os
import re
import json
import fitz  # PyMuPDF
from typing import Optional, Dict, List, Any

# GROQ API
groq_client = None
GROQ_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    print("[RESUME_ANALYZER] GROQ not available, using fallback scoring")

# Fallback imports for non-AI scoring
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[RESUME_ANALYZER] sklearn not available")


class ResumeAnalyzer:
    """
    AI-Powered Resume Analysis Module
    Uses GROQ LLM for intelligent HR-style resume evaluation
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key or os.environ.get('GROQ_API_KEY')
        self.groq_client = None
        
        if GROQ_AVAILABLE and self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"[RESUME_ANALYZER] GROQ client init failed: {e}")
        
        # Fallback TF-IDF vectorizer
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        
        self.skill_keywords = [
            'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'nosql', 'mongodb',
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'linux',
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp',
            'data analysis', 'data science', 'excel', 'power bi', 'tableau',
            'html', 'css', 'rest api', 'graphql', 'agile', 'scrum', 'jira',
            'communication', 'leadership', 'teamwork', 'problem solving',
            'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'typescript',
            'mysql', 'postgresql', 'redis', 'elasticsearch', 'kafka',
            'spring', 'laravel', 'rails', 'fastapi', 'nextjs', 'svelte'
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str | Dict:
        """Extract text content from PDF file"""
        try:
            if not os.path.exists(pdf_path):
                return {"error": f"PDF file not found: {pdf_path}"}
            
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                page_text = page.get_text()
                if isinstance(page_text, str):
                    text += page_text + " "
            doc.close()
            return text.strip()
        except Exception as e:
            return {"error": f"Error extracting PDF: {str(e)}"}
    
    def build_job_context(self, job_data: Dict) -> str:
        """Build job context string from 4 key sections only"""
        sections = []
        
        # 📋 Job Description
        if job_data.get('description'):
            sections.append(f"📋 JOB DESCRIPTION:\n{job_data['description']}")
        
        # ✅ Requirements
        if job_data.get('requirements'):
            sections.append(f"✅ REQUIREMENTS:\n{job_data['requirements']}")
        
        # 💼 Responsibilities
        if job_data.get('responsibilities'):
            sections.append(f"💼 RESPONSIBILITIES:\n{job_data['responsibilities']}")
        
        # 🛠️ Skills Required
        if job_data.get('skills_required'):
            sections.append(f"🛠️ SKILLS REQUIRED:\n{job_data['skills_required']}")
        
        return "\n\n".join(sections)
    
    def analyze_with_groq(self, resume_text: str, job_context: str, job_data: Dict) -> Dict:
        """
        Use GROQ LLM for intelligent HR-style resume evaluation
        Evaluates against 4 sections: Description, Requirements, Responsibilities, Skills
        """
        if not self.groq_client:
            return {'error': 'GROQ client not available'}
        
        system_prompt = """You are an expert HR Recruiter evaluating resumes for job fit. 

You will receive a job posting with 4 key sections:
📋 JOB DESCRIPTION - Overall job summary
✅ REQUIREMENTS - Required qualifications and skills
💼 RESPONSIBILITIES - Key duties of the role
🛠️ SKILLS REQUIRED - Technical and soft skills needed

Evaluate the resume against these 4 sections and provide a MATCH PERCENTAGE.

🎯 SCORING CRITERIA (100 points):

1. SKILLS MATCH (40 points)
   - Match resume skills with 🛠️ SKILLS REQUIRED
   - Give partial credit for similar/related technologies
   - Required skills = 30 pts, Bonus skills = 10 pts

2. REQUIREMENTS FIT (30 points)
   - Does resume meet ✅ REQUIREMENTS?
   - Education, experience years, certifications
   - Core qualifications mentioned in requirements

3. RESPONSIBILITIES ALIGNMENT (20 points)
   - Can candidate handle 💼 RESPONSIBILITIES?
   - Past experience matches job duties
   - Similar projects or roles

4. OVERALL FIT (10 points)
   - Resume quality and professionalism
   - Career trajectory alignment
   - Overall impression

📊 SCORE INTERPRETATION:
- 80-100%: Excellent match - Highly Recommended ✅
- 65-79%: Good match - Recommended for Interview
- 50-64%: Partial match - Consider with Reservations  
- 35-49%: Weak match - Not Recommended
- Below 35%: Poor match - Reject

BE HONEST. Don't inflate scores. If skills are missing, deduct accordingly.

RETURN ONLY THIS JSON FORMAT:
{
    "overall_score": <number 0-100>,
    "breakdown": {
        "skills_match": {"score": <0-40>, "details": "<what matched/missing>"},
        "requirements_fit": {"score": <0-30>, "details": "<how well meets requirements>"},
        "responsibilities_alignment": {"score": <0-20>, "details": "<can handle duties?>"},
        "overall_fit": {"score": <0-10>, "details": "<overall impression>"}
    },
    "matched_skills": ["skill1", "skill2"],
    "missing_skills": ["skill1", "skill2"],
    "strengths": ["strength1", "strength2"],
    "concerns": ["concern1", "concern2"],
    "recommendation": "<1-2 sentence HR recommendation>"
}"""

        user_prompt = f"""Evaluate this resume against the job posting.

=== JOB POSTING ===
{job_context}

=== CANDIDATE RESUME ===
{resume_text[:8000]}

Analyze and return JSON with match percentage."""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'status': 'success',
                    'score': result.get('overall_score', 0),
                    'breakdown': result.get('breakdown', {}),
                    'matched_skills': result.get('matched_skills', []),
                    'missing_skills': result.get('missing_skills', []),
                    'strengths': result.get('strengths', []),
                    'concerns': result.get('concerns', []),
                    'recommendation': result.get('recommendation', ''),
                    'ai_powered': True
                }
            else:
                return {'error': 'Could not parse GROQ response', 'raw': response_text}
                
        except Exception as e:
            print(f"[RESUME_ANALYZER] GROQ API error: {e}")
            return {'error': str(e)}
    
    def analyze_fallback(self, resume_text: str, job_description: str, job_requirements: str, job_skills: str) -> Dict:
        """Fallback analysis using TF-IDF when GROQ is unavailable"""
        try:
            # Combine job texts
            full_job_text = f"{job_description} {job_requirements}"
            
            # Parse job skills
            additional_skills = []
            if job_skills:
                if isinstance(job_skills, str):
                    additional_skills = [s.strip().lower() for s in job_skills.split(',')]
                else:
                    additional_skills = [s.strip().lower() for s in job_skills]
            
            # Calculate similarity
            similarity_score = 0
            if SKLEARN_AVAILABLE:
                documents = [resume_text, full_job_text]
                tfidf_matrix = self.vectorizer.fit_transform(documents)
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                similarity_score = float(similarity[0][0]) * 100
            
            # Extract skills
            resume_lower = resume_text.lower()
            all_skills = self.skill_keywords + additional_skills
            found_skills = [s for s in all_skills if s.lower() in resume_lower]
            
            # Skills match
            if additional_skills:
                matched_skills = [s for s in additional_skills if s in resume_lower]
                skills_match_pct = (len(matched_skills) / len(additional_skills)) * 100
            else:
                skills_match_pct = min(len(found_skills) * 8, 100)
            
            # Experience extraction
            exp_patterns = [
                r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
                r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
            ]
            experience = 0
            for pattern in exp_patterns:
                match = re.search(pattern, resume_text.lower())
                if match:
                    experience = int(match.group(1))
                    break
            
            # Calculate final score
            final_score = (
                similarity_score * 0.35 +
                skills_match_pct * 0.35 +
                min(experience * 3, 20) +
                10  # Base points
            )
            final_score = min(max(final_score, 0), 100)
            
            return {
                'status': 'success',
                'score': round(final_score, 2),
                'breakdown': {
                    'skills_match': {'score': round(skills_match_pct * 0.35, 1), 'details': f'{len(found_skills)} skills found'},
                    'similarity': {'score': round(similarity_score * 0.35, 1), 'details': 'TF-IDF similarity'},
                    'experience': {'score': min(experience * 3, 20), 'details': f'{experience} years detected'}
                },
                'matched_skills': found_skills[:15],
                'missing_skills': [s for s in additional_skills if s not in resume_lower][:10],
                'ai_powered': False
            }
            
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'score': 0}
    
    def analyze(self, resume_path: str, job_description: str = "", job_requirements: str = "", 
                job_skills: str = "", job_data: Optional[Dict] = None) -> Dict:
        """
        Main analysis method - analyzes resume against job
        
        Args:
            resume_path: Path to resume PDF
            job_description: Job description text
            job_requirements: Job requirements text  
            job_skills: Required skills (comma-separated)
            job_data: Full job data dict with all fields (for GROQ analysis)
        
        Returns:
            dict: {
                'score': float (0-100),
                'status': 'success' or 'error',
                'analysis': detailed analysis dict,
                'error': error message if failed
            }
        """
        try:
            print(f"\n🔍 [RESUME ANALYZER] Starting AI-powered analysis...")
            
            # Extract resume text
            resume_text = self.extract_text_from_pdf(resume_path)
            if isinstance(resume_text, dict) and 'error' in resume_text:
                return {
                    'score': 0,
                    'status': 'error',
                    'error': resume_text['error'],
                    'analysis': {}
                }
            
            if not resume_text or len(resume_text) < 50:
                return {
                    'score': 0,
                    'status': 'error',
                    'error': 'Could not extract sufficient text from resume',
                    'analysis': {}
                }
            
            print(f"   ✅ Resume text extracted: {len(resume_text)} characters")
            
            # Build job context if job_data provided
            if job_data:
                job_context = self.build_job_context(job_data)
            else:
                # Build from individual fields
                job_data = {
                    'description': job_description,
                    'requirements': job_requirements,
                    'skills_required': job_skills
                }
                job_context = self.build_job_context(job_data)
            
            # Try GROQ analysis first
            if self.groq_client:
                print(f"   🤖 Using GROQ AI for intelligent analysis...")
                groq_result = self.analyze_with_groq(resume_text, job_context, job_data)
                
                if groq_result.get('status') == 'success':
                    score = groq_result['score']
                    print(f"   ✅ AI Resume Score: {score}%")
                    print(f"   ✅ Matched Skills: {len(groq_result.get('matched_skills', []))}")
                    print(f"   ✅ Recommendation: {groq_result.get('recommendation', 'N/A')[:80]}...")
                    
                    return {
                        'score': score,
                        'status': 'success',
                        'analysis': {
                            'breakdown': groq_result.get('breakdown', {}),
                            'matched_skills': groq_result.get('matched_skills', []),
                            'missing_skills': groq_result.get('missing_skills', []),
                            'strengths': groq_result.get('strengths', []),
                            'concerns': groq_result.get('concerns', []),
                            'recommendation': groq_result.get('recommendation', ''),
                            'ai_powered': True
                        },
                        'error': None
                    }
                else:
                    print(f"   ⚠️ GROQ analysis failed, using fallback: {groq_result.get('error')}")
            
            # Fallback to TF-IDF
            print(f"   📊 Using fallback TF-IDF analysis...")
            fallback_result = self.analyze_fallback(resume_text, job_description, job_requirements, job_skills)
            
            if fallback_result.get('status') == 'success':
                print(f"   ✅ Fallback Score: {fallback_result['score']}%")
                return {
                    'score': fallback_result['score'],
                    'status': 'success',
                    'analysis': fallback_result,
                    'error': None
                }
            
            return {
                'score': 50,
                'status': 'error',
                'error': fallback_result.get('error', 'Analysis failed'),
                'analysis': {}
            }
            
        except Exception as e:
            print(f"   ❌ Resume analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'score': 0,
                'status': 'error',
                'error': str(e),
                'analysis': {}
            }


# Singleton instance for easy import
_analyzer_instance = None

def get_analyzer(api_key: Optional[str] = None) -> ResumeAnalyzer:
    """Get or create singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ResumeAnalyzer(api_key)
    return _analyzer_instance


def analyze_resume(resume_path: str, job_description: str = "", job_requirements: str = "", 
                   job_skills: str = "", job_data: Optional[Dict] = None, 
                   api_key: Optional[str] = None) -> Dict:
    """
    Convenience function for resume analysis
    
    Args:
        resume_path: Path to resume PDF
        job_description: Job description text
        job_requirements: Job requirements text
        job_skills: Required skills (comma-separated)
        job_data: Full job data dict with ALL job fields for comprehensive AI analysis
        api_key: Optional GROQ API key
    
    Returns:
        dict with 'score', 'status', 'analysis', 'error'
    """
    analyzer = get_analyzer(api_key)
    return analyzer.analyze(resume_path, job_description, job_requirements, job_skills, job_data)


if __name__ == "__main__":
    # Test the module
    print("Resume Analyzer Module - AI Powered Test")
    print("="*50)
    
    # Test with sample data
    sample_resume = "test_resume.pdf"
    sample_job = {
        'title': 'AI Engineer',
        'overview': 'We are seeking a skilled AI Engineer to design intelligent solutions.',
        'job_type': 'Full-time',
        'work_mode': 'Hybrid',
        'location': 'Karachi',
        'experience_required': '3-5 years',
        'education_required': "Bachelor's in CS/AI",
        'responsibilities': '''• Design, develop, and deploy AI & ML models
• Work on Deep Learning, NLP, Computer Vision solutions
• Build and integrate LLM-based applications''',
        'requirements': '''• Bachelor's degree in AI/CS or related field
• Strong proficiency in Python
• Experience with TensorFlow, PyTorch, or Scikit-learn''',
        'preferred_qualifications': '''• Experience with LLMs, Prompt Engineering
• Knowledge of MLOps tools (Docker, MLflow)''',
        'skills_required': 'Python, TensorFlow, PyTorch, NLP, Computer Vision, LLMs, Docker',
        'description': 'Full job description here...'
    }
    
    if os.path.exists(sample_resume):
        result = analyze_resume(sample_resume, job_data=sample_job)
        print(f"\nResult: {json.dumps(result, indent=2)}")
    else:
        print("No test resume found. Module loaded successfully.")
        print(f"GROQ Available: {GROQ_AVAILABLE}")
