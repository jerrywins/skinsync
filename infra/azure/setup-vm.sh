#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 VM for SkinSync (run as the VM's normal user, with sudo).
#   bash infra/azure/setup-vm.sh
# Installs Docker Engine + Compose plugin (Docker's official convenience script), adds 2 GB of swap so the
# web build fits on a 4 GB VM, and lets the current user run docker. Safe to run twice.
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "== Installing Docker"
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sudo sh /tmp/get-docker.sh
fi
sudo usermod -aG docker "$USER"

if ! swapon --show | grep -q /swapfile; then
  echo "== Adding 2 GB swap"
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

sudo apt-get install -y -qq make git >/dev/null
echo "== Done. Log out and back in (or run: newgrp docker), then check: docker compose version"
