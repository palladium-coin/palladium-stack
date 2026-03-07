# Palladium Core Binaries

This directory must contain the pre-compiled Palladium Core binaries used by the Docker node container.

## Recommended (new flow)

Use the helper script in this folder:

```bash
cd daemon
./download-binaries.sh
```

What it does:

- downloads the latest release assets from `palladium-coin/palladiumcore`
- auto-selects a compatible archive for your platform/architecture
- extracts binaries and copies them into `daemon/`
- removes temporary files

## Script options

```bash
./download-binaries.sh --help
```

Common examples:

```bash
# default (recommended for Docker): Linux + auto-detected arch
./download-binaries.sh

# force Linux architecture
./download-binaries.sh --platform linux --arch x86_64
./download-binaries.sh --platform linux --arch aarch64

# download Windows binaries (.exe)
./download-binaries.sh --platform windows --arch x86_64
```

## Architecture notes

For this stack, Docker needs Linux binaries matching your host CPU architecture.

- `x86_64` / `amd64`: most servers and desktops
- `aarch64` / `arm64`: Raspberry Pi 4/5 (64-bit OS), ARM servers
- `armv7l`: 32-bit ARM builds (not the default setup for this stack)

Check your architecture:

```bash
uname -m
```

## Required binaries for Docker node

The `Dockerfile.palladium-node` expects these files in `daemon/`:

```
daemon/
  palladiumd           # Full node daemon (required)
  palladium-cli        # RPC command-line client (required)
  palladium-tx         # Transaction utility
  palladium-wallet     # Wallet utility
```

After downloading binaries, rebuild the node image:

```bash
docker compose build palladiumd
```
