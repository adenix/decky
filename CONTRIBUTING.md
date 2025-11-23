# Contributing to Decky

First off, thank you for considering contributing to Decky! It's people like you that make Decky such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide your configuration file** (redact sensitive info)
- **Include logs** from `decky logs` or `journalctl --user -u decky`
- **Describe the expected behavior**
- **Include screenshots** if applicable
- **Specify your environment** (OS, Python version, Stream Deck model, DE)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Provide specific examples** to demonstrate the enhancement
- **Describe the current behavior** and **explain the expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Install pre-commit hooks**: `pre-commit install`
3. **Make your changes** following the coding standards below
4. **Add tests** if you've added code that should be tested
5. **Ensure the test suite passes**: `pytest`
6. **Format your code**: `black src/ tests/`
7. **Run linters**: `flake8 src/`
8. **Update documentation** if needed
9. **Write a good commit message**
10. **Submit that pull request**!

## Development Setup

### Prerequisites

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install python3-pip python3-venv libhidapi-libusb0 libhidapi-dev

# Clone the repository
git clone https://github.com/yourusername/decky.git
cd decky

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/decky --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_actions.py

# Run specific test
pytest tests/unit/test_actions.py::TestCommandAction::test_execute_command_success
```

### Code Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/

# Type check
mypy src/decky

# Security scan
bandit -r src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these specifics:

- **Line length**: 100 characters
- **Formatting**: Black (automatically handled)
- **Import sorting**: isort with Black profile
- **Type hints**: Required for all public methods
- **Docstrings**: Google style for all classes and public methods

### Example

```python
from typing import Dict, Any, Optional


class MyAction(BaseAction):
    """
    Brief description of the action.

    Longer description if needed, explaining the purpose
    and any important details.
    """

    action_type = "my_action"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        """
        Execute the action.

        Args:
            context: Execution context with controller and platform info
            config: Action configuration from YAML

        Returns:
            True if successful, False otherwise
        """
        # Implementation
        return True

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate action configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        return "required_param" in config
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools
- `ci`: Changes to CI configuration

**Examples**:
```
feat(actions): add URL action type for opening web pages

fix(controller): prevent reconnection during shutdown

docs(readme): update installation instructions for Arch Linux

test(actions): add tests for application launcher fallback
```

### Testing Guidelines

1. **Write tests for all new features**
2. **Maintain test coverage above 80%**
3. **Use descriptive test names** that explain what's being tested
4. **Use fixtures** from `conftest.py` for common test data
5. **Mock external dependencies** (subprocess, file I/O, USB devices)
6. **Write both positive and negative test cases**

### Adding New Actions

To add a new action type:

1. **Create a new file** in `src/decky/actions/` (e.g., `myaction.py`)
2. **Inherit from `BaseAction`**
3. **Define `action_type`** class variable
4. **Implement `execute()` method**
5. **Implement `validate_config()` if needed**
6. **Add tests** in `tests/unit/test_actions.py`
7. **Document** in README.md action types section
8. **Add example** in example configs

Example:
```python
# src/decky/actions/myaction.py
from .base import BaseAction, ActionContext
from typing import Dict, Any

class MyAction(BaseAction):
    action_type = "my_action"

    def execute(self, context: ActionContext, config: Dict[str, Any]) -> bool:
        # Your implementation
        return True
```

The action will be automatically discovered and registered!

## Project Structure

```
decky/
├── src/decky/           # Source code
│   ├── actions/         # Action plugins
│   ├── config/          # Configuration handling
│   ├── device/          # Stream Deck device interface
│   ├── platforms/       # Platform-specific code
│   ├── controller.py    # Main orchestrator
│   ├── main.py          # Entry point
│   └── cli.py           # CLI tool
├── tests/               # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test fixtures
├── configs/             # Example configurations
└── .github/             # CI/CD workflows
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples to `configs/` directory
- Update REVIEW.md if fixing issues from the review

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

