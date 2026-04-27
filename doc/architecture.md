# Architecture

## Services

| Component | Image | Container | Description |
|-----------|-------|-----------|-------------|
| **Palladium Full Node** | `palladium-node:local` | `palladium-node` | Full blockchain node (`palladiumd`) |
| **ElectrumX Server** | `plm-electrumx:local` | `plm-electrumx` | Electrum protocol server for wallet connections |
| **Web Dashboard** | `palladium-dashboard:local` | `palladium-dashboard` | Real-time monitoring UI + REST API |

## Network diagram

```
Internet              Docker Host
   │                       │
   ├─ P2P  :2333 ──────► palladium-node ◄─────────────────────────────┐
   ├─ TCP  :50001 ─────► plm-electrumx  ◄── palladiumd:2332 (RPC)     │  palladium
   ├─ SSL  :50002 ─────► plm-electrumx                                │  (Docker network)
   └─ HTTP :8080  ─────► palladium-dashboard ◄── palladiumd + electrumx ◄┘
```

All services share the `palladium` Docker network. RPC and ZMQ ports are **not** exposed on the host — internal communication uses Docker service names (e.g. `palladiumd:2332`).

## Internal endpoints

| Service | Hostname | Port | Protocol |
|---------|----------|------|----------|
| Palladium node RPC | `palladiumd` | `2332` | HTTP JSON-RPC |
| ZMQ hashblock | `palladiumd` | `28332` | ZMQ pub |
| ZMQ rawblock | `palladiumd` | `28334` | ZMQ pub |
| ZMQ rawtx | `palladiumd` | `28335` | ZMQ pub |
| ElectrumX TCP | `electrumx` | `50001` | Electrum protocol |
| ElectrumX SSL | `electrumx` | `50002` | Electrum protocol (SSL) |
| Web Dashboard | `dashboard` | `8080` | HTTP |

## Connecting other Docker stacks

If you run another stack on the same host (e.g. a mining pool, explorer, or bot) that needs to reach the node or ElectrumX, join the shared `palladium` network — no ports need to be exposed on the host.

**In your external `docker-compose.yml`:**

```yaml
networks:
  palladium:
    external: true   # already created by this stack

services:
  myapp:
    image: ...
    networks:
      - palladium
    environment:
      RPC_HOST: palladiumd
      RPC_PORT: "2332"
      ZMQ_HASHBLOCK: "tcp://palladiumd:28332"
      ZMQ_RAWBLOCK:  "tcp://palladiumd:28334"
      ZMQ_RAWTX:     "tcp://palladiumd:28335"
      ELECTRUMX_HOST: electrumx
      ELECTRUMX_PORT: "50001"
```

> Start this stack before starting any dependent stack.

## Exposing internal ports to the host (optional)

Only needed for applications running directly on the host (not in Docker):

```yaml
ports:
  - "127.0.0.1:2332:2332"   # RPC — localhost only
  - "127.0.0.1:28332:28332" # ZMQ hashblock — localhost only
```

Use `127.0.0.1:` to restrict access to the local machine. Avoid `0.0.0.0:` for RPC and ZMQ.
