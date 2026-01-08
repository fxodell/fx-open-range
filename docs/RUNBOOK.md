# Trading Application Runbook

## Common Issues and Solutions

### Issue: API Token Not Set

**Symptoms**: Error message "ERROR: OANDA_API_TOKEN not set!"

**Solution**:
1. Create a `.env` file in the project root
2. Add: `OANDA_API_TOKEN=your-token-here`
3. Restart the application

### Issue: 400 Bad Request Error

**Symptoms**: `400 Client Error: Bad Request` when fetching candles

**Cause**: Datetime format issue in API requests

**Solution**: This has been fixed. Ensure you're using the latest code version. The datetime format is now RFC3339 compliant: `YYYY-MM-DDTHH:MM:SS.000000Z`

### Issue: No Trades Executed

**Symptoms**: Application runs but no trades are placed

**Possible Causes**:
1. Outside trading hours
2. Already reached max daily trades
3. Signal is 'flat' (no trading signal)
4. Insufficient market data (need at least SMA_PERIOD days)

**Solution**:
- Check logs for specific reason
- Verify trading hours configuration
- Check that market data is being fetched successfully

### Issue: Connection Errors

**Symptoms**: `ConnectionError` or `Timeout` errors

**Solution**:
- Check internet connection
- Verify OANDA API is accessible
- Retry logic with exponential backoff is now implemented
- Check API status page

### Issue: Format String Errors

**Symptoms**: `ValueError: Invalid format specifier` in logs

**Solution**: This has been fixed. Update to latest code version.

## Monitoring

### Check Application Status

```bash
python -m app.main --status
```

### View Recent Logs

```bash
tail -f logs/trading_$(date +%Y%m%d).log
```

### Check Metrics

Metrics are logged periodically. Check logs for "Trading Metrics Summary" entries.

## Emergency Procedures

### Stop All Trading

```bash
python -m app.main --close-all
```

### View Open Positions

```bash
python -m app.main --status
```

### Manual Position Closure

Use OANDA web interface or API directly if application is unresponsive.





