import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import MCPToolkit
from camel.types import ModelPlatformType
from camel.toolkits.mcp_toolkit import _MCPServer

load_dotenv()

# Set your Anthropic API key (ensure this is valid).
os.environ["ANTHROPIC_API_KEY"] = # anthropic api key defined 0


async def interactive_input_loop(agent: ChatAgent):
    loop = asyncio.get_event_loop()
    print("\nEntering interactive mode. Type 'exit' at any prompt to quit.")

    while True:
        choice = await loop.run_in_executor(
            None,
            input,
            "\nChoose an action (Type 'exit' to end loop or press Enter to use current directory):\n"
            "1. Read a file\n"
            "2. List a directory\nYour choice (1/2): "
        )
        choice = choice.strip().lower()
        if choice == "exit":
            print("Exiting interactive mode.")
            break

        if choice == "1":
            file_path = await loop.run_in_executor(
                None,
                input,
                "Enter the file path to read (default: README.md): "
            )
            file_path = file_path.strip() or "README.md"
            query = f"Use the read_file tool to display the content of {file_path}. Do not generate an answer from your internal knowledge."
        elif choice == "2":
            dir_path = await loop.run_in_executor(
                None,
                input,
                "Enter the directory path to list (default: .): "
            )
            dir_path = dir_path.strip() or "."
            query = f"Call the list_directory tool to show me all files in {dir_path}. Do not answer directly."
        else:
            print("Invalid choice. Please enter 1 or 2.")
            continue

        response = await agent.astep(query)
        print(f"\nYour Query: {query}")
        print("Full Agent Response:")
        print(response.info)
        if response.msgs and response.msgs[0].content:
            print("Agent Output:")
            print(response.msgs[0].content.rstrip())
        else:
            print("No output received.")

async def main(server_transport: str = 'stdio'):
    if server_transport == 'stdio':
        # Assuming both files are in the same folder structure, determine the path to the server file.
        server_script_path = Path(__file__).resolve().parent / "filesystem_server_mcp.py"
        if not server_script_path.is_file():
            print(f"Error: Server script not found at {server_script_path}")
            return
        # Create an _MCPServer instance for our filesystem server.
        server = _MCPServer(
            command_or_url=sys.executable,
            args=[str(server_script_path)]
        )
        mcp_toolkit = MCPToolkit(servers=[server])
    else:
        mcp_toolkit = MCPToolkit("tcp://localhost:5000")

    async with mcp_toolkit.connection() as toolkit:
        tools = toolkit.get_tools()
        sys_msg = (
            "You are a helpful assistant. Always use the provided external tools for filesystem operations "
            "and answer filesystem-related questions using these tools."
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.ANTHROPIC,
            model_type="claude-3-7-sonnet-20250219",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model_config_dict={"temperature": 0.8, "max_tokens": 4096},
        )
        camel_agent = ChatAgent(
            system_message=sys_msg,
            model=model,
            tools=tools,
        )
        camel_agent.reset()
        camel_agent.memory.clear()
        await interactive_input_loop(camel_agent)

if __name__ == "__main__":
    asyncio.run(main())
