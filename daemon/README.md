# Palladium Core Binaries

This directory must contain the pre-compiled Palladium Core binaries used by the Docker node container.

## Download

Download the latest release from the official repository:

**https://github.com/palladium-coin/palladiumcore/releases**

## Architecture

The binaries **must match the host architecture** where Docker is running.
Choose the correct archive for your platform:

| Host Architecture | Archive to download     | Common hardware                     |
|-------------------|-------------------------|-------------------------------------|
| `x86_64`          | `x86_64-linux-gnu.tar.gz`  | Standard PCs, most VPS/cloud servers |
| `aarch64`         | `aarch64-linux-gnu.tar.gz` | Single-board computers (Raspberry Pi 4/5, Orange Pi, etc.) |

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

```bash
# Example for aarch64 (Raspberry Pi)
tar xzf palladiumcore-*-aarch64-linux-gnu.tar.gz
cp palladiumcore-*/bin/palladium{d,-cli,-tx,-wallet} daemon/

# Example for x86_64 (VPS/PC)
tar xzf palladiumcore-*-x86_64-linux-gnu.tar.gz
cp palladiumcore-*/bin/palladium{d,-cli,-tx,-wallet} daemon/
```

After placing the binaries, rebuild the node image:

```bash
docker compose build palladiumd
```
