# pyright: reportMissingImports=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
"""
Communication Analyzer Module (Pillar 3)
Analyze audio transcript for communication quality
Evaluates: Clarity, Sentence Structure, Vocabulary, Fluency
Output: Communication Score percentage
"""
import os
import re
import json
from typing import Optional, Dict, List, Any
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords

# Ensure NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Try to import textstat for readability
textstat = None
try:
    import textstat as ts
    textstat = ts
except ImportError:
    print("[COMMUNICATION_ANALYZER] textstat not available, using fallback methods")


class CommunicationAnalyzer:
    """
    Independent Communication Analysis Module
    Analyzes speech transcript for communication quality
    Returns Communication Score %
    """
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
        # Filler words that indicate poor communication
        self.filler_words = {
            'um', 'uh', 'like', 'you know', 'basically', 'actually', 'literally',
            'so', 'well', 'right', 'okay', 'i mean', 'sort of', 'kind of',
            'you see', 'honestly', 'frankly', 'anyway', 'whatever'
        }
        
        # Professional vocabulary indicators
        self.professional_words = {
            'therefore', 'furthermore', 'however', 'moreover', 'consequently',
            'specifically', 'particularly', 'additionally', 'subsequently',
            'effectively', 'efficiently', 'strategically', 'significantly',
            'implement', 'analyze', 'develop', 'optimize', 'integrate',
            'collaborate', 'coordinate', 'facilitate', 'demonstrate'
        }
    
    def analyze_clarity(self, transcript: str) -> Dict:
        """
        Analyze clarity of speech
        Measures: sentence structure, completeness, coherence
        """
        try:
            if not transcript or len(transcript.strip()) < 10:
                return {'score': 0, 'details': 'No transcript'}
            
            sentences = sent_tokenize(transcript)
            words = word_tokenize(transcript.lower())
            word_count = len([w for w in words if w.isalnum()])
            
            if not sentences or word_count == 0:
                return {'score': 0, 'details': 'No valid content'}
            
            # Average words per sentence (ideal: 15-20)
            avg_words_per_sentence = word_count / len(sentences)
            
            # Score based on sentence length
            if 10 <= avg_words_per_sentence <= 25:
                length_score = 100
            elif 5 <= avg_words_per_sentence < 10:
                length_score = 60 + (avg_words_per_sentence - 5) * 8
            elif 25 < avg_words_per_sentence <= 35:
                length_score = 100 - (avg_words_per_sentence - 25) * 4
            else:
                length_score = 40
            
            # Check for complete sentences (ending with punctuation)
            complete_sentences = sum(1 for s in sentences if s.strip()[-1] in '.!?')
            completeness_score = (complete_sentences / len(sentences)) * 100
            
            # Overall clarity
            clarity_score = (length_score * 0.5 + completeness_score * 0.5)
            
            return {
                'score': round(clarity_score, 2),
                'avg_words_per_sentence': round(avg_words_per_sentence, 1),
                'sentence_count': len(sentences),
                'complete_sentences': complete_sentences,
                'word_count': word_count
            }
            
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def analyze_vocabulary(self, transcript: str) -> Dict:
        """
        Analyze vocabulary usage
        Measures: variety, professional terms, filler word frequency
        """
        try:
            if not transcript or len(transcript.strip()) < 10:
                return {'score': 0, 'details': 'No transcript'}
            
            words = word_tokenize(transcript.lower())
            all_words = [w for w in words if w.isalnum()]
            content_words = [w for w in all_words if w not in self.stop_words and len(w) > 2]
            
            if not all_words:
                return {'score': 0, 'details': 'No words found'}
            
            # Vocabulary diversity (unique words / total words)
            unique_words = set(content_words)
            diversity_ratio = len(unique_words) / len(content_words) if content_words else 0
            diversity_score = min(100, diversity_ratio * 150)  # Scale up
            
            # Filler word penalty
            filler_count = sum(transcript.lower().count(f) for f in self.filler_words)
            filler_ratio = filler_count / len(all_words) if all_words else 0
            filler_penalty = min(30, filler_ratio * 500)
            
            # Professional vocabulary bonus
            professional_count = sum(1 for w in content_words if w in self.professional_words)
            professional_bonus = min(20, professional_count * 4)
            
            # Calculate final vocabulary score
            vocab_score = diversity_score - filler_penalty + professional_bonus
            vocab_score = max(0, min(100, vocab_score))
            
            return {
                'score': round(vocab_score, 2),
                'unique_words': len(unique_words),
                'total_words': len(all_words),
                'diversity_ratio': round(diversity_ratio, 3),
                'filler_count': filler_count,
                'professional_terms': professional_count
            }
            
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def analyze_fluency(self, transcript: str, duration_seconds: float = 0) -> Dict:
        """
        Analyze speech fluency
        Measures: speaking rate, pauses, repetitions
        """
        try:
            if not transcript or len(transcript.strip()) < 10:
                return {'score': 0, 'details': 'No transcript'}
            
            words = word_tokenize(transcript.lower())
            all_words = [w for w in words if w.isalnum()]
            word_count = len(all_words)
            
            # Words per minute (if duration provided)
            if duration_seconds > 0:
                wpm = (word_count / duration_seconds) * 60
                # Ideal speaking rate: 120-150 WPM
                if 100 <= wpm <= 170:
                    rate_score = 100
                elif 70 <= wpm < 100:
                    rate_score = 60 + (wpm - 70) * 1.33
                elif 170 < wpm <= 200:
                    rate_score = 100 - (wpm - 170) * 2
                else:
                    rate_score = 50
            else:
                wpm = 0
                rate_score = 70  # Default without timing
            
            # Check for repetitions
            word_pairs = [f"{all_words[i]} {all_words[i+1]}" for i in range(len(all_words)-1)]
            repetitions = len(word_pairs) - len(set(word_pairs))
            repetition_ratio = repetitions / len(word_pairs) if word_pairs else 0
            repetition_penalty = min(20, repetition_ratio * 200)
            
            # Check for stuttering patterns (same word repeated consecutively)
            stutter_count = sum(1 for i in range(len(all_words)-1) if all_words[i] == all_words[i+1])
            stutter_penalty = min(15, stutter_count * 3)
            
            fluency_score = rate_score - repetition_penalty - stutter_penalty
            fluency_score = max(0, min(100, fluency_score))
            
            return {
                'score': round(fluency_score, 2),
                'words_per_minute': round(wpm, 1) if wpm > 0 else 'N/A',
                'word_count': word_count,
                'repetitions': repetitions,
                'stutters': stutter_count
            }
            
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def analyze_readability(self, transcript: str) -> Dict:
        """
        Analyze readability/complexity of language
        Uses textstat if available, otherwise fallback
        """
        try:
            if not transcript or len(transcript.strip()) < 50:
                return {'score': 0, 'details': 'Insufficient text for readability analysis'}
            
            if textstat:
                # Use textstat for accurate readability
                flesch_score = textstat.flesch_reading_ease(transcript)
                grade_level = textstat.flesch_kincaid_grade(transcript)
                
                # Ideal for professional communication: grade 8-12
                if 8 <= grade_level <= 12:
                    readability_score = 100
                elif 6 <= grade_level < 8:
                    readability_score = 80 + (grade_level - 6) * 10
                elif 12 < grade_level <= 14:
                    readability_score = 100 - (grade_level - 12) * 10
                else:
                    readability_score = 60
                
                return {
                    'score': round(readability_score, 2),
                    'flesch_reading_ease': round(flesch_score, 1),
                    'grade_level': round(grade_level, 1)
                }
            else:
                # Fallback: simple syllable-based analysis
                words = word_tokenize(transcript.lower())
                word_list = [w for w in words if w.isalnum()]
                
                # Estimate complexity by average word length
                avg_word_length = sum(len(w) for w in word_list) / len(word_list) if word_list else 0
                
                if 4 <= avg_word_length <= 6:
                    readability_score = 100
                elif 3 <= avg_word_length < 4:
                    readability_score = 70 + (avg_word_length - 3) * 30
                elif 6 < avg_word_length <= 8:
                    readability_score = 100 - (avg_word_length - 6) * 15
                else:
                    readability_score = 60
                
                return {
                    'score': round(readability_score, 2),
                    'avg_word_length': round(avg_word_length, 2)
                }
                
        except Exception as e:
            return {'score': 0, 'error': str(e)}
    
    def analyze(self, transcript: str, duration_seconds: float = 0) -> Dict:
        """
        Main analysis method - comprehensive communication evaluation
        
        Args:
            transcript: Speech transcript text
            duration_seconds: Duration of speech in seconds (optional)
        
        Returns:
            dict: {
                'score': float (0-100),
                'status': 'success' or 'error',
                'clarity': dict,
                'vocabulary': dict,
                'fluency': dict,
                'readability': dict,
                'analysis_detail': str (JSON),
                'error': str or None
            }
        """
        try:
            print(f"\n{'='*50}")
            print(f"🎙️ [COMMUNICATION_ANALYZER] Starting analysis...")
            print(f"{'='*50}")
            print(f"   📝 Transcript length: {len(transcript)} chars")
            
            if not transcript or len(transcript.strip()) < 20:
                return {
                    'score': 0,
                    'status': 'error',
                    'clarity': {},
                    'vocabulary': {},
                    'fluency': {},
                    'readability': {},
                    'analysis_detail': json.dumps({'error': 'Insufficient transcript'}),
                    'error': 'Transcript is too short for analysis'
                }
            
            # Analyze all components
            clarity = self.analyze_clarity(transcript)
            vocabulary = self.analyze_vocabulary(transcript)
            fluency = self.analyze_fluency(transcript, duration_seconds)
            readability = self.analyze_readability(transcript)
            
            print(f"   ✅ Clarity Score: {clarity['score']}%")
            print(f"   ✅ Vocabulary Score: {vocabulary['score']}%")
            print(f"   ✅ Fluency Score: {fluency['score']}%")
            print(f"   ✅ Readability Score: {readability['score']}%")
            
            # Calculate weighted overall score
            overall_score = (
                clarity['score'] * 0.30 +
                vocabulary['score'] * 0.25 +
                fluency['score'] * 0.25 +
                readability['score'] * 0.20
            )
            
            analysis_detail = {
                'clarity': clarity,
                'vocabulary': vocabulary,
                'fluency': fluency,
                'readability': readability,
                'weights': {
                    'clarity': 0.30,
                    'vocabulary': 0.25,
                    'fluency': 0.25,
                    'readability': 0.20
                }
            }
            
            print(f"\n{'='*50}")
            print(f"✅ [COMMUNICATION_ANALYZER] Analysis complete!")
            print(f"   📊 Overall Communication Score: {overall_score:.1f}%")
            print(f"{'='*50}")
            
            return {
                'score': round(overall_score, 2),
                'status': 'success',
                'clarity': clarity,
                'vocabulary': vocabulary,
                'fluency': fluency,
                'readability': readability,
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
                'clarity': {},
                'vocabulary': {},
                'fluency': {},
                'readability': {},
                'analysis_detail': json.dumps({'error': str(e)}),
                'error': str(e)
            }


# Singleton instance
_analyzer_instance = None

def get_analyzer():
    """Get or create singleton analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CommunicationAnalyzer()
    return _analyzer_instance


def analyze_communication(transcript: str, duration_seconds: float = 0) -> Dict:
    """
    Convenience function for communication analysis
    
    Args:
        transcript: Speech transcript
        duration_seconds: Speech duration in seconds
    
    Returns:
        dict with 'score', 'status', 'clarity', 'vocabulary', 'fluency', 'readability', 'error'
    """
    analyzer = get_analyzer()
    return analyzer.analyze(transcript, duration_seconds)


if __name__ == "__main__":
    print("Communication Analyzer Module - Test")
    print("="*50)
    
    test_transcript = """
    Thank you for the opportunity to discuss my experience. I have been working 
    as a software developer for the past five years, primarily focusing on 
    Python and JavaScript development. In my current role, I have successfully 
    implemented several microservices architectures and collaborated with 
    cross-functional teams to deliver high-quality solutions. I believe my 
    experience in agile methodologies and my strong problem-solving skills 
    would be valuable for this position. I am particularly interested in the 
    opportunity to work on challenging technical problems and contribute to 
    the team's success.
    """
    
    result = analyze_communication(test_transcript, duration_seconds=60)
    print(f"\nResult: {json.dumps(result, indent=2)}")
