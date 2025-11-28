FROM lukechilds/electrumx

COPY electrumx-patch/coins_plm.py /electrumx/src/electrumx/lib/coins_plm.py

RUN python3 - <<'PY'
import re, pathlib
p = pathlib.Path('/electrumx/src/electrumx/lib/coins.py')
s = p.read_text(encoding='utf-8')

# Import both Palladium and PalladiumTestnet
if 'from electrumx.lib.coins_plm import Palladium, PalladiumTestnet' not in s:
    s += '\nfrom electrumx.lib.coins_plm import Palladium, PalladiumTestnet\n'

# Register both coins in COIN_CLASSES
if '"Palladium": Palladium' not in s:
    s = re.sub(r'(COIN_CLASSES\s*=\s*\{)', r'\1\n    "Palladium": Palladium,', s)

if '"PalladiumTestnet": PalladiumTestnet' not in s:
    s = re.sub(r'(COIN_CLASSES\s*=\s*\{)', r'\1\n    "PalladiumTestnet": PalladiumTestnet,', s)

p.write_text(s, encoding='utf-8')
print('>> Patched ElectrumX with Palladium and PalladiumTestnet coins')
PY

RUN mkdir -p /certs && \
    cat >/certs/openssl.cnf <<'EOF' && \
    openssl req -x509 -nodes -newkey rsa:4096 -days 3650 \
      -keyout /certs/server.key -out /certs/server.crt \
      -config /certs/openssl.cnf && \
    chmod 600 /certs/server.key && chmod 644 /certs/server.crt
[req]
distinguished_name = dn
x509_extensions = v3_req
prompt = no

[dn]
C  = IT
ST = -
L  = -
O  = ElectrumX
CN = plm.local

[v3_req]
keyUsage         = keyEncipherment, dataEncipherment, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName   = @alt_names

[alt_names]
DNS.1 = plm.local
IP.1  = 127.0.0.1
EOF

ENV SSL_CERTFILE=/certs/server.crt
ENV SSL_KEYFILE=/certs/server.key
