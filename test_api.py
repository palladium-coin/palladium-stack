#!/usr/bin/env python3
"""
Tests for the web dashboard API endpoints.

Loads API_KEY from .env and verifies:
  - Authentication enforcement for external IPs (X-API-Key / Bearer token)
  - Correct JSON structure for every /api/* route
  - Cache-Control headers on API responses

Run:
    pip install pytest flask flask-cors requests psutil python-dateutil
    pytest test_api.py -v
"""

import os
import sys
from unittest.mock import patch

import pytest

# ── 1. Load .env before importing the app ────────────────────────────────────

def _load_dotenv(path: str) -> dict:
    env_vars: dict = {}
    try:
        with open(path) as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, val = line.partition('=')
                env_vars[key.strip()] = val.strip()
    except FileNotFoundError:
        pass
    return env_vars


_dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
for _k, _v in _load_dotenv(_dotenv_path).items():
    os.environ.setdefault(_k, _v)

API_KEY: str = os.getenv('API_KEY', '').strip()

# ── 2. Import the Flask app ───────────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web-dashboard'))
from app import app as flask_app  # noqa: E402

# ── 3. Fixtures ───────────────────────────────────────────────────────────────

EXTERNAL_IP = '8.8.8.8'   # non-RFC1918 → auth required
TRUSTED_IP  = '127.0.0.1' # loopback   → no auth required


@pytest.fixture()
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def _ext(**extra_headers):
    """Return kwargs that simulate an external client with optional extra headers."""
    return dict(environ_base={'REMOTE_ADDR': EXTERNAL_IP}, headers=extra_headers)


def _local():
    """Return kwargs that simulate a trusted local client."""
    return dict(environ_base={'REMOTE_ADDR': TRUSTED_IP})


# ── 4. Mock data for RPC / ElectrumX ─────────────────────────────────────────

_BLOCKCHAIN_INFO = {
    'chain': 'main', 'blocks': 100_000, 'headers': 100_000,
    'difficulty': 1_234_567.89, 'bestblockhash': 'ab' * 32,
}
_NETWORK_INFO  = {'version': 180_000, 'subversion': '/Palladium:1.8.0/', 'connections': 8}
_MINING_INFO   = {'networkhashps': 9_876_543_210.0, 'difficulty': 1_234_567.89}
_PEER_INFO     = [{'addr': '1.2.3.4:2333', 'inbound': False, 'subver': '/Palladium/',
                   'conntime': 1_000, 'bytessent': 512, 'bytesrecv': 1_024}]
_MEMPOOL_INFO  = {'size': 0, 'bytes': 0}
_BLOCK_HASH    = 'deadbeef' * 8
_BLOCK         = {'height': 100_000, 'hash': _BLOCK_HASH, 'time': 1_700_000_000,
                  'size': 300, 'tx': ['tx1']}
_SUBSIDY       = {'miner': 50.0, 'masternode': 0.0}

_RPC_DISPATCH = {
    'getblockchaininfo': _BLOCKCHAIN_INFO,
    'getnetworkinfo':    _NETWORK_INFO,
    'getmininginfo':     _MINING_INFO,
    'getpeerinfo':       _PEER_INFO,
    'getmempoolinfo':    _MEMPOOL_INFO,
    'getblockcount':     100_000,
    'getnetworkhashps':  9_876_543_210.0,
    'getdifficulty':     1_234_567.89,
    'getblocksubsidy':   _SUBSIDY,
    'getblockhash':      _BLOCK_HASH,
    'getblock':          _BLOCK,
}


def _rpc(method, params=None):
    return _RPC_DISPATCH.get(method)


_ELECTRUMX_STATS = {
    'server_version':       'ElectrumX 1.16.0',
    'protocol_min':         '1.4',
    'protocol_max':         '1.4.2',
    'genesis_hash':         'abcdef01234567890...',
    'genesis_hash_full':    'abcdef0123456789' * 4,
    'hash_function':        'sha256d',
    'pruning':              None,
    'sessions':             3,
    'peer_discovery':       'on',
    'peer_announce':        'on',
    'active_servers':       [{'host': '1.2.3.4', 'tcp_port': '50001', 'ssl_port': '50002',
                              'tcp_reachable': True, 'ssl_reachable': True}],
    'active_servers_count': 1,
    'requests':             0,
    'subs':                 0,
    'uptime':               3_600,
    'db_size':              1_073_741_824,
    'tcp_port':             '50001',
    'ssl_port':             '50002',
    'server_ip':            '5.6.7.8',
}


# ── 5. Authentication tests ───────────────────────────────────────────────────

class TestApiKeyAuth:
    """API key authentication is enforced for external (non-RFC1918) clients."""

    def test_no_key_returns_401(self, client):
        r = client.get('/api/health', **_ext())
        assert r.status_code == 401
        assert 'error' in r.get_json()

    @pytest.mark.skipif(not API_KEY, reason='API_KEY not set in .env')
    def test_valid_xapikey_header_passes(self, client):
        """X-API-Key header with the correct key must pass auth."""
        r = client.get('/api/health', **_ext(**{'X-API-Key': API_KEY}))
        assert r.status_code != 401, f"Got 401 even with a valid API key"

    @pytest.mark.skipif(not API_KEY, reason='API_KEY not set in .env')
    def test_valid_bearer_token_passes(self, client):
        """Authorization: Bearer <key> must pass auth."""
        r = client.get('/api/health', **_ext(Authorization=f'Bearer {API_KEY}'))
        assert r.status_code != 401

    @pytest.mark.skipif(not API_KEY, reason='API_KEY not set in .env')
    def test_wrong_key_returns_401(self, client):
        r = client.get('/api/health', **_ext(**{'X-API-Key': 'wrong-key-999'}))
        assert r.status_code == 401

    def test_trusted_ip_needs_no_auth(self, client):
        """Localhost/LAN clients must never receive 401."""
        r = client.get('/api/health', **_local())
        assert r.status_code != 401

    @pytest.mark.skipif(not API_KEY, reason='API_KEY not set in .env')
    def test_all_api_routes_respect_auth(self, client):
        """Every /api/* route must return 401 for external requests without a key."""
        routes = [
            '/api/health',
            '/api/palladium/info',
            '/api/palladium/block-height',
            '/api/palladium/network-hashrate',
            '/api/palladium/difficulty',
            '/api/palladium/coinbase-subsidy',
            '/api/palladium/peers',
            '/api/palladium/blocks/recent',
            '/api/electrumx/stats',
            '/api/electrumx/servers',
            '/api/system/resources',
        ]
        for route in routes:
            r = client.get(route, **_ext())
            assert r.status_code == 401, f"{route} should return 401 without key, got {r.status_code}"


# ── 6. Endpoint response structure tests (mocked backends) ───────────────────

class TestApiEndpoints:
    """
    Verify JSON structure of every /api/* endpoint using mocked RPC and
    ElectrumX backends so the tests are self-contained.
    """

    # Helper ------------------------------------------------------------------

    def _get(self, client, path):
        return client.get(path, **_local())

    # /api/health -------------------------------------------------------------

    @patch('app.get_electrumx_stats_cached', return_value=_ELECTRUMX_STATS)
    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_health(self, _rpc_mock, _stats_mock, client):
        r = self._get(client, '/api/health')
        assert r.status_code == 200
        data = r.get_json()
        assert 'status' in data
        assert 'services' in data
        assert 'palladium' in data['services']
        assert 'electrumx' in data['services']
        assert 'timestamp' in data

    # /api/palladium/* --------------------------------------------------------

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_palladium_info(self, _mock, client):
        r = self._get(client, '/api/palladium/info')
        assert r.status_code == 200
        data = r.get_json()
        assert 'blockchain' in data
        assert 'network'    in data
        assert 'mining'     in data
        assert 'peers'      in data
        assert 'mempool'    in data
        assert 'timestamp'  in data

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_block_height(self, _mock, client):
        r = self._get(client, '/api/palladium/block-height')
        assert r.status_code == 200
        data = r.get_json()
        assert data.get('block_height') == 100_000
        assert 'timestamp' in data

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_network_hashrate(self, _mock, client):
        r = self._get(client, '/api/palladium/network-hashrate')
        assert r.status_code == 200
        data = r.get_json()
        assert 'network_hashrate' in data
        assert data.get('unit') == 'H/s'
        assert isinstance(data['network_hashrate'], float)

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_difficulty(self, _mock, client):
        r = self._get(client, '/api/palladium/difficulty')
        assert r.status_code == 200
        data = r.get_json()
        assert 'difficulty' in data
        assert isinstance(data['difficulty'], float)

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_coinbase_subsidy(self, _mock, client):
        r = self._get(client, '/api/palladium/coinbase-subsidy')
        assert r.status_code == 200
        data = r.get_json()
        assert 'coinbase_subsidy' in data
        assert 'timestamp' in data

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_peers(self, _mock, client):
        r = self._get(client, '/api/palladium/peers')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data.get('peers'), list)
        assert data.get('total') == 1
        peer = data['peers'][0]
        assert 'addr' in peer
        assert 'inbound' in peer

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_recent_blocks(self, _mock, client):
        r = self._get(client, '/api/palladium/blocks/recent')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data.get('blocks'), list)
        if data['blocks']:
            blk = data['blocks'][0]
            assert 'height' in blk
            assert 'hash'   in blk

    # /api/electrumx/* --------------------------------------------------------

    @patch('app.get_electrumx_stats_cached', return_value=_ELECTRUMX_STATS)
    def test_electrumx_stats(self, _mock, client):
        r = self._get(client, '/api/electrumx/stats')
        assert r.status_code == 200
        data = r.get_json()
        assert 'stats' in data
        stats = data['stats']
        assert 'server_version' in stats
        assert 'timestamp' in data

    @patch('app.get_electrumx_stats_cached', return_value=_ELECTRUMX_STATS)
    def test_electrumx_servers(self, _mock, client):
        r = self._get(client, '/api/electrumx/servers')
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data.get('servers'), list)
        assert data.get('total') == len(_ELECTRUMX_STATS['active_servers'])
        assert 'timestamp' in data

    # /api/system/* -----------------------------------------------------------

    def test_system_resources(self, client):
        r = self._get(client, '/api/system/resources')
        assert r.status_code == 200
        data = r.get_json()
        assert 'cpu'    in data
        assert 'memory' in data
        assert 'disk'   in data
        assert 'percent' in data['cpu']
        assert 'percent' in data['memory']
        assert 'percent' in data['disk']


# ── 7. Cache-Control header tests ────────────────────────────────────────────

class TestCacheHeaders:
    """Every /api/* response must carry no-store Cache-Control headers."""

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_no_store_header_present(self, _mock, client):
        r = client.get('/api/palladium/block-height',
                       environ_base={'REMOTE_ADDR': TRUSTED_IP})
        cc = r.headers.get('Cache-Control', '')
        assert 'no-store' in cc
        assert 'no-cache' in cc

    @patch('app.palladium_rpc_call', side_effect=_rpc)
    def test_pragma_no_cache(self, _mock, client):
        r = client.get('/api/palladium/info',
                       environ_base={'REMOTE_ADDR': TRUSTED_IP})
        assert r.headers.get('Pragma') == 'no-cache'
