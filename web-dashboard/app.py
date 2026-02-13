#!/usr/bin/env python3
"""
Web Dashboard API for Palladium Node and ElectrumX Server Statistics
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import requests
import json
import os
import time
import copy
import threading
from datetime import datetime
import psutil
import socket

app = Flask(__name__)
CORS(app)

# Configuration
PALLADIUM_RPC_HOST = os.getenv('PALLADIUM_RPC_HOST', 'palladiumd')
PALLADIUM_RPC_PORT = int(os.getenv('PALLADIUM_RPC_PORT', '2332'))
ELECTRUMX_RPC_HOST = os.getenv('ELECTRUMX_RPC_HOST', 'electrumx')
ELECTRUMX_RPC_PORT = int(os.getenv('ELECTRUMX_RPC_PORT', '8000'))
ELECTRUMX_STATS_TTL = int(os.getenv('ELECTRUMX_STATS_TTL', '60'))
ELECTRUMX_SERVERS_TTL = int(os.getenv('ELECTRUMX_SERVERS_TTL', '120'))
ELECTRUMX_EMPTY_SERVERS_TTL = int(os.getenv('ELECTRUMX_EMPTY_SERVERS_TTL', '15'))

# In-memory caches for fast card stats and heavier server probing stats
_electrumx_stats_cache = {'timestamp': 0.0, 'stats': None}
_electrumx_servers_cache = {'timestamp': 0.0, 'stats': None}


def warm_electrumx_caches_async():
    """Pre-warm caches in background to reduce first-load latency."""
    def _worker():
        try:
            get_electrumx_stats_cached(force_refresh=True, include_addnode_probes=False)
            get_electrumx_stats_cached(force_refresh=True, include_addnode_probes=True)
        except Exception as e:
            print(f"ElectrumX cache warmup error: {e}")

    threading.Thread(target=_worker, daemon=True).start()


def parse_addnode_hosts(conf_path='/palladium-config/palladium.conf'):
    """Extract addnode hosts from palladium.conf"""
    hosts = []
    try:
        with open(conf_path, 'r') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#') or not line.startswith('addnode='):
                    continue
                value = line.split('=', 1)[1].strip()
                if not value:
                    continue
                host = value.rsplit(':', 1)[0] if ':' in value else value
                if host and host not in hosts:
                    hosts.append(host)
    except Exception as e:
        print(f"Error parsing addnode hosts: {e}")
    return hosts


def probe_electrum_server(host, port=50001, timeout=1.2):
    """Check if an Electrum server is reachable and speaking protocol on host:port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        request = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "server.version",
            "params": ["palladium-dashboard", "1.4"]
        }
        sock.send((json.dumps(request) + '\n').encode())
        response = sock.recv(4096).decode()
        sock.close()
        data = json.loads(response)
        if 'result' in data:
            return True
    except Exception:
        return False
    return False


def is_electrumx_reachable(timeout=1.0):
    """Fast ElectrumX liveness check used by /api/health"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ELECTRUMX_RPC_HOST, 50001))
        request = {
            "jsonrpc": "2.0",
            "id": 999,
            "method": "server.version",
            "params": ["palladium-health", "1.4"]
        }
        sock.send((json.dumps(request) + '\n').encode())
        response = sock.recv(4096).decode()
        sock.close()
        data = json.loads(response)
        return 'result' in data
    except Exception:
        return False


def is_electrumx_reachable_retry():
    """Retry-aware liveness check to avoid transient false negatives."""
    if is_electrumx_reachable(timeout=1.2):
        return True
    time.sleep(0.15)
    return is_electrumx_reachable(timeout=2.0)


def get_electrumx_stats_cached(force_refresh=False, include_addnode_probes=False):
    """Return cached ElectrumX stats unless cache is stale."""
    cache = _electrumx_servers_cache if include_addnode_probes else _electrumx_stats_cache
    ttl = ELECTRUMX_SERVERS_TTL if include_addnode_probes else ELECTRUMX_STATS_TTL
    now = time.time()
    cached = cache.get('stats')
    cached_ts = cache.get('timestamp', 0.0)

    if (
        include_addnode_probes
        and cached is not None
        and (cached.get('active_servers_count', 0) == 0)
    ):
        ttl = ELECTRUMX_EMPTY_SERVERS_TTL

    if not force_refresh and cached is not None and (now - cached_ts) < ttl:
        return copy.deepcopy(cached)

    fresh = get_electrumx_stats(include_addnode_probes=include_addnode_probes)
    if fresh is not None:
        cache['timestamp'] = now
        cache['stats'] = fresh
        return copy.deepcopy(fresh)

    # Fallback to stale cache if fresh fetch fails
    if cached is not None:
        return copy.deepcopy(cached)
    return None

# Read RPC credentials from palladium.conf
def get_rpc_credentials():
    """Read RPC credentials from palladium.conf"""
    try:
        conf_path = '/palladium-config/palladium.conf'
        rpc_user = None
        rpc_password = None

        with open(conf_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('rpcuser='):
                    rpc_user = line.split('=', 1)[1]
                elif line.startswith('rpcpassword='):
                    rpc_password = line.split('=', 1)[1]

        return rpc_user, rpc_password
    except Exception as e:
        print(f"Error reading RPC credentials: {e}")
        return None, None

def palladium_rpc_call(method, params=None):
    """Make RPC call to Palladium node"""
    if params is None:
        params = []

    rpc_user, rpc_password = get_rpc_credentials()
    if not rpc_user or not rpc_password:
        return None

    url = f"http://{PALLADIUM_RPC_HOST}:{PALLADIUM_RPC_PORT}"
    headers = {'content-type': 'application/json'}
    payload = {
        "jsonrpc": "2.0",
        "id": "dashboard",
        "method": method,
        "params": params
    }

    try:
        response = requests.post(
            url,
            auth=(rpc_user, rpc_password),
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('result')
        return None
    except Exception as e:
        print(f"RPC call error ({method}): {e}")
        return None

def get_electrumx_stats(include_addnode_probes=False):
    """Get ElectrumX statistics via Electrum protocol and system info"""
    try:
        import socket
        import json
        import subprocess
        from datetime import datetime

        stats = {
            'server_version': 'Unknown',
            'protocol_min': '',
            'protocol_max': '',
            'genesis_hash': '',
            'hash_function': '',
            'pruning': None,
            'sessions': 0,
            'peer_discovery': 'unknown',
            'peer_announce': 'unknown',
            'active_servers': [],
            'active_servers_count': 0,
            'requests': 0,
            'subs': 0,
            'uptime': 0,
            'db_size': 0,
            'tcp_port': 50001,
            'ssl_port': 50002,
            'server_ip': 'Unknown'
        }

        # Get server IP address
        try:
            # Try to get public IP from external service
            response = requests.get('https://api.ipify.org?format=json', timeout=0.4)
            if response.status_code == 200:
                stats['server_ip'] = response.json().get('ip', 'Unknown')
            else:
                # Fallback to local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                stats['server_ip'] = s.getsockname()[0]
                s.close()
        except Exception as e:
            print(f"IP detection error: {e}")
            # Last fallback: get hostname IP
            try:
                stats['server_ip'] = socket.gethostbyname(socket.gethostname())
            except:
                stats['server_ip'] = 'Unknown'

        # Get server features via Electrum protocol
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ELECTRUMX_RPC_HOST, 50001))

            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "server.features",
                "params": []
            }

            sock.send((json.dumps(request) + '\n').encode())
            response = sock.recv(4096).decode()
            sock.close()

            data = json.loads(response)
            if 'result' in data:
                result = data['result']
                stats['server_version'] = result.get('server_version', 'Unknown')
                stats['protocol_min'] = result.get('protocol_min', '')
                stats['protocol_max'] = result.get('protocol_max', '')
                stats['genesis_hash'] = result.get('genesis_hash', '')[:16] + '...'
                stats['hash_function'] = result.get('hash_function', '')
                stats['pruning'] = result.get('pruning')
        except Exception as e:
            print(f"ElectrumX protocol error: {e}")

        # Get peers discovered by ElectrumX
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ELECTRUMX_RPC_HOST, 50001))

            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "server.peers.subscribe",
                "params": []
            }

            sock.send((json.dumps(request) + '\n').encode())
            response = sock.recv(65535).decode()
            sock.close()

            data = json.loads(response)
            if 'result' in data and isinstance(data['result'], list):
                peers = []
                for peer in data['result']:
                    if not isinstance(peer, list) or len(peer) < 3:
                        continue
                    host = peer[1]
                    features = peer[2] if isinstance(peer[2], list) else []
                    tcp_port = None
                    ssl_port = None
                    for feat in features:
                        if isinstance(feat, str) and feat.startswith('t') and feat[1:].isdigit():
                            tcp_port = feat[1:]
                        if isinstance(feat, str) and feat.startswith('s') and feat[1:].isdigit():
                            ssl_port = feat[1:]
                    if host:
                        peers.append({
                            'host': host,
                            'tcp_port': tcp_port,
                            'ssl_port': ssl_port
                        })

                stats['active_servers'] = peers
                stats['active_servers_count'] = len(peers)
        except Exception as e:
            print(f"ElectrumX peers error: {e}")

        # Keep peers list without self for dashboard card count
        try:
            merged = []
            seen = set()
            self_host = (stats.get('server_ip') or '').strip()
            for peer in (stats.get('active_servers') or []):
                host = (peer.get('host') or '').strip()
                tcp_port = str(peer.get('tcp_port') or '50001')
                if not host:
                    continue
                if self_host and host == self_host:
                    continue
                key = f"{host}:{tcp_port}"
                if key in seen:
                    continue
                seen.add(key)
                merged.append({
                    'host': host,
                    'tcp_port': tcp_port,
                    'ssl_port': peer.get('ssl_port')
                })
            stats['active_servers'] = merged
            stats['active_servers_count'] = len(merged)
        except Exception as e:
            print(f"Electrum peers normalization error: {e}")

        # Optional full probing for dedicated servers page
        if include_addnode_probes:
            try:
                addnode_hosts = parse_addnode_hosts()
                extra_servers = []
                for host in addnode_hosts:
                    if probe_electrum_server(host, 50001, timeout=0.5):
                        extra_servers.append({
                            'host': host,
                            'tcp_port': '50001',
                            'ssl_port': None
                        })

                merged = []
                seen = set()
                self_host = (stats.get('server_ip') or '').strip()
                for peer in (stats.get('active_servers') or []) + extra_servers:
                    host = (peer.get('host') or '').strip()
                    tcp_port = str(peer.get('tcp_port') or '50001')
                    if not host:
                        continue
                    if self_host and host == self_host:
                        continue
                    key = f"{host}:{tcp_port}"
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append({
                        'host': host,
                        'tcp_port': tcp_port,
                        'ssl_port': peer.get('ssl_port')
                    })

                stats['active_servers'] = merged
                stats['active_servers_count'] = len(merged)
            except Exception as e:
                print(f"Supplemental Electrum discovery error: {e}")

        # Read peer discovery/announce settings from electrumx container env
        try:
            result = subprocess.run(
                ['docker', 'exec', 'electrumx-server', 'sh', '-c',
                 'printf "%s|%s" "${PEER_DISCOVERY:-unknown}" "${PEER_ANNOUNCE:-unknown}"'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                values = (result.stdout or '').strip().split('|', 1)
                if len(values) == 2:
                    stats['peer_discovery'] = values[0] or 'unknown'
                    stats['peer_announce'] = values[1] or 'unknown'
        except Exception as e:
            print(f"Peer discovery env read error: {e}")

        # Try to get container stats via Docker
        try:
            # Get container uptime
            result = subprocess.run(
                ['docker', 'inspect', 'electrumx-server', '--format', '{{.State.StartedAt}}'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                started_at = result.stdout.strip()
                # Parse and calculate uptime
                from dateutil import parser
                start_time = parser.parse(started_at)
                uptime_seconds = int((datetime.now(start_time.tzinfo) - start_time).total_seconds())
                stats['uptime'] = uptime_seconds
        except Exception as e:
            print(f"Docker uptime error: {e}")

        # Try to estimate DB size from data directory
        try:
            result = subprocess.run(
                ['docker', 'exec', 'electrumx-server', 'du', '-sb', '/data'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                db_size = int(result.stdout.split()[0])
                stats['db_size'] = db_size
        except Exception as e:
            print(f"DB size error: {e}")

        # Count active connections (TCP sessions)
        try:
            result = subprocess.run(
                ['docker', 'exec', 'electrumx-server', 'sh', '-c',
                 'netstat -an 2>/dev/null | grep ":50001.*ESTABLISHED" | wc -l'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                sessions = int(result.stdout.strip())
                stats['sessions'] = sessions
        except Exception as e:
            print(f"Sessions count error: {e}")

        return stats
    except Exception as e:
        print(f"ElectrumX stats error: {e}")
        return None

@app.route('/')
def index():
    """Serve main dashboard page"""
    return render_template('index.html')

@app.route('/peers')
def peers():
    """Serve peers page"""
    return render_template('peers.html')

@app.route('/electrum-servers')
def electrum_servers():
    """Serve Electrum active servers page"""
    return render_template('electrum_servers.html')

@app.route('/api/palladium/info')
def palladium_info():
    """Get Palladium node blockchain info"""
    try:
        blockchain_info = palladium_rpc_call('getblockchaininfo')
        network_info = palladium_rpc_call('getnetworkinfo')
        mining_info = palladium_rpc_call('getmininginfo')
        peer_info = palladium_rpc_call('getpeerinfo')
        mempool_info = palladium_rpc_call('getmempoolinfo')

        data = {
            'blockchain': blockchain_info or {},
            'network': network_info or {},
            'mining': mining_info or {},
            'peers': len(peer_info) if peer_info else 0,
            'mempool': mempool_info or {},
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/palladium/peers')
def palladium_peers():
    """Get detailed peer information"""
    try:
        peer_info = palladium_rpc_call('getpeerinfo')
        if not peer_info:
            return jsonify({'peers': []})

        peers_data = []
        for peer in peer_info:
            peers_data.append({
                'addr': peer.get('addr', 'Unknown'),
                'inbound': peer.get('inbound', False),
                'version': peer.get('subver', 'Unknown'),
                'conntime': peer.get('conntime', 0),
                'bytessent': peer.get('bytessent', 0),
                'bytesrecv': peer.get('bytesrecv', 0)
            })

        return jsonify({
            'peers': peers_data,
            'total': len(peers_data),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/palladium/blocks/recent')
def recent_blocks():
    """Get recent blocks information"""
    try:
        blockchain_info = palladium_rpc_call('getblockchaininfo')
        if not blockchain_info:
            return jsonify({'error': 'Cannot get blockchain info'}), 500

        current_height = blockchain_info.get('blocks', 0)
        blocks = []

        # Get last 10 blocks
        for i in range(min(10, current_height)):
            height = current_height - i
            block_hash = palladium_rpc_call('getblockhash', [height])
            if block_hash:
                block = palladium_rpc_call('getblock', [block_hash])
                if block:
                    blocks.append({
                        'height': height,
                        'hash': block_hash,
                        'time': block.get('time'),
                        'size': block.get('size'),
                        'tx_count': len(block.get('tx', []))
                    })

        return jsonify({'blocks': blocks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/electrumx/stats')
def electrumx_stats():
    """Get ElectrumX server statistics"""
    try:
        stats = get_electrumx_stats_cached(include_addnode_probes=False)
        if stats:
            # If fast path reports no servers, reuse full servers cache if available.
            if (stats.get('active_servers_count') or 0) == 0:
                heavy_stats = get_electrumx_stats_cached(include_addnode_probes=True)
                if heavy_stats and (heavy_stats.get('active_servers_count') or 0) > 0:
                    stats['active_servers'] = heavy_stats.get('active_servers', [])
                    stats['active_servers_count'] = heavy_stats.get('active_servers_count', 0)

            # Get additional info from logs if available
            try:
                # Try to get container stats
                import subprocess
                result = subprocess.run(
                    ['docker', 'exec', 'electrumx-server', 'sh', '-c',
                     'ps aux | grep electrumx_server | grep -v grep'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    # Process is running, add placeholder stats
                    stats['status'] = 'running'
                    stats['requests'] = 0
                    stats['subs'] = 0
            except:
                pass

            return jsonify({
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
        return jsonify({'error': 'Cannot connect to ElectrumX'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/electrumx/servers')
def electrumx_servers():
    """Get active Electrum servers discovered by this node"""
    try:
        stats = get_electrumx_stats_cached(include_addnode_probes=True)
        if not stats:
            return jsonify({'error': 'Cannot connect to ElectrumX'}), 500

        servers = stats.get('active_servers') or []
        if len(servers) == 0:
            # Fallback to fast discovery results if full probing is temporarily empty.
            fast_stats = get_electrumx_stats_cached(include_addnode_probes=False)
            if fast_stats:
                servers = fast_stats.get('active_servers') or []
        return jsonify({
            'servers': servers,
            'total': len(servers),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/resources')
def system_resources():
    """Get system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        data = {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'used': memory.used,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'percent': disk.percent
            },
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health():
    """Health check endpoint"""
    palladium_ok = palladium_rpc_call('getblockchaininfo') is not None
    stats = get_electrumx_stats_cached(include_addnode_probes=False)
    if not stats or stats.get('server_version') in (None, '', 'Unknown'):
        stats = get_electrumx_stats_cached(force_refresh=True, include_addnode_probes=False)
    electrumx_ok = bool(stats and (stats.get('server_version') not in (None, '', 'Unknown')))

    return jsonify({
        'status': 'healthy' if (palladium_ok and electrumx_ok) else 'degraded',
        'services': {
            'palladium': 'up' if palladium_ok else 'down',
            'electrumx': 'up' if electrumx_ok else 'down'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    warm_electrumx_caches_async()
    app.run(host='0.0.0.0', port=8080, debug=False)
