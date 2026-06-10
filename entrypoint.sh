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
TCP_PORT="${ELECTRUMX_TCP_PORT:-50001}"
SSL_PORT="${ELECTRUMX_SSL_PORT:-50002}"
if [ -z "$REPORT_SERVICES" ]; then
    echo "REPORT_SERVICES not set, detecting public IP..."
    # Retry: if the network is not ready at boot, giving up here would leave
    # the server permanently unannounced to the peer network.
    for attempt in 1 2 3 4 5; do
        for url in https://icanhazip.com https://ifconfig.me https://api.ipify.org; do
            # -4: force IPv4 — an IPv6 address without brackets would produce
            # a malformed service URL that ElectrumX cannot parse.
            PUBLIC_IP=$(curl -sf4 --max-time 5 "$url" 2>/dev/null | tr -d '[:space:]')
            if [ -n "$PUBLIC_IP" ]; then
                export REPORT_SERVICES="tcp://${PUBLIC_IP}:${TCP_PORT},ssl://${PUBLIC_IP}:${SSL_PORT}"
                echo ">> Auto-detected REPORT_SERVICES: ${REPORT_SERVICES}"
                break 2
            fi
        done
        echo ">> Public IP detection failed (attempt ${attempt}/5), retrying in 10s..."
        sleep 10
    done
    if [ -z "$REPORT_SERVICES" ]; then
        echo ">> WARNING: Could not detect public IP. Peer discovery will not announce this server."
    fi
fi

# Append extra seed peers to the coin definition (comma-separated entries
# in ElectrumX format, e.g. "1.2.3.4 t,my.server.org s t").
# Lets a new server bootstrap from any existing peer without rebuilding the image.
if [ -n "$EXTRA_PEERS" ]; then
    echo "Adding extra seed peers: ${EXTRA_PEERS}"
    python3 - "$EXTRA_PEERS" <<'PEERPATCH'
import sys, pathlib, re

extra = [e.strip() for e in sys.argv[1].split(',') if e.strip()]
for target in [
    '/usr/local/lib/python3.13/dist-packages/electrumx/lib/coins.py',
    '/electrumx/src/electrumx/lib/coins.py',
]:
    p = pathlib.Path(target)
    if not p.exists():
        continue
    s = p.read_text()
    m = re.search(r'class Palladium\(Bitcoin\):.*?PEERS = \[(.*?)\]', s, re.DOTALL)
    if not m:
        print(f'>> WARNING: PEERS list not found in {target}')
        continue
    existing = m.group(1)
    new_entries = ''.join(
        f"        '{e}',\n" for e in extra if f"'{e}'" not in existing
    )
    if new_entries:
        s = s[:m.end(1)] + new_entries.rstrip('\n') + '\n    ' + s[m.end(1):]
        p.write_text(s)
        print(f'>> Added {len(new_entries.splitlines())} extra peer(s) to {target}')
    else:
        print('>> Extra peers already present, nothing to add')
PEERPATCH
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

# ── SSL certificate generation (skip if certs already exist) ──
if [ ! -f /certs/server.crt ] || [ ! -f /certs/server.key ]; then
    echo "SSL certificates not found, generating self-signed certificate..."

    # Collect SAN entries
    SAN="DNS.1 = localhost"
    SAN_IDX=1
    IP_IDX=1
    SAN="${SAN}\nIP.${IP_IDX} = 127.0.0.1"

    # Try to detect public IP for SAN
    for url in https://icanhazip.com https://ifconfig.me https://api.ipify.org; do
        DETECTED_IP=$(curl -sf4 --max-time 5 "$url" 2>/dev/null | tr -d '[:space:]')
        if [ -n "$DETECTED_IP" ]; then
            IP_IDX=$((IP_IDX + 1))
            SAN="${SAN}\nIP.${IP_IDX} = ${DETECTED_IP}"
            echo ">> Including public IP in certificate SAN: ${DETECTED_IP}"
            break
        fi
    done

    cat >/tmp/openssl.cnf <<SSLEOF
[req]
distinguished_name = dn
x509_extensions = v3_req
prompt = no

[dn]
C  = IT
ST = -
L  = -
O  = PalladiumStack
CN = localhost

[v3_req]
keyUsage         = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName   = @alt_names

[alt_names]
$(echo -e "$SAN")
SSLEOF

    openssl req -x509 -nodes -newkey rsa:4096 -days 3650 \
        -keyout /certs/server.key -out /certs/server.crt \
        -config /tmp/openssl.cnf 2>/dev/null

    chmod 600 /certs/server.key
    chmod 644 /certs/server.crt
    rm -f /tmp/openssl.cnf
    echo ">> SSL certificate generated successfully"
else
    echo ">> Using existing SSL certificates from /certs/"
fi

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
