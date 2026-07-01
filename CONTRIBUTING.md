# Contributing to GuardWeave

Thank you for your interest in contributing to GuardWeave! We welcome contributions from everyone.

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### 1. Reporting Issues

- **Bug reports**: Include your OS, Python version, GuardWeave version, and steps to reproduce
- **Feature requests**: Describe the use case and why it's important
- **Security issues**: Email maintainers directly (see SECURITY.md)

### 2. Setting Up Development

```bash
git clone https://github.com/anomalyco/guardweave.git
cd guardweave
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### 3. Development Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linting: `ruff check src/`
5. Run type checking: `mypy src/`
6. Commit using conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, etc.
7. Push and open a pull request

### 4. Pull Request Guidelines

- Keep PRs focused on a single change
- Add tests for new functionality
- Update documentation as needed
- Ensure all CI checks pass
- Request review from maintainers

### 5. Coding Standards

- Python 3.12+ only
- Type hints required for all public APIs
- Async-first for all I/O operations
- Docstrings for all public modules, classes, and functions
- Follow existing code patterns and naming conventions

### 6. Testing

- Write tests for all new features
- Aim for >80% code coverage
- Run the full test suite before submitting:
  ```bash
  pytest --cov=guardweave tests/
  ```

### 7. Documentation

- Update README.md if adding new features
- Add or update docs in `docs/` directory
- Include inline code examples

## Project Structure

```
src/guardweave/
├── api/           # FastAPI REST API
├── cli/           # CLI commands
├── core/          # Core models and enums
├── dashboard/     # Gradio dashboard
├── engine/        # Policy evaluation
├── audit/         # Audit logging
├── hitl/          # Human-in-the-loop
├── sandbox/       # Execution sandbox
├── sdk/           # Python SDK
└── persistence/   # Data storage
```

## Release Process

1. Update version in `src/guardweave/__version__.py`
2. Update CHANGELOG.md
3. Create a GitHub release with release notes

## Questions?

Open a [Discussion](https://github.com/anomalyco/guardweave/discussions) or join our community chat (coming soon).
