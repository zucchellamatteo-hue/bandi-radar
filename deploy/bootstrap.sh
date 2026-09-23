#!/usr/bin/env bash
# Bandi Radar - preparazione del VPS (Ubuntu 24.04, OVH).
# Si lancia UNA volta, da root, sul server appena creato:
#   curl -fsSL https://raw.githubusercontent.com/zucchellamatteo-hue/bandi-radar/main/deploy/bootstrap.sh | sudo bash
# E' idempotente: rilanciarlo non fa danni.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/zucchellamatteo-hue/bandi-radar.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="/srv/bandi-radar"
DEPLOY_USER="deploy"

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "Lancialo con sudo."; exit 1; }
export DEBIAN_FRONTEND=noninteractive

log "Aggiornamento del sistema"
apt-get update -q
apt-get upgrade -yq

log "Pacchetti di base"
apt-get install -yq ca-certificates curl git gnupg ufw fail2ban unattended-upgrades

log "Aggiornamenti di sicurezza automatici"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'CONF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
CONF

log "Fuso orario e swap"
timedatectl set-timezone Europe/Rome
if ! swapon --show | grep -q swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

log "Firewall: solo SSH, HTTP e HTTPS"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

log "fail2ban su SSH"
cat > /etc/fail2ban/jail.local <<'CONF'
[sshd]
enabled = true
maxretry = 5
bantime = 1h
CONF
systemctl enable --now fail2ban

log "Docker (repository ufficiale)"
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -yq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker

log "Utente di servizio '$DEPLOY_USER'"
id -u "$DEPLOY_USER" >/dev/null 2>&1 || useradd -m -s /bin/bash -G docker "$DEPLOY_USER"
usermod -aG docker "$DEPLOY_USER"

log "Copia del repository in $APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR"

log "Aggiornamento automatico da GitHub ogni 5 minuti"
cat > /usr/local/bin/bandi-radar-deploy <<'SCRIPT'
#!/usr/bin/env bash
# Scarica le novita' dal repository e, se c'e' un docker-compose, (ri)avvia i servizi.
set -euo pipefail
cd /srv/bandi-radar
BEFORE=$(git rev-parse HEAD)
git fetch -q origin
git reset -q --hard "origin/$(git rev-parse --abbrev-ref HEAD)"
AFTER=$(git rev-parse HEAD)
if [ -f docker-compose.yml ] || [ -f compose.yml ]; then
  if [ "$BEFORE" != "$AFTER" ] || ! docker compose ps --quiet 2>/dev/null | grep -q .; then
    docker compose pull -q || true
    docker compose up -d --build --remove-orphans
    echo "$(date -Is) deploy $BEFORE -> $AFTER"
  fi
fi
SCRIPT
chmod +x /usr/local/bin/bandi-radar-deploy

cat > /etc/systemd/system/bandi-radar-deploy.service <<'UNIT'
[Unit]
Description=Bandi Radar: aggiornamento da GitHub
After=network-online.target docker.service
[Service]
Type=oneshot
User=deploy
WorkingDirectory=/srv/bandi-radar
ExecStart=/usr/local/bin/bandi-radar-deploy
UNIT

cat > /etc/systemd/system/bandi-radar-deploy.timer <<'UNIT'
[Unit]
Description=Bandi Radar: controlla GitHub ogni 5 minuti
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now bandi-radar-deploy.timer

log "Backup notturno del database (quando esistera')"
mkdir -p /var/backups/bandi-radar
cat > /etc/cron.d/bandi-radar-backup <<'CRON'
# ogni notte alle 03:30: dump di Postgres se il container esiste; tiene 14 giorni
30 3 * * * deploy cd /srv/bandi-radar && docker compose ps --services 2>/dev/null | grep -qx db && docker compose exec -T db pg_dumpall -U postgres | gzip > /var/backups/bandi-radar/db-$(date +\%F).sql.gz; find /var/backups/bandi-radar -name 'db-*.sql.gz' -mtime +14 -delete
CRON
chown deploy /var/backups/bandi-radar

log "Fatto."
echo "Repository in $APP_DIR (branch $BRANCH). Ogni 5 minuti il server scarica le novita' da GitHub."
echo "Log degli aggiornamenti: journalctl -u bandi-radar-deploy.service"
