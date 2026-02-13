#!/bin/bash
set -e

PALLADIUM_CONF="/palladium-config/palladium.conf"

# Function to extract value from palladium.conf
get_conf_value() {
    local key=$1
    local value=$(grep "^${key}=" "$PALLADIUM_CONF" 2>/dev/null | cut -d'=' -f2- | tr -d ' \r\n')
    echo "$value"
}

# Check if palladium.conf exists
if [ ! -f "$PALLADIUM_CONF" ]; then
    echo "ERROR: palladium.conf not found at $PALLADIUM_CONF"
    echo "Please ensure the .palladium volume is mounted correctly."
    exit 1
fi

# Extract RPC credentials from palladium.conf
RPC_USER=$(get_conf_value "rpcuser")
RPC_PASSWORD=$(get_conf_value "rpcpassword")
RPC_PORT=$(get_conf_value "rpcport")

# Validate extracted credentials
if [ -z "$RPC_USER" ] || [ -z "$RPC_PASSWORD" ]; then
    echo "ERROR: Unable to extract rpcuser or rpcpassword from palladium.conf"
    echo "Please ensure your palladium.conf contains:"
    echo "  rpcuser=your_username"
    echo "  rpcpassword=your_password"
    exit 1
fi

# Default RPC port based on network if not specified in conf
if [ -z "$RPC_PORT" ]; then
    if [ "$NET" = "testnet" ]; then
        RPC_PORT=12332
    else
        RPC_PORT=2332
    fi
fi

# Build DAEMON_URL with extracted credentials
export DAEMON_URL="http://${RPC_USER}:${RPC_PASSWORD}@palladiumd:${RPC_PORT}/"

# Auto-detect public IP and set REPORT_SERVICES for peer discovery
if [ -z "$REPORT_SERVICES" ]; then
    echo "REPORT_SERVICES not set, detecting public IP..."
    for url in https://icanhazip.com https://ifconfig.me https://api.ipify.org; do
        PUBLIC_IP=$(curl -sf --max-time 5 "$url" 2>/dev/null | tr -d '[:space:]')
        if [ -n "$PUBLIC_IP" ]; then
            export REPORT_SERVICES="tcp://${PUBLIC_IP}:50001,ssl://${PUBLIC_IP}:50002"
            echo ">> Auto-detected REPORT_SERVICES: ${REPORT_SERVICES}"
            break
        fi
    done
    if [ -z "$REPORT_SERVICES" ]; then
        echo ">> WARNING: Could not detect public IP. Peer discovery will not announce this server."
    fi
fi

echo "=========================================="
echo "ElectrumX Configuration"
echo "=========================================="
echo "Coin: ${COIN}"
echo "Network: ${NET}"
echo "RPC User: ${RPC_USER}"
echo "RPC Port: ${RPC_PORT}"
echo "DAEMON_URL: http://${RPC_USER}:***@palladiumd:${RPC_PORT}/"
echo "REPORT_SERVICES: ${REPORT_SERVICES:-not set}"
echo "=========================================="

# Update TX_COUNT / TX_COUNT_HEIGHT in coins.py from the live node
echo "Fetching chain tx stats from palladiumd..."
TX_STATS=$(curl -sf --user "${RPC_USER}:${RPC_PASSWORD}" \
  --data-binary '{"jsonrpc":"1.0","method":"getchaintxstats","params":[]}' \
  -H 'Content-Type: text/plain;' \
  "http://palladiumd:${RPC_PORT}/" 2>/dev/null || true)

if [ -n "$TX_STATS" ]; then
    TX_COUNT=$(echo "$TX_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['txcount'])" 2>/dev/null || true)
    TX_HEIGHT=$(echo "$TX_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['window_final_block_height'])" 2>/dev/null || true)

    if [ -n "$TX_COUNT" ] && [ -n "$TX_HEIGHT" ]; then
        echo "Patching coins.py: TX_COUNT=${TX_COUNT}, TX_COUNT_HEIGHT=${TX_HEIGHT}"
        python3 - "$TX_COUNT" "$TX_HEIGHT" <<'TXPATCH'
import sys, pathlib, re
tx_count, tx_height = sys.argv[1], sys.argv[2]
for target in [
    '/usr/local/lib/python3.13/dist-packages/electrumx/lib/coins.py',
    '/electrumx/src/electrumx/lib/coins.py',
]:
    p = pathlib.Path(target)
    if not p.exists():
        continue
    s = p.read_text()
    s = re.sub(r'(class Palladium\(Bitcoin\):.*?TX_COUNT\s*=\s*)\d+', rf'\g<1>{tx_count}', s, count=1, flags=re.DOTALL)
    s = re.sub(r'(class Palladium\(Bitcoin\):.*?TX_COUNT_HEIGHT\s*=\s*)\d+', rf'\g<1>{tx_height}', s, count=1, flags=re.DOTALL)
    p.write_text(s)
TXPATCH
        echo ">> TX stats updated from live node"
    else
        echo ">> Could not parse tx stats, using defaults from coins_plm.py"
    fi
else
    echo ">> Node not reachable yet, using defaults from coins_plm.py"
fi

# Execute the original electrumx command
exec /usr/local/bin/electrumx_server
