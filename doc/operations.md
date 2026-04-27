# Operations

## Common commands

```bash
# Start / stop
docker compose up -d
docker compose down
docker compose restart

# Rebuild after code or config changes
docker compose up -d --build

# Status and resource usage
docker compose ps
docker stats
```

## Logs

```bash
docker compose logs -f                  # all services
docker compose logs -f palladiumd      # node only
docker compose logs -f electrumx       # ElectrumX only
docker compose logs -f dashboard       # dashboard only
```

Log rotation is configured per service: max **10 MB × 3 files** (30 MB per container). Managed automatically by Docker.

## Query the node directly

```bash
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS getblockchaininfo
```

## Backup

| What | Path |
|------|------|
| Blockchain data | `.palladium/blocks/`, `.palladium/chainstate/` |
| Wallet | `.palladium/wallet.dat` — **back this up regularly** |
| ElectrumX index | `./electrumx-data/` |
| SSL certificates | `./certs/` |

To speed up a fresh install by copying an existing synced blockchain:

```bash
cp -r ~/.palladium/blocks    .palladium/
cp -r ~/.palladium/chainstate .palladium/
cp -r ~/.palladium/indexes   .palladium/
```

## Updating binaries

```bash
cd daemon
./download-binaries.sh         # downloads latest release
docker compose build palladiumd
docker compose up -d palladiumd
```

See [daemon/README.md](../daemon/README.md) for architecture options (`--arch`, `--platform`).
