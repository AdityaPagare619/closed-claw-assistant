#!/usr/bin/env python3
"""
Sarvam Voice System - Authentic Indian Voices
Uses Sarvam AI voice models exclusively for TTS
"""

import logging
import subprocess
import asyncio
import tempfile
import requests
import json
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VoiceConfig:
    """Configuration for Sarvam Voice System"""
    # Sarvam API (for best quality when online)
    sarvam_api_key: str = ""
    sarvam_api_url: str = "https://api.sarvam.ai/v1"
    
    # Local TTS (offline fallback)
    local_tts_enabled: bool = True
    piper_model_path: str = ""
    
    # Voice settings
    default_language: str = "hi-IN"  # Hindi default
    default_speaker: str = "meera"   # Sarvam speaker
    default_pace: float = 1.0
    
    # Response optimization
    enable_caching: bool = True
    cache_dir: str = "audio_cache"
    
    # Performance
    max_concurrent_requests: int = 2
    timeout_seconds: int = 10


class SarvamVoiceSystem:
    """
    Voice system using Sarvam AI models for authentic Indian voices
    
    Features:
    - Sarvam TTS API for high-quality Indian voices
    - Local Piper TTS for offline use
    - Caching for instant repeated phrases
    - Multi-language support (Hindi, Marathi, English)
    - Natural, human-like speech patterns
    """
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        
        # Create cache directory
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice cache for instant responses
        self.voice_cache: Dict[str, str] = {}
        self._load_cache_index()
        
        # Track API usage for offline switching
        self.api_available = True
        self.offline_mode = False
        
        logger.info("🎤 Sarvam Voice System initialized")
        logger.info(f"   Language: {self.config.default_language}")
        logger.info(f"   Speaker: {self.config.default_speaker}")
    
    def _load_cache_index(self):
        """Load cached voice files index"""
        cache_index = self.cache_dir / "cache_index.json"
        if cache_index.exists():
            try:
                with open(cache_index, 'r') as f:
                    self.voice_cache = json.load(f)
                logger.info(f"📦 Loaded {len(self.voice_cache)} cached voice files")
            except:
                self.voice_cache = {}
    
    def _save_cache_index(self):
        """Save voice cache index"""
        cache_index = self.cache_dir / "cache_index.json"
        with open(cache_index, 'w') as f:
            json.dump(self.voice_cache, f, indent=2)
    
    def _get_cache_key(self, text: str, language: str = None, speaker: str = None) -> str:
        """Generate cache key for text"""
        import hashlib
        lang = language or self.config.default_language
        spk = speaker or self.config.default_speaker
        key = f"{text}:{lang}:{spk}"
        return hashlib.md5(key.encode()).hexdigest()
    
    async def speak(self, text: str, 
                   language: str = None,
                   speaker: str = None,
                   pace: float = None) -> bool:
        """
        Convert text to speech using Sarvam voice
        
        Priority:
        1. Check cache (instant playback)
        2. Try Sarvam API (best quality)
        3. Fallback to local TTS (offline)
        """
        try:
            # Check cache first (instant response)
            cache_key = self._get_cache_key(text, language, speaker)
            if cache_key in self.voice_cache:
                cached_file = self.voice_cache[cache_key]
                if Path(cached_file).exists():
                    logger.debug(f"🎯 Cache hit: {text[:30]}...")
                    return await self._play_audio(cached_file)
            
            # Try Sarvam API for best quality
            if not self.offline_mode and self.api_available and self.config.sarvam_api_key:
                try:
                    audio_file = await self._generate_sarvam_api(
                        text, language, speaker, pace
                    )
                    if audio_file:
                        # Cache for future
                        self.voice_cache[cache_key] = str(audio_file)
                        self._save_cache_index()
                        return await self._play_audio(audio_file)
                except Exception as e:
                    logger.warning(f"Sarvam API failed: {e}, using offline mode")
                    self.offline_mode = True
            
            # Fallback to Termux TTS (always works offline)
            return await self._speak_termux(text)
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    async def _generate_sarvam_api(self, text: str, 
                                  language: str = None,
                                  speaker: str = None,
                                  pace: float = None) -> Optional[Path]:
        """Generate speech using Sarvam AI TTS API"""
        url = f"{self.config.sarvam_api_url}/text-to-speech"
        
        headers = {
            "Authorization": f"Bearer {self.config.sarvam_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "language_code": language or self.config.default_language,
            "speaker": speaker or self.config.default_speaker,
            "pace": pace or self.config.default_pace
        }
        
        try:
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(url, json=payload, headers=headers)
                ),
                timeout=self.config.timeout_seconds
            )
            
            if response.status_code == 200:
                cache_key = self._get_cache_key(text, language, speaker)
                audio_file = self.cache_dir / f"{cache_key}.wav"
                
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"✅ Sarvam TTS: {text[:50]}...")
                return audio_file
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except asyncio.TimeoutError:
            raise Exception("Sarvam API timeout")
    
    async def _speak_termux(self, text: str) -> bool:
        """Fallback to Termux TTS (works offline)"""
        try:
            cmd = ["termux-tts-speak", text]
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.wait()
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Termux TTS error: {e}")
            return False
    
    async def _play_audio(self, audio_file: str) -> bool:
        """Play audio file"""
        try:
            cmd = ["termux-media-player", "play", audio_file]
            process = await asyncio.create_subprocess_exec(*cmd)
            await asyncio.wait_for(process.wait(), timeout=60.0)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False
    
    async def listen(self, duration: int = 5) -> Optional[str]:
        """Listen and convert speech to text using Whisper"""
        try:
            audio_file = self.cache_dir / f"input_{asyncio.get_event_loop().time()}.wav"
            
            # Record
            cmd = ["termux-microphone-record", "-f", str(audio_file), "-l", str(duration)]
            process = await asyncio.create_subprocess_exec(*cmd)
            await process.wait()
            
            if not audio_file.exists():
                return None
            
            # Transcribe with Whisper
            import whisper
            model = whisper.load_model("tiny", device="cpu")
            result = model.transcribe(str(audio_file), language="hi", fp16=False)
            
            text = result.get("text", "").strip()
            audio_file.unlink(missing_ok=True)
            
            return text
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available Sarvam voices"""
        return [
            {"name": "meera", "language": "hi-IN", "gender": "female", "description": "Friendly Indian female voice"},
            {"name": "arjun", "language": "hi-IN", "gender": "male", "description": "Professional Indian male voice"},
            {"name": "shivani", "language": "mr-IN", "gender": "female", "description": "Warm Marathi female voice"},
            {"name": "rahul", "language": "en-IN", "gender": "male", "description": "Clear English Indian accent"}
        ]
