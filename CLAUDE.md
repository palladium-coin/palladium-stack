# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Dockerized stack for running a **Palladium (PLM)** cryptocurrency node + **ElectrumX** server + monitoring **web dashboard**. Palladium is a Bitcoin fork that **shares Bitcoin's genesis hash** — this matters for ElectrumX peer discovery (Bitcoin Electrum servers would pass the genesis check) and explains `CHECKPOINTS = []` in the coin definition.

## Commands

```bash
# First-time setup
cd daemon && ./download-binaries.sh   # fetch palladiumd binaries (not built here)
cp .env.example .env                  # then set passwords/API key
./generate-api-key.sh                 # prints an API_KEY line for .env

# Run
docker compose up -d
docker compose logs -f electrumx      # watch sync
docker compose build electrumx        # rebuild after Dockerfile/entrypoint changes

# Tests (dashboard API; mocks RPC calls, no containers needed)
pytest test_api.py -v

# Manual Electrum protocol probe against a live server
python3 test-server.py <host> <port>

# Validation before committing
docker compose config --quiet && bash -n entrypoint.sh && python3 -m py_compile web-dashboard/app.py

# ElectrumX admin RPC (inside Docker network only)
docker exec plm-electrumx electrumx_rpc -p 8000 peers
```

## Architecture

Four services on a Docker network with the **fixed name `palladium`** (other stacks on the host join it with `external: true`). RPC (2332) and ZMQ ports are never exposed on the host; inter-service traffic uses Docker DNS names (`palladiumd:2332`).

### Autoheal

`palladiumd`, `electrumx`, and `dashboard` all carry the label `autoheal=true`; the `autoheal` service (`willfarrell/autoheal`, watching `docker.sock`) restarts any of them once Docker's healthcheck marks it **unhealthy** — `restart: unless-stopped` alone only reacts to the process exiting, not to a wedged-but-alive process. Add the label to any new service that should recover automatically from a stuck healthcheck.

### ElectrumX: upstream image + layered patching (the core pattern)

There is no ElectrumX fork in this repo. `Dockerfile.electrumx` starts from `lukechilds/electrumx` and patches installed sources **at build time** with inline Python heredocs:

1. Appends the `Palladium`/`PalladiumTestnet` classes from `electrumx-patch/coins_plm.py` to the installed `coins.py`
2. Rewrites `server/history.py` from uint16 to uint32 flush IDs (the stock code crashes with `struct.error` after 65535 flushes). **This changes the LevelDB key format**: any change there requires wiping `electrumx-data/` and a full resync.

Each patch targets both candidate install paths (`/usr/local/lib/python3.13/dist-packages/...` and `/electrumx/src/...`); follow that pattern for new patches.

Then `entrypoint.sh` patches **again at runtime**, before exec'ing the server:
- Extracts `rpcuser`/`rpcpassword` from the mounted `palladium.conf` and builds `DAEMON_URL` (never configure RPC credentials anywhere else)
- Auto-detects the public IP for `REPORT_SERVICES` (peer announcement) with retries; `curl -4` is deliberate — an IPv6 without brackets makes a service URL ElectrumX can't parse
- Generates a self-signed SSL cert into `certs/` if missing
- Updates `TX_COUNT`/`TX_COUNT_HEIGHT` in coins.py from the live node's `getchaintxstats`
- Appends `EXTRA_PEERS` (env) entries to the coin's `PEERS` list

ElectrumX opens client ports 50001/50002 **only after the first full sync completes**; only the admin RPC (8000) is up from startup — that's why the compose healthcheck probes 8000, and why a syncing server showing no peers is normal.

### Dashboard (web-dashboard/)

Flask app served by **gunicorn with exactly 1 worker** (multi-thread): caches and locks live in process memory, multiple workers would diverge. Key behaviors:

- Auth model: RFC1918/localhost clients need no auth; external IPs need Basic Auth (pages) or `API_KEY` (API). `API_KEY` also signs session cookies.
- Discovers ElectrumX's actual ports by running `docker exec plm-electrumx` through the mounted docker.sock — the container name `plm-electrumx` is hardcoded in app.py, so renaming containers breaks the dashboard.
- Cache warm-up runs at module import time (not under `__main__`) so it works under gunicorn.

### Configuration contract

All user-tunable parameters live in `.env` (template: `.env.example`, documented in `doc/configuration.md`) and flow through compose `${VAR:-default}` interpolation — never hardcode a value that duplicates an `.env` variable. `palladium.conf` is the single source of truth for RPC credentials, mounted read-only into electrumx and dashboard. Docker-internal ports (ElectrumX RPC 8000, dashboard container port 8080) are intentionally fixed and not in `.env`.

## Repo conventions

- Commit style: conventional commits (`fix(electrumx): ...`, `chore(dashboard): ...`)
- Documentation lives in `doc/` (architecture, configuration, security, operations, troubleshooting); update `doc/configuration.md` when adding `.env` variables
- `daemon/` binaries, `.palladium/` chain data, `electrumx-data/`, and `certs/` are runtime artifacts — never commit their contents
