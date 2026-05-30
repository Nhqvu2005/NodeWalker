# Contributing to NodeWalker

Thank you for your interest in contributing to NodeWalker! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Use the latest version of NodeWalker
3. Verify the bug is reproducible

When reporting:
- Describe the expected vs actual behavior
- Provide minimal reproduction steps
- Include your environment (OS, Python version, Chrome version)
- Add relevant logs or screenshots

### Suggesting Features

Feature requests are welcome! Please:
- Explain the use case and motivation
- Describe the proposed solution
- Consider alternative approaches
- Check if it aligns with NodeWalker's scope (lightweight, AI-focused)

### Pull Requests

1. **Fork and clone** the repository
2. **Create a branch** for your feature/fix
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow existing code style
   - Add tests if applicable
   - Update documentation
4. **Test your changes**
   ```bash
   pytest tests/
   ```
5. **Commit with clear messages**
   ```bash
   git commit -m "Add feature: description"
   ```
6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Development Setup

```bash
# Clone repository
git clone https://github.com/Nhqvu2005/NodeWalker.git
cd NodeWalker

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-asyncio black ruff

# Run tests
pytest tests/

# Format code
black nodewalker/
ruff check nodewalker/
```

## Code Style

- Follow PEP 8
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings for public APIs
- Use descriptive variable names

Example:
```python
async def navigate(self, url: str, wait_for_load: bool = True) -> dict:
    """Navigate the browser to a URL.
    
    Args:
        url: The URL to navigate to.
        wait_for_load: Whether to wait for page load event.
        
    Returns:
        Dict with success status, url, and title.
    """
    # Implementation
```

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for high coverage on core functionality
- Use pytest fixtures for common setup

```python
import pytest
from nodewalker import BrowserController

@pytest.mark.asyncio
async def test_navigate():
    async with BrowserController() as browser:
        result = await browser.navigate("https://example.com")
        assert result["success"] is True
        assert "example.com" in result["url"]
```

## Documentation

- Update README.md for user-facing changes
- Update TOOLS.md for new tools
- Add examples for significant features
- Keep docstrings up to date

## Project Structure

```
nodewalker/
├── nodewalker/
│   ├── __init__.py          # Public API exports
│   ├── __main__.py          # CLI entry point
│   ├── server.py            # FastAPI server
│   ├── core/
│   │   ├── cdp_client.py    # Low-level CDP client
│   │   ├── actions.py       # High-level browser actions
│   │   └── browser_launcher.py  # Auto browser launcher
│   └── tools/
│       ├── schemas.py       # Tool definitions
│       └── executor.py      # Tool dispatcher
├── tests/                   # Test suite
├── examples/                # Usage examples
└── docs/                    # Documentation
```

## Adding a New Tool

1. **Define the schema** in `nodewalker/tools/schemas.py`:
```python
{
    "type": "function",
    "function": {
        "name": "your_tool",
        "description": "What it does",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "..."}
            },
            "required": ["param"]
        }
    }
}
```

2. **Implement the action** in `nodewalker/core/actions.py`:
```python
async def your_tool(self, param: str) -> dict:
    """Implementation."""
    # Your code here
    return {"success": True, "result": ...}
```

3. **Add dispatcher** in `nodewalker/tools/executor.py`:
```python
async def _your_tool(self, args: dict) -> dict:
    return await self.browser.your_tool(param=args["param"])
```

4. **Register in executor**:
```python
self._action_map = {
    # ...
    "your_tool": self._your_tool,
}
```

5. **Write tests** in `tests/test_your_tool.py`

6. **Update TOOLS.md** with usage documentation

## Release Process

1. Update version in:
   - `pyproject.toml`
   - `nodewalker/__init__.py`
   - `nodewalker/__main__.py`
   - `nodewalker/server.py`

2. Update `CHANGELOG.md`

3. Create git tag:
   ```bash
   git tag v0.2.0
   git push --tags
   ```

4. Build and publish:
   ```bash
   python -m build
   twine upload dist/*
   ```

## Questions?

- Open an issue for questions
- Join discussions in GitHub Discussions
- Check existing documentation first

Thank you for contributing! 🚀
