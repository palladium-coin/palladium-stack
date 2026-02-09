// Peers Page JavaScript

// Format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format duration
function formatDuration(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
}

// Update peers table and statistics
async function updatePeers() {
    try {
        const response = await fetch('/api/palladium/peers');
        const data = await response.json();

        if (data.error) {
            console.error('Peers error:', data.error);
            return;
        }

        const tbody = document.getElementById('peersTableBody');
        tbody.innerHTML = '';

        if (data.peers && data.peers.length > 0) {
            let inboundCount = 0;
            let outboundCount = 0;
            let totalSent = 0;
            let totalReceived = 0;

            data.peers.forEach(peer => {
                const row = document.createElement('tr');
                const direction = peer.inbound ? '⬇️ Inbound' : '⬆️ Outbound';
                const directionClass = peer.inbound ? 'peer-inbound' : 'peer-outbound';

                // Count inbound/outbound
                if (peer.inbound) {
                    inboundCount++;
                } else {
                    outboundCount++;
                }

                // Sum traffic
                totalSent += peer.bytessent || 0;
                totalReceived += peer.bytesrecv || 0;

                // Extract version number
                let version = peer.subver || peer.version || 'Unknown';
                const versionMatch = version.match(/([\d.]+)/);
                if (versionMatch) {
                    version = 'v' + versionMatch[1];
                }

                // Format connection time
                const connTime = peer.conntime ? formatDuration(Math.floor(Date.now() / 1000) - peer.conntime) : '--';

                // Calculate total traffic for this peer
                const peerTotal = (peer.bytessent || 0) + (peer.bytesrecv || 0);

                row.innerHTML = `
                    <td class="peer-addr">${peer.addr}</td>
                    <td><span class="${directionClass}">${direction}</span></td>
                    <td>${version}</td>
                    <td>${connTime}</td>
                    <td>${formatBytes(peer.bytessent || 0)}</td>
                    <td>${formatBytes(peer.bytesrecv || 0)}</td>
                    <td><strong>${formatBytes(peerTotal)}</strong></td>
                `;
                tbody.appendChild(row);
            });

            // Update statistics
            document.getElementById('totalPeers').textContent = data.peers.length;
            document.getElementById('inboundPeers').textContent = inboundCount;
            document.getElementById('outboundPeers').textContent = outboundCount;
            document.getElementById('totalTraffic').textContent = formatBytes(totalSent + totalReceived);

        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="loading">No peers connected</td></tr>';
            document.getElementById('totalPeers').textContent = '0';
            document.getElementById('inboundPeers').textContent = '0';
            document.getElementById('outboundPeers').textContent = '0';
            document.getElementById('totalTraffic').textContent = '0 B';
        }

    } catch (error) {
        console.error('Error fetching peers:', error);
        document.getElementById('peersTableBody').innerHTML = '<tr><td colspan="7" class="loading">Error loading peers</td></tr>';
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
    await updatePeers();
}

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Initial update
    await updateAll();

    // Auto-refresh every 10 seconds
    setInterval(updateAll, 10000);
});
