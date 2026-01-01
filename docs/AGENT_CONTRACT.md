# Agent Contract

This document defines behavioral rules for AI agents working on this project.

## Core Rules

1. **Read Context First**: Always read `docs/CONTEXT.md` before making changes
2. **Respect Project Structure**: Don't create files in repo root (use `scratch/` or `sandbox/`)
3. **Document Decisions**: Add ADRs in `docs/DECISIONS.md` for architectural changes
4. **Update Context**: Update `docs/CONTEXT.md` when behavior changes significantly
5. **No API Keys**: Don't require or reference external API keys (use Cursor built-in features)

## File Organization

- **Production Code**: `app/`, `src/`, `scripts/`
- **Experiments**: `scratch/`, `sandbox/` (gitignored)
- **Documentation**: `docs/`
- **Data**: `data/` (may be gitignored if large)
- **Tests**: `tests/`

## Code Quality Standards

- Remove debug prints and commented code before committing
- Add tests for new functionality
- Follow existing code style and patterns
- Include docstrings for functions and classes
- Handle errors gracefully with comprehensive error handling and appropriate logging
- Use try/except blocks for all critical operations (API calls, trade execution, data fetching)
- Log errors with appropriate context (use `exc_info=True` for exceptions)

## Trading-Specific Rules

- **Never commit API keys** or sensitive credentials
- **Default to practice mode** in trading applications
- **Prevent lookahead bias** in backtesting (use only past data)
- **Include transaction costs** in backtest calculations
- **Log all trading activity** for audit purposes (file and console logging)
- **Respect trading hours** configuration (22:00-23:00 UTC default for daily open)
- **Handle errors gracefully** in trading operations (don't crash on API failures)
- **Use CLI commands appropriately** (`--once` for testing, `--status` for monitoring)

## Documentation Requirements

- Update relevant README files when adding features
- Document architectural decisions in `docs/DECISIONS.md`
- Keep `docs/CONTEXT.md` current with project status
- Add usage examples for new features

## Testing Requirements

- Test backtesting logic thoroughly (financial correctness critical)
- Test trading engine in practice mode before live
- Verify no lookahead bias in strategy signals
- Test error handling and edge cases

## AI Tool Usage

- Use Cursor's built-in AI (`Cmd+L`, `Cmd+I`, `Cmd+K`)
- Don't create scripts requiring external API keys
- See `docs/AI_QUICK_START.md` for AI usage guidelines
- Keep experiments in `scratch/` or `sandbox/`

## Cleanup Before Committing

- Run `docs/CLEANUP.md` checklist
- Remove experimental files from production directories
- Ensure no files from `scratch/` or `sandbox/` are committed
- Update documentation if needed

## Cursor-Specific Rules

Cursor-specific behavioral rules are defined in Cursor Project Instructions.
Terminal agents should respect them when reasonable.

## Questions?

When in doubt:
1. Check `docs/CONTEXT.md` for project context
2. Review `docs/DECISIONS.md` for architectural guidance
3. Follow existing patterns in the codebase
4. Ask for clarification rather than making assumptions
