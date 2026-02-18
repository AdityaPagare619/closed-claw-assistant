"""
Telegram CLI Wrapper

MTProto-based Telegram client using telegram-cli.
Requires telegram-cli to be installed separately.
"""

import asyncio
import json
import logging
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class TelegramButton:
    """Inline keyboard button."""
    text: str
    callback_data: str
    url: Optional[str] = None


@dataclass
class TelegramMessage:
    """Telegram message structure."""
    message_id: int
    chat_id: int
    user_id: int
    username: Optional[str]
    text: str
    timestamp: datetime
    reply_to: Optional[int] = None
    buttons: List[List[TelegramButton]] = field(default_factory=list)


class TelegramCLI:
    """
    MTProto Telegram client wrapper using telegram-cli.
    
    Requires telegram-cli binary to be installed and configured.
    """
    
    def __init__(
        self,
        socket_path: str = "/tmp/tg-cli.sock",
        public_key_path: str = "/etc/telegram-cli/server.pub",
        config_dir: str = "~/.telegram-cli"
    ):
        self.socket_path = Path(socket_path)
        self.public_key_path = Path(public_key_path)
        self.config_dir = Path(config_dir).expanduser()
        
        self._cli_process: Optional[subprocess.Popen] = None
        self._connected = False
        self._message_handlers: List[Callable[[TelegramMessage], None]] = []
        self._button_handlers: Dict[str, Callable[[str, int], None]] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        # User state tracking
        self._authorized_users: Set[int] = set()
        self._user_sessions: Dict[int, dict] = {}
    
    async def connect(self) -> bool:
        """
        Connect to telegram-cli daemon.
        
        Returns:
            True if connection successful
        """
        try:
            # Check if telegram-cli is available
            result = subprocess.run(
                ["which", "telegram-cli"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("telegram-cli not found. Please install it first.")
                return False
            
            # Start telegram-cli in daemon mode
            cmd = [
                "telegram-cli",
                "-k", str(self.public_key_path),
                "-S", str(self.socket_path),
                "-d",
                "-W",  # Wait for network
                "-C"   # No color
            ]
            
            self._cli_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            
            # Wait for socket to be created
            await asyncio.sleep(2)
            
            if not self.socket_path.exists():
                logger.error("telegram-cli socket not created")
                return False
            
            self._connected = True
            self._read_task = asyncio.create_task(self._read_loop())
            
            logger.info("Connected to telegram-cli")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to telegram-cli: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from telegram-cli."""
        self._connected = False
        
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        if self._cli_process:
            self._cli_process.terminate()
            try:
                self._cli_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._cli_process.kill()
        
        logger.info("Disconnected from telegram-cli")
    
    def is_connected(self) -> bool:
        """Check if connected to telegram-cli."""
        return self._connected and self._cli_process is not None
    
    async def _execute(self, command: str) -> str:
        """Execute a telegram-cli command."""
        if not self.is_connected():
            raise ConnectionError("Not connected to telegram-cli")
        
        # Use socat to communicate with daemon
        cmd = f'echo "{command}" | socat - UNIX-CONNECT:{self.socket_path}'
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed: {stderr.decode()}")
        
        return stdout.decode()
    
    async def send_message(
        self,
        user_id: int,
        text: str,
        parse_mode: str = "markdown",
        buttons: Optional[List[List[TelegramButton]]] = None
    ) -> bool:
        """
        Send message to user.
        
        Args:
            user_id: Target user ID
            text: Message text
            parse_mode: 'markdown' or 'html'
            buttons: Optional inline keyboard buttons
            
        Returns:
            True if sent successfully
        """
        try:
            # Escape quotes in text
            safe_text = text.replace('"', '\\"')
            
            if buttons:
                # Create inline keyboard markup
                keyboard = self._format_inline_keyboard(buttons)
                command = f'msg user#{user_id} "{safe_text}" {keyboard}'
            else:
                command = f'msg user#{user_id} "{safe_text}"'
            
            result = await self._execute(command)
            
            if "SUCCESS" in result or len(result.strip()) > 0:
                logger.debug(f"Message sent to user {user_id}")
                return True
            else:
                logger.warning(f"Failed to send message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _format_inline_keyboard(
        self,
        buttons: List[List[TelegramButton]]
    ) -> str:
        """Format inline keyboard for telegram-cli."""
        rows = []
        for row in buttons:
            row_buttons = []
            for btn in row:
                if btn.url:
                    row_buttons.append(f"[\\\"{btn.text}\\\"](\\\"{btn.url}\\\")")
                else:
                    row_buttons.append(f"[\\\"{btn.text}\\\"](\\\"{btn.callback_data}\\\")")
            rows.append("[" + ",".join(row_buttons) + "]")
        
        return "[" + ",".join(rows) + "]"
    
    async def _read_loop(self):
        """Background loop to read incoming messages."""
        while self._connected:
            try:
                # Use dialog_list to poll for updates
                result = await self._execute("dialog_list 10")
                
                # Parse messages
                messages = self._parse_messages(result)
                
                for msg in messages:
                    await self._message_queue.put(msg)
                    await self._process_message(msg)
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                await asyncio.sleep(5)
    
    def _parse_messages(self, raw_output: str) -> List[TelegramMessage]:
        """Parse telegram-cli output into messages."""
        messages = []
        
        # Simple parsing - telegram-cli format varies
        lines = raw_output.strip().split('\n')
        
        for line in lines:
            # Match pattern: [chat_id] [user_id] [username] [timestamp] [message]
            match = re.match(
                r'\[(\d+)\]\s*\[(\d+)\]\s*@?(\w*)\s*\[(\d{2}:\d{2})\]\s*(.+)',
                line
            )
            
            if match:
                chat_id = int(match.group(1))
                user_id = int(match.group(2))
                username = match.group(3) or None
                timestamp = datetime.strptime(match.group(4), "%H:%M")
                text = match.group(5)
                
                msg = TelegramMessage(
                    message_id=hash(line),  # Approximate
                    chat_id=chat_id,
                    user_id=user_id,
                    username=username,
                    text=text,
                    timestamp=timestamp
                )
                messages.append(msg)
        
        return messages
    
    async def _process_message(self, message: TelegramMessage):
        """Process incoming message."""
        # Check for button callbacks
        if message.text.startswith("/"):
            callback_data = message.text[1:]
            if callback_data in self._button_handlers:
                handler = self._button_handlers[callback_data]
                asyncio.create_task(handler(callback_data, message.user_id))
                return
        
        # Call registered handlers
        for handler in self._message_handlers:
            try:
                asyncio.create_task(handler(message))
            except Exception as e:
                logger.error(f"Error in message handler: {e}")
    
    def on_message(self, handler: Callable[[TelegramMessage], None]):
        """Register message handler."""
        self._message_handlers.append(handler)
        return handler
    
    def on_button(
        self,
        callback_data: str,
        handler: Callable[[str, int], None]
    ):
        """Register button callback handler."""
        self._button_handlers[callback_data] = handler
        return handler
    
    async def answer_callback_query(
        self,
        query_id: str,
        text: Optional[str] = None
    ) -> bool:
        """Answer callback query (acknowledge button press)."""
        try:
            command = f'answer_inline_query {query_id}'
            if text:
                command += f' "{text}"'
            
            await self._execute(command)
            return True
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
            return False
    
    async def delete_message(self, user_id: int, message_id: int) -> bool:
        """Delete a sent message."""
        try:
            command = f'delete_msg user#{user_id} {message_id}'
            await self._execute(command)
            return True
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    async def get_user_info(self, user_id: int) -> Optional[dict]:
        """Get user information."""
        try:
            result = await self._execute(f'user_info user#{user_id}')
            # Parse user info from output
            return {"user_id": user_id, "raw": result}
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def register_user(self, user_id: int):
        """Register authorized user."""
        self._authorized_users.add(user_id)
        logger.info(f"User {user_id} registered")
    
    def unregister_user(self, user_id: int):
        """Unregister user."""
        self._authorized_users.discard(user_id)
        self._user_sessions.pop(user_id, None)
        logger.info(f"User {user_id} unregistered")
    
    def is_user_authorized(self, user_id: int) -> bool:
        """Check if user is authorized."""
        return user_id in self._authorized_users
