# Palladium Dashboard — Features & API Reference

Web dashboard for monitoring the Palladium node and ElectrumX server in real time.

---

## Access

| Context | URL |
|---------|-----|
| Same machine | `http://localhost:8080` |
| LAN | `http://<server-ip>:8080` |
| Internet | `http://<public-ip>:8080` (requires auth — see below) |

To find your server's local IP:
```bash
hostname -I | awk '{print $1}'
```

---

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Main Dashboard | `/` | System resources, node stats, ElectrumX stats, mempool, recent blocks |
| Network Peers | `/peers` | Full peer list with traffic stats, auto-refreshes every 10 s |
| Electrum Servers | `/electrum-servers` | Discovered ElectrumX peers with TCP/SSL reachability |

---

## Authentication

| Client origin | Dashboard pages | API (`/api/*`) |
|---------------|-----------------|----------------|
| Localhost / LAN (RFC1918 private IPs) | No auth | No auth |
| External / public IP | HTTP Basic Auth | API key required |

### Configure external access

```bash
# From the project root:
./generate-api-key.sh    # prints a secure random key
cp .env.example .env
nano .env                # fill in the three variables
```

`.env` variables:

| Variable | Used for |
|----------|---------|
| `DASHBOARD_AUTH_USERNAME` | Basic Auth username (dashboard pages, external clients) |
| `DASHBOARD_AUTH_PASSWORD` | Basic Auth password (dashboard pages, external clients) |
| `API_KEY` | API key for `/api/*` calls from external IPs |

After editing `.env`, apply it:
```bash
docker compose up -d --force-recreate dashboard
```

---

## REST API

All endpoints return JSON. No authentication is required from localhost or LAN.
External clients must pass the API key via header:

```bash
# Option A — custom header
curl -H "X-API-Key: <your-key>" http://<host>:8080/api/health

# Option B — Bearer token
curl -H "Authorization: Bearer <your-key>" http://<host>:8080/api/health
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Overall service health (`palladium` + `electrumx` status) |
| `GET` | `/api/system/resources` | CPU, memory, and disk usage |
| `GET` | `/api/palladium/info` | Node info: blockchain, network, mining, mempool |
| `GET` | `/api/palladium/block-height` | Current block height |
| `GET` | `/api/palladium/network-hashrate` | Network hashrate in H/s |
| `GET` | `/api/palladium/difficulty` | Current network difficulty |
| `GET` | `/api/palladium/peers` | Detailed peer list with traffic stats |
| `GET` | `/api/palladium/blocks/recent` | Last 10 blocks (height, hash, time, size, tx count) |
| `GET` | `/api/electrumx/stats` | ElectrumX version, uptime, DB size, active servers |
| `GET` | `/api/electrumx/servers` | Discovered ElectrumX peers with TCP/SSL reachability |

### Example calls

```bash
BASE="http://localhost:8080"          # local
# BASE="http://192.168.1.100:8080"   # LAN
# BASE="http://<public-ip>:8080"     # internet (add -H "X-API-Key: ..." )

# Health check
curl "$BASE/api/health" | jq

# Block height
curl "$BASE/api/palladium/block-height" | jq

# Full node info
curl "$BASE/api/palladium/info" | jq

# ElectrumX stats
curl "$BASE/api/electrumx/stats" | jq

# System resources
curl "$BASE/api/system/resources" | jq
```

### Common error responses

| Code | Body | Cause |
|------|------|-------|
| `401` | `{"error":"Valid API key required"}` | Missing or wrong API key |
| `503` | `{"error":"API key is not configured"}` | `API_KEY` not set in `.env` |

---

## Test Suite (`test_api.py`)

A self-contained pytest suite that verifies the API without a running node or ElectrumX (all backend calls are mocked). It also tests real authentication flows using the `API_KEY` from your `.env`.

**Install dependencies:**
```bash
pip install pytest flask flask-cors requests psutil python-dateutil
```

**Run all tests:**
```bash
python3 -m pytest test_api.py -v
```

**Test groups:**

| Group | What is tested |
|-------|---------------|
| `TestApiKeyAuth` | No key → 401; valid `X-API-Key` passes; valid `Bearer` passes; wrong key → 401; LAN IP bypasses auth; all 11 `/api/*` routes block anonymous external requests |
| `TestApiEndpoints` | JSON structure and key fields for every endpoint |
| `TestCacheHeaders` | Every `/api/*` response carries `Cache-Control: no-store` and `Pragma: no-cache` |

Auth tests are automatically skipped if `.env` is missing or `API_KEY` is still the placeholder value.

---

## Technology Stack

- **Backend:** Python 3.11, Flask
- **Frontend:** HTML5, CSS3, vanilla JavaScript, Chart.js
- **Containerized:** Dockerfile.dashboard, port 8080
