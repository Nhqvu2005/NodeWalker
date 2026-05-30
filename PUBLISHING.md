# Publishing NodeWalker to PyPI

This guide explains how to build and publish NodeWalker to PyPI.

## Prerequisites

```bash
pip install build twine
```

## Build the Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build wheel and source distribution
python -m build
```

This creates:
- `dist/nodewalker-0.2.0-py3-none-any.whl` (wheel)
- `dist/nodewalker-0.2.0.tar.gz` (source)

## Test Locally

```bash
# Install from local wheel
pip install dist/nodewalker-0.2.0-py3-none-any.whl

# Test the CLI
nodewalker --help

# Uninstall
pip uninstall nodewalker
```

## Publish to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ nodewalker
```

## Publish to PyPI (Production)

```bash
# Upload to PyPI
twine upload dist/*

# Verify
pip install nodewalker
```

## Post-Publishing Checklist

- [ ] Test `pip install nodewalker` on clean environment
- [ ] Verify CLI works: `nodewalker --help`
- [ ] Check PyPI page: https://pypi.org/project/nodewalker/
- [ ] Update GitHub release with changelog
- [ ] Announce on social media / forums

## Version Bumping

Before next release:

1. Update version in `pyproject.toml`
2. Update version in `nodewalker/__init__.py`
3. Update version in `nodewalker/__main__.py` banner
4. Update version in `nodewalker/server.py`
5. Add entry to `CHANGELOG.md`
6. Git tag: `git tag v0.2.0 && git push --tags`

## Troubleshooting

**Error: "File already exists"**
- You're trying to upload the same version twice
- Bump version number in `pyproject.toml`

**Error: "Invalid credentials"**
- Run `twine upload` with `--username __token__ --password <your-token>`
- Or configure `~/.pypirc`:
  ```ini
  [pypi]
  username = __token__
  password = pypi-...
  ```

**Import errors after install**
- Check `[tool.setuptools]` packages list in `pyproject.toml`
- Ensure all subpackages are included
