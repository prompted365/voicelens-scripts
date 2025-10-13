# Contributing to VoiceLens Scripts

We love your input! We want to make contributing to VoiceLens Scripts as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows our style guidelines
6. Issue that pull request!

## Code Style

We use automated formatting and linting:

- **Black** for code formatting
- **isort** for import sorting  
- **Ruff** for fast linting
- **mypy** for type checking

Run these before submitting:

```bash
make lint    # Run all checks
make format  # Auto-format code
```

## Testing

We use pytest for testing:

```bash
make test              # Run all tests
make test-coverage     # Run with coverage report
```

### Test Structure

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`  
- Fixtures in `tests/fixtures/`

All tests should be fast and deterministic. Use temporary SQLite databases for integration tests.

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding/updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements

Examples:
```
feat(generator): add support for multi-language scenarios
fix(classifier): handle edge case in agent role detection  
docs(readme): update installation instructions
```

## Pull Request Process

1. Update README.md or docs/ with details of changes if applicable
2. Add tests for new functionality
3. Ensure all status checks pass
4. Get approval from at least one maintainer
5. Squash and merge when ready

## Bug Reports

Use GitHub Issues with the bug report template. Include:

- Your operating system and Python version
- Exact command that caused the issue
- Full error message and stack trace
- Steps to reproduce
- Expected vs actual behavior

## Feature Requests  

Use GitHub Issues with the feature request template. Include:

- Clear description of the problem you're solving
- Proposed solution and alternatives considered
- Example usage/API if applicable
- Impact on existing functionality

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/voicelens-scripts.git
cd voicelens-scripts

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
make test
```

## Project Structure

```
voicelens-scripts/
├── src/voicelens_seeder/     # Main package
│   ├── cli.py                # CLI entry point
│   ├── config/               # Configuration management
│   ├── db/                   # Database schema & migrations
│   ├── generator/            # Synthetic data generation
│   ├── normalizers/          # VCP payload processing
│   ├── classifiers/          # Agent role detection
│   └── utils/               # Common utilities
├── tests/                   # Test suite
├── docs/                    # Documentation
└── examples/               # Example data & configs
```

## Performance Guidelines

- Use batch database operations where possible
- Profile performance-critical code paths
- Avoid loading large datasets into memory
- Use appropriate SQLite pragmas and indexes

## Documentation

- Update docstrings for public APIs
- Include usage examples in docstrings
- Update relevant docs/ files
- Add CLI help text for new commands

## Questions?

Feel free to open a Discussion or reach out to the maintainers. We're here to help!