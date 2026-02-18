# Security Policy

## ⚠️ IMPORTANT - NEVER COMMIT CREDENTIALS

### Protected Files (Never Commit to Git):

1. **config/config.local.json** - Contains real API keys, tokens, passwords
2. **.env** - Environment variables with secrets
3. **telegram.session** - Telegram authentication session
4. **whatsapp_session/** - WhatsApp Web session data
5. **logs/** - May contain sensitive conversation data

### How to Use Credentials Safely:

```bash
# 1. Copy example config
cp config/config.example.json config/config.local.json

# 2. Edit with your real credentials
nano config/config.local.json

# 3. Application automatically loads config.local.json
# (it's in .gitignore, so won't be committed)
```

### What Happens If You Accidentally Commit:

1. **Immediately revoke/change the exposed credential**
2. Remove from git history:
   ```bash
   git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch config/config.local.json' --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push (be careful!): `git push origin main --force`

### For Local Testing Only:

Use `config/config.local.json` - this file is:
- ✅ Loaded by the application
- ✅ Never committed to Git (in .gitignore)
- ✅ Safe for real credentials

### Token Safety:

The bot token you provided should ONLY be in:
- `config/config.local.json` (local file)
- NEVER in: `config.json`, source code, or GitHub

---
**Security First: Credentials committed to GitHub are public forever!**
