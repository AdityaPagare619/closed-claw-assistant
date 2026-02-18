"""
WhatsApp Monitor - Read-only WhatsApp Web monitoring using Baileys library bridge
Local processing only, no cloud storage, no message sending capability
"""

import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppMonitor:
    """
    Read-only WhatsApp Web monitor using Baileys Node.js library
    Monitors multiple chats, handles reconnections, stores session locally
    """
    
    def __init__(self, 
                 session_dir: str = "./whatsapp_session",
                 on_message_callback: Optional[Callable] = None,
                 on_qr_callback: Optional[Callable] = None):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        self.on_message = on_message_callback
        self.on_qr = on_qr_callback
        
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        self.chats: Dict[str, Dict] = {}
        self.process: Optional[subprocess.Popen] = None
        self._stop_event = asyncio.Event()
        
        # Baileys Node.js wrapper script path
        self.wrapper_script = self.session_dir / "baileys_wrapper.js"
        self._create_wrapper_script()
    
    def _create_wrapper_script(self):
        """Create Node.js wrapper script for Baileys library"""
        wrapper_code = '''
const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require('@whiskeysockets/baileys');
const fs = require('fs');
const path = require('path');

const SESSION_DIR = process.env.WA_SESSION_DIR || './whatsapp_session';

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
    
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        syncFullHistory: false,  // Don't sync full history for privacy
        markOnlineOnConnect: false,  // Don't mark as online
        shouldSyncHistoryMessage: () => false,  // Skip history sync
    });
    
    sock.ev.on('creds.update', saveCreds);
    
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        
        if (qr) {
            console.log(JSON.stringify({
                type: 'qr',
                data: qr,
                timestamp: Date.now()
            }));
        }
        
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut);
            console.log(JSON.stringify({
                type: 'disconnected',
                shouldReconnect: shouldReconnect,
                timestamp: Date.now()
            }));
            
            if (shouldReconnect) {
                setTimeout(() => connectToWhatsApp(), 5000);
            }
        } else if (connection === 'open') {
            console.log(JSON.stringify({
                type: 'connected',
                timestamp: Date.now()
            }));
        }
    });
    
    sock.ev.on('messages.upsert', (m) => {
        if (m.type === 'notify') {
            m.messages.forEach(msg => {
                if (!msg.key.fromMe) {  // Only process incoming messages
                    console.log(JSON.stringify({
                        type: 'message',
                        data: {
                            id: msg.key.id,
                            remoteJid: msg.key.remoteJid,
                            participant: msg.key.participant,
                            message: msg.message,
                            messageTimestamp: msg.messageTimestamp,
                            pushName: msg.pushName
                        },
                        timestamp: Date.now()
                    }));
                }
            });
        }
    });
    
    return sock;
}

connectToWhatsApp().catch(console.error);
'''
        self.wrapper_script.write_text(wrapper_code)
    
    async def start(self) -> bool:
        """Start WhatsApp monitoring with session persistence"""
        try:
            # Check if Baileys is installed
            if not self._check_baileys_installed():
                logger.error("Baileys library not installed. Run: npm install @whiskeysockets/baileys")
                return False
            
            logger.info("Starting WhatsApp monitor...")
            
            # Start Node.js process
            env = os.environ.copy()
            env['WA_SESSION_DIR'] = str(self.session_dir)
            
            self.process = subprocess.Popen(
                ['node', str(self.wrapper_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(self.session_dir.parent)
            )
            
            # Start reading output
            asyncio.create_task(self._read_output())
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WhatsApp monitor: {e}")
            return False
    
    def _check_baileys_installed(self) -> bool:
        """Check if Baileys library is installed"""
        try:
            result = subprocess.run(
                ['npm', 'list', '@whiskeysockets/baileys'],
                capture_output=True,
                text=True,
                cwd=str(self.session_dir.parent)
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def _read_output(self):
        """Read output from Node.js process"""
        while not self._stop_event.is_set() and self.process:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.process.stdout.readline
                )
                
                if line:
                    self._handle_output(line.strip())
                    
            except Exception as e:
                logger.error(f"Error reading output: {e}")
                await asyncio.sleep(1)
    
    def _handle_output(self, line: str):
        """Handle output from Baileys wrapper"""
        try:
            data = json.loads(line)
            msg_type = data.get('type')
            
            if msg_type == 'qr':
                logger.info("QR Code received - scan with WhatsApp")
                if self.on_qr:
                    self.on_qr(data['data'])
                    
            elif msg_type == 'connected':
                logger.info("WhatsApp connected successfully")
                self.connected = True
                self.reconnect_attempts = 0
                
            elif msg_type == 'disconnected':
                logger.warning("WhatsApp disconnected")
                self.connected = False
                
                if data.get('shouldReconnect') and self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    logger.info(f"Reconnecting... Attempt {self.reconnect_attempts}")
                    
            elif msg_type == 'message':
                self._handle_message(data['data'])
                
        except json.JSONDecodeError:
            # Not JSON, might be regular log output
            if line:
                logger.debug(f"Baileys: {line}")
        except Exception as e:
            logger.error(f"Error handling output: {e}")
    
    def _handle_message(self, msg_data: Dict[str, Any]):
        """Process incoming message"""
        try:
            message = {
                'id': msg_data.get('id'),
                'chat_id': msg_data.get('remoteJid'),
                'sender': msg_data.get('participant') or msg_data.get('remoteJid'),
                'sender_name': msg_data.get('pushName', 'Unknown'),
                'timestamp': msg_data.get('messageTimestamp'),
                'message': msg_data.get('message', {}),
                'is_group': '@g.us' in (msg_data.get('remoteJid') or '')
            }
            
            # Store in chats
            chat_id = message['chat_id']
            if chat_id not in self.chats:
                self.chats[chat_id] = {
                    'messages': [],
                    'unread_count': 0
                }
            
            self.chats[chat_id]['messages'].append(message)
            self.chats[chat_id]['unread_count'] += 1
            
            # Call callback if provided
            if self.on_message:
                self.on_message(message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def stop(self):
        """Stop WhatsApp monitoring"""
        logger.info("Stopping WhatsApp monitor...")
        self._stop_event.set()
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        
        self.connected = False
        logger.info("WhatsApp monitor stopped")
    
    def is_session_active(self) -> bool:
        """Check if there's an active session"""
        creds_file = self.session_dir / "creds.json"
        return creds_file.exists()
    
    def logout(self):
        """Logout and clear session"""
        import shutil
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
            logger.info("WhatsApp session cleared")
    
    def get_chat_summary(self) -> Dict[str, int]:
        """Get summary of monitored chats with unread counts"""
        return {
            chat_id: info['unread_count']
            for chat_id, info in self.chats.items()
        }
    
    def get_messages(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """Get messages from a specific chat"""
        if chat_id in self.chats:
            messages = self.chats[chat_id]['messages']
            return messages[-limit:]
        return []


# Convenience function for simple usage
def create_monitor(on_message: Callable, session_dir: str = "./whatsapp_session") -> WhatsAppMonitor:
    """Create and configure a WhatsApp monitor"""
    return WhatsAppMonitor(
        session_dir=session_dir,
        on_message_callback=on_message
    )


# Example usage
if __name__ == "__main__":
    async def main():
        def on_msg(msg):
            print(f"[WhatsApp] {msg['sender_name']}: {msg}")
        
        def on_qr(qr_data):
            print(f"[QR Code] Scan this: {qr_data[:50]}...")
        
        monitor = WhatsAppMonitor(
            on_message_callback=on_msg,
            on_qr_callback=on_qr
        )
        
        if await monitor.start():
            print("Monitor started. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                await monitor.stop()
        else:
            print("Failed to start monitor")
    
    asyncio.run(main())
