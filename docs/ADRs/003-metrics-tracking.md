# ADR-003: Metrics Tracking

## Status

Accepted

## Context

Need visibility into trading performance and API health. Without metrics, it's difficult to:
- Monitor win rate
- Track API performance
- Identify issues early
- Make data-driven decisions

## Decision

Implement a simple metrics tracking system that logs key metrics periodically. Use a singleton pattern for global metrics access.

## Implementation

- Created `app/utils/metrics.py` with `TradingMetrics` class
- Tracks: trades, API calls, win rate, P/L, latency
- Thread-safe using locks
- Logs summary periodically
- Integrated into `TradingEngine`

## Consequences

**Positive**:
- Visibility into trading performance
- Early detection of issues
- Data for optimization decisions
- Simple implementation (no external dependencies)

**Negative**:
- In-memory only (lost on restart)
- No historical tracking (could add database later)
- Additional memory usage (minimal)

## Alternatives Considered

1. **External Metrics Service (Prometheus)**: More powerful but requires infrastructure
2. **Database Storage**: Persistent but adds complexity
3. **Simple In-Memory (Chosen)**: Good starting point, can upgrade later

