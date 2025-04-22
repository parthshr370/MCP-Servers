import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import MCPToolkit # camels implementation of the mcp protocol
from camel.types import ModelPlatformType
from camel.toolkits.mcp_toolkit import MCPClient


# Ensure your Anthropic API key is set in your environment variables
# os.environ["ANTHROPIC_API_KEY"] = "YOUR_ANTHROPIC_API_KEY"
# you can also use your gemini api key here


# Starting the interactive input loop for the camel ai client 
async def interactive_input_loop(agent: ChatAgent):
    loop = asyncio.get_event_loop()
    print("\nEntering interactive mode. Type 'exit' at any prompt to quit.")
# exit conditions 
    while True:
        uri = await loop.run_in_executor(
            None,
            input,
            "\nEnter the URI (http:, https:, file:, data:) to convert to Markdown (or type 'exit'): "
        )
        uri = uri.strip()
        if uri.lower() == "exit":
            print("Exiting interactive mode.")
            break

        if not uri:
            print("URI cannot be empty.")
            continue

        # Prepend file:// scheme if it looks like a local absolute path
        if uri.startswith('/') and not uri.startswith('file://'):
            print(f"Detected local path, prepending 'file://' to URI: {uri}")
            formatted_uri = f"file://{uri}"
        else:
            formatted_uri = uri

        # The prompt clearly tells the agent which tool to use and what the parameter is.
        query = f"Use the convert_to_markdown tool to convert the content at the URI '{formatted_uri}' to Markdown. Do not generate an answer from your internal knowledge, just show the Markdown output from the tool."

        print(f"\nSending query to agent: {query}")
        response = await agent.astep(query)

        print("\nFull Agent Response Info:")
        print(response.info) # Shows tool calls and parameters

        # Check for direct message output first
        if response.msgs and response.msgs[0].content:
            print("\nAgent Output (Markdown):")
            print("-" * 20)
            print(response.msgs[0].content.rstrip())
            print("-" * 20)
        # If no direct message, check if the tool call info is available in response.info
        elif 'tool_calls' in response.info and response.info['tool_calls']:
             print("\nTool Call Response (Raw from info):")
             print("-" * 20)
             found_output = False
             # Iterate through the tool calls list in response.info
             for tool_call in response.info['tool_calls']:
                 # Camel AI structure might place output here (adjust key if needed based on ToolCallingRecord structure)
                 if hasattr(tool_call, 'result') and tool_call.result:
                     print(str(tool_call.result).rstrip())
                     found_output = True
                 # Add other potential output locations if needed

             if not found_output:
                 print("(No tool result found in tool call info)")
             print("-" * 20)
        else:
            print("No output message or tool output received.")


# main funct
async def main(server_transport: str = 'stdio'):
    if server_transport != 'stdio':
        print("Error: This client currently only supports 'stdio' transport.")
        return

    print("Starting MarkItDown MCP server in stdio mode...")
    server_command = sys.executable
    server_args = ["-m", "markitdown_mcp"]

    # Get the root directory of the script (assuming it's in the project root)
    project_root = Path(__file__).resolve().parent

    # Create an MCPClient instance, adding the cwd
    server = MCPClient(
        command_or_url=server_command,
        args=server_args,
        # Set the working directory for the server process
        env={"PYTHONPATH": str(project_root / "packages" / "markitdown-mcp" / "src") + os.pathsep + str(project_root / "packages" / "markitdown" / "src") + os.pathsep + os.environ.get("PYTHONPATH", ""), "CWD": str(project_root)},
        # Optional: timeout=None
    )

    # Pass the MCPClient object in a list
    mcp_toolkit = MCPToolkit(servers=[server])

    print("Connecting to MCP server...")
    async with mcp_toolkit.connection() as toolkit:
        print("Connection successful. Retrieving tools...")
        tools = toolkit.get_tools()
        if not tools:
            print("Error: No tools retrieved from the server. Make sure the server started correctly and defined tools.")
            return
        print(f"Tools retrieved: {[tool.func.__name__ for tool in tools]}")

        # Check if the required tool is available using func.__name__
        if not any(tool.func.__name__ == "convert_to_markdown" for tool in tools):
             print("Error: 'convert_to_markdown' tool not found on the server.")
             return

        sys_msg = (
            "You are a helpful assistant. You have access to an external tool called 'convert_to_markdown' which takes a single argument, 'uri'. "
            "When asked to convert a URI to Markdown, you MUST use this tool by providing the URI to the 'uri' parameter. "
            "Provide ONLY the Markdown output received from the tool, without any additional explanation or introductory text."
        )

        # Ensure GOOGLE_API_KEY is set in environment variables
        # print(f"DEBUG: Value of GOOGLE_API_KEY from os.getenv: {os.getenv('GOOGLE_API_KEY')}")
        api_key = os.getenv("GOOGLE_API_KEY") # Check for GOOGLE_API_KEY
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable not set.") # Update error message
            print("Please set it before running the client.")
            return

        # Configure the model for Google Gemini
        # You might need to install the camel-google extra: pip install camel-ai[google]
        try:
            model = ModelFactory.create(
                model_platform=ModelPlatformType.GEMINI, # Change platform
                # Set the desired Gemini model
                model_type="gemini-2.5-pro-preview-03-25", # Using 1.5 Pro as 2.5 is not yet a valid identifier in CAMEL AI
                api_key=api_key,
                model_config_dict={"temperature": 0.0, "max_tokens": 8192}, # Adjust config if needed
            )
        except Exception as e:
             print(f"Error creating model: {e}")
             print("Ensure you have the necessary dependencies installed (e.g., `pip install camel-ai[google]`)")
             return

        camel_agent = ChatAgent(
            system_message=sys_msg,
            model=model,
            tools=tools,
        )
        camel_agent.reset()
        camel_agent.memory.clear()

        await interactive_input_loop(camel_agent)

if __name__ == "__main__":
    # This client only supports stdio for now
    asyncio.run(main(server_transport='stdio')) 