#!/bin/bash
# ============================================
# Article Factory — VPS Setup Script
# ============================================
# Tested on: Ubuntu 22.04+ / Debian 12+
# Usage: sudo bash deploy/setup.sh
# ============================================

set -e

APP_DIR="/opt/article-factory"
APP_USER="www-data"

echo "============================================"
echo "Article Factory — VPS Setup"
echo "============================================"

# 1. System packages
echo "[1/7] Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv redis-server supervisor git

# 2. Redis
echo "[2/7] Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

# 3. App directory
echo "[3/7] Setting up app directory..."
mkdir -p "$APP_DIR/logs"
if [ ! -d "$APP_DIR/.git" ]; then
    echo "  Copy your project files to $APP_DIR first, then re-run."
    echo "  Example: rsync -avz --exclude='.git' ./ user@vps:$APP_DIR/"
fi

# 4. Virtual environment
echo "[4/7] Creating virtual environment..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# 5. .env file
echo "[5/7] Checking .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env" 2>/dev/null || true
    echo "  WARNING: Edit $APP_DIR/.env with your real credentials!"
fi

# 6. Supervisor
echo "[6/7] Configuring Supervisor..."
cp "$APP_DIR/deploy/supervisor.conf" /etc/supervisor/conf.d/article-factory.conf
supervisorctl reread
supervisorctl update

# 7. Crontab
echo "[7/7] Installing crontab..."
crontab -l 2>/dev/null | grep -v "article-factory" | cat - "$APP_DIR/deploy/crontab.txt" | crontab -

# Permissions
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo ""
echo "============================================"
echo "Setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit $APP_DIR/.env with your credentials"
echo "  2. Copy tenant configs to $APP_DIR/config/tenants/"
echo "  3. Copy service_account.json to $APP_DIR/config/"
echo "  4. Check workers: supervisorctl status"
echo "  5. Check health: python $APP_DIR/health_check.py"
echo "  6. View dashboard: http://your-vps-ip:9181"
echo ""
