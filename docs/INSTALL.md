# Installation Guide

Complete step-by-step installation for Closed Claw Assistant v3.0

---

## 📋 Prerequisites

### Required
- Android phone (Android 8.0+)
- 4GB+ RAM (6GB recommended)
- 2GB+ free storage
- Internet connection (for initial setup only)

### Recommended
- Moto G45 or equivalent
- Termux from F-Droid (not Google Play)
- Telegram account

---

## 🚀 Quick Install (Recommended)

### Step 1: Install Termux

1. **Download F-Droid**:
   - Visit https://f-droid.org/
   - Download and install F-Droid app

2. **Install Termux via F-Droid**:
   - Open F-Droid
   - Search for "Termux"
   - Install Termux and Termux:API

3. **Grant Permissions**:
   - Open Android Settings
   - Apps → Termux → Permissions
   - Enable: Storage, Microphone, Phone, SMS, Contacts

### Step 2: One-Command Setup

```bash
# Open Termux and run:
curl -sSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/scripts/setup-termux.sh | bash
```

This will take 15-30 minutes depending on your internet speed.

### Step 3: Configure Telegram

```bash
cd ~/closed-claw-assistant
bash scripts/setup-telegram.sh
```

Follow prompts to:
1. Enter your phone number
2. Enter Telegram verification code
3. Set your PIN for security

### Step 4: Download AI Model

```bash
bash scripts/download-models.sh
```

This downloads:
- Sarvam-1 2B model (~1.2GB)
- Piper TTS voice (~100MB)
- Whisper STT model (~75MB)

### Step 5: Start Assistant

```bash
bash scripts/start.sh
```

You should see:
```
🦞 Starting Closed Claw v3.0...
✅ AI Brain loaded
✅ Voice system ready
✅ Call handler active
✅ WhatsApp monitoring started
✅ Telegram interface connected
✅ All systems operational
```

---

## 🛠️ Manual Installation

If quick install fails, follow these manual steps:

### 1. Update Termux

```bash
pkg update && pkg upgrade -y
```

### 2. Install System Dependencies

```bash
pkg install -y \
    git \
    cmake \
    clang \
    python \
    python-pip \
    nodejs \
    golang \
    termux-api \
    wget \
    curl \
    jq \
    ffmpeg \
    libffi \
    libxml2 \
    libxslt \
    openssl
```

### 3. Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies

```bash
npm install -g @whiskeysockets/baileys
npm install -g qrcode-terminal
```

### 5. Install llama.cpp

```bash
# Option 1: Pre-built binary
pkg install llama-cpp

# Option 2: Build from source (recommended for best performance)
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
mkdir build && cd build
cmake .. \
    -DLLAMA_NATIVE=OFF \
    -DLLAMA_ARM_NEON=ON \
    -DLLAMA_ARM_FMA=ON \
    -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
cp bin/llama-server $PREFIX/bin/
```

### 6. Clone Repository

```bash
cd ~
git clone https://github.com/AdityaPagare619/closed-claw-assistant.git
cd closed-claw-assistant
```

### 7. Create Directories

```bash
mkdir -p models logs sessions whatsapp_session audio
```

### 8. Download Models

#### Sarvam-1 2B
```bash
cd models

# Download quantized model
wget https://huggingface.co/sarvamai/sarvam-1-2b-gguf/resolve/main/sarvam-1-2b-q4_0_4_4.gguf

# Or better quality (larger)
wget https://huggingface.co/sarvamai/sarvam-1-2b-gguf/resolve/main/sarvam-1-2b-q4_k_m.gguf

cd ..
```

#### Piper TTS
```bash
mkdir -p ~/.local/share/piper
cd ~/.local/share/piper

# Download English voice
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/en_US-lessac-medium.onnx.json

# Or Hindi voice (if available)
# wget [hindi voice model]

cd ~/closed-claw-assistant
```

#### Whisper STT
```bash
mkdir -p ~/.local/share/whisper
cd ~/.local/share/whisper

# Download tiny model (fastest)
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin

# Or small model (better quality)
# wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin

cd ~/closed-claw-assistant
```

### 9. Install Telegram CLI

```bash
pkg install telegram-cli

# Or build from source for latest version
git clone https://github.com/vysheng/tg.git
cd tg
./configure
make
make install
```

### 10. Configure

```bash
cp config/config.example.json config/config.json
nano config/config.json
```

Edit these fields:
```json
{
  "telegram": {
    "phone": "+91YOUR_PHONE_NUMBER"
  },
  "security": {
    "pin_code": "YOUR_4_DIGIT_PIN"
  }
}
```

### 11. Authenticate Telegram

```bash
telegram-cli
```

In the Telegram CLI:
```
# Enter your phone number
phone +91XXXXXXXXXX

# Enter verification code sent to Telegram
code XXXXX

# You should see your contacts list
# Exit with: quit
```

### 12. Test Installation

```bash
# Test AI brain
python3 -c "
from src.brain.sarvam_brain import SarvamBrain
brain = SarvamBrain({'model_path': 'models/sarvam-1-2b-q4_0_4_4.gguf'})
print('✅ Brain loaded successfully')
"

# Test voice
termux-tts-speak "Test successful"

# Test Telegram
python3 -c "
from src.interface.telegram_cli import TelegramInterface
tg = TelegramInterface({})
print('✅ Telegram interface ready')
"
```

### 13. Start Assistant

```bash
python3 src/agent/daemon.py
```

Or use the start script:
```bash
bash scripts/start.sh
```

---

## 🔧 Post-Installation

### Set Up Auto-Start

To start Closed Claw automatically when Termux opens:

```bash
# Edit Termux properties
nano ~/.termux/termux.properties

# Add:
# allow-external-apps=true

# Create startup script
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-closed-claw.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/closed-claw-assistant
bash scripts/start.sh &
EOF

chmod +x ~/.termux/boot/start-closed-claw.sh
```

### Battery Optimization

To prevent Android from killing Termux:

1. **Disable Battery Optimization**:
   - Settings → Apps → Termux → Battery
   - Select "Don't optimize" or "Unrestricted"

2. **Disable Phantom Process Killing** (requires ADB):
   ```bash
   # From PC with ADB:
   adb shell settings put global settings_enable_monitor_phantom_procs false
   ```

3. **Use Wake Lock** (automatic in our start script):
   ```bash
   termux-wake-lock
   ```

### Test All Features

```bash
# Run comprehensive test
bash scripts/test-all.sh
```

This will test:
- ✅ AI brain response
- ✅ Voice synthesis
- ✅ Telegram connection
- ✅ Call detection
- ✅ WhatsApp monitoring
- ✅ Permission system

---

## 🐛 Troubleshooting

### Issue: "llama.cpp not found"

**Solution**:
```bash
# Reinstall llama.cpp
cd ~/llama.cpp
git pull
mkdir -p build && cd build
cmake .. -DLLAMA_ARM_NEON=ON
make -j4
sudo cp bin/llama-server $PREFIX/bin/
```

### Issue: "Permission denied"

**Solution**:
```bash
# Grant storage permission
termux-setup-storage

# Fix permissions
chmod -R 755 ~/closed-claw-assistant
```

### Issue: "Out of memory"

**Solution**:
1. Use smaller model: `sarvam-1-2b-q4_0_4_4.gguf` instead of Q4_K_M
2. Reduce context size in config: `"context_size": 2048`
3. Close other apps

### Issue: "Telegram CLI not connecting"

**Solution**:
```bash
# Clear session and re-authenticate
rm -rf ~/.telegram-cli

# Re-authenticate
telegram-cli
# Enter phone and code again
```

### Issue: "Voice not working"

**Solution**:
```bash
# Test Termux TTS
termux-tts-speak "Hello"

# If that works, check Piper installation
ls ~/.local/share/piper/

# Re-download if missing
```

### Issue: "Assistant crashes on startup"

**Solution**:
```bash
# Check logs
cat logs/agent.log

# Run with debug mode
python3 src/agent/daemon.py --debug
```

---

## 📊 Verification Checklist

After installation, verify everything works:

- [ ] AI brain responds to queries
- [ ] Voice synthesis works (TTS)
- [ ] Telegram messages send/receive
- [ ] Call detection active
- [ ] WhatsApp monitoring (if configured)
- [ ] Permission system blocks L2+ without PIN
- [ ] Banking apps inaccessible
- [ ] Audit logs created
- [ ] Battery drain <3%/hour
- [ ] Auto-start works

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**:
   ```bash
   cat logs/agent.log
   cat logs/error.log
   ```

2. **Run Diagnostics**:
   ```bash
   bash scripts/diagnose.sh
   ```

3. **Create Issue**:
   - GitHub: https://github.com/AdityaPagare619/closed-claw-assistant/issues
   - Include logs and error messages

4. **Community Support**:
   - Telegram: @ClosedClawAssistant

---

## ✅ Next Steps

After successful installation:

1. **Read Usage Guide**: [USAGE.md](USAGE.md)
2. **Configure Preferences**: Edit `config/config.json`
3. **Test Features**: Try commands from usage guide
4. **Customize**: Add your own tools and automations

---

**You're all set!** 🎉

Your personal AI assistant is now running securely on your phone.
