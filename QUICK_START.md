# 🚀 CLOSED CLAW v3.0 - QUICK START CHEAT SHEET

## 10-Second Overview
```
Moto G45 + Termux + Closed Claw = Your Personal AI Assistant
Auto call pickup • WhatsApp monitor • 100% private • 100% offline
```

---

## ⚡ ONE-COMMAND INSTALL

```bash
curl -sSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/scripts/setup-termux.sh | bash
```

**Then:**
```bash
bash scripts/start.sh
```

**Done!** ✅

---

## 📋 STEP-BY-STEP

### 1. Install Termux (5 min)
```
1. Download F-Droid: https://f-droid.org/
2. In F-Droid, install: Termux + Termux:API
3. Settings → Apps → Termux → Permissions → ALL ON
4. Battery → "Unrestricted"
```

### 2. Setup Termux (3 min)
```bash
# Open Termux and type:
pkg update
termux-setup-storage
pkg install -y git
```

### 3. Download & Install (25 min)
```bash
cd ~
git clone https://github.com/AdityaPagare619/closed-claw-assistant.git
cd closed-claw-assistant
bash scripts/setup-termux.sh

# Answer prompts:
# - Phone: +91YOUR_NUMBER
# - Telegram code: (from app)
# - PIN: 1234
```

### 4. Configure (3 min)
```bash
nano config/config.json
# Change phone and PIN
# Save: Ctrl+O, Enter, Ctrl+X
```

### 5. Start (1 min)
```bash
bash scripts/start.sh
```

### 6. Test (2 min)
```
Open Telegram → Message:
- "status" (should respond)
- "help" (shows commands)
```

**Total Time: 40 minutes**

---

## 🎯 DAILY COMMANDS

| Command | Result |
|---------|--------|
| `status` | Check if running |
| `help` | List all commands |
| `Read my WhatsApp` | Check messages |
| `What's my schedule?` | Calendar |
| `Pickup this call` | Answer call |
| `Go to sleep` | Save battery |

---

## 🔧 QUICK FIXES

```bash
# Restart:
bash scripts/stop.sh && bash scripts/start.sh

# Fix permissions:
termux-setup-storage

# View logs:
cat logs/agent.log
```

---

## 📞 SUPPORT

GitHub: https://github.com/AdityaPagare619/closed-claw-assistant

**Full Guide**: See COMPLETE_SETUP_GUIDE.md
