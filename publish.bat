@echo off
REM Quick Publish Script for NodeWalker (Windows)
REM Run this after reviewing all changes

echo ==========================================
echo NodeWalker v0.2.0 - Quick Publish Script
echo ==========================================
echo.

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo Error: pyproject.toml not found. Are you in the NodeWalker directory?
    exit /b 1
)

echo [OK] Found pyproject.toml
echo.

REM Step 1: Git initialization
echo Step 1: Initialize Git Repository
echo ----------------------------------
set /p INIT_GIT="Initialize git repository? (y/n): "
if /i "%INIT_GIT%"=="y" (
    git init
    git add .
    git commit -m "feat: NodeWalker v0.2.0 - PyPI package + Docker support"
    echo [OK] Git repository initialized and committed
) else (
    echo [SKIP] Skipped git initialization
)
echo.

REM Step 2: GitHub remote
echo Step 2: Add GitHub Remote
echo --------------------------
set /p GITHUB_URL="GitHub repository URL (or press Enter to skip): "
if not "%GITHUB_URL%"=="" (
    git remote add origin "%GITHUB_URL%"
    git branch -M main
    echo [OK] Remote added: %GITHUB_URL%

    set /p PUSH_GIT="Push to GitHub now? (y/n): "
    if /i "!PUSH_GIT!"=="y" (
        git push -u origin main
        git tag v0.2.0
        git push --tags
        echo [OK] Pushed to GitHub with tag v0.2.0
    )
) else (
    echo [SKIP] Skipped GitHub remote
)
echo.

REM Step 3: Build package
echo Step 3: Build Python Package
echo -----------------------------
set /p BUILD_PKG="Build package for PyPI? (y/n): "
if /i "%BUILD_PKG%"=="y" (
    echo Installing build tools...
    pip install build twine

    echo Cleaning previous builds...
    if exist dist rmdir /s /q dist
    if exist build rmdir /s /q build

    echo Building package...
    python -m build

    echo [OK] Package built successfully
    dir dist
) else (
    echo [SKIP] Skipped package build
)
echo.

REM Step 4: Test package locally
echo Step 4: Test Package Locally
echo -----------------------------
set /p TEST_PKG="Test install package locally? (y/n): "
if /i "%TEST_PKG%"=="y" (
    echo Installing package...
    pip install dist\nodewalker-0.2.0-py3-none-any.whl --force-reinstall

    echo Testing CLI...
    nodewalker --help

    echo [OK] Package works locally
) else (
    echo [SKIP] Skipped local test
)
echo.

REM Step 5: Publish to TestPyPI
echo Step 5: Publish to TestPyPI
echo ----------------------------
set /p TEST_PYPI="Publish to TestPyPI first? (recommended) (y/n): "
if /i "%TEST_PYPI%"=="y" (
    echo Uploading to TestPyPI...
    twine upload --repository testpypi dist/*

    echo [OK] Published to TestPyPI
    echo Test with: pip install --index-url https://test.pypi.org/simple/ nodewalker
) else (
    echo [SKIP] Skipped TestPyPI
)
echo.

REM Step 6: Publish to PyPI
echo Step 6: Publish to PyPI (Production)
echo -------------------------------------
echo WARNING: This will publish to production PyPI!
set /p PROD_PYPI="Publish to production PyPI? (y/n): "
if /i "%PROD_PYPI%"=="y" (
    echo Uploading to PyPI...
    twine upload dist/*

    echo [OK] Published to PyPI
    echo Install with: pip install nodewalker
    echo View at: https://pypi.org/project/nodewalker/
) else (
    echo [SKIP] Skipped PyPI publication
)
echo.

REM Step 7: Docker test
echo Step 7: Test Docker Build
echo --------------------------
set /p TEST_DOCKER="Test Docker build? (y/n): "
if /i "%TEST_DOCKER%"=="y" (
    echo Building Docker image...
    docker build -t nodewalker:0.2.0 .

    echo [OK] Docker image built
    echo Run with: docker run -p 8585:8585 nodewalker:0.2.0
) else (
    echo [SKIP] Skipped Docker build
)
echo.

REM Summary
echo ==========================================
echo [OK] Publish Process Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Create GitHub release
echo 2. Add topics to GitHub repo
echo 3. Announce on social media
echo 4. Monitor issues and feedback
echo.

pause
