# ElectrumX Server with Palladium (PLM) Full Node

Complete Dockerized setup for running an **ElectrumX server** with an integrated **Palladium (PLM) full node** and **Web Dashboard** for monitoring.

---

## What You Get

| Component | Description | Ports |
|-----------|-------------|-------|
| **Palladium Full Node** | Full blockchain node (palladiumd) | `2333` P2P · `2332` RPC (localhost only) |
| **ElectrumX Server** | Electrum protocol server for wallet connections | `50001` TCP · `50002` SSL |
| **Web Dashboard** | Real-time monitoring UI + REST API | `8080` HTTP |

---

## Requirements

- Docker 20.10+ and Docker Compose 2.0+
- 64-bit system (AMD64 or ARM64)
- 4 GB+ RAM, 50 GB+ free disk space
- Palladium binaries — see [daemon/README.md](daemon/README.md)

**Tested on:** Debian 12/13, Ubuntu 22.04/24.04, Raspberry Pi OS (ARM64), WSL2

---

## Architecture

```
Internet              Docker Host
   │                       │
   ├─ P2P  :2333 ──────► palladiumd
   ├─ TCP  :50001 ─────► electrumx ◄── palladiumd (internal RPC)
   ├─ SSL  :50002 ─────► electrumx
   └─ HTTP :8080  ─────► dashboard ◄── palladiumd (RPC) + electrumx (Electrum protocol)
```

---

## Quick Start

### Step 1 — Get Palladium Binaries

Download the binaries for your architecture and place them in `daemon/`.
→ See [daemon/README.md](daemon/README.md) for detailed instructions.

### Step 2 — Set RPC Credentials

Open `.palladium/palladium.conf` and set strong values:

```conf
rpcuser=your_username      # ← change this
rpcpassword=your_password  # ← use a strong password
```

### Step 3 — (Optional) Enable External Access

Skip this step if you only need local/LAN access.

If you plan to expose the dashboard or API to the internet:

```bash
./generate-api-key.sh   # generates a secure API key
cp .env.example .env
nano .env               # paste the key, set username and password
```

→ See [Security](#security) for what each variable controls.

### Step 4 — Start

```bash
docker compose up -d
```

First build: 5–10 minutes. Follow progress with:

```bash
docker compose logs -f
```

### Step 5 — Open the Dashboard

```
http://localhost:8080           # same machine
http://<your-server-ip>:8080   # from LAN
```

→ See [web-dashboard/README.md](web-dashboard/README.md) for features and REST API reference.

---

## Port Forwarding (Public Access)

To expose the stack to the internet, forward these ports on your router:

| Port | Protocol | Service | Required? |
|------|----------|---------|-----------|
| `2333` | TCP | Palladium P2P node sync | **Yes** |
| `50001` | TCP | ElectrumX — Electrum wallet connections | Recommended |
| `50002` | TCP | ElectrumX SSL — encrypted wallet connections | Recommended |
| `8080` | TCP | Web Dashboard | Optional — see [Security](#security) |

Set the forwarding destination to your server's local IP (`hostname -I | awk '{print $1}'`).

---

## Testnet

1. In `.palladium/palladium.conf`: add `testnet=1` and `rpcport=12332`
2. In `docker-compose.yml` (electrumx service): set `NET: "testnet"`
3. Clear ElectrumX database: `rm -rf ./electrumx-data/*`
4. Restart: `docker compose up -d`

---

## Common Commands

```bash
# Start / stop
docker compose up -d
docker compose down
docker compose restart

# Logs
docker compose logs -f                 # all services
docker compose logs -f palladiumd     # node only
docker compose logs -f electrumx      # ElectrumX only
docker compose logs -f dashboard      # dashboard only

# Status and resource usage
docker compose ps
docker stats

# Rebuild after code changes
docker compose up -d --build

# Query the node directly
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS getblockchaininfo
```

---

## Troubleshooting

**Containers not starting**
Check logs first: `docker compose logs <service-name>`
Common causes: wrong binary architecture, incorrect RPC credentials, port already in use.

**ElectrumX can't connect to the node**
Verify the node is running and credentials in `palladium.conf` are correct:
```bash
docker exec palladium-node palladium-cli -rpcuser=USER -rpcpassword=PASS getblockchaininfo
```

**Dashboard shows services as "down"**
The node and/or ElectrumX may still be syncing or indexing. Check logs and wait.

**Port already in use**
```bash
sudo lsof -i :<port>    # find what is using the port
```

**Wrong binary architecture**
```bash
uname -m                  # your system: x86_64 or aarch64
file daemon/palladiumd   # binary must match
```

**Dashboard not loading from LAN**
```bash
sudo ufw status           # check firewall
sudo ufw allow 8080/tcp  # open port if needed
netstat -tln | grep 8080  # verify dashboard is listening on 0.0.0.0:8080
```

---

## Security

**Authentication model:**

| Client origin | Dashboard (`/`) | API (`/api/*`) |
|---------------|-----------------|----------------|
| Localhost / LAN (RFC1918) | No auth required | No auth required |
| External / public IP | HTTP Basic Auth | API key required |

Configure in `.env` (copy from `.env.example`):

| Variable | Purpose |
|----------|---------|
| `DASHBOARD_AUTH_USERNAME` | Basic Auth username for external dashboard access |
| `DASHBOARD_AUTH_PASSWORD` | Basic Auth password for external dashboard access |
| `API_KEY` | Key for external API calls (`X-API-Key` header or `Authorization: Bearer`) |

**Firewall (recommended):**
```bash
sudo ufw allow 2333/tcp    # P2P
sudo ufw allow 50001/tcp   # ElectrumX TCP
sudo ufw allow 50002/tcp   # ElectrumX SSL
# Do NOT open 8080 without configuring auth in .env
sudo ufw enable
```

**SSL certificates:** Auto-generated on first startup in `./certs/` (self-signed, includes the server's public IP in the SAN). Replace with your own certificates (e.g. Let's Encrypt) by placing `server.crt` and `server.key` in `./certs/` before starting.

---

## Project Structure

```
palladium-stack/
├── daemon/                    # Palladium binaries (add these — see daemon/README.md)
├── .palladium/
│   ├── palladium.conf         # Node configuration (edit RPC credentials here)
│   ├── blocks/                # Blockchain data (auto-generated)
│   └── chainstate/            # Chain state (auto-generated)
├── certs/                     # SSL certificates (auto-generated on first run)
├── electrumx-data/            # ElectrumX database (auto-generated)
├── electrumx-patch/           # Palladium coin definition for ElectrumX
├── web-dashboard/             # Dashboard source (Flask backend + HTML/JS/CSS)
│   └── README.md              # Dashboard features and API reference
├── docker-compose.yml         # Service orchestration
├── Dockerfile.palladium-node
├── Dockerfile.electrumx
├── Dockerfile.dashboard
├── entrypoint.sh              # ElectrumX startup (SSL, IP detection, RPC config)
├── generate-api-key.sh        # Helper to generate a secure API key
├── .env.example               # Environment variables template
└── test_api.py                # Dashboard API test suite
```

---

## Backup

- Blockchain: `.palladium/blocks/`, `.palladium/chainstate/`
- Wallet (if used): `.palladium/wallet.dat` — **back this up regularly**
- ElectrumX index: `./electrumx-data/`
- Certificates: `./certs/`

To speed up a fresh install by copying an existing synced blockchain:
```bash
cp -r ~/.palladium/blocks .palladium/
cp -r ~/.palladium/chainstate .palladium/
cp -r ~/.palladium/indexes .palladium/
```

---

## Credits

- **ElectrumX:** [kyuupichan/electrumx](https://github.com/kyuupichan/electrumx)
- **Palladium Full Node:** [palladium-coin/palladiumcore](https://github.com/palladium-coin/palladiumcore)

Distributed under the **MIT License** — see `LICENSE`.
