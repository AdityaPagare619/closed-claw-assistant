# 🧪 Testing Call Pickup & All Features

## Quick Test Commands:

### 1. Run Full Test Suite:
```bash
python3 scripts/test-suite.py
```

### 2. Test Voice (Sarvam):
```bash
python3 -c "from src.brain.sarvam_voice_system import SarvamVoiceSystem; import asyncio; v = SarvamVoiceSystem(); asyncio.run(v.speak('Namaste'))"
```

### 3. Simulate Call:
```bash
python3 scripts/simulate-call.sh
```

### 4. Test AI Brain:
```bash
python3 -c "from src.brain.sarvam_brain import SarvamBrain; import asyncio; b = SarvamBrain({'model_path': 'models/sarvam-1-q4_0_4_4.gguf'}); print(asyncio.run(b.generate('Hello')))"
```

## Real Call Testing:

1. Start assistant: `bash scripts/start.sh`
2. Ask friend to call your phone
3. Don't answer - wait 20 seconds
4. Assistant picks up automatically
5. Check Telegram for summary

## Hardware Optimization:

- **Model**: Use `sarvam-1-q4_0_4_4.gguf` (optimized for ARM)
- **Threads**: 6 (leave 2 for system)
- **Context**: 2048 tokens (balance speed/quality)
- **Cache**: 100 phrases preloaded for instant response
- **RAM**: ~1.4GB peak usage

## Performance Targets:

- AI Response: 1-2 seconds
- Voice (cached): <1 second
- Voice (API): <2 seconds
- Call pickup: <1 second
- Battery: <3%/hour

Full testing guide in local file.
