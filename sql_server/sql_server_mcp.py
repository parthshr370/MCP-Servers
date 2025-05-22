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
import re # Added for table name validation
from mcp.server.fastmcp import FastMCP
from camel.logger import get_logger
from pathlib import Path

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
    
    conn = None
    try:
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
            
            return json.dumps({"status": "success", "data": results}, indent=2)
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            affected_rows = cursor.rowcount
            return json.dumps({"status": "success", "affected_rows": affected_rows}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error executing SQL query: {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

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
    
    conn = None
    try:
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Query to get all table names in SQLite
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        # Fetch and format results
        tables = [row[0] for row in cursor.fetchall()]
        return json.dumps({"status": "success", "tables": tables}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error listing tables: {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

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
    
    conn = None
    try:
        # Check if file already exists
        if os.path.exists(db_path):
            return json.dumps({"status": "exists", "message": f"Database already exists at {db_path}"}, indent=2)
        
        conn = sqlite3.connect(db_path)
        conn.close()
        
        return json.dumps({"status": "success", "message": f"Database created at {db_path}"}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error creating database: {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

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

    # Validate table_name to be a simple identifier to reduce SQL injection risk with PRAGMA
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return json.dumps({"status": "error", "message": f"Invalid table name: '{table_name}'. Must be a valid SQL identifier."}, indent=2)

    conn = None
    try:
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # PRAGMA statements do not support placeholders for table names.
        cursor.execute(f"PRAGMA table_info({table_name});")
        
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
        
        if not columns:
             return json.dumps({"status": "not_found", "message": f"Table '{table_name}' not found or has no columns."}, indent=2)
        return json.dumps({"status": "success", "table": table_name, "columns": columns}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error describing table '{table_name}': {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

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

@mcp.tool()
async def delete_database(db_path: str) -> str:
    r"""Deletes an existing SQLite database file at the specified path.
    Args:
        db_path (str): The path to the SQLite database file to be deleted.
    Returns:
        str: A JSON string indicating success or an error message if deletion fails.
    """
    logger.info(f"delete_database triggered with db_path: {db_path}")
    
    try:
        if not os.path.exists(db_path):
            return json.dumps({"status": "not_found", "message": f"Database file not found at {db_path}"}, indent=2)
        
        os.remove(db_path)
        return json.dumps({"status": "success", "message": f"Database deleted from {db_path}"}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error deleting database: {str(e)}"}, indent=2)

delete_database.inputSchema = {
    "type": "object",
    "properties": {
         "db_path": {
             "type": "string",
             "title": "Database Path",
             "description": "The path to the SQLite database file to be deleted."
         }
    },
    "required": ["db_path"]
}

@mcp.tool()
async def delete_table(connection_string: str, table_name: str) -> str:
    r"""Deletes a specified table from the SQLite database.
    Args:
        connection_string (str): The connection string or path to the SQLite database.
        table_name (str): The name of the table to delete.
    Returns:
        str: A JSON string indicating success or failure.
    """
    logger.info(f"delete_table triggered for table: {table_name} in db: {connection_string}")

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return json.dumps({"status": "error", "message": f"Invalid table name: '{table_name}'. Must be a valid SQL identifier."}, indent=2)

    conn = None
    try:
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Check if table exists first for a more specific message
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        if cursor.fetchone() is None:
            return json.dumps({"status": "not_found", "message": f"Table '{table_name}' not found. No action taken."}, indent=2)
            
        # Table name is validated, safe to use in f-string for DROP TABLE
        cursor.execute(f"DROP TABLE {table_name};")
        conn.commit()
        
        return json.dumps({"status": "success", "message": f"Table '{table_name}' deleted successfully."}, indent=2)
    
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Error deleting table '{table_name}': {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

delete_table.inputSchema = {
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
             "description": "The name of the table to delete."
         }
    },
    "required": ["connection_string", "table_name"]
}

@mcp.tool()
async def get_table_row_count(connection_string: str, table_name: str) -> str:
    r"""Gets the row count for a specified table.
    Args:
        connection_string (str): The connection string or path to the SQLite database.
        table_name (str): The name of the table.
    Returns:
        str: A JSON string containing the table name and its row count, or an error message.
    """
    logger.info(f"get_table_row_count triggered for table: {table_name} in db: {connection_string}")
    
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return json.dumps({"status": "error", "message": f"Invalid table name: '{table_name}'. Must be a valid SQL identifier."}, indent=2)

    conn = None
    try:
        conn = sqlite3.connect(connection_string)
        cursor = conn.cursor()
        
        # Table name is validated, safe to use in f-string for SELECT COUNT(*)
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        
        return json.dumps({"status": "success", "table": table_name, "row_count": count}, indent=2)
    
    except sqlite3.OperationalError as e: # Catches errors like "no such table"
        return json.dumps({"status": "error", "message": f"Error getting row count for table '{table_name}': {str(e)}. Ensure table exists."}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": f"An unexpected error occurred while getting row count for table '{table_name}': {str(e)}"}, indent=2)
    finally:
        if conn:
            conn.close()

get_table_row_count.inputSchema = {
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
             "description": "The name of the table to get row count for."
         }
    },
    "required": ["connection_string", "table_name"]
}

async def init_db():
    db_path = Path.cwd() / "your_sqlite_database.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create a sample table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sample_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

async def main():
    await init_db()
    
    # Keep the server running
    while True:
        await asyncio.sleep(1)

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
    asyncio.run(main(transport_mode))