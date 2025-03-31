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

import os
import asyncio  # noqa: F401
import sqlite3
import json
from mcp.server.fastmcp import FastMCP
from camel.logger import get_logger

logger = get_logger(__name__)
mcp = FastMCP("sqldb")

@mcp.tool()
async def execute_query(connection_string: str, query: str) -> str:
    r"""Executes the SQL query on the given database.
    Args:
        connection_string (str): The connection string or path to the SQLite database.
        query (str): The SQL query to execute.
    Returns:
        str: The result of the query as a JSON string, or an error message if execution fails.
    """
    logger.info(f"execute_query triggered with connection_string: {connection_string}")
    # For security reasons, don't log the full query in production
    logger.info(f"Query starts with: {query[:20]}...")
    
    try:
        # For this example, we'll use SQLite which just takes a file path
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Check if this is a SELECT query (has results to fetch)
        if query.strip().upper().startswith("SELECT"):
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch results and format as a list of dictionaries
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            conn.close()
            return json.dumps(results, indent=2)
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            affected_rows = cursor.rowcount
            conn.close()
            return json.dumps({"affected_rows": affected_rows}, indent=2)
    
    except Exception as e:
        return f"Error executing SQL query: {e}"

execute_query.inputSchema = {
    "type": "object",
    "properties": {
         "connection_string": {
             "type": "string",
             "title": "Connection String",
             "description": "The connection string or path to the SQLite database."
         },
         "query": {
             "type": "string",
             "title": "SQL Query",
             "description": "The SQL query to execute."
         }
    },
    "required": ["connection_string", "query"]
}

@mcp.tool()
async def list_tables(connection_string: str) -> str:
    r"""Lists all tables in the specified database.
    Args:
        connection_string (str): The connection string or path to the SQLite database.
    Returns:
        str: A JSON string containing the list of tables, or an error message if listing fails.
    """
    logger.info(f"list_tables triggered with connection_string: {connection_string}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Query to get all table names in SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        # Fetch and format results
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return json.dumps({"tables": tables}, indent=2)
    
    except Exception as e:
        return f"Error listing tables: {e}"

list_tables.inputSchema = {
    "type": "object",
    "properties": {
         "connection_string": {
             "type": "string",
             "title": "Connection String",
             "description": "The connection string or path to the SQLite database."
         }
    },
    "required": ["connection_string"]
}

@mcp.tool()
async def create_database(db_path: str) -> str:
    r"""Creates a new SQLite database at the specified path.
    Args:
        db_path (str): The path where the new database should be created.
    Returns:
        str: A success message or an error message if creation fails.
    """
    logger.info(f"create_database triggered with db_path: {db_path}")
    
    try:
        # Check if file already exists
        if os.path.exists(db_path):
            return f"Database already exists at {db_path}"
        
        # Create a new SQLite database by connecting to it
        conn = sqlite3.connect(db_path)
        conn.close()
        
        return json.dumps({"status": "success", "message": f"Database created at {db_path}"}, indent=2)
    
    except Exception as e:
        return f"Error creating database: {e}"

create_database.inputSchema = {
    "type": "object",
    "properties": {
         "db_path": {
             "type": "string",
             "title": "Database Path",
             "description": "The path where the new SQLite database should be created."
         }
    },
    "required": ["db_path"]
}

@mcp.tool()
async def describe_table(connection_string: str, table_name: str) -> str:
    r"""Describes the schema of a specified table.
    Args:
        connection_string (str): The connection string or path to the SQLite database.
        table_name (str): The name of the table to describe.
    Returns:
        str: A JSON string containing the table schema, or an error message if the operation fails.
    """
    logger.info(f"describe_table triggered with connection_string: {connection_string}, table_name: {table_name}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Query to get table schema in SQLite
        cursor.execute(f"PRAGMA table_info({table_name});")
        
        # Fetch and format results
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "notnull": row[3],
                "default_value": row[4],
                "pk": row[5]
            })
        
        conn.close()
        
        return json.dumps({"table": table_name, "columns": columns}, indent=2)
    
    except Exception as e:
        return f"Error describing table: {e}"

describe_table.inputSchema = {
    "type": "object",
    "properties": {
         "connection_string": {
             "type": "string",
             "title": "Connection String",
             "description": "The connection string or path to the SQLite database."
         },
         "table_name": {
             "type": "string",
             "title": "Table Name",
             "description": "The name of the table to describe."
         }
    },
    "required": ["connection_string", "table_name"]
}

def main(transport: str = "stdio"):
    r"""Runs the SQL MCP Server.
    This server provides SQL database functionalities via MCP.
    Args:
        transport (str): The transport mode ('stdio' or 'sse').
    """
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'sse':
        mcp.run(transport='sse')
    else:
        print(f"Unknown transport mode: {transport}")

if __name__ == "__main__":
    import sys
    transport_mode = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    main(transport_mode)