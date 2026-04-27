# Palladium Stack

Dockerized setup for running a **Palladium (PLM) full node**, an **ElectrumX server**, and a **Web Dashboard** for monitoring.

---

## Components

| Service | Description | Public ports |
|---------|-------------|-------------|
| **palladium-node** | Full blockchain node (`palladiumd`) | `2333` P2P |
| **plm-electrumx** | Electrum protocol server for wallet connections | `50001` TCP · `50002` SSL |
| **palladium-dashboard** | Real-time monitoring UI + REST API | `8080` HTTP |

---

## Requirements

- Docker 20.10+ and Docker Compose 2.0+
- 64-bit system (AMD64 or ARM64)
- 4 GB+ RAM, 50 GB+ free disk space

**Tested on:** Debian 12/13, Ubuntu 22.04/24.04, Raspberry Pi OS (ARM64), WSL2

---

## Quick Start

**1. Get Palladium binaries**

```bash
cd daemon && ./download-binaries.sh
```

→ See [daemon/README.md](daemon/README.md) for `--arch` / `--platform` options.

**2. Set RPC credentials**

Open `.palladium/palladium.conf` and set `rpcuser` and `rpcpassword`.

**3. (Optional) Configure external access**

```bash
./generate-api-key.sh
cp .env.example .env
nano .env
```

**4. Start**

```bash
docker compose up -d
docker compose logs -f
```

**5. Open the dashboard**

```
http://localhost:8080          # same machine
http://<server-ip>:8080       # LAN
```

---

## Documentation

| Topic | Link |
|-------|------|
| Architecture & Docker network | [doc/architecture.md](doc/architecture.md) |
| Configuration (palladium.conf, .env, ports, testnet) | [doc/configuration.md](doc/configuration.md) |
| Security (auth, firewall, SSL, port forwarding) | [doc/security.md](doc/security.md) |
| Operations (commands, logs, backup, updates) | [doc/operations.md](doc/operations.md) |
| Troubleshooting | [doc/troubleshooting.md](doc/troubleshooting.md) |
| Palladium binaries | [daemon/README.md](daemon/README.md) |
| Dashboard & REST API reference | [web-dashboard/README.md](web-dashboard/README.md) |

---

## Credits

- **ElectrumX:** [kyuupichan/electrumx](https://github.com/kyuupichan/electrumx)
- **Palladium Full Node:** [palladium-coin/palladiumcore](https://github.com/palladium-coin/palladiumcore)

Distributed under the **MIT License** — see [LICENSE](LICENSE).
