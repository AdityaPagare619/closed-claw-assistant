# 🦞 Closed Claw v3.0

**Secure Offline AI Assistant for Android - 100% Local, Zero Cloud**

---

## ⚡ One-Command Install (Run in Termux)

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh | bash
```

That's it! The installer will:
1. Check Termux environment ✅
2. Install all dependencies ✅
3. Download the project ✅
4. Configure your assistant (interactive) ✅
5. Download AI model (optional) ✅
6. Create launch commands ✅

---

## 🚀 After Install

```bash
cd ~/closed-claw-assistant
./claw
```

## Key Features

- **Model Persistence** - Loads ONCE, stays in memory for instant responses!
- **100% Offline** - No cloud, no data sharing
- **Banking Protection** - Blocks 45+ banking apps
- **Self-Aware AI** - Knows its identity, skills, limitations
- **Indian Voice** - Sarvam AI with natural Indian accent
- **Call Handling** - Auto-answers calls like a human

## First Use

1. Model takes 1-2 minutes to load on first message
2. After that, all responses are **instant**!
3. Type `help` for commands

## Storage

- **Model**: ~1.6 GB (Sarvam-1 2B Q4)
- **Install**: ~500 MB
- **Total**: ~3 GB free space
- **RAM**: ~2 GB when running

## Supported Devices

- Moto G45 (4GB RAM) - Works
- 6GB+ RAM devices - Full performance
- 8GB+ RAM devices - High performance

## Stop Assistant

```bash
./claw-stop
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

---

## Security

- ✅ 100% offline mode
- ✅ No data sharing  
- ✅ Banking app blocking (45+ apps)
- ✅ Audit logging
- ✅ Self-aware AI
- ✅ No cloud dependencies

---

## Compare with OpenClaw

| Feature | OpenClaw | Closed Claw v3.0 |
|---------|----------|------------------|
| Model Persistence | ❌ Reloads every message | ✅ Stays loaded |
| Response Time | 2+ min per message | Instant after first! |
| Data Sharing | ⚠️ Shares with Moltbook | ✅ 100% local |
| Security | CVE-2026-25253 | ✅ Secure |
| Banking Apps | ❌ Accessible | ✅ Blocked |

---

## GitHub

https://github.com/AdityaPagare619/closed-claw-assistant

---

**Made with ❤️ in India** 🇮🇳

*Privacy is a right, not a privilege.*
