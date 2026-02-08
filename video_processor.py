# pyright: reportOptionalCall=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
"""
Video Processing Module (Pillar Support)
Handles: Video saving, Audio extraction, Speech-to-Text transcription
Passes transcript to Answer & Communication modules
"""
import os
import tempfile
from typing import Optional, Dict, Any

# Optional imports with availability flags
whisper = None
VideoFileClip = None
subprocess = None
wave = None

WHISPER_AVAILABLE = False
MOVIEPY_AVAILABLE = False

# MoviePy for video processing
try:
    from moviepy.video.io.VideoFileClip import VideoFileClip as VFC
    VideoFileClip = VFC
    MOVIEPY_AVAILABLE = True
except ImportError:
    print("[VIDEO_PROCESSOR] MoviePy not available")

# Whisper for speech-to-text
try:
    import whisper as whisper_module
    whisper = whisper_module
    WHISPER_AVAILABLE = True
except ImportError:
    print("[VIDEO_PROCESSOR] Whisper not available")

# subprocess for ffmpeg fallback
try:
    import subprocess as sp
    subprocess = sp
except ImportError:
    pass

# wave for audio processing
try:
    import wave as wave_module
    wave = wave_module
except ImportError:
    pass


class VideoProcessor:
    """
    Independent Video Processing Module
    Handles: Video → Audio → Text conversion
    """
    
    def __init__(self):
        self.whisper_model = None
        self.whisper_model_size = "base"
        
    def _load_whisper_model(self):
        """Lazy load Whisper model"""
        if not WHISPER_AVAILABLE:
            return False
        
        if self.whisper_model is None:
            try:
                print(f"   📥 Loading Whisper model ({self.whisper_model_size})...")
                self.whisper_model = whisper.load_model(self.whisper_model_size)
                print("   ✅ Whisper model loaded")
                return True
            except Exception as e:
                print(f"   ❌ Failed to load Whisper: {e}")
                return False
        return True
    
    def extract_audio(self, video_path, output_audio_path=None):
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_audio_path: Optional path for audio output
        
        Returns:
            dict: {'status': str, 'audio_path': str or None, 'error': str or None}
        """
        try:
            print(f"\n🎵 [VIDEO_PROCESSOR] Extracting audio from: {video_path}")
            
            if not os.path.exists(video_path):
                return {
                    'status': 'error',
                    'audio_path': None,
                    'error': f'Video file not found: {video_path}'
                }
            
            # Generate output path if not provided
            if output_audio_path is None:
                video_dir = os.path.dirname(video_path)
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_audio_path = os.path.join(video_dir, f"{video_name}_audio.wav")
            
            # Try MoviePy first
            if MOVIEPY_AVAILABLE:
                try:
                    print("   📌 Using MoviePy for extraction...")
                    video = VideoFileClip(video_path)
                    
                    if video.audio is None:
                        video.close()
                        return {
                            'status': 'error',
                            'audio_path': None,
                            'error': 'Video has no audio track'
                        }
                    
                    video.audio.write_audiofile(
                        output_audio_path,
                        fps=16000,
                        nbytes=2,
                        codec='pcm_s16le',
                        verbose=False,
                        logger=None
                    )
                    video.close()
                    
                    print(f"   ✅ Audio extracted: {output_audio_path}")
                    return {
                        'status': 'success',
                        'audio_path': output_audio_path,
                        'error': None
                    }
                    
                except Exception as e:
                    print(f"   ⚠️ MoviePy failed: {e}, trying ffmpeg...")
            
            # Fallback to ffmpeg
            if subprocess is not None:
                try:
                    print("   📌 Using ffmpeg for extraction...")
                    cmd = [
                        'ffmpeg', '-y', '-i', video_path,
                        '-vn', '-acodec', 'pcm_s16le',
                        '-ar', '16000', '-ac', '1',
                        output_audio_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0 and os.path.exists(output_audio_path):
                        print(f"   ✅ Audio extracted via ffmpeg: {output_audio_path}")
                        return {
                            'status': 'success',
                            'audio_path': output_audio_path,
                            'error': None
                        }
                    else:
                        return {
                            'status': 'error',
                            'audio_path': None,
                            'error': f'ffmpeg failed: {result.stderr}'
                        }
                        
                except Exception as e:
                    return {
                        'status': 'error',
                        'audio_path': None,
                        'error': f'ffmpeg extraction failed: {str(e)}'
                    }
            
            return {
                'status': 'error',
                'audio_path': None,
                'error': 'No audio extraction method available (install moviepy or ffmpeg)'
            }
            
        except Exception as e:
            print(f"   ❌ Audio extraction error: {e}")
            return {
                'status': 'error',
                'audio_path': None,
                'error': str(e)
            }
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe audio to text using Whisper
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            dict: {'status': str, 'transcript': str, 'segments': list, 'error': str or None}
        """
        try:
            print(f"\n📝 [VIDEO_PROCESSOR] Transcribing audio: {audio_path}")
            
            if not os.path.exists(audio_path):
                return {
                    'status': 'error',
                    'transcript': '',
                    'segments': [],
                    'error': f'Audio file not found: {audio_path}'
                }
            
            if not WHISPER_AVAILABLE:
                return {
                    'status': 'error',
                    'transcript': '',
                    'segments': [],
                    'error': 'Whisper not available. Install with: pip install openai-whisper'
                }
            
            # Load model
            if not self._load_whisper_model():
                return {
                    'status': 'error',
                    'transcript': '',
                    'segments': [],
                    'error': 'Failed to load Whisper model'
                }
            
            # Transcribe
            print("   🎙️ Transcribing...")
            result = self.whisper_model.transcribe(audio_path, fp16=False)
            
            transcript = result.get('text', '').strip()
            segments = result.get('segments', [])
            
            print(f"   ✅ Transcript length: {len(transcript)} characters")
            print(f"   ✅ Segments: {len(segments)}")
            
            return {
                'status': 'success',
                'transcript': transcript,
                'segments': segments,
                'language': result.get('language', 'unknown'),
                'error': None
            }
            
        except Exception as e:
            print(f"   ❌ Transcription error: {e}")
            return {
                'status': 'error',
                'transcript': '',
                'segments': [],
                'error': str(e)
            }
    
    def process_video(self, video_path, keep_audio=False):
        """
        Complete video processing pipeline:
        1. Extract audio from video
        2. Transcribe audio to text
        
        Args:
            video_path: Path to video file
            keep_audio: Whether to keep the extracted audio file
        
        Returns:
            dict: {
                'status': str,
                'transcript': str,
                'segments': list,
                'audio_path': str or None,
                'video_duration': float,
                'error': str or None
            }
        """
        try:
            print(f"\n{'='*50}")
            print(f"🎬 [VIDEO_PROCESSOR] Processing video: {video_path}")
            print(f"{'='*50}")
            
            if not os.path.exists(video_path):
                return {
                    'status': 'error',
                    'transcript': '',
                    'segments': [],
                    'audio_path': None,
                    'video_duration': 0,
                    'error': f'Video file not found: {video_path}'
                }
            
            # Get video duration
            video_duration = 0
            if MOVIEPY_AVAILABLE:
                try:
                    video = VideoFileClip(video_path)
                    video_duration = video.duration
                    video.close()
                except:
                    pass
            
            # Step 1: Extract audio
            audio_result = self.extract_audio(video_path)
            
            if audio_result['status'] == 'error':
                return {
                    'status': 'error',
                    'transcript': '',
                    'segments': [],
                    'audio_path': None,
                    'video_duration': video_duration,
                    'error': audio_result['error']
                }
            
            audio_path = audio_result['audio_path']
            
            # Step 2: Transcribe audio
            transcript_result = self.transcribe_audio(audio_path)
            
            # Cleanup audio if not needed
            if not keep_audio and audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    audio_path = None
                except:
                    pass
            
            print(f"\n{'='*50}")
            print(f"✅ [VIDEO_PROCESSOR] Processing complete!")
            print(f"{'='*50}")
            
            return {
                'status': transcript_result['status'],
                'transcript': transcript_result['transcript'],
                'segments': transcript_result.get('segments', []),
                'audio_path': audio_path if keep_audio else None,
                'video_duration': video_duration,
                'language': transcript_result.get('language', 'unknown'),
                'error': transcript_result.get('error')
            }
            
        except Exception as e:
            print(f"   ❌ Video processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'transcript': '',
                'segments': [],
                'audio_path': None,
                'video_duration': 0,
                'error': str(e)
            }
    
    def get_video_info(self, video_path):
        """Get basic video information"""
        try:
            if not os.path.exists(video_path):
                return {'error': 'Video not found'}
            
            info = {
                'path': video_path,
                'size_mb': os.path.getsize(video_path) / (1024 * 1024),
                'duration': 0,
                'has_audio': False
            }
            
            if MOVIEPY_AVAILABLE:
                video = VideoFileClip(video_path)
                info['duration'] = video.duration
                info['has_audio'] = video.audio is not None
                info['fps'] = video.fps
                info['size'] = video.size  # (width, height)
                video.close()
            
            return info
            
        except Exception as e:
            return {'error': str(e)}


# Singleton instance
_processor_instance = None

def get_processor():
    """Get or create singleton processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = VideoProcessor()
    return _processor_instance


def process_interview_video(video_path, keep_audio=False):
    """
    Convenience function to process interview video
    
    Returns:
        dict with 'status', 'transcript', 'segments', 'audio_path', 'video_duration', 'error'
    """
    processor = get_processor()
    return processor.process_video(video_path, keep_audio)


def extract_audio_from_video(video_path, output_path=None):
    """
    Convenience function to extract audio only
    """
    processor = get_processor()
    return processor.extract_audio(video_path, output_path)


def transcribe_video(video_path):
    """
    Convenience function to get transcript from video
    """
    result = process_interview_video(video_path, keep_audio=False)
    return result['transcript'] if result['status'] == 'success' else ''


if __name__ == "__main__":
    print("Video Processor Module - Test")
    print("="*50)
    print(f"MoviePy Available: {MOVIEPY_AVAILABLE}")
    print(f"Whisper Available: {WHISPER_AVAILABLE}")
    print("\nModule loaded successfully.")
