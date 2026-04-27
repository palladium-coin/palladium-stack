# Troubleshooting

Always start with logs:

```bash
docker compose logs <service-name>
```

---

## Containers not starting

Common causes: wrong binary architecture, incorrect RPC credentials, port already in use.

Check logs first:
```bash
docker compose logs palladiumd
docker compose logs electrumx
docker compose logs dashboard
```

---

## ElectrumX can't connect to the node

Verify the node is running and credentials are correct:

```bash
docker exec palladium-node palladium-cli \
  -rpcuser=USER -rpcpassword=PASS getblockchaininfo
```

---

## Dashboard shows services as "down"

The node and/or ElectrumX may still be syncing or indexing. Check their logs and wait.

---

## Port already in use

```bash
sudo lsof -i :<port>    # find what is using the port
```

---

## Wrong binary architecture

```bash
uname -m                        # your system: x86_64 or aarch64
file daemon/palladiumd          # binary must match
```

If needed, re-download:
```bash
./daemon/download-binaries.sh --platform linux --arch x86_64
```

---

## Dashboard not loading from LAN

```bash
sudo ufw status              # check firewall
sudo ufw allow 8080/tcp      # open port if needed
netstat -tln | grep 8080     # verify dashboard is listening on 0.0.0.0:8080
```

---

## Testnet / mainnet switch issues

When switching between mainnet and testnet, always clear the ElectrumX database to avoid index corruption:

```bash
rm -rf ./electrumx-data/*
docker compose up -d
```
