# Storage Requirements

## Closed Claw v3.0 - Storage Breakdown

### Model Size
- **Sarvam-1 2B (Q4)**: ~1.6 GB
- Download from: https://huggingface.co/sarvam/sarvam-1-2b

### Installation
- Python packages: ~500 MB
- Project files: ~50 MB
- Logs & cache: ~100 MB

### Total Required
- **Minimum**: 3 GB free space
- **Recommended**: 5 GB free space

### Runtime RAM
- Model loaded: ~1.4 GB
- System overhead: ~500 MB
- **Total RAM**: ~2 GB

### Supported Devices
- Moto G45 (4GB RAM) - Works with reduced context
- 6GB+ RAM devices - Full performance
- 8GB+ RAM devices - High performance mode

## Optimize Storage

Remove unused models:
```bash
rm ~/closed-claw-assistant/models/*.gguf
```

Re-download when needed:
```bash
cd ~/closed-claw-assistant/models
wget https://huggingface.co/sarvam/sarvam-1-2b/resolve/main/sarvam-1-2b-q4.gguf
```