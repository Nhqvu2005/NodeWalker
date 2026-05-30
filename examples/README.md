# NodeWalker Examples

This directory contains practical examples demonstrating NodeWalker's capabilities.

## Prerequisites

All examples require:
1. **Chrome running with remote debugging**:
   ```bash
   chrome --remote-debugging-port=9222
   ```

2. **NodeWalker installed**:
   ```bash
   pip install -r ../requirements.txt
   ```

## Examples

### 1. Basic Navigation (`01_basic_navigation.py`)
**What it does**: Navigate to a website, extract text, take screenshot

**Run**:
```bash
python 01_basic_navigation.py
```

**Learn**:
- Connecting to Chrome via CDP
- Basic navigation
- Screenshot capture
- Text extraction

---

### 2. Form Filling (`02_form_filling.py`)
**What it does**: Automate login form submission

**Run**:
```bash
python 02_form_filling.py
```

**Learn**:
- Finding elements with CSS selectors
- Typing text into inputs
- Clicking buttons
- Waiting for elements

---

### 3. Web Scraping (`03_web_scraping.py`)
**What it does**: Scrape quotes from multiple pages and save to JSON

**Run**:
```bash
python 03_web_scraping.py
```

**Learn**:
- Multi-page navigation
- JavaScript evaluation for data extraction
- Pagination handling
- Structured data export

---

### 4. OpenAI Integration (`04_openai_integration.py`)
**What it does**: Let GPT-4 control the browser via function calling

**Prerequisites**:
- Start NodeWalker server: `python -m nodewalker`
- Set API key: `export OPENAI_API_KEY='sk-...'`
- Install: `pip install openai`

**Run**:
```bash
python 04_openai_integration.py
```

**Learn**:
- OpenAI function calling with NodeWalker
- AI-driven browser automation
- Tool execution via HTTP API

---

### 5. Claude Integration (`05_claude_integration.py`)
**What it does**: Let Claude control the browser via tool use

**Prerequisites**:
- Start NodeWalker server: `python -m nodewalker`
- Set API key: `export ANTHROPIC_API_KEY='sk-ant-...'`
- Install: `pip install anthropic`

**Run**:
```bash
python 05_claude_integration.py
```

**Learn**:
- Anthropic Claude tool use with NodeWalker
- Converting OpenAI schemas to Claude format
- Multi-turn AI conversations with tools

---

## Running with NodeWalker Server

Examples 4 and 5 require the NodeWalker HTTP server:

```bash
# Terminal 1: Start NodeWalker server
python -m nodewalker

# Terminal 2: Run the example
python 04_openai_integration.py
```

## Customizing Examples

All examples are self-contained and can be modified:

- Change URLs in navigation examples
- Adjust selectors for different websites
- Modify AI prompts for different tasks
- Add error handling and retries

## Troubleshooting

**"Connection refused"**
- Make sure Chrome is running with `--remote-debugging-port=9222`
- Check if port 9222 is already in use

**"Element not found"**
- Website structure may have changed
- Try inspecting the page and updating CSS selectors

**"API key not set"**
- Set environment variable: `export OPENAI_API_KEY='...'`
- Or add to your shell profile (~/.bashrc, ~/.zshrc)

**"Module not found"**
- Install dependencies: `pip install -r ../requirements.txt`
- For AI examples: `pip install openai anthropic`

## Next Steps

- Read [TOOLS.md](../TOOLS.md) for complete tool reference
- Check [README.md](../README.md) for API documentation
- Build your own automation scripts!
