"""
Anthropic Claude Integration Example

Demonstrates:
- Using NodeWalker with Anthropic Claude
- AI agent controlling the browser via tool use
- Multi-step browser automation
"""

import asyncio
import json
import os
import requests
from anthropic import Anthropic


# NodeWalker server must be running: python -m nodewalker
NODEWALKER_URL = "http://localhost:8585"


def get_nodewalker_tools():
    """Fetch tool schemas from NodeWalker and convert to Claude format."""
    response = requests.get(f"{NODEWALKER_URL}/tools")
    openai_tools = response.json()

    # Convert OpenAI format to Claude format
    claude_tools = []
    for tool in openai_tools:
        func = tool["function"]
        claude_tools.append({
            "name": func["name"],
            "description": func["description"],
            "input_schema": func["parameters"]
        })

    return claude_tools


def execute_tool(tool_name: str, arguments: dict):
    """Execute a NodeWalker tool via HTTP API."""
    response = requests.post(
        f"{NODEWALKER_URL}/execute",
        json={"tool": tool_name, "arguments": arguments}
    )
    return response.json()


async def main():
    """Let Claude control the browser to complete a task."""

    # Check if Anthropic API key is set
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("✗ Error: ANTHROPIC_API_KEY environment variable not set")
        print("  Set it with: export ANTHROPIC_API_KEY='sk-ant-...'")
        return

    client = Anthropic(api_key=api_key)

    # Load NodeWalker tools
    print("→ Loading NodeWalker tools...")
    tools = get_nodewalker_tools()
    print(f"✓ Loaded {len(tools)} tools")

    # Define the task
    task = """
    Go to quotes.toscrape.com, find a quote by Albert Einstein,
    and tell me what it says.
    """

    print(f"\n📋 Task: {task.strip()}")
    print("\n" + "=" * 60)

    # Start conversation with Claude
    messages = [
        {
            "role": "user",
            "content": task
        }
    ]

    max_iterations = 10

    for iteration in range(max_iterations):
        print(f"\n🤖 Claude Iteration {iteration + 1}")

        # Call Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system="You are a browser automation assistant. Use the provided tools to control a web browser and complete user tasks. Be concise and efficient.",
            messages=messages,
            tools=tools
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Claude has finished
            final_text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                None
            )
            if final_text:
                print(f"\n✓ Claude Response:\n{final_text}")
            break

        elif response.stop_reason == "tool_use":
            # Claude wants to use tools
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_args = block.input

                    print(f"  → Calling: {tool_name}({json.dumps(tool_args, indent=2)})")

                    # Execute the tool
                    result = execute_tool(tool_name, tool_args)

                    if result.get("success"):
                        print(f"  ✓ Success")
                    else:
                        print(f"  ✗ Failed: {result.get('error')}")

                    # Collect tool result
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })

            # Add assistant message and tool results to conversation
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": tool_results
            })

        else:
            print(f"\n✗ Unexpected stop reason: {response.stop_reason}")
            break

    print("\n" + "=" * 60)
    print("✓ Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("NodeWalker + Anthropic Claude Integration Example")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Start NodeWalker server: python -m nodewalker")
    print("  2. Set ANTHROPIC_API_KEY environment variable")
    print("  3. Install: pip install anthropic")
    print()

    asyncio.run(main())
