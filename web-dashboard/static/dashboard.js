// Dashboard JavaScript

// API fetch helper with optional API key injected from template
async function apiFetch(url, options = {}) {
    const apiKey = (window.DASHBOARD_API_KEY || "").trim();
    const headers = { ...(options.headers || {}) };
    if (apiKey) {
        headers["X-API-Key"] = apiKey;
    }
    return fetch(url, { ...options, headers });
}

// Format numbers
function formatNumber(num) {
    if (num >= 1000000000) return (num / 1000000000).toFixed(2) + 'B';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(2) + 'K';
    return num.toString();
}

// Format difficulty (always with M suffix and 1 decimal)
function formatDifficulty(num) {
    if (num >= 1000000000) return (num / 1000000000).toFixed(1) + ' B';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + ' M';
    if (num >= 1000) return (num / 1000).toFixed(1) + ' K';
    return num.toFixed(1);
}

// Format hashrate
function formatHashrate(hps) {
    const n = Number(hps);
    if (!Number.isFinite(n) || n <= 0) return "--";
    const units = ["H/s", "KH/s", "MH/s", "GH/s", "TH/s", "PH/s"];
    let value = n;
    let i = 0;
    while (value >= 1000 && i < units.length - 1) {
        value /= 1000;
        i += 1;
    }
    return value.toFixed(2) + " " + units[i];
}

// Format coin amount
function formatCoinAmount(amount) {
    const n = Number(amount);
    if (!Number.isFinite(n)) return "--";
    return n.toFixed(2);
}

// Format block height (always full integer with thousands separator)
function formatBlockHeight(num) {
    return num.toLocaleString('en-US');
}

// Format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format time
function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

// Format duration
function formatDuration(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

// Update health status
function updateHealthStatus(data) {
    const statusEl = document.getElementById('healthStatus');
    const statusDot = statusEl.querySelector('.status-dot');
    const statusText = statusEl.querySelector('.status-text');

    if (data.status === 'healthy') {
        statusEl.classList.remove('degraded');
        statusText.textContent = 'All Systems Operational';
    } else {
        statusEl.classList.add('degraded');
        statusText.textContent = 'Service Degraded';
    }
}

// Update system resources
async function updateSystemResources() {
    try {
        const response = await apiFetch('/api/system/resources');
        const data = await response.json();

        if (data.error) {
            console.error('System resources error:', data.error);
            return;
        }

        // Update CPU
        const cpuPercent = data.cpu.percent.toFixed(1);
        document.getElementById('cpuValue').textContent = cpuPercent + '%';
        document.getElementById('cpuProgress').style.width = cpuPercent + '%';

        // Update Memory
        const memPercent = data.memory.percent.toFixed(1);
        document.getElementById('memoryValue').textContent = memPercent + '%';
        document.getElementById('memoryProgress').style.width = memPercent + '%';

        // Update Disk
        const diskPercent = data.disk.percent.toFixed(1);
        document.getElementById('diskValue').textContent = diskPercent + '%';
        document.getElementById('diskProgress').style.width = diskPercent + '%';

    } catch (error) {
        console.error('Error fetching system resources:', error);
    }
}

// Update Palladium info
async function updatePalladiumInfo() {
    try {
        const response = await apiFetch('/api/palladium/info');
        const data = await response.json();

        if (data.error) {
            console.error('Palladium info error:', data.error);
            return;
        }

        // Update blockchain info
        if (data.blockchain) {
            document.getElementById('blockHeight').textContent = formatBlockHeight(data.blockchain.blocks || 0);
            document.getElementById('difficulty').textContent = formatDifficulty(data.blockchain.difficulty || 0);
            document.getElementById('network').textContent = (data.blockchain.chain || 'unknown').toUpperCase();

            const progress = ((data.blockchain.verificationprogress || 0) * 100).toFixed(2);
            document.getElementById('syncProgress').textContent = progress + '%';
        }

        // Update network info
        if (data.network) {
            let version = data.network.subversion || 'Unknown';
            // Extract version number from /Palladium:2.0.0/ format
            const match = version.match(/:([\d.]+)/);
            if (match) {
                version = 'v' + match[1];
            }
            document.getElementById('nodeVersion').textContent = version;
        }

        // Update connections
        document.getElementById('connections').textContent = data.peers || 0;

        // Update mempool info
        if (data.mempool) {
            document.getElementById('mempoolSize').textContent = data.mempool.size || 0;
            document.getElementById('mempoolBytes').textContent = formatBytes(data.mempool.bytes || 0);
            document.getElementById('mempoolMax').textContent = formatBytes(data.mempool.maxmempool || 0);

            // Calculate usage percentage
            if (data.mempool.maxmempool && data.mempool.bytes) {
                const usage = ((data.mempool.bytes / data.mempool.maxmempool) * 100).toFixed(1);
                document.getElementById('mempoolUsage').textContent = usage + '%';
            } else {
                document.getElementById('mempoolUsage').textContent = '0%';
            }
        }

        // Update network hashrate
        const hashrateResponse = await apiFetch("/api/palladium/network-hashrate");
        const hashrateData = await hashrateResponse.json();
        if (!hashrateData.error) {
            document.getElementById("networkHashrate").textContent = formatHashrate(hashrateData.network_hashrate);
        }

    } catch (error) {
        console.error('Error fetching Palladium info:', error);
    }
}

// Update recent blocks
async function updateRecentBlocks() {
    try {
        const response = await apiFetch('/api/palladium/blocks/recent');
        const data = await response.json();

        if (data.error) {
            console.error('Recent blocks error:', data.error);
            return;
        }

        const tbody = document.getElementById('recentBlocksTable');
        tbody.innerHTML = '';

        if (data.blocks && data.blocks.length > 0) {
            data.blocks.forEach(block => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${block.height}</strong></td>
                    <td class="hash-cell" title="${block.hash}">${block.hash.substring(0, 20)}...</td>
                    <td>${formatTime(block.time)}</td>
                    <td>${formatBytes(block.size)}</td>
                    <td>${block.tx_count}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No blocks available</td></tr>';
        }

    } catch (error) {
        console.error('Error fetching recent blocks:', error);
    }
}

// Peers are now on a separate page, no update needed here

// Update ElectrumX stats
async function updateElectrumXStats() {
    try {
        const response = await apiFetch('/api/electrumx/stats');
        const data = await response.json();

        if (data.error) {
            console.error('ElectrumX stats error:', data.error);
            return;
        }

        if (data.stats) {
            // Server version (extract version number like we do for node)
            let serverVersion = data.stats.server_version || 'Unknown';
            const versionMatch = serverVersion.match(/([\d.]+)/);
            if (versionMatch) {
                serverVersion = 'v' + versionMatch[1];
            }
            document.getElementById('serverVersion').textContent = serverVersion;

            // Database size
            const dbSize = data.stats.db_size > 0 ? formatBytes(data.stats.db_size) : '--';
            document.getElementById('dbSize').textContent = dbSize;

            // Uptime
            const uptime = data.stats.uptime > 0 ? formatDuration(data.stats.uptime) : '--';
            document.getElementById('uptime').textContent = uptime;

            // Server IP
            document.getElementById('serverIP').textContent = data.stats.server_ip || '--';

            // TCP Port
            document.getElementById('tcpPort').textContent = data.stats.tcp_port || '--';

            // SSL Port
            document.getElementById('sslPort').textContent = data.stats.ssl_port || '--';

            // Active servers from peer discovery
            const activeServers = Array.isArray(data.stats.active_servers) ? data.stats.active_servers : [];
            document.getElementById('activeServersCount').textContent = data.stats.active_servers_count ?? activeServers.length;
        }

    } catch (error) {
        console.error('Error fetching ElectrumX stats:', error);
    }
}

// Update health check
async function updateHealth() {
    try {
        const response = await apiFetch('/api/health');
        const data = await response.json();
        updateHealthStatus(data);
    } catch (error) {
        console.error('Error fetching health:', error);
    }
}

// Update last update time
function updateLastUpdateTime() {
    const now = new Date().toLocaleString();
    document.getElementById('lastUpdate').textContent = now;
}

// Update all data
async function updateAll() {
    updateLastUpdateTime();
    await Promise.all([
        updateHealth(),
        updateSystemResources(),
        updatePalladiumInfo(),
        updateRecentBlocks(),
        updateElectrumXStats()
    ]);
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    // Initial update
    await updateAll();

    // Auto-refresh every 10 seconds
    setInterval(updateAll, 10000);
});
