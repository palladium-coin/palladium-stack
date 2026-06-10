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
| `ELECTRUMX_CACHE_MB` | `800` | ElectrumX in-memory cache (MB); peak RAM can reach 2-3x this during sync |
| `ELECTRUMX_EXTRA_PEERS` | *(empty)* | Extra seed peers for discovery bootstrap (comma-separated, e.g. `1.2.3.4 t,host.org s t`) |
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

## Peer discovery

ElectrumX servers find each other automatically: each server announces itself
(`PEER_ANNOUNCE=true`) to the peers it knows, and every server propagates its
peer list to the others (`PEER_DISCOVERY=on`). A new server therefore reaches
the whole network knowing just **one** existing peer — the rest arrive through
gossip. Both options are already enabled in `docker-compose.yml`.

For a new server to join and be discovered:

1. **Reachability** — ports `50001`/`50002` must be reachable from the
   internet (router port-forwarding / firewall). Other servers verify an
   announcement by connecting back: an unreachable server is never propagated.
2. **Bootstrap** — the image ships with built-in seed peers. To bootstrap from
   a different server (or add your own seeds) set `ELECTRUMX_EXTRA_PEERS` in
   `.env` — no image rebuild needed.
3. **Announced address** — the public IP is auto-detected at startup (with
   retries). Behind complex NAT setups, set `REPORT_SERVICES` manually in
   `docker-compose.yml` to override.

Notes:

- Peer discovery starts **after** the initial sync completes; a syncing server
  shows no peers — that's normal.
- Peers are persisted in the ElectrumX database, so an already-discovered
  server keeps working even if all the original seeds go offline.

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
