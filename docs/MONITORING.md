# Monitoring Guide

## Metrics Tracked

The application tracks the following metrics:

- **Trades Executed**: Total number of trades
- **Win Rate**: Percentage of successful trades
- **Total Pips**: Cumulative pips gained/lost
- **Daily P/L**: Pips gained/lost today
- **API Calls**: Total API calls made
- **API Error Rate**: Percentage of failed API calls
- **Average API Latency**: Average response time for API calls

## Viewing Metrics

### From Logs

Metrics are logged periodically. Search for "Trading Metrics Summary" in log files:

```bash
grep "Trading Metrics Summary" logs/trading_*.log
```

### Programmatically

```python
from app.utils.metrics import get_metrics

metrics = get_metrics()
summary = metrics.get_summary()
print(summary)
```

## Log Files

### Location

Logs are stored in: `logs/trading_YYYYMMDD.log`

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (requires attention)

### Viewing Logs

```bash
# View today's log
tail -f logs/trading_$(date +%Y%m%d).log

# Search for errors
grep ERROR logs/trading_*.log

# Search for trades
grep "Order placed" logs/trading_*.log
```

## Health Checks

### Application Health

```bash
python -m app.main --status
```

This checks:
- API connectivity
- Account status
- Open positions
- Account balance

### API Health

Check OANDA API status:
- Practice: https://api-fxpractice.oanda.com
- Live: https://api-fxtrade.oanda.com

## Alerts

### Recommended Alerts

1. **High API Error Rate**: > 10% error rate
2. **No Trades**: No trades executed in 24 hours (if expected)
3. **High Daily Loss**: Daily loss exceeds threshold
4. **Application Crashes**: Process not running

### Setting Up Alerts

Use monitoring tools like:
- **systemd**: Built-in restart and monitoring
- **supervisord**: Process monitoring
- **Prometheus + Grafana**: Advanced metrics and alerting
- **Sentry**: Error tracking

## Performance Monitoring

### API Latency

Tracked automatically. Check metrics for `avg_api_latency_seconds`.

### Trade Execution Time

Monitor time between signal generation and order placement.

### Resource Usage

Monitor:
- CPU usage
- Memory usage
- Disk space (for logs)
- Network bandwidth

## Troubleshooting

### High API Error Rate

1. Check internet connectivity
2. Verify API token is valid
3. Check OANDA API status
4. Review rate limiting

### Slow Performance

1. Check API latency metrics
2. Review log file size
3. Check system resources
4. Verify network connection

### Missing Trades

1. Check trading hours configuration
2. Verify market data is being fetched
3. Check signal generation logic
4. Review daily trade limits



