# Palladium Network Dashboard

Modern web dashboard for monitoring Palladium Node and ElectrumX Server statistics.

## Features

- **Real-time Monitoring**: Auto-refresh every 10 seconds
- **Palladium Node Stats**: Block height, difficulty, connections, sync progress
- **ElectrumX Server Stats**: Active sessions, requests, subscriptions, uptime
- **System Resources**: CPU, memory, and disk usage monitoring
- **Interactive Charts**: Block time history and mempool transaction graphs
- **Recent Blocks Table**: View the latest blocks with detailed information
- **Professional UI**: Dark theme with responsive design

## API Endpoints

- `GET /` - Main dashboard page
- `GET /api/health` - Health check for all services
- `GET /api/palladium/info` - Palladium node information
- `GET /api/palladium/blocks/recent` - Recent blocks
- `GET /api/electrumx/stats` - ElectrumX server statistics
- `GET /api/system/resources` - System resource usage

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Charts**: Chart.js
- **Design**: Modern dark theme with gradient accents

## Access

After starting the services with `docker-compose up -d`, access the dashboard at:

```
http://localhost:8080
```

Or from another device on the network:

```
http://<your-server-ip>:8080
```
