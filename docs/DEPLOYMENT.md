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

### Using systemd (Linux) - Recommended

A systemd service file is provided at `/opt/fx-open-range/fx-open-range.service`.

**Quick Setup:**
```bash
# Install and enable the service
sudo /opt/fx-open-range/setup-service.sh

# Start the service
sudo systemctl start fx-open-range

# Check status
sudo systemctl status fx-open-range
```

**Manual Setup:**
```bash
# Copy service file to systemd directory
sudo cp /opt/fx-open-range/fx-open-range.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable fx-open-range

# Start the service
sudo systemctl start fx-open-range
```

**Service Management:**
```bash
# Check service status
sudo systemctl status fx-open-range

# View live logs
sudo journalctl -u fx-open-range -f

# View recent logs
sudo journalctl -u fx-open-range -n 100

# Stop the service
sudo systemctl stop fx-open-range

# Restart the service
sudo systemctl restart fx-open-range

# Disable auto-start on boot
sudo systemctl disable fx-open-range
```

**Note:** The service runs as user `mike` in practice mode by default. Ensure your `.env` file is configured with `OANDA_API_TOKEN` and `OANDA_PRACTICE_MODE=true` in `/opt/fx-open-range/.env`.

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





