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

# Load environment variables from .env file
load_dotenv()

# Set your Anthropic API key (ensure this is valid in your .env file)
os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

# Create a sample database for demonstration
async def create_sample_database():
    """Create a sample SQLite database with some data for demonstration."""
    import sqlite3
    
    # Create a temporary database in the current directory
    db_path = "sample.db"
    
    # If database already exists, remove it to start fresh
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create the database and add sample tables and data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create employees table
    cursor.execute("""
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT,
        salary REAL,
        hire_date TEXT
    )
    """)
    
    # Insert sample employee data
    employees = [
        (1, 'John Doe', 'Engineering', 85000.00, '2020-01-15'),
        (2, 'Jane Smith', 'Marketing', 75000.00, '2019-05-20'),
        (3, 'Bob Johnson', 'Engineering', 95000.00, '2018-11-10'),
        (4, 'Alice Brown', 'HR', 65000.00, '2021-03-05'),
        (5, 'Charlie Davis', 'Engineering', 90000.00, '2020-08-12')
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", employees)
    
    # Create departments table
    cursor.execute("""
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        budget REAL,
        location TEXT
    )
    """)
    
    # Insert sample department data
    departments = [
        (1, 'Engineering', 1000000.00, 'Building A'),
        (2, 'Marketing', 500000.00, 'Building B'),
        (3, 'HR', 300000.00, 'Building A'),
        (4, 'Finance', 600000.00, 'Building C')
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", departments)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Sample database created at: {db_path}")
    return db_path

# Interactive mode function to chat with the agent
async def interactive_input_loop(agent: ChatAgent, db_path: str):
    loop = asyncio.get_event_loop()
    print("\n==== SQL Assistant Interactive Mode ====")
    print("Type 'exit' at any prompt to quit.")
    print(f"\nUsing sample database at: {db_path}")
    print("\nSample queries you can try:")
    print("- Show me all tables in sample.db")
    print("- What columns are in the employees table in sample.db?")
    print("- List all employees in the Engineering department")
    print("- What is the average salary by department?")
    print("- How many employees are in each department?")
    print("- Find the employee with the highest salary")
    print("- Add a new employee named Michael Wilson to Finance with salary 82000")
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
async def main(server_transport: str = 'stdio'):
    # First create a sample database
    db_path = await create_sample_database()
    
    if server_transport == 'stdio':
        # Determine the path to the server file
        server_script_path = Path(__file__).resolve().parent / "sql_server_mcp.py"
        if not server_script_path.is_file():
            print(f"Error: Server script not found at {server_script_path}")
            return
            
        # Create an _MCPServer instance for our SQL server
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
            "You are a helpful SQL assistant. Use the provided external tools for database operations. "
            "Always use the tools to query the database rather than answering from your general knowledge. "
            f"The sample database is at '{db_path}'. It contains tables for employees and departments. "
            "When a user asks a question about the database, ALWAYS explicitly include the database path "
            f"'{db_path}' in your tool calls. First list the tables to understand the schema, "
            "then use describe_table to see column details before querying."
        )
        model = ModelFactory.create(
            model_platform=ModelPlatformType.ANTHROPIC,
            model_type="claude-3-7-sonnet-20250219",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model_config_dict={"temperature": 0.5, "max_tokens": 4096},
        )
        camel_agent = ChatAgent(
            system_message=sys_msg,
            model=model,
            tools=tools,
        )
        camel_agent.reset()
        camel_agent.memory.clear()
        await interactive_input_loop(camel_agent, db_path)
        
        # Clean up the sample database after we're done
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\nRemoved sample database: {db_path}")

# Entry point 
if __name__ == "__main__":
    asyncio.run(main())
