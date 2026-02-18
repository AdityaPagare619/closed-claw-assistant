"""
Voice System Module
Handles Text-to-Speech (TTS) and Speech-to-Text (STT)
Optimized for ARM devices (Moto G45) with lazy loading
Supports: English, Hindi, Marathi
"""

import os
import re
import json
import time
import wave
import logging
import tempfile
import subprocess
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceError(Exception):
    """Custom exception for voice-related errors"""
    pass


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    HINGLISH = "hi-en"  # Code-switching
    MANGLISH = "mr-en"  # Code-switching


@dataclass
class VoiceConfig:
    """Voice configuration"""
    tts_engine: str = "piper"  # 'piper', 'termux'
    stt_engine: str = "whisper"  # 'whisper', 'vosk'
    language: Language = Language.ENGLISH
    speaker_id: Optional[int] = None
    speed: float = 1.0
    volume: float = 1.0


class VoiceSystem:
    """
    Voice System for TTS and STT
    Supports local models with Termux fallback on Android
    """
    
    # Language-specific Piper model mappings
    PIPER_MODELS = {
        Language.ENGLISH: "en_US-lessac-medium",
        Language.HINDI: "hi_COVID-medium",  # Community model
        Language.MARATHI: "mr_COVID-medium",  # Community model
    }
    
    # Whisper model sizes (tiny = fastest for ARM)
    WHISPER_MODELS = {
        "tiny": "ggml-tiny.bin",
        "base": "ggml-base.bin",
        "small": "ggml-small.bin",
    }
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig()
        self._piper_path: Optional[str] = None
        self._whisper_path: Optional[str] = None
        self._vosk_path: Optional[str] = None
        self._is_termux = self._detect_termux()
        self._loaded_models: Dict[str, bool] = {}
        
        # Lazy loading flags
        self._piper_loaded = False
        self._whisper_loaded = False
        self._vosk_loaded = False
        
    def _detect_termux(self) -> bool:
        """Detect if running in Termux environment"""
        return (
            os.environ.get('TERMUX_VERSION') is not None or
            os.path.exists('/data/data/com.termux/files/usr/bin/termux-media-player')
        )
    
    def _find_binary(self, name: str) -> Optional[str]:
        """Find binary in common locations"""
        search_paths = [
            name,
            f'/data/data/com.termux/files/usr/bin/{name}',
            os.path.expanduser(f'~/.local/bin/{name}'),
            os.path.expanduser(f'~/bin/{name}'),
            f'/usr/local/bin/{name}',
        ]
        
        for path in search_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        
        # Try which command
        try:
            result = subprocess.run(['which', name], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    def _lazy_load_piper(self):
        """Lazy load Piper TTS"""
        if self._piper_loaded:
            return
        
        self._piper_path = self._find_binary('piper')
        
        if self._piper_path:
            # Check for models
            model_name = self.PIPER_MODELS.get(self.config.language, self.PIPER_MODELS[Language.ENGLISH])
            model_paths = [
                f"models/piper/{model_name}.onnx",
                os.path.expanduser(f'~/.local/share/piper/{model_name}.onnx'),
                f'/data/data/com.termux/files/home/.local/share/piper/{model_name}.onnx',
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    self._piper_model = path
                    self._piper_loaded = True
                    logger.info(f"Piper loaded: {path}")
                    return
            
            logger.warning("Piper binary found but model not found")
        
        logger.info("Piper not available, will use Termux fallback")
    
    def _lazy_load_whisper(self):
        """Lazy load Whisper STT"""
        if self._whisper_loaded:
            return
        
        self._whisper_path = self._find_binary('whisper-cli') or self._find_binary('whisper')
        
        if self._whisper_path:
            # Check for tiny model (best for ARM)
            model_name = self.WHISPER_MODELS["tiny"]
            model_paths = [
                f"models/whisper/{model_name}",
                os.path.expanduser(f'~/.local/share/whisper/{model_name}'),
                f'/data/data/com.termux/files/home/.local/share/whisper/{model_name}',
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    self._whisper_model = path
                    self._whisper_loaded = True
                    logger.info(f"Whisper loaded: {path}")
                    return
            
            logger.warning("Whisper binary found but model not found")
        
        logger.info("Whisper not available, will use Vosk fallback")
    
    def _lazy_load_vosk(self):
        """Lazy load Vosk STT"""
        if self._vosk_loaded:
            return
        
        try:
            import vosk
            self._vosk_loaded = True
            self._vosk_model_path = None
            
            # Look for model
            model_paths = [
                "models/vosk-model-small-en-us-0.15",
                os.path.expanduser('~/.local/share/vosk/model'),
                '/data/data/com.termux/files/home/.local/share/vosk/model',
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    self._vosk_model_path = path
                    logger.info(f"Vosk model found: {path}")
                    break
            
            logger.info("Vosk loaded")
        except ImportError:
            logger.info("Vosk not installed, will use Termux fallback")
    
    def text_to_speech(self, text: str, language: Optional[Language] = None) -> bool:
        """
        Convert text to speech
        Returns True if successful
        """
        if not text:
            return False
        
        lang = language or self.config.language
        
        # Try Piper first (local, offline)
        self._lazy_load_piper()
        
        if self._piper_loaded and self.config.tts_engine == "piper":
            return self._tts_piper(text, lang)
        
        # Fallback to Termux
        if self._is_termux:
            return self._tts_termux(text, lang)
        
        logger.error("No TTS engine available")
        return False
    
    def _tts_piper(self, text: str, language: Language) -> bool:
        """TTS using Piper"""
        try:
            # Clean text
            text = text.strip().replace('"', '\\"')
            
            # Create temp wav file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                wav_path = f.name
            
            # Generate speech
            cmd = [
                self._piper_path,
                '--model', self._piper_model,
                '--output_file', wav_path,
            ]
            
            if self.config.speaker_id is not None:
                cmd.extend(['--speaker', str(self.config.speaker_id)])
            
            result = subprocess.run(
                cmd,
                input=text.encode(),
                capture_output=True
            )
            
            if result.returncode != 0:
                logger.error(f"Piper error: {result.stderr.decode()}")
                return False
            
            # Play audio
            return self._play_audio(wav_path)
            
        except Exception as e:
            logger.error(f"Piper TTS failed: {e}")
            return False
    
    def _tts_termux(self, text: str, language: Language) -> bool:
        """TTS using Termux"""
        try:
            # Map languages to Termux locale
            lang_map = {
                Language.ENGLISH: "en",
                Language.HINDI: "hi",
                Language.MARATHI: "mr",
            }
            
            cmd = ['termux-tts-speak']
            
            if language in lang_map:
                cmd.extend(['-l', lang_map[language]])
            
            # Pitch and rate
            cmd.extend(['-r', str(self.config.speed)])
            
            result = subprocess.run(cmd + [text], capture_output=True)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Termux TTS failed: {e}")
            return False
    
    def _play_audio(self, audio_path: str) -> bool:
        """Play audio file"""
        try:
            if self._is_termux:
                cmd = ['termux-media-player', 'play', audio_path]
            else:
                # Try common players
                for player in ['ffplay', 'aplay', 'paplay', 'play']:
                    player_path = self._find_binary(player)
                    if player_path:
                        if player == 'ffplay':
                            cmd = [player_path, '-nodisp', '-autoexit', audio_path]
                        else:
                            cmd = [player_path, audio_path]
                        break
                else:
                    logger.error("No audio player found")
                    return False
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            # Cleanup temp file
            try:
                os.unlink(audio_path)
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            return False
    
    def speech_to_text(self, duration: int = 5, language: Optional[Language] = None) -> Optional[str]:
        """
        Record and transcribe speech
        Returns transcribed text or None on failure
        """
        lang = language or self.config.language
        
        # Record audio
        audio_path = self._record_audio(duration)
        if not audio_path:
            return None
        
        # Transcribe
        result = self.transcribe_audio(audio_path, lang)
        
        # Cleanup
        try:
            os.unlink(audio_path)
        except:
            pass
        
        return result
    
    def _record_audio(self, duration: int) -> Optional[str]:
        """Record audio to file"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                wav_path = f.name
            
            if self._is_termux:
                # Use Termux microphone
                cmd = [
                    'termux-microphone-record',
                    '-l', str(duration),
                    '-f', wav_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
                if result.returncode != 0:
                    logger.error(f"Recording failed: {result.stderr.decode()}")
                    return None
            else:
                # Use arecord or similar
                cmd = [
                    'arecord',
                    '-d', str(duration),
                    '-f', 'cd',
                    '-t', 'wav',
                    wav_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
                if result.returncode != 0:
                    logger.error(f"Recording failed: {result.stderr.decode()}")
                    return None
            
            return wav_path
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None
    
    def transcribe_audio(self, audio_path: str, language: Optional[Language] = None) -> Optional[str]:
        """
        Transcribe audio file to text
        """
        lang = language or self.config.language
        
        # Try Whisper first
        self._lazy_load_whisper()
        if self._whisper_loaded and self.config.stt_engine == "whisper":
            return self._stt_whisper(audio_path, lang)
        
        # Try Vosk
        self._lazy_load_vosk()
        if self._vosk_loaded:
            return self._stt_vosk(audio_path, lang)
        
        logger.error("No STT engine available")
        return None
    
    def _stt_whisper(self, audio_path: str, language: Language) -> Optional[str]:
        """STT using Whisper"""
        try:
            cmd = [
                self._whisper_path,
                '-m', self._whisper_model,
                '-f', audio_path,
                '--no-timestamps',
                '-otxt', '-of', '/dev/stdout'
            ]
            
            # Language hint
            lang_map = {
                Language.ENGLISH: "en",
                Language.HINDI: "hi",
                Language.MARATHI: "mr",
            }
            if language in lang_map:
                cmd.extend(['-l', lang_map[language]])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Whisper error: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Whisper STT failed: {e}")
            return None
    
    def _stt_vosk(self, audio_path: str, language: Language) -> Optional[str]:
        """STT using Vosk"""
        try:
            from vosk import Model, KaldiRecognizer
            import wave
            
            if not self._vosk_model_path:
                logger.error("Vosk model not found")
                return None
            
            model = Model(self._vosk_model_path)
            
            wf = wave.open(audio_path, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                logger.error("Audio file must be WAV format mono PCM")
                return None
            
            rec = KaldiRecognizer(model, wf.getframerate())
            
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part = json.loads(rec.Result())
                    if part.get('text'):
                        results.append(part['text'])
            
            part = json.loads(rec.FinalResult())
            if part.get('text'):
                results.append(part['text'])
            
            return ' '.join(results) if results else None
            
        except Exception as e:
            logger.error(f"Vosk STT failed: {e}")
            return None
    
    def is_available(self, capability: str) -> bool:
        """Check if a voice capability is available"""
        if capability == "tts":
            self._lazy_load_piper()
            return self._piper_loaded or self._is_termux
        elif capability == "stt":
            self._lazy_load_whisper()
            self._lazy_load_vosk()
            return self._whisper_loaded or self._vosk_loaded or self._is_termux
        return False
    
    def get_status(self) -> Dict:
        """Get voice system status"""
        self._lazy_load_piper()
        self._lazy_load_whisper()
        self._lazy_load_vosk()
        
        return {
            'tts_available': self._piper_loaded or self._is_termux,
            'tts_engine': 'piper' if self._piper_loaded else ('termux' if self._is_termux else None),
            'stt_available': self._whisper_loaded or self._vosk_loaded or self._is_termux,
            'stt_engine': 'whisper' if self._whisper_loaded else ('vosk' if self._vosk_loaded else None),
            'is_termux': self._is_termux,
            'language': self.config.language.value,
        }
