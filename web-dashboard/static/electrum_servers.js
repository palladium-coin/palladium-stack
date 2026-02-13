// Electrum Active Servers Page JavaScript

function updateLastUpdateTime() {
    const now = new Date().toLocaleString();
    document.getElementById('lastUpdate').textContent = now;
}

async function updateElectrumServers() {
    try {
        const response = await fetch('/api/electrumx/servers');
        const data = await response.json();

        if (data.error) {
            console.error('Electrum servers error:', data.error);
            return;
        }

        const servers = Array.isArray(data.servers) ? data.servers : [];
        const tbody = document.getElementById('electrumServersTable');
        tbody.innerHTML = '';

        if (servers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="loading">No active servers found</td></tr>';
            document.getElementById('totalServers').textContent = '0';
            document.getElementById('tcpReachable').textContent = '0';
            return;
        }

        servers.forEach(server => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="peer-addr">${server.host || '--'}</td>
                <td>${server.tcp_port || '--'}</td>
                <td>${server.ssl_port || '--'}</td>
            `;
            tbody.appendChild(row);
        });

        document.getElementById('totalServers').textContent = String(servers.length);
        const tcpCount = servers.filter(s => !!s.tcp_port).length;
        document.getElementById('tcpReachable').textContent = String(tcpCount);
    } catch (error) {
        console.error('Error fetching Electrum servers:', error);
        document.getElementById('electrumServersTable').innerHTML =
            '<tr><td colspan="3" class="loading">Error loading servers</td></tr>';
    }
}

async function updateAll() {
    updateLastUpdateTime();
    await updateElectrumServers();
}

document.addEventListener('DOMContentLoaded', async () => {
    await updateAll();
    setInterval(updateAll, 10000);
});
