# Security

## Authentication model

| Client origin | Dashboard (`/`) | API (`/api/*`) |
|---------------|-----------------|----------------|
| Localhost / LAN (RFC1918) | No auth required | No auth required |
| External / public IP | HTTP Basic Auth | API key required |

Configure in `.env` (see [configuration.md](configuration.md)):

```bash
./generate-api-key.sh   # generates a secure random key
cp .env.example .env
nano .env
```

## Firewall (recommended)

```bash
sudo ufw allow 2333/tcp    # Palladium P2P
sudo ufw allow 50001/tcp   # ElectrumX TCP
sudo ufw allow 50002/tcp   # ElectrumX SSL
# Only open 8080 if you have configured auth in .env
sudo ufw allow 8080/tcp    # Web Dashboard (optional)
sudo ufw enable
```

Do **not** open ports `2332` (RPC) or `28332–28335` (ZMQ) — these are Docker-internal only.

## SSL certificates

Self-signed certificates are generated automatically on first startup in `./certs/` (the server's public IP is included in the SAN).

To use your own certificates (e.g. Let's Encrypt):

```bash
cp /path/to/your/fullchain.pem ./certs/server.crt
cp /path/to/your/privkey.pem   ./certs/server.key
docker compose restart electrumx
```

## Port forwarding (public internet)

To expose the stack to the internet, forward these ports on your router:

| Port | Protocol | Service | Required? |
|------|----------|---------|-----------|
| `2333` | TCP | Palladium P2P | **Yes** (for node sync) |
| `50001` | TCP | ElectrumX TCP | Recommended |
| `50002` | TCP | ElectrumX SSL | Recommended |
| `8080` | TCP | Web Dashboard | Optional — configure auth first |

Set the forwarding destination to your server's local IP:

```bash
hostname -I | awk '{print $1}'
```
