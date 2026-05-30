# Changelog

All notable changes to NodeWalker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-30

### Added
- **PyPI Package Support**: Added `pyproject.toml` for pip installation
- **Docker Support**: Added Dockerfile and docker-compose.yml for containerized deployment
- **Examples**: Added 5 comprehensive examples demonstrating various use cases
  - Basic navigation and screenshot
  - Form filling automation
  - Web scraping with pagination
  - OpenAI GPT-4 integration
  - Anthropic Claude integration
- **Retry Logic**: Connection retry with exponential backoff (3 attempts)
- **Documentation**: Added DOCKER.md, PUBLISHING.md, and examples/README.md
- **License**: Added MIT License

### Changed
- Improved server startup with better error messages
- Enhanced connection reliability with retry mechanism

### Fixed
- Connection timeout issues on slow systems
- Browser launch race conditions

## [0.1.0] - 2024-03-09

### Added
- Initial release
- Chrome DevTools Protocol (CDP) client
- 27 browser control tools
- FastAPI HTTP server
- OpenAI-compatible tool schemas
- Auto browser launcher with multi-browser support
- Console and network log capture
- Page snapshot with accessibility tree
- Reference-based element interaction
