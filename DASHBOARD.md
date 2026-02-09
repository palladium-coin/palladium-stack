# Web Dashboard Quick Start

## Starting the Dashboard

The dashboard is automatically started when you run:

```bash
docker compose up -d
```

This will start three services:
1. **palladium-node** - The Palladium blockchain node
2. **electrumx-server** - The ElectrumX server
3. **palladium-dashboard** - The web monitoring dashboard

## Accessing the Dashboard

Once all services are running, access the dashboard at:

**From the same machine:**
```
http://localhost:8080
```

**From another device on your network:**
```
http://<your-raspberry-pi-ip>:8080
```

To find your Raspberry Pi IP address:
```bash
hostname -I | awk '{print $1}'
```

## Dashboard Features

### Overview Cards
- **System Resources**: Real-time CPU, memory, and disk usage
- **Palladium Node**: Block height, difficulty, connections, sync progress
- **ElectrumX Server**: Active sessions, requests, subscriptions, uptime

### Charts
- **Block Time History**: Line chart showing block generation times
- **Mempool Transactions**: Bar chart of pending transactions

### Recent Blocks
Table showing the last 10 blocks with:
- Block height
- Block hash
- Timestamp
- Block size
- Transaction count

## Auto-Refresh

The dashboard automatically refreshes every 10 seconds to show the latest data.

## Troubleshooting

### Dashboard Not Loading

1. Check if all containers are running:
   ```bash
   docker ps
   ```

   You should see three containers:
   - `palladium-node`
   - `electrumx-server`
   - `palladium-dashboard`

2. Check dashboard logs:
   ```bash
   docker logs palladium-dashboard
   ```

3. Check if the port is accessible:
   ```bash
   curl http://localhost:8080/api/health
   ```

### Services Showing as "Down"

If services show as down in the dashboard:

1. **Palladium Node**: May still be syncing. Check logs:
   ```bash
   docker logs palladium-node
   ```

2. **ElectrumX Server**: May be waiting for the node to sync. Check logs:
   ```bash
   docker logs electrumx-server
   ```

### Network Access Issues

If you can't access from another device:

1. Check firewall rules:
   ```bash
   sudo ufw status
   ```

2. Allow port 8080 if needed:
   ```bash
   sudo ufw allow 8080/tcp
   ```

3. Verify the dashboard is listening on all interfaces:
   ```bash
   netstat -tln | grep 8080
   ```

   Should show: `0.0.0.0:8080`

## Stopping the Dashboard

To stop all services including the dashboard:

```bash
docker compose down
```

To stop only the dashboard:

```bash
docker stop palladium-dashboard
```

## Rebuilding the Dashboard

If you make changes to the dashboard code:

```bash
docker compose build dashboard
docker compose up -d dashboard
```

## API Endpoints

The dashboard also provides REST API endpoints:

- `GET /api/health` - Health check
- `GET /api/palladium/info` - Node information
- `GET /api/palladium/blocks/recent` - Recent blocks
- `GET /api/electrumx/stats` - Server statistics
- `GET /api/system/resources` - System resources

Example:
```bash
curl http://localhost:8080/api/health | jq
```

## Security Note

The dashboard is exposed on `0.0.0.0:8080` making it accessible from your network. If you're running this on a public server, consider:

1. Using a reverse proxy (nginx) with authentication
2. Restricting access with firewall rules
3. Using HTTPS with SSL certificates
