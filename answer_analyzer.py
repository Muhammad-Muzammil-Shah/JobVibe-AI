# pyright: reportArgumentType=false
# pyright: reportOptionalSubscript=false
"""
Answer/Knowledge Analyzer Module (Pillar 4)
Compare transcribed answers with interview questions
Evaluate: correctness, relevance, conceptual soundness
Output: Knowledge Score percentage
"""
import os
import re
import json
from typing import Optional, List, Dict, Any
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Ensure NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')


class AnswerAnalyzer:
    """
    Independent Answer/Knowledge Analysis Module
    Compares candidate answers with expected responses
    Returns Knowledge Score %
    """
    
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key or os.environ.get('GROQ_API_KEY')
        self.groq_client = None
        self.model = 'llama-3.3-70b-versatile'  # Updated from deprecated llama3-70b-8192
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=3000)
        
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                print("[ANSWER_ANALYZER] Groq API initialized")
            except Exception as e:
                print(f"[ANSWER_ANALYZER] Groq init failed: {e}")
    
    def _call_groq(self, system_prompt: str, user_prompt: str, max_tokens: int = 1500):
        """Make a request to Groq API"""
        if not self.groq_client:
            return None
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"   ⚠️ Groq API error: {e}")
            return None
    
    def calculate_keyword_match(self, answer: str, expected_keywords: str) -> float:
        """Calculate percentage of expected keywords found in answer"""
        if not expected_keywords or not answer:
            return 0.0  # Return 0 if no content to match
        
        # Parse keywords
        keywords = [k.strip().lower() for k in expected_keywords.split(',') if k.strip()]
        if not keywords:
            return 0.0
        
        answer_lower = answer.lower()
        matched = sum(1 for kw in keywords if kw in answer_lower)
        
        return (matched / len(keywords)) * 100
    
    def calculate_similarity(self, answer: str, question: str) -> float:
        """Calculate relevance using cosine similarity"""
        try:
            if not answer or not question:
                return 0.0
            
            # Add question context to make it more relevant
            combined_text = f"{question}"
            documents = [answer, combined_text]
            
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])  # type: ignore
            return float(similarity[0][0]) * 100
            
        except Exception as e:
            print(f"   ⚠️ Similarity error: {e}")
            return 0.0
    
    def analyze_answer_length(self, answer: str, min_words: int = 20) -> Dict:
        """Analyze answer length and completeness"""
        if not answer:
            return {'score': 0, 'word_count': 0, 'sentence_count': 0}
        
        words = word_tokenize(answer)
        sentences = sent_tokenize(answer)
        
        word_count = len([w for w in words if w.isalnum()])
        sentence_count = len(sentences)
        
        # Score based on length
        if word_count < min_words:
            length_score = (word_count / min_words) * 60
        elif word_count < min_words * 3:
            length_score = 60 + ((word_count - min_words) / (min_words * 2)) * 30
        else:
            length_score = 90 + min(10, (word_count - min_words * 3) / 20)
        
        return {
            'score': min(100, length_score),
            'word_count': word_count,
            'sentence_count': sentence_count
        }
    
    def evaluate_with_ai(self, question: str, answer: str, expected_keywords: str = "") -> Dict:
        """Use AI to evaluate answer quality"""
        if not self.groq_client:
            return {'score': None, 'feedback': 'AI evaluation not available'}
        
        system_prompt = """You are an expert interview evaluator. Analyze the candidate's answer to the interview question.
        
Evaluate based on:
1. Correctness - Is the answer factually accurate?
2. Relevance - Does it address the question directly?
3. Completeness - Does it cover key aspects?
4. Technical Depth - For technical questions, does it show understanding?
5. Communication - Is it well-structured and clear?

Respond in JSON format only:
{
    "score": <number 0-100>,
    "correctness": <number 0-100>,
    "relevance": <number 0-100>,
    "completeness": <number 0-100>,
    "technical_depth": <number 0-100>,
    "feedback": "<brief constructive feedback>",
    "key_points_covered": ["point1", "point2"],
    "missing_points": ["point1", "point2"]
}"""
        
        user_prompt = f"""Question: {question}

Expected Keywords/Concepts: {expected_keywords if expected_keywords else 'Not specified'}

Candidate's Answer: {answer}

Evaluate this answer and provide scores in JSON format."""
        
        try:
            response = self._call_groq(system_prompt, user_prompt)
            
            if response:
                # Parse JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
            
            return {'score': None, 'feedback': 'Could not parse AI response'}
            
        except Exception as e:
            print(f"   ⚠️ AI evaluation error: {e}")
            return {'score': None, 'feedback': str(e)}
    
    def evaluate_single_answer(self, question: str, answer: str, expected_keywords: str = "") -> Dict:
        """
        Evaluate a single answer
        
        Returns:
            dict: {
                'score': float (0-100),
                'keyword_score': float,
                'relevance_score': float,
                'length_analysis': dict,
                'ai_evaluation': dict or None,
                'feedback': str
            }
        """
        try:
            print(f"\n   📝 Evaluating answer for: {question[:50]}...")
            
            if not answer or len(answer.strip()) < 10:
                return {
                    'score': 0,
                    'status': 'error',
                    'error': 'No answer provided or answer too short',
                    'feedback': 'No substantial answer detected'
                }
            
            # Calculate component scores
            keyword_score = self.calculate_keyword_match(answer, expected_keywords)
            relevance_score = self.calculate_similarity(answer, question)
            length_analysis = self.analyze_answer_length(answer)
            
            # Try AI evaluation
            ai_eval = self.evaluate_with_ai(question, answer, expected_keywords)
            ai_score = ai_eval.get('score') if ai_eval.get('score') is not None else None
            
            # Calculate final score
            if ai_score is not None:
                # Weight AI heavily if available
                final_score = (
                    ai_score * 0.50 +
                    keyword_score * 0.20 +
                    relevance_score * 0.15 +
                    length_analysis['score'] * 0.15
                )
            else:
                # Fallback without AI
                final_score = (
                    keyword_score * 0.40 +
                    relevance_score * 0.35 +
                    length_analysis['score'] * 0.25
                )
            
            print(f"      ✅ Keyword Match: {keyword_score:.1f}%")
            print(f"      ✅ Relevance: {relevance_score:.1f}%")
            print(f"      ✅ AI Score: {ai_score if ai_score else 'N/A'}")
            print(f"      ✅ Final Score: {final_score:.1f}%")
            
            return {
                'score': round(final_score, 2),
                'status': 'success',
                'keyword_score': round(keyword_score, 2),
                'relevance_score': round(relevance_score, 2),
                'length_analysis': length_analysis,
                'ai_evaluation': ai_eval if ai_score is not None else None,
                'feedback': ai_eval.get('feedback', 'Evaluation complete')
            }
            
        except Exception as e:
            print(f"      ❌ Evaluation error: {e}")
            return {
                'score': 0,  # Return 0 on error - not fake score
                'status': 'error',
                'error': str(e),
                'feedback': f'Evaluation error: {str(e)}'
            }
    
    def analyze(self, questions: List[Dict], transcript: str) -> Dict:
        """
        Main analysis method - evaluate all answers
        
        Args:
            questions: List of dicts with 'question_text', 'expected_keywords'
            transcript: Full interview transcript
        
        Returns:
            dict: {
                'score': float (overall 0-100),
                'status': 'success' or 'error',
                'individual_scores': list,
                'analysis_detail': str (JSON),
                'error': str or None
            }
        """
        try:
            print(f"\n{'='*50}")
            print(f"💡 [ANSWER_ANALYZER] Starting knowledge evaluation...")
            print(f"{'='*50}")
            print(f"   📋 Questions: {len(questions)}")
            print(f"   📝 Transcript length: {len(transcript)} chars")
            
            if not transcript or len(transcript.strip()) < 20:
                return {
                    'score': 0,
                    'status': 'error',
                    'individual_scores': [],
                    'analysis_detail': json.dumps({'error': 'No transcript available'}),
                    'error': 'Transcript is empty or too short'
                }
            
            if not questions:
                return {
                    'score': 0,
                    'status': 'error',
                    'individual_scores': [],
                    'analysis_detail': json.dumps({'error': 'No questions provided'}),
                    'error': 'No questions to evaluate against'
                }
            
            # Evaluate each question against the transcript
            individual_scores = []
            
            for i, q in enumerate(questions):
                question_text = q.get('question_text', q.get('text', ''))
                expected_keywords = q.get('expected_keywords', '')
                
                result = self.evaluate_single_answer(
                    question_text,
                    transcript,
                    expected_keywords
                )
                
                individual_scores.append({
                    'question_index': i + 1,
                    'question': question_text[:100],
                    'score': result['score'],
                    'feedback': result.get('feedback', '')
                })
            
            # Calculate overall knowledge score
            scores = [s['score'] for s in individual_scores]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            analysis_detail = {
                'questions_evaluated': len(questions),
                'transcript_length': len(transcript),
                'individual_scores': individual_scores,
                'ai_used': self.groq_client is not None
            }
            
            print(f"\n{'='*50}")
            print(f"✅ [ANSWER_ANALYZER] Evaluation complete!")
            print(f"   📊 Overall Knowledge Score: {overall_score:.1f}%")
            print(f"{'='*50}")
            
            return {
                'score': round(overall_score, 2),
                'status': 'success',
                'individual_scores': individual_scores,
                'analysis_detail': json.dumps(analysis_detail),
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'score': 0,
                'status': 'error',
                'individual_scores': [],
                'analysis_detail': json.dumps({'error': str(e)}),
                'error': str(e)
            }


# Singleton instance
_analyzer_instance = None

def get_analyzer(api_key: Optional[str] = None):
    """Get or create singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = AnswerAnalyzer(api_key)
    return _analyzer_instance


def evaluate_knowledge(questions: List[Dict], transcript: str, api_key: Optional[str] = None) -> Dict:
    """
    Convenience function for knowledge evaluation
    
    Args:
        questions: List of question dicts
        transcript: Full interview transcript
        api_key: Optional Groq API key
    
    Returns:
        dict with 'score', 'status', 'individual_scores', 'analysis_detail', 'error'
    """
    analyzer = get_analyzer(api_key)
    return analyzer.analyze(questions, transcript)


if __name__ == "__main__":
    print("Answer Analyzer Module - Test")
    print("="*50)
    
    # Test data
    test_questions = [
        {
            'question_text': 'What is Python and why is it popular?',
            'expected_keywords': 'python, programming, easy, readable, libraries'
        },
        {
            'question_text': 'Explain Object Oriented Programming',
            'expected_keywords': 'class, object, inheritance, encapsulation, polymorphism'
        }
    ]
    
    test_transcript = """
    Python is a high-level programming language known for its readability and simplicity.
    It's popular because of its easy syntax and vast library ecosystem.
    For OOP, it supports classes and objects. Inheritance allows code reuse.
    Encapsulation helps hide internal details. Polymorphism enables flexible interfaces.
    """
    
    result = evaluate_knowledge(test_questions, test_transcript)
    print(f"\nResult: {json.dumps(result, indent=2)}")
