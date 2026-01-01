# Clean Project Workflow  
### Cursor + Cursor Agents

This document defines a **clean, repeatable workflow** for developing software while:
- Preventing junk / trial-and-error files
- Keeping architecture decisions documented
- Using AI tools without polluting the repo
- Making the project easy to understand for new contributors

This workflow is designed to be **shared with teams**.

---

## 1. Core Principles

1. **The repo root stays clean**
2. **Experiments have a designated home**
3. **Architecture decisions are explicit**
4. **AI tools have clear roles**
5. **Only durable knowledge is committed**

---

## 2. Recommended Folder Structure

```
fx-open-range-project/
├── app/                    # Production trading application
├── src/                    # Backtesting framework
├── data/                   # Historical data (gitignored if large)
├── docs/                   # Documentation
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── scratch/                # Temporary experiments (gitignored)
├── sandbox/               # Safe testing area (gitignored)
└── logs/                   # Log files (gitignored)
```

---

## 3. AI Tool Usage Guidelines

### Cursor Built-in AI
- **Primary tool** for code generation, refactoring, and debugging
- Use `Cmd+L` for chat, `Cmd+I` for Composer, `Cmd+K` for inline edits
- No API keys required - uses Cursor's built-in features
- See `docs/AI_QUICK_START.md` for usage guide

### When to Use AI
- ✅ Code generation and refactoring
- ✅ Explaining complex code
- ✅ Debugging errors
- ✅ Code reviews
- ✅ Documentation generation

### When NOT to Use AI
- ❌ Don't commit AI-generated experimental code directly
- ❌ Don't use AI for sensitive data or API keys
- ❌ Don't rely on AI for critical financial calculations without verification

---

## 4. File Organization Rules

### Production Code
- `app/` - Production trading application
- `src/` - Backtesting and analysis framework
- `scripts/` - Utility scripts (must be documented)

### Experimental Code
- `scratch/` - Temporary experiments, can be deleted anytime
- `sandbox/` - Safe testing area for new features
- Both are gitignored - feel free to experiment here

### Documentation
- `docs/` - All project documentation
- Keep README files updated in relevant directories
- Document architectural decisions in `docs/DECISIONS.md`

---

## 5. Commit Workflow

### Before Committing
1. Run cleanup checklist (`docs/CLEANUP.md`)
2. Remove debug prints and commented code
3. Update `docs/CONTEXT.md` if behavior changed
4. Add ADR in `docs/DECISIONS.md` if architecture changed
5. Ensure no files from `scratch/` or `sandbox/` are committed

### Commit Messages
- Use clear, descriptive messages
- Reference issues/PRs if applicable
- Group related changes together

---

## 6. Development Workflow

1. **Plan**: Document decisions in `docs/DECISIONS.md`
2. **Experiment**: Use `scratch/` or `sandbox/` for trials
3. **Implement**: Move to production directories when ready
4. **Test**: Add tests in `tests/`
5. **Document**: Update `docs/CONTEXT.md` and relevant docs
6. **Clean**: Run cleanup checklist before committing

---

## 7. AI Agent Guidelines

When working with Cursor agents:
- Read `docs/CONTEXT.md` first
- Respect `docs/AGENT_CONTRACT.md` rules
- Don't create files in repo root
- Use `scratch/` or `sandbox/` for experiments
- Update documentation when making significant changes

---

## 8. Best Practices

- **Keep it clean**: Remove experimental files regularly
- **Document decisions**: Use ADRs for architectural choices
- **Test thoroughly**: Especially for trading logic
- **Version control**: Commit working, tested code only
- **Security**: Never commit API keys or sensitive data
