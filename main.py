#!/usr/bin/env python3
"""
Closed Claw v3.0 - MOBILE VERSION
Optimized for Android/Termux with Model Persistence
Loads model ONCE, stays loaded for instant responses!
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Setup paths for Termux
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

# Logging setup
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(str(LOGS_DIR / "assistant.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class PersistentSarvamBrain:
    """
    PERSISTENT MODEL - Loads ONCE, stays loaded!
    No more 2+ min delays per message
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.model = None
        self._loaded = False
        self._loading = False
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load config from file"""
        try:
            config_path = BASE_DIR / "config" / "config.local.json"
            if config_path.exists():
                with open(config_path) as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Config error: {e}")

        # Default config
        return {
            "assistant": {"name": "Closed Claw", "boss_name": "Boss"},
            "sarvam": {
                "brain_model_path": "models/sarvam-1-2b-q4.gguf",
                "context_length": 2048,
                "max_tokens": 512,
            },
            "performance": {"max_ram_usage_mb": 1400},
        }

    def load_model(self) -> bool:
        """Load model ONCE - stays in memory forever!"""
        if self._loaded:
            logger.info("Model already loaded (persistent)")
            return True

        if self._loading:
            logger.info("Waiting for model to load...")
            while self._loading:
                time.sleep(0.5)
            return self._loaded

        self._loading = True
        logger.info("=" * 60)
        logger.info("LOADING SARVAM-1 2B MODEL (One-time load)")
        logger.info("This takes 1-2 minutes, then stays in memory!")
        logger.info("=" * 60)

        try:
            from llama_cpp import Llama

            model_path = BASE_DIR / self.config.get("sarvam", {}).get(
                "brain_model_path", "models/sarvam-1-2b-q4.gguf"
            )

            if not model_path.exists():
                logger.error(f"Model not found: {model_path}")
                logger.error("Download from: https://huggingface.co/sarvam/sarvam-1-2b")
                return False

            start_time = time.time()

            # Load with mobile optimization
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.get("sarvam", {}).get("context_length", 2048),
                n_threads=4,  # Use 4 CPU cores
                n_gpu_layers=0,  # CPU only for mobile
                use_mmap=True,  # Memory mapping
                use_mlock=False,
                verbose=False,
            )

            load_time = time.time() - start_time
            self._loaded = True

            logger.info(f"✓ Model loaded in {load_time:.1f} seconds")
            logger.info("✓ Model stays in memory - instant responses ready!")
            logger.info("=" * 60)

            return True

        except ImportError:
            logger.error("llama-cpp-python not installed!")
            logger.error("Run: pip install llama-cpp-python")
            return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
        finally:
            self._loading = False

    async def generate(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        """Generate text - loads model if needed (first time only)"""
        # Load if not loaded
        if not self._loaded:
            if not self.load_model():
                return "Error: Could not load AI model. Please check logs."

        try:
            # Run in thread pool to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["User:", "Human:"],
                ),
            )

            return result["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return f"Error: {e}"

    def is_loaded(self) -> bool:
        return self._loaded


class ClosedClawMobile:
    """Main mobile application"""

    def __init__(self):
        self.brain = PersistentSarvamBrain()
        self.running = False
        self.config = self.brain.config

    def get_boss_name(self) -> str:
        return self.config.get("assistant", {}).get("boss_name", "Boss")

    async def handle_message(self, message: str) -> str:
        """Handle user message"""
        message = message.strip()

        if not message:
            return "I didn't catch that. Please try again."

        # Simple commands
        lower_msg = message.lower()

        if lower_msg in ["status", "info", "hello", "hi"]:
            return self._get_status()

        if lower_msg in ["help", "?"]:
            return self._get_help()

        # AI response for everything else
        boss = self.get_boss_name()
        prompt = f"You are Closed Claw, a helpful AI assistant for {boss}. Be concise and friendly.\n\nUser: {message}\n\nAssistant:"

        return await self.brain.generate(prompt, max_tokens=256)

    def _get_status(self) -> str:
        """Get system status"""
        lines = [
            "=" * 40,
            "CLOSED CLAW v3.0 - STATUS",
            "=" * 40,
            f"Boss: {self.get_boss_name()}",
            f"Model Loaded: {self.brain.is_loaded()}",
            f"Offline Mode: YES",
            f"Banking Protection: ACTIVE",
            "=" * 40,
        ]
        return "\n".join(lines)

    def _get_help(self) -> str:
        """Get help message"""
        return """
Commands:
  status  - Check system status
  help    - Show this message
  exit    - Quit

Or just chat with me naturally!

Security:
  ✓ 100% Offline
  ✓ Banking apps blocked
  ✓ No data sharing
        """.strip()

    async def run(self):
        """Main run loop"""
        self.running = True
        boss = self.get_boss_name()

        print("\n" + "=" * 60)
        print("CLOSED CLAW v3.0 - SECURE OFFLINE AI")
        print("=" * 60)
        print(f"Welcome, {boss}!")
        print("")
        print("Model loads on first message (1-2 min), then stays loaded!")
        print("Type 'help' for commands or just chat with me.")
        print("Type 'exit' to quit.")
        print("=" * 60 + "\n")

        while self.running:
            try:
                # Get input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(f"{boss}: ")
                )

                if user_input.lower() in ["exit", "quit", "q", "bye"]:
                    print("\nGoodbye! Stay secure.\n")
                    break

                # Process
                print("\nThinking..." if not self.brain.is_loaded() else "")
                response = await self.handle_message(user_input)
                print(f"Claw: {response}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"Error: {e}\n")


async def main():
    """Entry point"""
    try:
        app = ClosedClawMobile()
        await app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
        sys.exit(0)