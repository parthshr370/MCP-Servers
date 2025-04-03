#!/usr/bin/env python
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2023-2024 @ CAMEL-AI.org. All Rights Reserved. =========

"""
Example run script for the Google Forms MCP Server

This script demonstrates creating and managing Google Forms through the MCP Server.
It performs a series of operations that test all the functionality of the server.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import argparse
from typing import Optional

from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits import MCPToolkit
from camel.types import ModelPlatformType

# Load environment variables from .env file
load_dotenv()

# Set your Anthropic API key (ensure this is valid in your .env file)
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# Check if the necessary credentials file exists
def check_credentials():
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json not found!")
        print("Please follow these steps to set up Google Forms API access:")
        print("1. Go to https://console.developers.google.com/")
        print("2. Create a new project or select an existing one")
        print("3. Enable the Google Forms API, Google Drive API, and Google Sheets API")
        print("4. Create credentials (OAuth client ID) for a desktop application")
        print("5. Download the credentials JSON file and save it as 'credentials.json' in this directory")
        return False
    return True

# Function to print nicely formatted JSON responses
def print_response(title, response):
    try:
        json_data = json.loads(response)
        print(f"\n{title}:")
        print(json.dumps(json_data, indent=2))
    except:
        print(f"\n{title}:")
        print(response)

# Automated test run that demonstrates all features
async def run_automated_test(tools):
    print("\n==== Google Forms MCP Server Automated Test ====")
    print("This test will demonstrate all functionalities of the Google Forms MCP Server")
    
    try:
        # Step 1: Create a new form
        print("\n--- Step 1: Creating a new form ---")
        create_form_response = await tools["create_form"](
            title="Customer Satisfaction Survey",
            description="Help us improve our services by providing your feedback"
        )
        print_response("Form created", create_form_response)
        
        # Extract form ID for further operations
        form_data = json.loads(create_form_response)
        form_id = form_data["form_id"]
        
        # Step 2: Modify form settings
        print("\n--- Step 2: Modifying form settings ---")
        settings_response = await tools["modify_form_settings"](
            form_id=form_id,
            collect_email=True,
            limit_responses=True
        )
        print_response("Form settings updated", settings_response)
        
        # Step 3: Add a section
        print("\n--- Step 3: Adding a section ---")
        section_response = await tools["add_section"](
            form_id=form_id,
            title="About Your Experience",
            description="Please tell us about your recent experience with our product/service"
        )
        print_response("Section added", section_response)
        
        # Step 4: Add multiple choice question
        print("\n--- Step 4: Adding a multiple choice question ---")
        mc_response = await tools["add_multiple_choice"](
            form_id=form_id,
            question_text="How would you rate our service?",
            choices=["Excellent", "Good", "Average", "Poor", "Very Poor"],
            required=True,
            help_text="Please select one option"
        )
        print_response("Multiple choice question added", mc_response)
        
        # Step 5: Add a checkbox question
        print("\n--- Step 5: Adding a checkbox question ---")
        checkbox_response = await tools["add_checkboxes"](
            form_id=form_id,
            question_text="Which aspects of our service did you appreciate?",
            choices=["Responsiveness", "Quality", "Value for money", "Customer support", "Other"],
            required=False,
            help_text="Select all that apply"
        )
        print_response("Checkbox question added", checkbox_response)
        
        # Step 6: Add a dropdown question
        print("\n--- Step 6: Adding a dropdown question ---")
        dropdown_response = await tools["add_dropdown"](
            form_id=form_id,
            question_text="How often do you use our service?",
            choices=["Daily", "Weekly", "Monthly", "Quarterly", "Yearly", "First time"],
            required=True
        )
        print_response("Dropdown question added", dropdown_response)
        
        # Step 7: Add a short answer question
        print("\n--- Step 7: Adding a short answer question ---")
        short_answer_response = await tools["add_short_answer"](
            form_id=form_id,
            question_text="What is your customer ID?",
            required=False,
            help_text="Please enter your customer ID if you have one"
        )
        print_response("Short answer question added", short_answer_response)
        
        # Step 8: Add a paragraph question
        print("\n--- Step 8: Adding a paragraph question ---")
        paragraph_response = await tools["add_paragraph"](
            form_id=form_id,
            question_text="Do you have any suggestions for improvement?",
            required=False,
            help_text="Please share any ideas on how we can serve you better"
        )
        print_response("Paragraph question added", paragraph_response)
        
        # Step 9: Add a file upload question
        print("\n--- Step 9: Adding a file upload question ---")
        file_upload_response = await tools["add_file_upload"](
            form_id=form_id,
            question_text="Would you like to upload any relevant documents?",
            required=False,
            help_text="You can upload screenshots or other documents"
        )
        print_response("File upload question added", file_upload_response)
        
        # Step 10: Add another section
        print("\n--- Step 10: Adding another section ---")
        section2_response = await tools["add_section"](
            form_id=form_id,
            title="Additional Information",
            description="Help us personalize our services"
        )
        print_response("Another section added", section2_response)
        
        # Step 11: List all forms
        print("\n--- Step 11: Listing all forms ---")
        list_forms_response = await tools["list_forms"]()
        print_response("Forms list", list_forms_response)
        
        # Step 12: Export responses (might not have any responses yet)
        print("\n--- Step 12: Setting up response export ---")
        export_response = await tools["export_responses"](
            form_id=form_id,
            format="sheets"
        )
        print_response("Export setup", export_response)
        
        # Step 13: Try to get responses (likely empty, but tests the functionality)
        print("\n--- Step 13: Getting responses ---")
        responses = await tools["get_responses"](
            form_id=form_id
        )
        print_response("Form responses", responses)
        
        print("\n=== Test completed successfully! ===")
        print(f"Created form can be viewed at: {form_data['view_url']}")
        print(f"Created form can be edited at: {form_data['edit_url']}")
        
    except Exception as e:
        print(f"\nError during test: {str(e)}")
        raise

# Interactive mode function to chat with the agent
async def interactive_input_loop(agent: ChatAgent):
    loop = asyncio.get_event_loop()
    print("\n==== Google Forms Assistant Interactive Mode ====")
    print("Type 'exit' at any prompt to quit.")
    print("\nSample queries you can try:")
    print("- Create a new feedback form")
    print("- Add a customer satisfaction survey with multiple choice questions")
    print("- List all my forms")
    print("- Create a job application form with sections for personal info, education, and experience")
    print("- Export responses from a form to CSV")
    print("======================================")

    while True:
        query = await loop.run_in_executor(
            None, 
            input, 
            "\nEnter your query (or type 'exit' to quit): "
        )
        
        if query.lower() == 'exit':
            print("Exiting interactive mode.")
            break
        
        print("\nProcessing query...")
        response = await agent.astep(query)
        
        print("\nAgent Response:")
        if response.msgs and response.msgs[0].content:
            print(response.msgs[0].content.rstrip())
        else:
            print("No output received.")

# Main function to run the entire example
async def main(server_transport: str = 'stdio', mode: str = 'automated', 
             server_url: Optional[str] = None):
    # First check if credentials exist
    if not check_credentials():
        return
        
    mcp_toolkit = None
    server_process = None
    
    try: # Wrap setup and execution in try
        # Configure based on transport type
        if server_transport == 'stdio':
            # Original stdio logic (may still deadlock, but kept for reference)
            print("Using stdio transport (Note: May cause deadlock during auth)")
            current_dir = Path(__file__).resolve().parent
            server_script_path = current_dir / "google_forms_server_mcp.py"
            
            print(f"Looking for server script at: {server_script_path}")
            print(f"Directory contents: {[f.name for f in current_dir.iterdir() if f.is_file()]}")
            
            if not server_script_path.is_file():
                print(f"Error: Server script not found at {server_script_path}")
                return
                
            # Use the _MCPServer helper for stdio 
            from camel.toolkits.mcp_toolkit import _MCPServer # Import locally
            server_process = _MCPServer([sys.executable, str(server_script_path), "stdio"])
            await server_process.start()
            mcp_toolkit = MCPToolkit(mcp_server_process=server_process)
            print("MCP Server started via stdio.")
            
        elif server_transport == 'sse':
            # SSE logic: Connect to an existing HTTP/SSE server
            if not server_url:
                print("Error: --server-url is required for SSE transport.")
                print("Example: python google_forms_example_run.py --transport sse --server-url http://127.0.0.1:8000")
                return
                
            print(f"Connecting to MCP Server via SSE at: {server_url}")
            mcp_toolkit = MCPToolkit(servers=[server_url])
            # Move the connection test inside the 'async with' block
            
        else:
            print(f"Error: Unsupported server transport: {server_transport}")
            return

        # Initialize the LLM model
        # Reverting to model_config_dict based on user example, and adding api_key explicitly
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
             print("Error: ANTHROPIC_API_KEY not found in environment variables or .env file.")
             # Decide how to handle missing key - raise error or return
             return # Or raise ValueError("Missing Anthropic API Key")

        model = ModelFactory.create(
            model_platform=ModelPlatformType.ANTHROPIC,
            model_type="claude-3-haiku-20240307", # Use a suitable Anthropic model
            # temperature=0.0 # Replaced by model_config_dict
            api_key=anthropic_api_key, # Explicitly pass API key
            model_config_dict={"temperature": 0.0} # Use the dict from user example
        )

        # Main execution block within the try
        async with mcp_toolkit.connection() as toolkit:
            # Test connection *after* establishing context
            try:
                await toolkit.list_tools() # Use toolkit here
                print("Successfully connected to WebSocket MCP server and listed tools.")
            except Exception as e:
                print(f"Error testing connection/listing tools with server at {server_url}: {e}")
                print("Please ensure the server is running correctly.")
                print(f"Run: python google_forms_server_mcp.py --transport sse")
                return # Exit if connection test fails

            print("\nInitializing ChatAgent...")
            # Initialize ChatAgent with the MCP toolkit
            camel_agent = ChatAgent(
                model=model,
                tools=toolkit.get_tools(),
                verbose=True
            )
            print("ChatAgent initialized.")
            
            # Choose mode: automated test or interactive loop
            if mode == 'automated':
                await run_automated_test(toolkit.get_tools())
            elif mode == 'interactive':
                await interactive_input_loop(camel_agent)

    finally: # Finally block associated with the outer try
        print("\nCleaning up...")
        # Clean up resources only if server was started by this script (stdio mode)
        if server_process:
            print("Stopping stdio MCP server process...")
            try:
                await server_process.stop()
                print("Server process stopped.")
            except Exception as e:
                 print(f"Error stopping server process: {e}")
        # For WebSocket, we assume the server runs independently
        print("Cleanup complete.")

# Add argument parsing for command-line execution (this remains outside the main function)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Forms MCP Example Runner")
    parser.add_argument(
        "--mode", 
        default="automated", 
        choices=["automated", "interactive"], 
        help="Run mode (default: automated)"
    )
    parser.add_argument(
        "--transport", 
        default="sse",  # Default to SSE for client too
        choices=["stdio", "sse"], # Only allow stdio or sse
        help="Server transport method (default: sse)"
    )
    parser.add_argument(
        "--server-url", 
        default="http://127.0.0.1:8000",  # Default SSE URL (HTTP)
        help="URL of the running MCP SSE server (required for sse transport)"
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(server_transport=args.transport, mode=args.mode, server_url=args.server_url))
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")