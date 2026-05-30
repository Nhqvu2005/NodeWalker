#!/bin/bash
# Quick Publish Script for NodeWalker
# Run this after reviewing all changes

set -e

echo "=========================================="
echo "NodeWalker v0.2.0 - Quick Publish Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Are you in the NodeWalker directory?"
    exit 1
fi

echo "✓ Found pyproject.toml"
echo ""

# Step 1: Git initialization
echo "Step 1: Initialize Git Repository"
echo "----------------------------------"
read -p "Initialize git repository? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git init
    git add .
    git commit -m "feat: NodeWalker v0.2.0 - PyPI package + Docker support

- Add PyPI package configuration (pyproject.toml)
- Add Docker support (Dockerfile, docker-compose.yml)
- Add 5 comprehensive examples
- Add connection retry logic with exponential backoff
- Add CI/CD pipeline (GitHub Actions)
- Add complete documentation
- Add MIT License"
    echo "✓ Git repository initialized and committed"
else
    echo "⊘ Skipped git initialization"
fi
echo ""

# Step 2: GitHub remote
echo "Step 2: Add GitHub Remote"
echo "--------------------------"
echo "Create a new repository on GitHub first, then enter the URL:"
read -p "GitHub repository URL (or press Enter to skip): " GITHUB_URL
if [ ! -z "$GITHUB_URL" ]; then
    git remote add origin "$GITHUB_URL"
    git branch -M main
    echo "✓ Remote added: $GITHUB_URL"

    read -p "Push to GitHub now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push -u origin main
        git tag v0.2.0
        git push --tags
        echo "✓ Pushed to GitHub with tag v0.2.0"
    fi
else
    echo "⊘ Skipped GitHub remote"
fi
echo ""

# Step 3: Build package
echo "Step 3: Build Python Package"
echo "-----------------------------"
read -p "Build package for PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if build tools are installed
    if ! python -m build --version &> /dev/null; then
        echo "→ Installing build tools..."
        pip install build twine
    fi

    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/

    # Build
    echo "→ Building package..."
    python -m build

    echo "✓ Package built successfully"
    echo "  Files created:"
    ls -lh dist/
else
    echo "⊘ Skipped package build"
fi
echo ""

# Step 4: Test package locally
echo "Step 4: Test Package Locally"
echo "-----------------------------"
read -p "Test install package locally? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Installing package..."
    pip install dist/nodewalker-0.2.0-py3-none-any.whl --force-reinstall

    echo "→ Testing CLI..."
    nodewalker --help

    echo "✓ Package works locally"
else
    echo "⊘ Skipped local test"
fi
echo ""

# Step 5: Publish to TestPyPI
echo "Step 5: Publish to TestPyPI"
echo "----------------------------"
read -p "Publish to TestPyPI first? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*

    echo "✓ Published to TestPyPI"
    echo "  Test with: pip install --index-url https://test.pypi.org/simple/ nodewalker"
else
    echo "⊘ Skipped TestPyPI"
fi
echo ""

# Step 6: Publish to PyPI
echo "Step 6: Publish to PyPI (Production)"
echo "-------------------------------------"
echo "⚠️  WARNING: This will publish to production PyPI!"
read -p "Publish to production PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Uploading to PyPI..."
    twine upload dist/*

    echo "✓ Published to PyPI"
    echo "  Install with: pip install nodewalker"
    echo "  View at: https://pypi.org/project/nodewalker/"
else
    echo "⊘ Skipped PyPI publication"
fi
echo ""

# Step 7: Docker test
echo "Step 7: Test Docker Build"
echo "--------------------------"
read -p "Test Docker build? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "→ Building Docker image..."
    docker build -t nodewalker:0.2.0 .

    echo "✓ Docker image built"
    echo "  Run with: docker run -p 8585:8585 nodewalker:0.2.0"
else
    echo "⊘ Skipped Docker build"
fi
echo ""

# Summary
echo "=========================================="
echo "✓ Publish Process Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create GitHub release at: $GITHUB_URL/releases/new"
echo "2. Add topics to GitHub repo: browser-automation, ai-agents, python"
echo "3. Announce on social media"
echo "4. Monitor issues and feedback"
echo ""
echo "Documentation:"
echo "- PyPI: https://pypi.org/project/nodewalker/"
echo "- GitHub: $GITHUB_URL"
echo "- Docker Hub: (optional) docker push nhqvu2005/nodewalker:0.2.0"
echo ""
