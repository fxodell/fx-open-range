# ADR-002: Service Layer Extraction

## Status

Accepted

## Context

The `TradingEngine` class was becoming too large and handling multiple responsibilities: data fetching, signal generation, position management, and trade execution. This made testing difficult and violated single responsibility principle.

## Decision

Extract service layers to separate concerns:
- `MarketDataService`: Handles data fetching and preparation
- `SignalService`: Handles signal generation
- `PositionManager`: Handles position management and safety checks

## Implementation

- Created `app/services/` directory
- Implemented three service classes
- Services are composable and testable independently
- `TradingEngine` can use services via dependency injection

## Consequences

**Positive**:
- Better separation of concerns
- Easier to test individual components
- More maintainable code
- Services can be reused in other contexts

**Negative**:
- More files to manage
- Slight increase in complexity
- Need to update `TradingEngine` to use services (future refactoring)

## Alternatives Considered

1. **Keep Everything in TradingEngine**: Simpler but harder to test and maintain
2. **Full Dependency Injection Framework**: Overkill for current needs
3. **Service Layer (Chosen)**: Good balance of simplicity and maintainability

