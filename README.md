# ElectrumX Server with Palladium (PLM) Full Node

Complete Dockerized setup for running an **ElectrumX server** with an integrated **Palladium (PLM) full node** and professional **Web Dashboard** for monitoring.

Everything runs in Docker containers - no need to install dependencies on your host system!

---

## What You Get

- **Palladium Full Node** (palladiumd) - Runs in Docker with full blockchain sync ([binary setup](daemon/README.md))
- **ElectrumX Server** - Pre-configured for Palladium network with automatic indexing
- **Web Dashboard** - Professional monitoring interface with real-time statistics, peer views, and Electrum server discovery ([quick start](DASHBOARD.md) | [technical docs](web-dashboard/README.md))
- **Automatic RPC Configuration** - ElectrumX reads credentials directly from palladium.conf
- **Self-Signed SSL Certificates** - Auto-generated on first startup, persisted in `./certs/`
- **Public IP Auto-Detection** - Automatically configures REPORT_SERVICES and SSL certificate SAN
- **Production Ready** - Includes restart policies, health endpoint, and Basic Auth for external dashboard access

---

## Tested Platforms

* Debian 12/13
* Ubuntu 24.04/22.04 LTS
* Raspberry Pi OS (ARM64)
* WSL2 (Windows Subsystem for Linux)

**System Requirements:**
- 64-bit system (AMD64 or ARM64)
- 4GB+ RAM recommended
- 50GB+ free disk space for blockchain
- Stable internet connection

---

## Project Structure

```
palladium-stack/
├── daemon/                          # Palladium binaries (YOU must add these)
│   ├── palladiumd                   # Node daemon (required)
│   ├── palladium-cli                # CLI tool (required)
│   ├── palladium-tx                 # Transaction tool (optional)
│   ├── palladium-wallet             # Wallet tool (optional)
│   └── README.md                    # Binary download instructions
├── .palladium/
│   ├── palladium.conf               # Node configuration (edit this!)
│   ├── blocks/                      # Blockchain blocks (auto-generated)
│   ├── chainstate/                  # Blockchain state (auto-generated)
│   └── ...                          # Other runtime data (auto-generated)
├── certs/                           # SSL certificates (auto-generated on first run)
│   ├── server.crt                   # Self-signed certificate
│   └── server.key                   # Private key
├── electrumx-data/                  # ElectrumX database (auto-generated)
├── electrumx-patch/
│   └── coins_plm.py                 # Palladium coin definition for ElectrumX
├── web-dashboard/                   # Web monitoring dashboard
│   ├── app.py                       # Flask backend API
│   ├── templates/                   # HTML templates
│   ├── static/                      # CSS and JavaScript
│   └── README.md                    # Dashboard technical docs
├── Dockerfile.palladium-node        # Builds Palladium node container
├── Dockerfile.electrumx             # Builds ElectrumX server container
├── Dockerfile.dashboard             # Builds web dashboard container
├── docker-compose.yml               # Main orchestration file
├── entrypoint.sh                    # ElectrumX startup (auto-config, SSL, IP detection)
├── test-server.py                   # ElectrumX protocol test client
├── .env.example                     # Environment variables template
└── DASHBOARD.md                     # Dashboard quick start guide
```

**Palladium Full Node:** [palladium-coin/palladiumcore](https://github.com/palladium-coin/palladiumcore)

---

## Architecture

```
Internet                Router/Firewall           Docker Network
   │                          │                          │
   │                    ┌─────▼──────┐                   │
   │                    │  Port      │                   │
   │    P2P (2333) ────►│  Forward   │──────────┐        │
   │    TCP (50001)────►│  Rules     │────┐     │        │
   │    SSL (50002)────►│            │──┐ │     │        │
   │    Web (8080) ────►│            │─┐│ │     │        │
   │                    └────────────┘ ││ │     │        │
   │                                   ││ │     │        │
   │                         ┌─────────▼▼─▼─────▼─────┐  │
   │                         │   Docker Host          │  │
   │                         │                        │  │
   │                         │  ┌───────────────────┐ │  │
   │                         │  │  Palladium Node   │ │  │
   │                         │  │   (palladiumd)    │ │  │
   │                         │  │   Port: 2333      │ │  │
   │                         │  └────────┬──────────┘ │  │
   │                         │           │            │  │
   │                         │  ┌────────▼──────────┐ │  │
   │                         │  │  ElectrumX Server │ │  │
Clients◄────────────────────────┤  TCP: 50001       │ │  │
(Electrum                    │  │  SSL: 50002       │ │  │
 Wallets)                    │  └────────┬──────────┘ │  │
   │                         │           │            │  │
   │                         │  ┌────────▼─────────┐  │  │
   ▼                         │  │  Web Dashboard   │  │  │
Browser◄───────────────────────┤  Port: 8080       │  │  │
                             │  └──────────────────┘  │  │
                             └────────────────────────┘  │
```

**Component Communication:**
- **ElectrumX** ↔ **Palladium Node**: RPC over internal Docker network
- **Web Dashboard** ↔ **Palladium Node**: RPC for blockchain data
- **Web Dashboard** ↔ **ElectrumX**: Electrum protocol + Docker API for stats
- **External Clients** → **ElectrumX**: TCP (50001) or SSL (50002)
- **Browsers** → **Web Dashboard**: HTTP (8080)

---

## Requirements

* [Docker](https://docs.docker.com/get-docker/) 20.10+
* [Docker Compose](https://docs.docker.com/compose/install/) 2.0+
* **Palladium binaries** - See installation instructions below

---

## Quick Start Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/palladium-coin/palladium-stack.git
cd palladium-stack
```

---

### Step 2: Get Palladium Binaries

**IMPORTANT:** Download binaries matching your system architecture in `daemon/`. 

See [daemon/README.md](daemon/README.md) for detailed instructions.

---

### Step 3: Configure Network and Router

#### 3.1 Configure RPC Credentials

Open the configuration file:

```bash
nano .palladium/palladium.conf
```

**Change these credentials:**
```conf
rpcuser=your_username     # ← Change this
rpcpassword=your_password # ← Use a strong password!
```

Save and close (`Ctrl+X`, then `Y`, then `Enter`).

#### 3.2 Router Port Forwarding (Required for Public Access)

For your ElectrumX server to be accessible from the internet, you **must** configure port forwarding on your router.

**Ports to Forward:**

| Port | Protocol | Service | Description | Required? |
|------|----------|---------|-------------|-----------|
| **2333** | TCP | Palladium P2P | Node connections | **Yes** (for node sync) |
| **50001** | TCP | ElectrumX TCP | Wallet connections | Recommended |
| **50002** | TCP | ElectrumX SSL | Encrypted wallet connections | **Recommended** |
| **8080** | TCP | Web Dashboard | Monitoring interface | Optional |

**How to Configure Port Forwarding:**

1. **Find Your Internal IP:**
   ```bash
   # Linux/Mac:
   hostname -I

   # Or check in Docker host:
   ip addr show
   ```
   Example: `192.168.1.100`

2. **Access Your Router:**
   - Open browser and go to your router's admin page (usually `192.168.1.1` or `192.168.0.1`)
   - Login with router credentials

3. **Add Port Forwarding Rules:**

   Navigate to **Port Forwarding** or **Virtual Server** section and add:

   ```
   Service Name: Palladium P2P
   External Port: 2333
   Internal Port: 2333
   Internal IP: 192.168.1.100 (your server's IP)
   Protocol: TCP

   Service Name: ElectrumX SSL
   External Port: 50002
   Internal Port: 50002
   Internal IP: 192.168.1.100
   Protocol: TCP

   Service Name: ElectrumX TCP
   External Port: 50001
   Internal Port: 50001
   Internal IP: 192.168.1.100
   Protocol: TCP

   Service Name: PLM Dashboard (optional)
   External Port: 8080
   Internal Port: 8080
   Internal IP: 192.168.1.100
   Protocol: TCP
   ```

4. **Save and Apply** the configuration.

5. **Find Your Public IP:**
   ```bash
   curl ifconfig.me
   ```
   Or visit: https://whatismyipaddress.com

**Security Notes:**
- Only forward port **8080** if you want the dashboard accessible from internet (not recommended without authentication)
- Consider using a VPN for dashboard access instead
- External dashboard clients (public IPs) require Basic Auth. Configure `DASHBOARD_AUTH_USERNAME` and `DASHBOARD_AUTH_PASSWORD` in `.env` (see `.env.example`).
- External API calls (`/api/*`) from public/external IPs require `API_KEY` via `X-API-Key` header (or `Authorization: Bearer`).
- Ports **50001** and **50002** need to be public for Electrum wallets to connect
- Port **2333** is required for the node to sync with the Palladium network

---

#### 3.3: (Optional) Configure Dashboard Authentication

If you plan to expose the dashboard to the internet (port 8080), configure Basic Auth credentials:

```bash
# 1) Generate a secure API key first
./generate-api-key.sh

# 2) Create your env file
cp .env.example .env

# 3) Paste the generated API key and set username/password
nano .env
```

Set strong credentials:
```bash
DASHBOARD_AUTH_USERNAME=admin
DASHBOARD_AUTH_PASSWORD=a-strong-random-password
API_KEY=a-long-random-api-key
```

LAN clients (private IPs) can access the dashboard without authentication. External clients (public IPs) use Basic Auth for dashboard pages, while `/api/*` requests require `API_KEY`.

---

### Step 4: (Optional) Copy Existing Blockchain Data

If you have a synced Palladium blockchain, copy it to speed up initial sync:

```bash
cp -r ~/.palladium/blocks .palladium/
cp -r ~/.palladium/chainstate .palladium/
cp -r ~/.palladium/indexes .palladium/
```

**Skip this** if syncing from scratch - the node will automatically start syncing.

---

### Step 5: Build and Start

```bash
docker compose up -d
```

**What happens:**
1. Builds three Docker images: `palladium-node`, `electrumx-server`, and `palladium-dashboard`
2. Starts Palladium node first
3. Starts ElectrumX (waits for node to be ready, auto-generates SSL certificates in `./certs/` if not present)
4. Starts Web Dashboard (connects to both services)

**First build takes 5-10 minutes.**

---

### Step 6: Monitor Progress

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f palladiumd
docker compose logs -f electrumx
docker compose logs -f dashboard
```

**What to look for:**
- **Palladium node:** "UpdateTip" messages (syncing blockchain)
- **ElectrumX:** "height X/Y" (indexing blocks)
- **Dashboard:** "Running on http://0.0.0.0:8080"

Press `Ctrl+C` to exit log view (containers keep running).

---

### Step 7: Access Web Dashboard

**Local access:**
```
http://localhost:8080
```

**Network access:**
```
http://<your-server-ip>:8080
```

**From internet (if port 8080 forwarded):**
```
http://<your-public-ip>:8080
```

The dashboard shows:
- System resources (CPU, RAM, Disk)
- Palladium node status (height, difficulty, connections, sync progress)
- ElectrumX server stats (version, active servers, DB size, uptime, **server IP**, ports)
- Mempool information (transactions, size, usage)
- Recent blocks table
- Network peers (click "Connections" to view detailed peer list)
- Electrum active servers page (click "Active Servers")

---

## Web Dashboard Features

See also: [DASHBOARD.md](DASHBOARD.md) for quick start | [web-dashboard/README.md](web-dashboard/README.md) for technical details

### Main Dashboard (http://localhost:8080)

**System Monitoring:**
- Real-time CPU, Memory, and Disk usage with animated progress bars
- Health status indicator with pulse animation

**Palladium Node:**
- Block Height (formatted with thousands separator: 380,050)
- Difficulty (abbreviated: 18.5 M)
- **Connections** (clickable - opens dedicated peers page)
- Network type (MAINNET/TESTNET)
- Sync Progress percentage
- Node version (vX.X.X format)

**ElectrumX Server:**
- Server Version
- Database Size
- Uptime
- Active Servers (clickable to dedicated server list)
- **Server IP** (for client configuration)
- TCP Port (50001)
- SSL Port (50002)

**Mempool:**
- Transaction count
- Total size (bytes)
- Usage percentage
- Max size limit

**Recent Blocks:**
- Last 10 blocks with hash, time, size, and transaction count

### Network Peers Page (http://localhost:8080/peers)

**Statistics:**
- Total Peers count
- Inbound connections
- Outbound connections
- Total traffic (sent + received)

**Detailed Peer List:**
- IP Address and port
- Direction (⬇️ Inbound / ⬆️ Outbound)
- Node version
- Connection time
- Data sent
- Data received
- Total traffic per peer

**Auto-refresh:** Every 10 seconds

### Electrum Active Servers Page (http://localhost:8080/electrum-servers)

**Summary:**
- Total Active Servers
- TCP 50001 Reachable

**Detailed Server List:**
- Host
- TCP Port
- SSL Port
- TCP Reachable (Yes/No)
- SSL Reachable (Yes/No)

Servers are filtered by genesis hash to show only peers on the same network (mainnet or testnet).

**Auto-refresh:** Every 10 seconds

---

## Verify Installation

### Check Container Status

```bash
docker compose ps
```

Should show all three containers "Up".

### Test Palladium Node

```bash
docker exec palladium-node palladium-cli \
  -rpcuser=<your_username> \
  -rpcpassword=<your_password> \
  getblockchaininfo
```

### Test ElectrumX Server

```bash
python test-server.py <your-server-ip>:50002
```

### Check from External Network

From another machine:
```bash
# Test dashboard
curl http://<your-public-ip>:8080

# Test ElectrumX (with Python)
python test-server.py <your-public-ip>:50002
```

---

### API Test Suite (`test_api.py`)

`test_api.py` is a self-contained pytest suite that verifies the dashboard API without needing a running Palladium node or ElectrumX server (all backend calls are mocked). It also uses the `API_KEY` from your `.env` file to test real authentication flows.

**Prerequisites:**

```bash
pip install pytest flask flask-cors requests psutil python-dateutil
```

**Run all tests:**

```bash
python3 -m pytest test_api.py -v
```

**What is tested:**

| Group | Tests |
|-------|-------|
| `TestApiKeyAuth` | No key → 401; valid `X-API-Key` header passes; valid `Bearer` token passes; wrong key → 401; trusted LAN IP never gets 401; all 11 `/api/*` routes block anonymous external requests |
| `TestApiEndpoints` | JSON structure and key fields for every endpoint: `/api/health`, `/api/palladium/info`, `block-height`, `network-hashrate`, `difficulty`, `peers`, `blocks/recent`, `/api/electrumx/stats`, `electrumx/servers`, `/api/system/resources` |
| `TestCacheHeaders` | Every `/api/*` response carries `Cache-Control: no-store, no-cache` and `Pragma: no-cache` |

**How authentication tests work:**

- Tests that require `API_KEY` are automatically **skipped** (`pytest.mark.skipif`) if `.env` is missing or the key is still the default placeholder.
- The test client simulates an **external IP** (`8.8.8.8`) to trigger the auth enforcement logic, and a **trusted IP** (`127.0.0.1`) for endpoint structure tests.

**Run only a specific group:**

```bash
# Only auth tests
python3 -m pytest test_api.py::TestApiKeyAuth -v

# Only endpoint structure tests
python3 -m pytest test_api.py::TestApiEndpoints -v

# Only cache header tests
python3 -m pytest test_api.py::TestCacheHeaders -v
```

**Expected output (all passing):**

```
test_api.py::TestApiKeyAuth::test_no_key_returns_401            PASSED
test_api.py::TestApiKeyAuth::test_valid_xapikey_header_passes   PASSED
test_api.py::TestApiKeyAuth::test_valid_bearer_token_passes     PASSED
test_api.py::TestApiKeyAuth::test_wrong_key_returns_401         PASSED
test_api.py::TestApiKeyAuth::test_trusted_ip_needs_no_auth      PASSED
test_api.py::TestApiKeyAuth::test_all_api_routes_respect_auth   PASSED
test_api.py::TestApiEndpoints::test_health                      PASSED
...
19 passed in ~3s
```

### REST API Endpoints

The dashboard exposes a REST API for programmatic access:

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Service health check (palladium + electrumx status) |
| `GET /api/system/resources` | CPU, memory, and disk usage |
| `GET /api/palladium/info` | Node info (blockchain, network, mining, mempool) |
| `GET /api/palladium/block-height` | Current block height |
| `GET /api/palladium/network-hashrate` | Current network hashrate (H/s) |
| `GET /api/palladium/difficulty` | Current network difficulty |
| `GET /api/palladium/peers` | Detailed peer list with traffic stats |
| `GET /api/palladium/blocks/recent` | Last 10 blocks |
| `GET /api/electrumx/stats` | ElectrumX version, uptime, DB size, active servers |
| `GET /api/electrumx/servers` | Discovered ElectrumX peers with reachability |

**How to call the API**

1. Set your base URL:
```bash
# Local host
BASE_URL="http://localhost:8080"

# LAN
# BASE_URL="http://<server-lan-ip>:8080"

# Internet/public
# BASE_URL="http://<your-public-ip>:8080"
```

2. Choose authentication mode:
- Local/LAN private IP clients: no API key required.
- Public/external IP clients: `API_KEY` required for `/api/*`.

3. Call endpoints with `curl`:
```bash
# Health
curl "$BASE_URL/api/health" | jq

# System resources
curl "$BASE_URL/api/system/resources" | jq

# Palladium info
curl "$BASE_URL/api/palladium/info" | jq

# Block height
curl "$BASE_URL/api/palladium/block-height" | jq

# Network hashrate
curl "$BASE_URL/api/palladium/network-hashrate" | jq

# Difficulty
curl "$BASE_URL/api/palladium/difficulty" | jq

# ElectrumX stats
curl "$BASE_URL/api/electrumx/stats" | jq
```

4. External/public calls with API key:
```bash
# Header: X-API-Key
curl -H "X-API-Key: <your-api-key>" "$BASE_URL/api/health" | jq

# Or Bearer token
curl -H "Authorization: Bearer <your-api-key>" "$BASE_URL/api/health" | jq
```

5. Troubleshooting:
- `401 {"error":"Valid API key required"}`: missing/invalid API key.
- `503 {"error":"API key is not configured"}`: set `API_KEY` in `.env` and restart `web-dashboard`.
- Connection refused/timeout: check firewall, router port forwarding, and `docker compose ps`.

```bash
# After updating .env
docker compose up -d --force-recreate web-dashboard
```

---

## Configuration Details

### Palladium Node Settings

Key settings in `.palladium/palladium.conf`:

| Setting | Value | Purpose |
|---------|-------|---------|
| `rpcuser` | `<your_username>` | RPC authentication |
| `rpcpassword` | `<your_password>` | RPC authentication |
| `server=1` | Required | Enable RPC server |
| `txindex=1` | Required | Index all transactions (ElectrumX needs this) |
| `addressindex=1` | Recommended | Index addresses for fast queries |
| `timestampindex=1` | Recommended | Index timestamps |
| `spentindex=1` | Recommended | Index spent outputs |
| `rpcbind=0.0.0.0` | Required | Allow Docker connections |
| `rpcallowip=10.0.0.0/8` | Recommended | Allow private RFC1918 networks |
| `rpcallowip=172.16.0.0/12` | Recommended | Allow private RFC1918 networks |
| `rpcallowip=192.168.0.0/16` | Recommended | Allow private RFC1918 networks |
| `port=2333` | Default | P2P network port (mainnet) |
| `rpcport=2332` | Default | RPC port (mainnet) |

**ZeroMQ Ports (optional):**
- `28332` - Block hash notifications
- `28333` - Transaction hash notifications
- `28334` - Raw block data
- `28335` - Raw transaction data

### ElectrumX Settings

Configured in `docker-compose.yml`:

```yaml
environment:
  COIN: "Palladium"        # Always "Palladium" for both networks
  NET: "mainnet"           # or "testnet"
  SERVICES: "tcp://0.0.0.0:50001,ssl://0.0.0.0:50002"
  # RPC credentials automatically read from palladium.conf
```

**Automatic Configuration (via `entrypoint.sh`):**
- **RPC credentials**: Read automatically from mounted `palladium.conf` — no need to configure `DAEMON_URL`
- **Public IP detection**: Discovers your public IP and sets `REPORT_SERVICES` for peer announcement
- **SSL certificates**: Auto-generated on first startup in `./certs/` with SAN including localhost and public IP (see [Security > SSL Certificates](#production-deployment))
- **TX stats patching**: Queries the live node for `TX_COUNT` / `TX_COUNT_HEIGHT` and patches the ElectrumX coin definition at startup
- Single source of truth for credentials across all services

---

## Network Support (Mainnet & Testnet)

### Running on Mainnet (Default)

Default configuration is for **mainnet** - no changes needed.

**Ports:**
- Palladium RPC: `2332`
- Palladium P2P: `2333`
- ElectrumX TCP: `50001`
- ElectrumX SSL: `50002`

### Switching to Testnet

1. **Edit `palladium.conf`:**
   ```conf
   testnet=1
   rpcport=12332
   ```

2. **Edit `docker-compose.yml`:**
   ```yaml
   environment:
     NET: "testnet"
   ```

3. **Clear database:**
   ```bash
   docker compose down
   rm -rf ./electrumx-data/*
   ```

4. **Restart:**
   ```bash
   docker compose up -d
   ```

**Testnet Ports:**
- Palladium RPC: `12332`
- Palladium P2P: `12333`
- ElectrumX: same (50001, 50002)

---

## Common Commands

### Container Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart services
docker compose restart

# Restart specific service
docker compose restart electrumx

# Rebuild after changes
docker compose up -d --build

# View status
docker compose ps

# View resource usage
docker stats
```

### Logs

```bash
# All logs (live)
docker compose logs -f

# Specific service
docker compose logs -f palladiumd
docker compose logs -f electrumx
docker compose logs -f dashboard

# Last 100 lines
docker compose logs --tail=100

# Since specific time
docker compose logs --since 30m
```

### Palladium Node Commands

```bash
# Blockchain info
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS \
  getblockchaininfo

# Network info
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS \
  getnetworkinfo

# Peer count
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS \
  getconnectioncount

# Peer details
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS \
  getpeerinfo
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker compose logs <service-name>
```

**Common issues:**
- Missing or incorrect RPC credentials
- Port already in use
- Insufficient disk space
- Wrong architecture binaries

### ElectrumX Can't Connect to Node

**Verify:**
1. Node is running: `docker compose ps`
2. RPC works: `docker exec palladium-node palladium-cli -rpcuser=USER -rpcpassword=PASS getblockchaininfo`
3. Credentials match in `palladium.conf`

### Slow Blockchain Sync

**Tips:**
- Copy existing blockchain (Step 4)
- Check internet speed
- Verify addnodes in config
- Be patient (initial sync takes hours/days)

### Port Already in Use

```bash
# Check what's using port
sudo lsof -i :50001

# Kill process or change port in docker-compose.yml
```

### Dashboard Shows Wrong Data

**Force refresh:**
1. Clear browser cache (Ctrl+Shift+R)
2. Check dashboard logs: `docker compose logs dashboard`
3. Restart dashboard: `docker compose restart dashboard`

### Binary Architecture Error

```bash
# Check your system
uname -m
# x86_64 = Intel/AMD 64-bit
# aarch64 = ARM 64-bit

# Check binary
file daemon/palladiumd
# Should match system architecture

# Fix: download correct binaries and rebuild
docker compose build --no-cache
```

---

## Security Recommendations

### Production Deployment

1. **Strong Credentials:**
   - Use long, random passwords for RPC
   - Don't use default credentials

2. **Firewall Configuration:**
   ```bash
   # Allow only required ports
   sudo ufw allow 2333/tcp    # P2P
   sudo ufw allow 50001/tcp   # ElectrumX TCP
   sudo ufw allow 50002/tcp   # ElectrumX SSL
   # Don't expose 8080 publicly without authentication
   sudo ufw enable
   ```

3. **SSL Certificates:**
   - Self-signed certificates are auto-generated on first startup in `./certs/`
   - The certificate includes localhost and the auto-detected public IP in its SAN
   - To use your own certificates (e.g. Let's Encrypt), place `server.crt` and `server.key` in `./certs/` before starting

4. **Dashboard Access:**
   - LAN clients (RFC1918 private IPs) can access without authentication
   - External clients (public IPs) require HTTP Basic Auth automatically
   - External API clients must provide `API_KEY` for `/api/*` requests
   - Recommended flow: generate API key first, then create `.env`:
     ```bash
     ./generate-api-key.sh
     cp .env.example .env
     nano .env
     ```
   - Configure credentials in `.env`:
     ```bash
     DASHBOARD_AUTH_USERNAME=admin
     DASHBOARD_AUTH_PASSWORD=a-strong-random-password
     API_KEY=a-long-random-api-key
     ```
   - Consider using a VPN instead of exposing port 8080 publicly

5. **Regular Updates:**
   ```bash
   # Update Palladium binaries
   # Update Docker images
   docker compose pull
   docker compose up -d
   ```

6. **Monitoring:**
   - Set up log monitoring
   - Monitor disk space
   - Watch for unusual activity in dashboard

---

## Performance Tuning

### System Resources

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 50GB storage

**Recommended:**
- 4+ CPU cores
- 8GB+ RAM
- 100GB+ SSD storage

### Docker Resource Limits

Edit `docker-compose.yml` to add limits:

```yaml
services:
  palladiumd:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### ElectrumX Performance

Increase concurrent indexing (in `docker-compose.yml`):

```yaml
environment:
  INITIAL_CONCURRENT: "4"  # Default: 2
```

---

## Notes

* **Data Persistence:** All data stored in `./.palladium/`, `./electrumx-data/`, and `./certs/`
* **Backup:** Regularly backup `.palladium/wallet.dat` if you store funds
* **Network Switch:** Always clear ElectrumX database when switching networks
* **Updates:** Check for Palladium Core updates regularly

---

## License

Distributed under the **MIT** license. See `LICENSE` file for details.

---

## Support

- **ElectrumX Documentation:** [Official Docs](https://electrumx.readthedocs.io/)

---

## Credits

- **ElectrumX:** [kyuupichan/electrumx](https://github.com/kyuupichan/electrumx)
