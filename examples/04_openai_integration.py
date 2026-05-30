"""
OpenAI Integration Example

Demonstrates:
- Using NodeWalker with OpenAI function calling
- AI agent controlling the browser
- Multi-step browser automation via LLM
"""

import asyncio
import json
import os
import requests
from openai import OpenAI


# NodeWalker server must be running: python -m nodewalker
NODEWALKER_URL = "http://localhost:8585"


def get_nodewalker_tools():
    """Fetch tool schemas from NodeWalker server."""
    response = requests.get(f"{NODEWALKER_URL}/tools")
    return response.json()


def execute_tool(tool_name: str, arguments: dict):
    """Execute a NodeWalker tool via HTTP API."""
    response = requests.post(
        f"{NODEWALKER_URL}/execute",
        json={"tool": tool_name, "arguments": arguments}
    )
    return response.json()


async def main():
    """Let OpenAI control the browser to complete a task."""

    # Check if OpenAI API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("✗ Error: OPENAI_API_KEY environment variable not set")
        print("  Set it with: export OPENAI_API_KEY='sk-...'")
        return

    client = OpenAI(api_key=api_key)

    # Load NodeWalker tools
    print("→ Loading NodeWalker tools...")
    tools = get_nodewalker_tools()
    print(f"✓ Loaded {len(tools)} tools")

    # Define the task
    task = """
    Go to example.com, take a screenshot, and tell me what the main heading says.
    """

    print(f"\n📋 Task: {task.strip()}")
    print("\n" + "=" * 60)

    # Start conversation with OpenAI
    messages = [
        {
            "role": "system",
            "content": "You are a browser automation assistant. Use the provided tools to control a web browser and complete user tasks."
        },
        {
            "role": "user",
            "content": task
        }
    ]

    max_iterations = 10

    for iteration in range(max_iterations):
        print(f"\n🤖 AI Iteration {iteration + 1}")

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Check if AI wants to call a tool
        if message.tool_calls:
            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  → Calling: {tool_name}({json.dumps(tool_args, indent=2)})")

                # Execute the tool
                result = execute_tool(tool_name, tool_args)

                if result.get("success"):
                    print(f"  ✓ Success")
                else:
                    print(f"  ✗ Failed: {result.get('error')}")

                # Add tool call and result to conversation
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call.model_dump()]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # Check if AI has a final answer
        elif message.content:
            print(f"\n✓ AI Response:\n{message.content}")
            break

        else:
            print("\n✗ Unexpected response from AI")
            break

    print("\n" + "=" * 60)
    print("✓ Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("NodeWalker + OpenAI Integration Example")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  1. Start NodeWalker server: python -m nodewalker")
    print("  2. Set OPENAI_API_KEY environment variable")
    print()

    asyncio.run(main())
