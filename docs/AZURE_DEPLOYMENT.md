# Deploying SkinSync to Azure (Azure for Students)

One Linux virtual machine on Azure runs the same Docker stack as your laptop, behind Caddy with automatic
HTTPS on a free Azure DNS name. About 1 hour the first time, mostly waiting for builds.

> **Honesty note:** these steps were written from Azure's documentation and the project's tested Docker
> setup, and the cloud settings were tested locally (staging mode, HTTPS cookies, generated `.env`). They have
> **not** been run on Azure by the author. If a step differs from what you see, follow the portal and ask.

## What it costs

Azure for Students gives **US$100 credit for 12 months, no credit card**, verified with your college email.
When the credit runs out the subscription is **disabled, not charged**. The free-tier VM sizes (B1s, B2ats v2,
B2pts v2) have only 1 GB of memory, which is too small for this app, so use a **4 GB size, paid from the credit**:
roughly US$1 per day while running (the portal shows the exact price). **Stop** the VM when you are not
using it; a stopped (deallocated) VM costs only its disk, a few cents a day.

## 1. Get the subscription

1. Go to https://azure.microsoft.com/free/students and click **Start free**.
2. Sign up with your **college email** (e.g. `@thapar.edu`) and verify it.
3. You land in the **Azure portal** (https://portal.azure.com). Search "Subscriptions": you should see
   **Azure for Students**.

## 2. Create the virtual machine

Portal → search **Virtual machines** → **Create** → **Azure virtual machine**.

**Basics tab**

| Field | Value |
|---|---|
| Subscription | Azure for Students |
| Resource group | **Create new** → `skinsync-rg` |
| Virtual machine name | `skinsync-vm` |
| Region | One close to you, e.g. **(Asia Pacific) Central India**. If creation later fails with "RequestDisallowedByPolicy" or the size is unavailable, pick another region: student subscriptions only allow some |
| Availability options | No infrastructure redundancy required |
| Security type | Standard (or the default) |
| Image | **Ubuntu Server 24.04 LTS - x64 Gen2** |
| Size | **Standard_B2s (2 vCPUs, 4 GiB)**. If not listed: B2s_v2 or B2as_v2 (also 2 vCPUs, 4 GiB). Click "See all sizes" |
| Authentication type | SSH public key |
| Username | `azureuser` |
| SSH public key source | Generate new key pair, Key pair name `skinsync-key` |
| Public inbound ports | Allow selected ports: **SSH (22), HTTP (80), HTTPS (443)** |

**Disks tab:** OS disk type **Standard SSD**. Default size (30 GiB) is enough.

**Networking tab:** keep the defaults (new virtual network, new public IP).

Click **Review + create** → **Create** → **Download private key and create resource**. Your browser
downloads `skinsync-key.pem`. Keep it safe: it is the only way in.

When it says "Your deployment is complete", click **Go to resource**.

## 3. Give it a name with HTTPS

On the VM's **Overview** page, next to **DNS name**, click **Not configured** (or the public IP address):

1. **DNS name label:** something unique such as `skinsync-yourname` → **Save**.
2. Your site address is now `skinsync-yourname.<region>.cloudapp.azure.com`, e.g.
   `skinsync-yourname.centralindia.cloudapp.azure.com`. Copy it from the Overview page; it is used below as
   **YOUR-DNS-NAME**.

## 4. Connect to the VM

On your Mac (Terminal), from the folder where the key was downloaded:

```bash
cd ~/Downloads
chmod 400 skinsync-key.pem
ssh -i skinsync-key.pem azureuser@YOUR-DNS-NAME
```

Type `yes` the first time. The prompt changes to `azureuser@skinsync-vm:~$`: everything from here runs **on the VM**.

## 5. Install Docker and get the code

```bash
git clone https://github.com/jerrywins/skinsync.git
cd skinsync
bash infra/azure/setup-vm.sh
newgrp docker
docker compose version
```

If the repository is private, `git clone` asks for your GitHub username and a token as the password (a token
with **Contents: Read** is enough).

## 6. Create the settings file

Replace both values. The passphrase is the admin password: at least 12 characters, using only letters, digits and hyphens (no spaces or `$`):

```bash
bash infra/azure/make-env.sh YOUR-DNS-NAME 'Your-Admin-Passphrase-1'
```

This writes `.env` with fresh random keys, HTTPS cookies, and `SKINSYNC_ENV=staging` (strong keys and HTTPS
are enforced; the labelled demo data is allowed).

## 7. Build and start

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d --build
docker compose ps
```

The first build takes 10–25 minutes. Wait until `api` is **(healthy)** and `web`, `worker`, `caddy` are **Up**.

## 8. Load the data

```bash
source .env
docker compose exec -e SKINSYNC_ADMIN_PASSWORD="$SKINSYNC_ADMIN_PASSWORD" api python -m skinsync.cli create-admin admin@example.com
docker compose exec api python -m skinsync.cli seed-demo
make import-obf          # optional: real Open Beauty Facts products (large download, several minutes)
```

## 9. Open it

Open **https://YOUR-DNS-NAME** from any device, including your phone. The padlock should show a valid
certificate (Caddy gets it from Let's Encrypt automatically on first visit; give it a minute).
Sign in as `admin@example.com` with your passphrase.

The camera on Analyze and Scan works on phones here because the site is HTTPS.

### Optional: switch on the draft rules for the demo (as on your Mac)

```bash
sed -i 's/review_status: draft/review_status: reviewed/' knowledge/rules.yaml
docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d --build
```

Then Admin → Knowledge versions → `kv-demo-1` → **Import reviewed files as a draft** → **Send to review** →
**Publish**. Do not commit this change. Undo with `git checkout knowledge/rules.yaml` and rebuild.

### Optional: see sign-up emails

Emails are caught by Mailpit on the VM, which is not public. From your Mac, open a tunnel:

```bash
ssh -i ~/Downloads/skinsync-key.pem -L 8025:localhost:8025 azureuser@YOUR-DNS-NAME
```

and open http://localhost:8025 on your Mac while it is connected.

## 10. Day-to-day

| Task | How |
|---|---|
| Stop paying for compute | Portal → VM → **Stop**. Status must say **Stopped (deallocated)** |
| Start again | Portal → VM → **Start**. The containers restart by themselves; the address stays the same |
| Update to the latest code | SSH in, `cd skinsync && git pull`, then the command in step 7 |
| See logs | `docker compose logs --tail=50 api` (or `web`, `caddy`) |
| Back up the database | `make backup` (writes to `backups/`) |
| Check remaining credit | Portal → search **Cost Management** (or Subscriptions → Azure for Students) |
| Delete everything | Portal → Resource groups → `skinsync-rg` → **Delete resource group** |

## If something goes wrong

| Symptom | Fix |
|---|---|
| `ssh: connect ... timed out` | VM stopped, or port 22 not allowed. Portal → VM → Networking: add inbound rule for 22 |
| Browser can't reach the site | Ports 80/443 not allowed: VM → Networking → add inbound rules for 80 and 443 |
| Certificate error | DNS label not set, or `SITE_ADDRESS` in `.env` differs from it. `docker compose logs caddy` |
| `api` restarting | `docker compose logs api --tail=60`. "must be set to a strong value" means `.env` was edited |
| Build killed / "exit 137" | Not enough memory: check the VM size is 4 GiB and the setup script added swap (`swapon --show`) |
| Size not available | Try B2s_v2 / B2as_v2, or another region |

## What is "cloud" here (for the report)

| Cloud concept | In this deployment |
|---|---|
| IaaS virtual machine | Azure VM (Ubuntu), B-series burstable, pay-per-hour from student credit |
| Networking & security groups | Azure Network Security Group: only 22, 80, 443 open; database and Redis unreachable from outside |
| Public IP and DNS | Static public IP with an Azure DNS label (`*.cloudapp.azure.com`) |
| TLS / HTTPS | Caddy reverse proxy with automatic Let's Encrypt certificates; HSTS; secure cookies |
| Containerisation | 7 Docker containers (Caddy, Next.js web, FastAPI API, RQ worker, PostgreSQL, Redis, Mailpit) via Compose |
| Persistent storage | Docker volumes on the VM's managed disk (database, Redis, encrypted uploads, certificates) |
| CI | GitHub Actions: lint, security scans, tests, image builds and vulnerability scans on every push |
| Elastic cost control | Stop/deallocate the VM when idle; only the disk is billed |
| Observability | Health checks per container; optional Prometheus + Grafana (`--profile observability`) |
