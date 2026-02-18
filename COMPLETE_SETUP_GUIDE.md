# 📱 CLOSED CLAW v3.0 - COMPLETE STEP-BY-STEP SETUP GUIDE
## For Moto G45 (Android) - Zero to Hero in 30 Minutes

---

## ⚠️ BEFORE YOU START

### What You Need:
- ✅ Moto G45 (or any Android 8.0+ phone)
- ✅ 4GB+ RAM (6GB recommended)
- ✅ 2GB free storage
- ✅ Internet connection (for setup only)
- ✅ Telegram account
- ✅ 30-45 minutes of uninterrupted time

### What Will Be Installed:
- Termux (Linux terminal on Android)
- Sarvam-1 2B AI model (~1.2GB)
- Piper TTS voice (~100MB)
- Whisper STT model (~75MB)
- All Python dependencies
- Node.js tools (Baileys for WhatsApp)

---

## 🎯 THE COMPLETE SETUP PROCESS

### PHASE 1: PREPARATION (5 minutes)

#### Step 1.1: Free Up Space
```
1. Go to Settings → Storage
2. Ensure at least 2GB free space
3. If needed, delete unused apps/photos
4. Check: Settings → Battery → Make sure phone is charged (>50%)
```

#### Step 1.2: Disable Battery Optimization
```
1. Go to Settings → Apps
2. Search "Termux" (may not be there yet)
3. Go back → Battery → Battery Optimization
4. Find "Termux" and select "Don't optimize"
5. This prevents Android from killing Termux
```

---

### PHASE 2: INSTALL TERMUX (10 minutes)

#### Step 2.1: Install F-Droid
**⚠️ IMPORTANT: Do NOT use Google Play for Termux!**

```
1. Open Chrome browser
2. Go to: https://f-droid.org/
3. Tap "Download F-Droid"
4. Download the APK
5. Tap downloaded file
6. If blocked: Settings → Enable "Unknown sources"
7. Install F-Droid
8. Open F-Droid
```

#### Step 2.2: Install Termux from F-Droid
```
1. In F-Droid, search "Termux"
2. Find "Termux" by "Termux Developers"
3. Tap INSTALL
4. Wait for download (~50MB)
5. Install
6. DO NOT OPEN YET!

Also install:
- Termux:API (required)
- Termux:Widget (optional)
```

#### Step 2.3: Grant All Permissions to Termux
```
1. Settings → Apps → Termux
2. Permissions → Enable ALL:
   ✓ Storage
   ✓ Microphone
   ✓ Phone
   ✓ SMS
   ✓ Contacts
3. Battery → "Unrestricted"
4. Enable "Allow background activity"
```

---

### PHASE 3: INITIAL TERMUX SETUP (10 minutes)

#### Step 3.1: Open Termux
```
1. Open Termux app
2. Black screen with $ prompt = good!
3. Grant any permission prompts
4. Wait 1-2 minutes for first setup
```

#### Step 3.2: Update Packages
```bash
# In Termux, type:
pkg update

# When prompted: Y
# Press Enter
# Wait 2-5 minutes
```

#### Step 3.3: Grant Storage Access
```bash
# Type:
termux-setup-storage

# Tap "Allow" when prompted
```

#### Step 3.4: Install Git
```bash
# Type:
pkg install -y git curl wget

# Wait 1-2 minutes
```

---

### PHASE 4: DOWNLOAD CLOSED CLAW (5 minutes)

#### Step 4.1: Clone Repository
```bash
# Type:
cd ~
git clone https://github.com/AdityaPagare619/closed-claw-assistant.git

# Wait for download
```

#### Step 4.2: Enter Directory
```bash
# Type:
cd closed-claw-assistant
ls

# You should see files listed
```

---

### PHASE 5: RUN SETUP (20-30 minutes)

#### Step 5.1: Start Setup
```bash
# Type:
bash scripts/setup-termux.sh

# ⏰ This takes 20-30 minutes!
# 🔋 Keep phone plugged in!
# 📱 Don't let screen lock!
```

#### Step 5.2: Answer Prompts
```
During setup, you'll see:

1. "Do you want to continue? [Y/n]"
   → Type: Y
   → Press Enter

2. "Enter phone number:"
   → Type: +91YOUR_NUMBER
   → Example: +919876543210
   → Press Enter

3. "Enter verification code:"
   → Check Telegram for code
   → Type code (5 digits)
   → Press Enter

4. "Set security PIN:"
   → Type 4-digit PIN (e.g., 1234)
   → Press Enter
   → Type again to confirm
   → Press Enter
```

#### Step 5.3: Wait for Completion
```
When done, you'll see:

✅ Setup Complete!
================================
Location: ~/closed-claw-assistant/
Start: bash scripts/start.sh
Stop: bash scripts/stop.sh
```

---

### PHASE 6: CONFIGURE (5 minutes)

#### Step 6.1: Edit Config
```bash
# Type:
nano config/config.json

# Navigate with arrow keys
```

#### Step 6.2: Change These Lines
```json
{
  "telegram": {
    "phone": "+919876543210"  ← YOUR NUMBER
  },
  "security": {
    "pin_code": "1234"  ← YOUR PIN
  },
  "calls": {
    "auto_pickup_delay": 20  ← seconds before pickup
  }
}
```

#### Step 6.3: Save File
```
In nano editor:
1. Press: Ctrl + O (letter O)
2. Press: Enter
3. Press: Ctrl + X
```

---

### PHASE 7: TELEGRAM AUTH (10 minutes)

#### Step 7.1: Setup Telegram CLI
```bash
# Type:
bash scripts/setup-telegram.sh

# Follow prompts...
```

#### Step 7.2: Enter Details
```
"Enter phone number:"
→ +91YOUR_NUMBER
→ Press Enter

"Enter verification code:"
→ Check Telegram app for code
→ Type 5-digit code
→ Press Enter

"Enter 2FA password (if any):"
→ Type your Telegram password
→ Press Enter
```

#### Step 7.3: Success Message
```
✅ Telegram CLI authenticated!
✅ Session saved
```

---

### PHASE 8: FIRST START (5 minutes)

#### Step 8.1: Start Assistant
```bash
# Type:
bash scripts/start.sh

# You'll see:
🦞 Starting Closed Claw v3.0...
[1/5] Starting AI Brain...
[2/5] Loading Voice System...
[3/5] Initializing Call Handler...
[4/5] Connecting to Telegram...
[5/5] All systems operational!

✅ Closed Claw is running!
```

#### Step 8.2: Test It
```
1. Open Telegram app
2. Find your conversation with assistant
3. Type: status
4. Should respond with status!

Try other commands:
- "help" - show commands
- "What time is it?" - test AI
- "Read my WhatsApp" - test WhatsApp (after setup)
```

---

### PHASE 9: WHATSAPP SETUP (Optional, 10 min)

#### Step 9.1: Enable WhatsApp
```bash
# In new Termux session or same:
bash scripts/setup-whatsapp.sh

# Shows QR code
```

#### Step 9.2: Link WhatsApp
```
1. Open WhatsApp on phone
2. Settings → Linked Devices
3. Link a Device
4. Scan QR code in Termux
5. Wait for "Connected!"
```

#### Step 9.3: Test
```
In Telegram:
"Read my WhatsApp"
→ Enter PIN
→ Should show messages!
```

---

### PHASE 10: TEST CALL PICKUP

#### Step 10.1: Test With Friend
```
1. Ask friend to call you
2. DON'T ANSWER
3. Wait 20 seconds
4. Assistant picks up automatically!
5. Friend hears voice greeting
6. You get Telegram summary
```

#### Step 10.2: Adjust if Needed
```bash
# To change pickup time:
nano config/config.json
# Change: "auto_pickup_delay": 20
# To: 30 (for 30 seconds)

# Restart:
bash scripts/stop.sh
bash scripts/start.sh
```

---

## ✅ YOU'RE DONE!

### Daily Usage:
```
Just message your assistant on Telegram!

Commands:
- "status" - Check if running
- "help" - Show all commands
- "Read my WhatsApp" - Check messages
- "What's my schedule?" - Calendar
- "Pickup this call" - Answer call
- "Go to sleep" - Save battery
```

---

## 🔧 MAINTENANCE

### Stop Assistant:
```bash
bash scripts/stop.sh
```

### Restart:
```bash
bash scripts/stop.sh
bash scripts/start.sh
```

### View Logs:
```bash
cat logs/agent.log
cat logs/error.log
```

### Auto-Start on Boot:
```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-closed-claw.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
cd ~/closed-claw-assistant
bash scripts/start.sh &
EOF
chmod +x ~/.termux/boot/start-closed-claw.sh
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "Permission denied" | Run: `termux-setup-storage` |
| "Out of memory" | Use smaller model in config |
| "Telegram not working" | Re-run: `bash scripts/setup-telegram.sh` |
| "Assistant not responding" | Restart: `bash scripts/stop.sh && bash scripts/start.sh` |
| "Voice not working" | Test: `termux-tts-speak "test"` |

---

## 📞 SUPPORT

- 📖 Docs: https://github.com/AdityaPagare619/closed-claw-assistant
- 🐛 Issues: https://github.com/AdityaPagare619/closed-claw-assistant/issues

---

**🎉 Congratulations! Your personal AI assistant is ready!**

*Everything runs locally on your phone. Your data stays private.*
