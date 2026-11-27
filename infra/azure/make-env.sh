#!/usr/bin/env bash
# Create .env for the cloud demo with fresh random keys.
#   bash infra/azure/make-env.sh skinsync-yourname.centralindia.cloudapp.azure.com 'Your-Admin-Passphrase-1'
# Refuses to overwrite an existing .env (that would orphan the database password and encrypted uploads).
set -euo pipefail
host="${1:?usage: make-env.sh <dns-name> <admin-passphrase>}"
admin_pw="${2:?usage: make-env.sh <dns-name> <admin-passphrase>}"
[ ${#admin_pw} -ge 12 ] || { echo "admin passphrase must be at least 12 characters"; exit 1; }
[ ! -e .env ] || { echo ".env already exists; not overwriting it"; exit 1; }
case "$host" in http*|*/*) echo "give only the host name, without https:// or a slash"; exit 1;; esac

cat > .env <<ENV
# Cloud demo settings (created by infra/azure/make-env.sh). Never commit this file.
POSTGRES_PASSWORD=$(openssl rand -hex 16)
SKINSYNC_SECRET_KEY=$(openssl rand -hex 32)
SKINSYNC_IMAGE_ENCRYPTION_KEY=$(openssl rand -base64 32)
SKINSYNC_ENV=staging
SKINSYNC_COOKIE_SECURE=true
PUBLIC_BASE_URL=https://${host}
SITE_ADDRESS=${host}
SKINSYNC_DEMO_MODE=true
SKINSYNC_SKIN_MODEL_ADAPTER=heuristic
SKINSYNC_ADMIN_EMAIL=admin@example.com
SKINSYNC_ADMIN_PASSWORD=${admin_pw}
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 12)
ENV
chmod 600 .env
echo "Wrote .env for https://${host}"
