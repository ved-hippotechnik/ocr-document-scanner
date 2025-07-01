# Docker Compose Installation Guide

## Quick Installation

### macOS
```bash
# Option 1: Using Homebrew (Recommended)
brew install docker-compose

# Option 2: Direct download
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Option 3: Using pip
pip3 install docker-compose
```

### Linux
```bash
# Download latest version
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Create symlink (optional)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

### Windows
```bash
# Using Chocolatey
choco install docker-compose

# Or download from: https://github.com/docker/compose/releases
```

## Verification
```bash
docker-compose --version
```

## Alternative: Use Docker Desktop
Docker Desktop includes Docker Compose. Download from:
- https://www.docker.com/products/docker-desktop

## After Installation
Once Docker Compose is installed, use the full deployment:
```bash
./deploy.sh deploy
```

## Current Testing
For immediate testing without Docker Compose:
```bash
./test_deploy.sh deploy
```

This will run a single-container version for basic testing.
