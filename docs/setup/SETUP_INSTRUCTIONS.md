# Personal AI Assistant - Setup Instructions

**Status:** Execution Phase  
**Last Updated:** December 10, 2025

---

## Phase 0: Environment Setup

### 1. Docker Desktop Installation (M4 MacBook)

**Via Homebrew (Recommended - Easiest):**

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Verify installation
docker --version
docker run hello-world
```

**Alternative: Direct Download**
- Go to https://www.docker.com/products/docker-desktop
- Download Docker.dmg for Apple Silicon (M4)
- Open and drag Docker.app to Applications
- Launch Docker from Applications
- Verify: `docker --version`

**After Installation:**
```bash
# Start Docker daemon (if not auto-started)
open /Applications/Docker.app

# Enable Docker to start on login:
# System Preferences → General → Login Items → Add Docker.app
```

---

### 2. SSH Key Setup for TrueNAS (moria)

**Step 1: Generate SSH Key Pair on M4**

```bash
# Generate Ed25519 key (more secure, faster than RSA)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "andy@m4-macbook"

# When prompted:
# - Enter passphrase (optional but recommended): [create a strong passphrase]
# - Confirm passphrase

# Verify keys created
ls -la ~/.ssh/
# You should see: id_ed25519 (private) and id_ed25519.pub (public)
```

**Step 2: Copy Public Key to TrueNAS (moria)**

```bash
# Option A: Automatic (requires password once)
ssh-copy-id -i ~/.ssh/id_ed25519 andy@moria

# When prompted, enter your TrueNAS password for 'andy' user

# Option B: Manual
# 1. Print your public key:
cat ~/.ssh/id_ed25519.pub

# 2. SSH into TrueNAS manually:
ssh andy@moria
# Enter password when prompted

# 3. Once connected to TrueNAS, create the authorized_keys file:
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 4. Add your public key (paste the output from step 1):
cat >> ~/.ssh/authorized_keys << 'EOF'
[paste your id_ed25519.pub content here]
EOF

chmod 600 ~/.ssh/authorized_keys
exit
```

**Step 3: Test SSH Connection (Cert-Based)**

```bash
# This should NOT prompt for password (or only for key passphrase)
ssh andy@moria

# You should be logged in to TrueNAS
# Verify you can run commands:
uname -a
exit
```

**Step 4: (Optional) Add SSH Key to Keychain**

```bash
# Add your SSH key passphrase to macOS Keychain (auto-unlock on login)
ssh-add --apple-load-keychain ~/.ssh/id_ed25519

# This prevents needing to enter passphrase every time
# Verify it's loaded:
ssh-add -l
```

---

### 3. GitHub Repository Setup

**Step 1: Create GitHub Repo (via browser)**

1. Go to https://github.com/new
2. Repository name: `personal-ai-assistant` (or similar)
3. Description: "Query-based personal AI assistant - thought capture, task management, Claude API integration"
4. Visibility: **Private** (keep your thoughts private!)
5. Initialize with: README.md
6. Create repository

**Step 2: Clone to Local M4**

```bash
# Navigate to your projects directory
cd ~/Dev  # or wherever you keep projects

# Clone the repo
git clone https://github.com/[YOUR_USERNAME]/personal-ai-assistant.git
cd personal-ai-assistant

# Verify it's set up
git remote -v
# Should show: origin https://github.com/.../personal-ai-assistant.git
```

**Step 3: Set Up Git Locally (if not done before)**

```bash
# Configure git with your info
git config --global user.name "Andy"
git config --global user.email "andy@[your-email].com"

# Verify
git config --global --list
```

**Step 4: Initial Commit Structure**

```bash
# From inside personal-ai-assistant directory

# Create project structure
mkdir -p {src,docs,tests,docker,scripts}

# Copy the architecture doc
cp ~/PersonalAI_Architecture.md docs/ARCHITECTURE.md

# Create initial files (see step below)

# Add everything to git
git add .
git commit -m "Initial project structure and architecture"
git push origin main
```

---

### 4. Create Initial Project Structure

**Run these commands from `~/Dev/personal-ai-assistant/`:**

```bash
# Create directories
mkdir -p src/api src/models src/services
mkdir -p tests/unit tests/integration
mkdir -p docker
mkdir -p docs

# Create initial Python files (empty, for structure)
touch src/__init__.py
touch src/api/__init__.py src/api/main.py
touch src/models/__init__.py src/models/thought.py src/models/task.py
touch src/services/__init__.py src/services/claude_service.py src/services/storage_service.py

# Create test files
touch tests/__init__.py tests/conftest.py
touch tests/unit/test_api.py tests/integration/test_claude_integration.py

# Create config/deployment files
touch docker/Dockerfile
touch docker/docker-compose.yml
touch requirements.txt
touch .gitignore
touch README.md
```

**Create `.gitignore`:**

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# OS
.DS_Store
.AppleDouble
.LSOverride

# Secrets
secrets/
*.key
*.pem
EOF
```

---

### 5. SSH Key for GitHub (Optional but Recommended)

**If you want to push to GitHub via SSH instead of HTTPS:**

```bash
# Generate separate key for GitHub (optional)
ssh-keygen -t ed25519 -f ~/.ssh/github -C "andy@github"

# Print public key
cat ~/.ssh/github.pub

# Go to GitHub → Settings → SSH and GPG Keys → New SSH Key
# Paste the contents of github.pub

# Add to SSH config for convenience
cat >> ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github
EOF

# Test connection
ssh -T git@github.com
# Should respond: "Hi [username]! You've successfully authenticated..."
```

---

## Phase 1: Verification Checklist

Before we proceed to actual development, verify everything works:

- [ ] Docker Desktop installed and running (`docker --version` works)
- [ ] SSH to moria works without password (`ssh andy@moria` connects)
- [ ] Git configured locally (`git config --list` shows your name/email)
- [ ] GitHub repo created and cloned locally
- [ ] Project structure initialized
- [ ] Initial commit pushed to GitHub

---

## Phase 2: Development Environment Setup (Optional but Recommended)

### Python Virtual Environment

```bash
# From personal-ai-assistant directory
python3 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install initial dependencies
pip install fastapi uvicorn sqlalchemy sqlite3 anthropic

# Generate requirements.txt
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

---

## Next Steps

Once Phase 1 is verified:

1. **I will create detailed specifications** for:
   - FastAPI service architecture (for Sonnet/Opus)
   - Database schema and models (for Sonnet/Opus)
   - API endpoint specifications (for Sonnet/Opus)
   - Test suite approach (for Sonnet/Opus)

2. **You will run those specs through Claude Sonnet/Opus** to generate initial code

3. **I will coordinate integration** and deployment to TrueNAS via Docker

4. **We will iterate** with regular sync-ups

---

## Commands Reference

**Quick SSH to TrueNAS:**
```bash
ssh andy@moria
```

**Quick Docker check:**
```bash
docker ps
docker images
```

**Git workflow:**
```bash
git status
git add .
git commit -m "your message"
git push origin main
```

---

## Troubleshooting

**SSH still asks for password:**
- Verify key is in TrueNAS `~/.ssh/authorized_keys`
- Check permissions: `ls -la ~/.ssh/` should show 700 on directory, 600 on files
- Try: `ssh -v andy@moria` for verbose debugging

**Docker won't start:**
- Restart Docker Desktop
- Check System Preferences → Security & Privacy → Docker permissions
- Try: `sudo dockutil --add /Applications/Docker.app`

**Git push fails:**
- Verify GitHub repo URL: `git remote -v`
- Check you have write permissions to the repo
- For SSH: verify GitHub key is added to https://github.com/settings/keys

---

## Questions?

Once you've completed Phase 1, let me know the results. We'll proceed with detailed specifications for the actual development work.
