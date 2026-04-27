# Configuration

## palladium.conf

Located at `.palladium/palladium.conf`. Edit before first start.

Minimum required settings:

```conf
rpcuser=your_username      # ← change this
rpcpassword=your_password  # ← use a strong password
```

For **testnet**, also add:

```conf
testnet=1
rpcport=12332
```

## Environment variables (.env)

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
nano .env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `ELECTRUMX_TCP_PORT` | `50001` | ElectrumX plain TCP port |
| `ELECTRUMX_SSL_PORT` | `50002` | ElectrumX SSL port |
| `DASHBOARD_PORT` | `8080` | Web dashboard port |
| `DASHBOARD_AUTH_USERNAME` | `admin` | Basic Auth username (external clients) |
| `DASHBOARD_AUTH_PASSWORD` | `change-me-now` | Basic Auth password (external clients) |
| `API_KEY` | *(empty)* | API key for external `/api/*` calls; also signs session cookies |
| `DASHBOARD_SESSION_HOURS` | `1` | Session duration after login (hours) |
| `DASHBOARD_SESSION_COOKIE_SECURE` | `false` | Set to `true` when serving over HTTPS |

Generate a secure API key:

```bash
./generate-api-key.sh
```

After editing `.env`, restart the dashboard:

```bash
docker compose up -d --force-recreate dashboard
```

## Ports summary

| Port | Protocol | Service | Exposed by default |
|------|----------|---------|-------------------|
| `2333` | TCP | Palladium P2P | Yes |
| `50001` | TCP | ElectrumX TCP | Yes |
| `50002` | TCP | ElectrumX SSL | Yes |
| `8080` | TCP | Web Dashboard | Yes |
| `2332` | HTTP | Node RPC | No (Docker-internal only) |
| `28332` | ZMQ | hashblock | No (Docker-internal only) |
| `28334` | ZMQ | rawblock | No (Docker-internal only) |
| `28335` | ZMQ | rawtx | No (Docker-internal only) |

## Testnet

1. In `.palladium/palladium.conf`: add `testnet=1` and `rpcport=12332`
2. In `docker-compose.yml` (electrumx service): set `NET: "testnet"`
3. Clear ElectrumX database: `rm -rf ./electrumx-data/*`
4. Restart: `docker compose up -d`
