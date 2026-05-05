# Contributing to AI-DLC MCP Server

Thank you for your interest in contributing to the AI-DLC MCP Server! This document provides guidelines for
contributing to the project.

## Development Guidelines

### Steering Rules

Before contributing, please review our comprehensive steering rules that guide development practices:

- **[MCP Server Development](.kiro/steering/mcp-server-development.md)** - Essential guidelines for MCP tools, resources, and architecture
- **[Testing Standards](.kiro/steering/testing-standards.md)** - Comprehensive testing guidelines for dual-workspace architecture
- **[Distinguished Engineer Principles](.kiro/steering/distinguished-engineer-principles.md)** - Code generation principles focused on simplicity
- **[Security Practices](.kiro/steering/security-practices.md)** - Security guidelines for input validation and file operations
- **[Performance Optimization](.kiro/steering/performance-optimization.md)** - Async operations and caching optimization patterns

📖 **Full Steering Rules Index**: [.kiro/steering/README.md](.kiro/steering/README.md)

## Development Setup

1. **Clone the monorepo**
   ```bash
   git clone https://github.com/awslabs/aidlc-workflows.git
   cd aidlc-workflows/aidlc-mcp-server
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Sync rules and install dependencies**
   ```bash
   ./scripts/sync-aidlc-rules.sh   # Copy rules from monorepo root
   pip install -e .[dev]
   ```

## Code Standards

### Quality Gates

All code must pass these quality gates before submission:

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy .

# Run tests
pytest --cov

# Security scan
bandit -r aidlc_mcp_server/
```

### Code Style

- **Line length**: 100 characters (enforced by black)
- **Type hints**: Required for all functions and methods
- **Docstrings**: Required for all public APIs
- **Imports**: Organized with isort (via ruff)

### Architecture

- Follow Clean Architecture principles
- Core domain must not depend on external frameworks
- Use domain-driven design patterns
- Maintain separation between tools, resources, and prompts
- **New**: Simplification services encapsulate LLM orchestration logic (see `core/services/simplification/`)

### System Maintenance

**Pre-commit Cleanup**: Use the comprehensive system cleanup script to maintain a clean development environment:

```bash
# Run comprehensive cleanup before commits
python tmp_files/system_cleanup_script.py

# What gets cleaned:
# - Temporary analysis/summary files (preserves essential files)
# - Cache directories (.mypy_cache, .pytest_cache, .ruff_cache, __pycache__)
# - Build artifacts (*.egg-info, build, dist)
# - Unused directories (mistaken "None" directories)
# - Generates cleanup report for transparency
```

**Essential Files Preserved**:
- `test_simplified_tools.py` - Core functionality test
- `final_checkpoint_validation.py` - System validation
- `system_cleanup_script.py` - The cleanup script itself

## Testing

- Write tests for all new features
- Maintain minimum 80% code coverage (current: 63%)
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Place tests in appropriate directories

### Dual-Workspace Test Architecture

The project uses a dual-workspace test architecture:

- **Core Tests** (`aidlc-mcp-server/tests/`): Rapid feedback (< 30 seconds)
- **Extended Tests** (`aidlc-mcp-server-tests/tests/`): Comprehensive validation (< 45 minutes)

### Test Migration

Use the specialized migration script to maintain the dual-workspace architecture:

```bash
# Migrate property-based, security, and concurrent operations tests
python scripts/migrate_property_security_tests.py
```

This migrates:
- 16 property-based tests (hypothesis-driven validation)
- 1 security test (comprehensive input validation)
- 1 concurrent operations test (scalability validation)
- 2 specialized fixtures (security scanner, load generator)

See [Property-Security Test Migration Guide](docs/guides/property-security-test-migration.md) for details.

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow code standards
   - Add tests
   - Update documentation

3. **Run quality gates**
   ```bash
   ./scripts/lint.sh
   ./scripts/test.sh
   
   # Optional: Clean up temporary files
   python tmp_files/system_cleanup_script.py
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   Use conventional commits format: `type(scope): description`

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements**
   - All quality gates pass
   - Tests added for new features
   - Documentation updated
   - No breaking changes without discussion

## Commit Message Format

Use conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's technical standards
