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

echo "=========================================="
echo "ElectrumX Configuration"
echo "=========================================="
echo "Coin: ${COIN}"
echo "Network: ${NET}"
echo "RPC User: ${RPC_USER}"
echo "RPC Port: ${RPC_PORT}"
echo "DAEMON_URL: http://${RPC_USER}:***@palladiumd:${RPC_PORT}/"
echo "=========================================="

# Execute the original electrumx command
exec /usr/local/bin/electrumx_server
