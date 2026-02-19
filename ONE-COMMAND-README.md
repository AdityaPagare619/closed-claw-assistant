# Closed Claw v3.0 - One-Command Install

## Quick Install (Run in Termux)

```bash
curl -fsSL https://raw.githubusercontent.com/AdityaPagare619/closed-claw-assistant/main/install.sh | bash
```

That's it! The installer will:
1. Check Termux environment
2. Install all dependencies
3. Download the project
4. Configure your assistant interactively
5. Download the AI model (optional)
6. Create launch commands

## After Install

```bash
cd ~/closed-claw-assistant
./claw
```

## Features

- **Model Persistence**: Loads once, stays in memory for instant responses
- **100% Offline**: No cloud, no data sharing
- **Banking Protection**: Blocks 45+ banking apps
- **Self-Aware**: Knows its identity, skills, limitations
- **Indian Voice**: Sarvam AI with natural Indian accent

## First Run

1. Model takes 1-2 minutes to load on first message
2. After that, responses are instant!
3. Type `help` for commands

## Troubleshooting

If model not found:
```bash
cd ~/closed-claw-assistant/models
wget https://huggingface.co/sarvam/sarvam-1-2b/resolve/main/sarvam-1-2b-q4.gguf
```

## Stop Assistant

```bash
./claw-stop
```