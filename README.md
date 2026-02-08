# ElectrumX with Palladium (PLM) Support

This repository provides a **complete Dockerized setup** of **ElectrumX** with an integrated **Palladium (PLM)** full node.

Everything runs in Docker containers - no need to install dependencies on your host system!

## What You Get

- **Palladium Full Node** (palladiumd) - Running in Docker
- **ElectrumX Server** - Pre-configured for Palladium
- **Automatic SSL certificates** - Secure connections ready
- **Easy configuration** - Just edit one config file
- **Reuse existing blockchain** - Or sync from scratch
- **Production ready** - Restart policies included

## Tested Platforms

* Debian 12/13
* Ubuntu 24.04/22.04 LTS
* WSL2 (Windows Subsystem for Linux)

## Project Structure

```
plm-electrumx/
├── daemon/                          # Palladium binaries (YOU must add these)
│   ├── palladiumd                   # Node daemon (required)
│   ├── palladium-cli                # CLI tool (required)
│   ├── palladium-tx                 # Transaction tool (optional)
│   └── palladium-wallet             # Wallet tool (optional)
├── palladium-node-data/
│   ├── palladium.conf               # Node configuration (edit this!)
│   ├── blocks/                      # Blockchain blocks (auto-generated)
│   ├── chainstate/                  # Blockchain state (auto-generated)
│   └── ...                          # Other runtime data (auto-generated)
├── electrumx-data/                            # ElectrumX database (auto-generated)
├── Dockerfile.palladium-node        # Builds Palladium node container
├── Dockerfile.electrumx             # Builds ElectrumX server container
└── docker-compose.yml               # Main orchestration file
```

**Important:** All blockchain data is stored in `./palladium-node-data/` directory, not externally.

🔗 Palladium Full Node: [palladium-coin/palladiumcore](https://github.com/palladium-coin/palladiumcore)

---

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Electrum      │    │   ElectrumX     │    │   Palladium     │
│   Clients       │◄──►│   Server        │◄──►│   Node Daemon   │
│                 │    │   (Docker)      │    │   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

This setup includes both ElectrumX and Palladium node (palladiumd) running in separate Docker containers.

---

## Requirements

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* Python 3.10+ (optional, to use `test-server.py`)
* **Palladium binaries** - See installation instructions below

**System Architecture**: This server requires a **64-bit system** (AMD64 or ARM64). 32-bit systems are **not** supported.

---

## Docker Installation

If you don't have Docker installed yet, follow the official guide:
- [Install Docker](https://docs.docker.com/get-docker/)

For Docker Compose:
- [Install Docker Compose](https://docs.docker.com/compose/install/)

---

## Quick Start Guide

Follow these simple steps to get your ElectrumX server running with Palladium node.

### Files Overview

This project uses two separate Dockerfiles:
- **`Dockerfile.palladium-node`**: Builds the Palladium daemon (palladiumd) container
- **`Dockerfile.electrumx`**: Builds the ElectrumX server container

**Data Storage:**
- **Configuration**: `./palladium-node-data/palladium.conf` (version controlled)
- **Blockchain data**: `./palladium-node-data/` (auto-generated, ignored by git)
- **ElectrumX database**: `./electrumx-data/` (auto-generated, ignored by git)

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/palladium-coin/plm-electrumx.git
cd plm-electrumx
```

---

### Step 2: Get Palladium Binaries

**IMPORTANT:** You must download the Palladium binaries that match your system architecture.

#### Option A: Download from Official Release

1. Go to the Palladium releases page: [palladium-coin/palladiumcore/releases](https://github.com/palladium-coin/palladiumcore/releases)

2. Download the correct version for your system:
   - **Linux x64 (Intel/AMD)**: `palladium-x.x.x-x86_64-linux-gnu.tar.gz`
   - **Linux ARM64 (Raspberry Pi, etc.)**: `palladium-x.x.x-aarch64-linux-gnu.tar.gz`

3. Extract the binaries:
   ```bash
   # Example for Linux x64
   tar -xzf palladium-*.tar.gz
   ```

4. Copy the binaries to the `daemon/` folder:
   ```bash
   mkdir -p daemon
   cp palladium-*/bin/palladiumd daemon/
   cp palladium-*/bin/palladium-cli daemon/
   cp palladium-*/bin/palladium-tx daemon/
   cp palladium-*/bin/palladium-wallet daemon/
   ```

5. Make them executable:
   ```bash
   chmod +x daemon/*
   ```

#### Option B: Use Existing Palladium Installation

If you already have Palladium Core installed on your system:

```bash
mkdir -p daemon
cp /usr/local/bin/palladiumd daemon/
cp /usr/local/bin/palladium-cli daemon/
cp /usr/local/bin/palladium-tx daemon/
cp /usr/local/bin/palladium-wallet daemon/
```

#### Verify Installation

Check that the binaries are in place:

```bash
ls -lh daemon/
```

You should see:
```
-rwxr-xr-x palladiumd       # Main daemon (required)
-rwxr-xr-x palladium-cli    # CLI tool (required)
-rwxr-xr-x palladium-tx     # Optional
-rwxr-xr-x palladium-wallet # Optional
```

**Architecture Warning:** The Docker container uses Ubuntu 22.04 base image. Make sure your binaries are compatible with Linux x64 or ARM64. Using macOS or Windows binaries will NOT work.

---

### Step 3: Configure RPC Credentials

Open the configuration file and change the default credentials:

```bash
nano palladium-node-data/palladium.conf
```

**IMPORTANT:** Change these two lines:
```conf
rpcuser=username        # ← Change this to your username
rpcpassword=password    # ← Change this to a secure password
```

Save and close the file (`Ctrl+X`, then `Y`, then `Enter` in nano).

**Security Note:** Use a strong password! These credentials control access to your Palladium node.

---

### Step 4: (Optional) Copy Existing Blockchain Data

If you already have a synced Palladium blockchain, you can copy it to speed up the initial sync:

```bash
# Copy from your existing .palladium directory
cp -r ~/.palladium/blocks palladium-node-data/
cp -r ~/.palladium/chainstate palladium-node-data/
cp -r ~/.palladium/indexes palladium-node-data/
```

**Skip this step** if you want to sync from scratch. The node will automatically start syncing when you run it.

---

### Step 5: Build and Start the Containers

Now you're ready to start everything:

```bash
docker-compose up -d
```

**What happens:**
- Docker builds two images: `palladium-node` and `electrumx-server`
- Starts the Palladium node container first
- Starts the ElectrumX server container (waits for Palladium node)
- Both run in the background (`-d` flag means "detached mode")

**First time?** The build process can take a few minutes.

---

### Step 6: Monitor the Logs

Watch what's happening in real-time:

```bash
# View all logs
docker-compose logs -f

# View only Palladium node logs
docker-compose logs -f palladiumd

# View only ElectrumX logs
docker-compose logs -f electrumx
```

Press `Ctrl+C` to stop viewing logs (containers keep running).

**What to look for:**
- Palladium node: "UpdateTip" messages (blockchain syncing)
- ElectrumX: "INFO:BlockProcessor:height..." (indexing blocks)

---

### Step 7: Verify Everything is Working

Check if containers are running:

```bash
docker-compose ps
```

You should see both containers with status "Up".

Test the Palladium node:

```bash
docker exec palladium-node palladium-cli -rpcuser=username -rpcpassword=password getblockchaininfo
```

(Replace `username` and `password` with your credentials)

You should see blockchain information including the current block height.

---

## Understanding the Configuration

### Palladium Node Configuration File

The `palladium-node-data/palladium.conf` file contains all settings for the Palladium daemon:

```conf
# RPC credentials (CHANGE THESE!)
rpcuser=username
rpcpassword=password

server=1
listen=1
daemon=1
discover=1
txindex=1
addressindex=1
timestampindex=1
spentindex=1

bind=0.0.0.0
port=2333
rpcport=2332
rpcbind=0.0.0.0

# Allow Docker containers to connect
rpcallowip=172.17.0.0/16
rpcallowip=172.18.0.0/16

maxconnections=50
fallbackfee=0.0001

# Addnodes:
seednode=dnsseed.palladium-coin.store

addnode=89.117.149.130:2333
addnode=66.94.115.80:2333
addnode=173.212.224.67:2333
addnode=82.165.218.152:2333

# ZeroMQ Configuration (optional)
zmqpubrawblock=tcp://0.0.0.0:28334
zmqpubrawtx=tcp://0.0.0.0:28335
zmqpubhashblock=tcp://0.0.0.0:28332
zmqpubhashtx=tcp://0.0.0.0:28333
```

**Key Settings Explained:**

| Setting | Purpose | Required? |
|---------|---------|-----------|
| `rpcuser`, `rpcpassword` | Credentials for RPC access | ✅ Yes - CHANGE THESE! |
| `txindex=1` | Index all transactions | ✅ Yes - ElectrumX needs this |
| `addressindex=1` | Index addresses | ⚡ Recommended for performance |
| `timestampindex=1` | Index timestamps | ⚡ Recommended for performance |
| `spentindex=1` | Index spent outputs | ⚡ Recommended for performance |
| `rpcbind=0.0.0.0` | Allow RPC connections from Docker | ✅ Yes |
| `rpcallowip=172.17.0.0/16` | Allow Docker network IPs | ✅ Yes |
| `addnode=...` | Known Palladium nodes to connect | 📡 Helps with sync |

---

## ElectrumX Configuration

The ElectrumX container **automatically reads RPC credentials** from the `palladium.conf` file. You don't need to manually configure credentials in `docker-compose.yml` anymore!

**How it works:**
1. ElectrumX mounts the `palladium-node-data/palladium.conf` file as read-only
2. On startup, it automatically extracts `rpcuser` and `rpcpassword`
3. Builds the `DAEMON_URL` dynamically with the correct credentials

**Benefits:**
- Single source of truth for credentials (only `palladium.conf`)
- No need to sync credentials between multiple files
- Easier to maintain and more secure

**Ports:** ElectrumX exposes:
- `50001` → TCP (unencrypted)
- `50002` → SSL (encrypted, recommended)

**Palladium node ports:**
- `2332` → RPC port (mainnet)
- `2333` → P2P port (mainnet)
- `28332-28335` → ZeroMQ ports (optional)

---

## Network Support (Mainnet & Testnet)

This ElectrumX server supports both **Palladium mainnet** and **testnet**. You can switch between networks by modifying the `docker-compose.yml` configuration.

### Network Comparison

| Network | COIN Value | NET Value | RPC Port | Bech32 Prefix | Address Prefix |
|---------|-----------|-----------|----------|---------------|----------------|
| **Mainnet** | `Palladium` | `mainnet` | `2332` | `plm` | Standard (starts with `1` or `3`) |
| **Testnet** | `Palladium` | `testnet` | `12332` | `tplm` | Testnet (starts with `t`) |

---

### Running on Mainnet (Default)

The default configuration is set for **mainnet**. No changes are needed if you want to run on mainnet.

**Configuration in `docker-compose.yml`:**
```yaml
environment:
  COIN: "Palladium"
  NET: "mainnet"
  # RPC credentials automatically read from palladium.conf
```

**Requirements:**
- Palladium Core node running on **mainnet**
- RPC port: `2332`
- RPC credentials configured in `palladium.conf`

---

### Switching to Testnet

To run ElectrumX on **testnet**, follow these steps:

#### Step 1: Configure Palladium Core for Testnet

Edit your Palladium Core configuration file (`palladium.conf`):

```conf
# Enable testnet
testnet=1

# Server mode (required for RPC)
server=1

# RPC credentials (change these!)
rpcuser=your_rpc_username
rpcpassword=your_secure_rpc_password

# RPC port for testnet
rpcport=12332

# Allow Docker containers to connect (REQUIRED for ElectrumX)
rpcbind=0.0.0.0
rpcallowip=127.0.0.1
rpcallowip=172.16.0.0/12
```

**Important:** The `rpcbind` and `rpcallowip` settings are **required** for Docker connectivity on all platforms. Without these, ElectrumX won't be able to connect to your Palladium node from inside the Docker container.

Restart your Palladium Core node to apply testnet configuration.

#### Step 2: Modify docker-compose.yml

Open `docker-compose.yml` and change these two values in the `environment` section:

**Before (Mainnet):**
```yaml
environment:
  COIN: "Palladium"
  NET: "mainnet"
  DAEMON_URL: "http://<rpcuser>:<rpcpassword>@host.docker.internal:2332/"
```

**After (Testnet):**
```yaml
environment:
  COIN: "Palladium"
  NET: "testnet"
  DAEMON_URL: "http://<rpcuser>:<rpcpassword>@host.docker.internal:12332/"
```

**Important changes:**
1. Change `NET` from `"mainnet"` to `"testnet"`
2. Change port in `DAEMON_URL` from `2332` to `12332`
3. Replace `<rpcuser>` and `<rpcpassword>` with your actual testnet RPC credentials

#### Step 3: Clear Existing Database (Important!)

When switching networks, you **must** clear the ElectrumX database to avoid conflicts:

```bash
# Stop the container
docker compose down

# Remove the database
rm -rf ./electrumx-data/*

# Or on Windows:
# rmdir /s /q data
# mkdir data
```

#### Step 4: Rebuild and Restart

```bash
# Rebuild and start the container
docker compose up -d --build

# Monitor the logs
docker compose logs -f
```

The ElectrumX server will now sync with the Palladium **testnet** blockchain.

---

### Testnet-Specific Information

**Genesis Block Hash (Testnet):**
```
000000000933ea01ad0ee984209779baaec3ced90fa3f408719526f8d77f4943
```

**Address Examples:**
- Legacy (P2PKH): starts with `t` (e.g., `tPLMAddress123...`)
- SegWit (Bech32): starts with `tplm` (e.g., `tplm1q...`)

**Network Ports:**
- Palladium Core RPC: `12332`
- Palladium Core P2P: `12333`
- ElectrumX TCP: `50001` (same as mainnet)
- ElectrumX SSL: `50002` (same as mainnet)

---

### Switching Back to Mainnet

To switch back from testnet to mainnet:

1. Edit `palladium.conf` and remove or comment `testnet=1`
2. Change `rpcport=2332` in `palladium.conf`
3. Restart Palladium Core node
4. In `docker-compose.yml`, change:
   - `NET: "testnet"` → `NET: "mainnet"`
   - Port in `DAEMON_URL` from `12332` → `2332`
5. Clear database: `rm -rf ./electrumx-data/*`
6. Restart ElectrumX: `docker compose down && docker compose up -d`

---

## Common Commands

### Starting and Stopping

```bash
# Start both containers
docker-compose up -d

# Stop both containers
docker-compose down

# Stop and remove all data (WARNING: deletes ElectrumX database)
docker-compose down -v

# Restart containers
docker-compose restart
```

### Viewing Logs

```bash
# All logs (live feed)
docker-compose logs -f

# Only Palladium node
docker-compose logs -f palladiumd

# Only ElectrumX
docker-compose logs -f electrumx

# Last 100 lines
docker-compose logs --tail=100
```

### Checking Status

```bash
# Container status
docker-compose ps

# Palladium blockchain info
docker exec palladium-node palladium-cli -rpcuser=YOUR_USER -rpcpassword=YOUR_PASS getblockchaininfo

# Palladium network info
docker exec palladium-node palladium-cli -rpcuser=YOUR_USER -rpcpassword=YOUR_PASS getnetworkinfo

# Check how many peers connected
docker exec palladium-node palladium-cli -rpcuser=YOUR_USER -rpcpassword=YOUR_PASS getpeerinfo | grep addr
```

### Rebuilding After Changes

If you modify configuration or update binaries:

```bash
# Rebuild images
docker-compose build

# Rebuild and restart
docker-compose up -d --build

# Force rebuild (no cache)
docker-compose build --no-cache
```

---

## Troubleshooting

### Palladium Node Not Starting

**Problem:** Container exits immediately

**Solution:**
1. Check logs: `docker-compose logs palladiumd`
2. Verify credentials in `palladium-node-data/palladium.conf`
3. Check if blockchain directory has permissions issues:
   ```bash
   ls -la palladium-node-data/
   ```
4. Verify binaries are correct architecture:
   ```bash
   file daemon/palladiumd
   # Should show: ELF 64-bit LSB executable, x86-64 (or aarch64)
   ```

### ElectrumX Can't Connect to Palladium Node

**Problem:** ElectrumX logs show "connection refused"

**Solution:**
1. Verify credentials match in both files:
   - `palladium-node-data/palladium.conf`
   - `docker-compose.yml` (DAEMON_URL line)
2. Check if Palladium node is running:
   ```bash
   docker-compose ps
   ```
3. Test RPC connection:
   ```bash
   docker exec palladium-node palladium-cli -rpcuser=YOUR_USER -rpcpassword=YOUR_PASS getblockchaininfo
   ```

### Blockchain Sync is Slow

**Problem:** Sync takes too long

**Tips:**
- Copy existing blockchain data to `palladium-node-data/` (see Step 5)
- Check internet connection
- Make sure addnodes are configured in `palladium.conf`
- Be patient - initial sync can take hours/days depending on blockchain size

### Port Already in Use

**Problem:** Error "port is already allocated"

**Solution:**
1. Check what's using the port:
   ```bash
   sudo lsof -i :2332  # or :50001, :50002
   ```
2. Stop the conflicting service, or change ports in `docker-compose.yml`

### Disk Space Running Out

**Problem:** Blockchain takes too much space

**Solution:**
- The Palladium blockchain can be several GB
- Make sure you have enough space in the project directory
- Check disk usage:
  ```bash
  df -h
  du -sh palladium-node-data/
  du -sh data/
  ```

### Binary Architecture Mismatch

**Problem:** "cannot execute binary file: Exec format error"

**Solution:**
- You're using binaries for the wrong architecture
- Check your system: `uname -m`
  - `x86_64` → need x86_64 Linux binaries
  - `aarch64` → need ARM64 Linux binaries
- Download the correct binaries and replace them in `daemon/`
- Rebuild: `docker-compose build --no-cache`

---

## Testing with `test-server.py`

The `test-server.py` script allows you to connect to the ElectrumX server and test its APIs.

Usage example:

```bash
python test-server.py 127.0.0.1:50002
```

The script will perform:

* Handshake (`server.version`)
* Feature request (`server.features`)
* Block header subscription (`blockchain.headers.subscribe`)

---

## Notes

* `coins_plm.py` defines both **Palladium (PLM)** mainnet and **PalladiumTestnet** classes
* See "Network Support" section for switching between mainnet and testnet
* Production recommendations:

  * Protect RPC credentials
  * Use valid SSL certificates
  * Monitor containers (logs, metrics, alerts)

---

## License

Distributed under the **MIT** license. See the `LICENSE` file for details.
