# Closed Claw v3.0 - Complete Installation Guide

## Prerequisites

1. **Android Phone** (Moto G45 or similar)
2. **Termux** - Install from F-Droid (NOT Google Play)
3. **Internet** - For downloading model (~1.6 GB)
4. **Storage** - At least 3 GB free space

## Installation Steps

### Step 1: Install Termux

```bash
# From F-Droid (recommended)
https://f-droid.org/packages/com.termux/

# OR from GitHub
https://github.com/termux/termux-app/releases
```

### Step 2: Run One-Command Installer

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh | bash
```

### Step 3: Follow Interactive Prompts

- Enter your name
- Enter Telegram bot token (optional)
- Select performance level

### Step 4: Start Closed Claw

```bash
cd ~/closed-claw-assistant
./claw
```

### Step 5: First Use

1. Send first message
2. Wait 1-2 minutes for model to load
3. Model stays in memory!
4. All subsequent responses are instant

## Configuration

Edit config:
```bash
nano ~/closed-claw-assistant/config/config.local.json
```

## Troubleshooting

### Model Not Found
```bash
cd ~/closed-claw-assistant/models
wget https://huggingface.co/sarvam/sarvam-1-2b/resolve/main/sarvam-1-2b-q4.gguf
```

### Permission Issues
```bash
termux-setup-storage
```

### Reinstall
```bash
rm -rf ~/closed-claw-assistant
curl -fsSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh | bash
```

## Security Features

- 100% offline mode
- No data sharing
- Banking app blocking (45+ apps)
- Audit logging
- Self-aware AI

## Support

- GitHub Issues: https://github.com/AdityaPagare619/closed-claw-assistant/issues