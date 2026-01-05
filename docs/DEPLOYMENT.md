# Deployment Guide

## Prerequisites

- Python 3.10+
- OANDA API token
- `.env` file with configuration

## Setup Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OANDA_API_TOKEN
   ```

3. **Verify Configuration**
   ```bash
   python -m app.main --status
   ```

## Running the Application

### Practice Mode (Default)

```bash
python -m app.main
```

### Live Mode

```bash
python -m app.main --mode live
```

### Run Once

```bash
python -m app.main --once
```

### Continuous Mode

```bash
python -m app.main --interval 60
```

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/trading-app.service`:

```ini
[Unit]
Description=FX Trading Application
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/path/to/fx-open-range-project
ExecStart=/usr/bin/python3 -m app.main
Restart=always
RestartSec=10
Environment="PATH=/usr/bin:/usr/local/bin"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable trading-app
sudo systemctl start trading-app
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]
```

Build and run:
```bash
docker build -t trading-app .
docker run -d --env-file .env trading-app
```

## Monitoring

- Logs: `logs/trading_YYYYMMDD.log`
- Metrics: Check logs for periodic metrics summaries
- Status: Use `--status` flag to check account status

## Backup and Recovery

- Backup `.env` file (securely)
- Backup logs directory
- Document current positions before major updates



