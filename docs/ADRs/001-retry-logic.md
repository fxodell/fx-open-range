# ADR-001: Retry Logic with Exponential Backoff

## Status

Accepted

## Context

OANDA API calls can fail due to transient network issues, rate limiting, or temporary server errors. Without retry logic, these failures cause the trading application to miss trading opportunities or fail to fetch critical market data.

## Decision

Implement retry logic with exponential backoff for all OANDA API calls. Use a decorator pattern to apply retries consistently across all API methods.

## Implementation

- Created `app/utils/retry.py` with `@retry_with_backoff` decorator
- Applied to `fetch_candles()` and `place_market_order()` methods
- Default: 3 retries with 1s initial delay, 2x backoff factor
- Only retries on `requests.exceptions.RequestException` (connection errors, timeouts)

## Consequences

**Positive**:
- Improved resilience to transient failures
- Automatic recovery from temporary network issues
- Better user experience (fewer manual interventions)

**Negative**:
- Slightly increased latency on retries
- May mask persistent issues (but logs errors after all retries fail)

## Alternatives Considered

1. **Circuit Breaker Pattern**: More complex, better for persistent failures
2. **Simple Retry**: Less sophisticated, may overwhelm API on retries
3. **No Retry**: Current approach - too fragile for production





