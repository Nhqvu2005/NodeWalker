FROM python:3.11-slim

# Install Chrome and dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY nodewalker/ ./nodewalker/
COPY browser_config.json .
COPY README.md .
COPY TOOLS.md .

# Create a non-root user for running Chrome
RUN useradd -m -s /bin/bash nodewalker && \
    chown -R nodewalker:nodewalker /app

USER nodewalker

# Expose ports
# 8585: NodeWalker HTTP API
# 9222: Chrome DevTools Protocol
EXPOSE 8585 9222

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8585/health')"

# Start Chrome in background, then start NodeWalker
CMD google-chrome-stable \
    --remote-debugging-port=9222 \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --headless=new \
    --disable-software-rasterizer \
    --disable-extensions \
    --no-first-run \
    --no-default-browser-check \
    about:blank & \
    sleep 3 && \
    python -m nodewalker --host 0.0.0.0 --port 8585 --debug-port 9222
