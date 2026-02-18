"""
Sarvam-1 2B LLM Integration Module
Handles llama.cpp server management and text generation
"""

import os
import json
import time
import logging
import requests
import subprocess
import threading
from typing import Optional, Dict, List, Generator
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM-related errors"""
    pass


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }


class SarvamBrain:
    """
    Sarvam-1 2B LLM Brain
    Manages llama.cpp server and provides text generation
    """
    
    DEFAULT_CONFIG = {
        'model_path': 'models/sarvam-1-2b-q4_0_4_4.gguf',
        'server_host': 'localhost',
        'server_port': 8080,
        'context_length': 4096,
        'threads': 4,  # Optimized for Moto G45 (ARM)
        'batch_size': 512,
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 40,
        'repeat_penalty': 1.1,
        'max_tokens': 512,
        'timeout': 30,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.server_process: Optional[subprocess.Popen] = None
        self._server_lock = threading.Lock()
        self._is_running = False
        self._chat_history: List[ChatMessage] = []
        self._max_retries = 3
        self._retry_delay = 2
        
    def _get_model_path(self) -> str:
        """Resolve model path"""
        model_path = self.config['model_path']
        if not os.path.isabs(model_path):
            # Check in common locations
            possible_paths = [
                model_path,
                os.path.expanduser(f'~/.local/share/closed-claw/{model_path}'),
                os.path.expanduser(f'~/closed-claw/{model_path}'),
                f'/data/data/com.termux/files/home/closed-claw/{model_path}',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        return model_path
    
    def start_server(self) -> bool:
        """Start the llama.cpp server if not already running"""
        with self._server_lock:
            if self._is_running:
                return True
            
            model_path = self._get_model_path()
            if not os.path.exists(model_path):
                logger.error(f"Model not found: {model_path}")
                raise LLMError(f"Model file not found: {model_path}")
            
            # Check if server is already running
            if self._check_server_health():
                logger.info("llama.cpp server already running")
                self._is_running = True
                return True
            
            # Build server command
            cmd = [
                'llama-server',
                '-m', model_path,
                '--host', self.config['server_host'],
                '--port', str(self.config['server_port']),
                '-c', str(self.config['context_length']),
                '-t', str(self.config['threads']),
                '-b', str(self.config['batch_size']),
                '--log-disable'
            ]
            
            try:
                logger.info(f"Starting llama.cpp server with model: {model_path}")
                self.server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                
                # Wait for server to be ready
                for attempt in range(30):
                    if self._check_server_health():
                        self._is_running = True
                        logger.info("llama.cpp server started successfully")
                        return True
                    time.sleep(0.5)
                
                raise LLMError("Server failed to start within timeout")
                
            except FileNotFoundError:
                raise LLMError("llama-server not found. Install llama.cpp first.")
            except Exception as e:
                raise LLMError(f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the llama.cpp server"""
        with self._server_lock:
            if self.server_process:
                logger.info("Stopping llama.cpp server")
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                self.server_process = None
            self._is_running = False
    
    def _check_server_health(self) -> bool:
        """Check if server is responding"""
        try:
            response = requests.get(
                f"http://{self.config['server_host']}:{self.config['server_port']}/health",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make API request to llama.cpp server with retry logic"""
        url = f"http://{self.config['server_host']}:{self.config['server_port']}{endpoint}"
        
        for attempt in range(self._max_retries):
            try:
                response = requests.post(
                    url,
                    json=data,
                    timeout=self.config['timeout']
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.ConnectionError:
                if attempt == 0:
                    # Try to start server
                    self.start_server()
                else:
                    time.sleep(self._retry_delay)
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout, attempt {attempt + 1}")
                time.sleep(self._retry_delay)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise LLMError(f"API request failed: {e}")
        
        raise LLMError("Max retries exceeded")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        if not self._is_running:
            self.start_server()
        
        params = {
            'prompt': prompt,
            'temperature': kwargs.get('temperature', self.config['temperature']),
            'top_p': kwargs.get('top_p', self.config['top_p']),
            'top_k': kwargs.get('top_k', self.config['top_k']),
            'repeat_penalty': kwargs.get('repeat_penalty', self.config['repeat_penalty']),
            'n_predict': kwargs.get('max_tokens', self.config['max_tokens']),
            'stop': kwargs.get('stop', ["</s>", "Human:", "User:"]),
        }
        
        try:
            result = self._make_request('/completion', params)
            return result.get('content', '').strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise LLMError(f"Text generation failed: {e}")
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream text generation"""
        if not self._is_running:
            self.start_server()
        
        params = {
            'prompt': prompt,
            'temperature': kwargs.get('temperature', self.config['temperature']),
            'top_p': kwargs.get('top_p', self.config['top_p']),
            'n_predict': kwargs.get('max_tokens', self.config['max_tokens']),
            'stream': True,
        }
        
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/completion"
        
        try:
            response = requests.post(url, json=params, stream=True, timeout=self.config['timeout'])
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8').replace('data: ', ''))
                        if 'content' in data:
                            yield data['content']
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise LLMError(f"Streaming generation failed: {e}")
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> str:
        """Chat interface with history"""
        # Add system prompt if first message
        if system_prompt and not self._chat_history:
            self._chat_history.append(ChatMessage('system', system_prompt))
        
        # Add user message
        self._chat_history.append(ChatMessage('user', message))
        
        # Build prompt from history
        prompt = self._format_chat_prompt()
        
        # Generate response
        response = self.generate(prompt)
        
        # Add assistant response to history
        self._chat_history.append(ChatMessage('assistant', response))
        
        # Trim history if needed
        self._trim_history()
        
        return response
    
    def _format_chat_prompt(self) -> str:
        """Format chat history into prompt"""
        prompt_parts = []
        
        for msg in self._chat_history:
            if msg.role == 'system':
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == 'user':
                prompt_parts.append(f"Human: {msg.content}")
            elif msg.role == 'assistant':
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")
        return '\n'.join(prompt_parts)
    
    def _trim_history(self):
        """Trim chat history to fit context window"""
        # Rough estimation: 4 chars ~= 1 token
        total_chars = sum(len(msg.content) for msg in self._chat_history)
        max_chars = self.config['context_length'] * 3  # Leave room for response
        
        while total_chars > max_chars and len(self._chat_history) > 2:
            # Remove oldest non-system message
            for i, msg in enumerate(self._chat_history):
                if msg.role != 'system':
                    total_chars -= len(msg.content)
                    self._chat_history.pop(i)
                    break
    
    def clear_history(self):
        """Clear chat history"""
        self._chat_history = []
    
    def get_history(self) -> List[Dict]:
        """Get chat history as list of dicts"""
        return [msg.to_dict() for msg in self._chat_history]
    
    def __enter__(self):
        self.start_server()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()
        return False
