# Palladium Core Binaries

This directory must contain the pre-compiled Palladium Core binaries used by the Docker node container.

## Download

Download from the official release repository: **https://github.com/palladium-coin/palladiumcore/releases/latest**

## Architecture

The binaries **must match the host architecture** where Docker is running.
Choose the correct archive for your platform:

| Host Architecture | Archive to download     | Common hardware                     |
|-------------------|-------------------------|-------------------------------------|
| `x86_64`          | `palladium-linux-x86_64.tar.gz`  | Standard PCs, most VPS/cloud servers |
| `aarch64`         | `palladium-linux-aarch64.tar.gz` | Single-board computers (Raspberry Pi 4/5, Orange Pi, etc.) |

To check your host architecture:

```bash
uname -m
```

## Required binaries

Extract the following files from the release archive and place them in this directory:

```
daemon/
  palladiumd           # Full node daemon (required)
  palladium-cli        # RPC command-line client (required)
  palladium-tx         # Transaction utility
  palladium-wallet     # Wallet utility
```

## Quick setup

### Example for x86_64 (VPS/PC)

```bash
cd daemon
wget https://github.com/palladium-coin/palladiumcore/releases/latest/download/palladium-linux-x86_64.tar.gz
tar -xzf palladium-linux-x86_64.tar.gz
cd linux-x86_64
mv palladium* ..
cd ..
rm -rf linux-x86_64/ && rm palladium-linux-x86_64.tar.gz
```

### Example for aarch64 (Raspberry Pi)

```bash
cd daemon
wget https://github.com/palladium-coin/palladiumcore/releases/latest/download/palladium-linux-aarch64.tar.gz
tar -xzf palladium-linux-aarch64.tar.gz
cd linux-aarch64
mv palladium* ..
cd ..
rm -rf linux-aarch64/ && rm palladium-linux-aarch64.tar.gz
```

After placing the binaries, rebuild the node image:

```bash
docker compose build palladiumd
```
