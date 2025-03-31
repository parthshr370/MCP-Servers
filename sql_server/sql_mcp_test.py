import asyncio  # noqa: F401
import os
import tempfile
import json
import sqlite3
import pytest

# Import the async tools to test
from sql_server_mcp import (
    execute_query,
    list_tables,
    create_database,
    describe_table,
)

@pytest.mark.asyncio
async def test_create_database():
    """
    Test that create_database creates a valid SQLite database.
    """
    # Create a temporary file name
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Delete the file as we just want the name
        os.unlink(tmp_path)
        
        # Call the create_database tool
        result = await create_database(db_path=tmp_path)
        result_json = json.loads(result)
        
        # Check that creation was successful
        assert result_json["status"] == "success"
        
        # Verify the file exists
        assert os.path.exists(tmp_path)
        
        # Verify it's a valid SQLite database
        conn = sqlite3.connect(tmp_path)
        conn.close()
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@pytest.mark.asyncio
async def test_execute_query():
    """
    Test that execute_query can create a table, insert data, and query it.
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Set up a test database
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        cursor.execute("INSERT INTO test_table (id, name) VALUES (1, 'Test Name')")
        conn.commit()
        conn.close()
        
        # Test SELECT query
        query = "SELECT * FROM test_table"
        result = await execute_query(connection_string=tmp_path, query=query)
        result_json = json.loads(result)
        
        # Check if the result contains our test data
        assert len(result_json) == 1
        assert result_json[0]["id"] == 1
        assert result_json[0]["name"] == "Test Name"
        
        # Test INSERT query
        insert_query = "INSERT INTO test_table (id, name) VALUES (2, 'Second Test')"
        insert_result = await execute_query(connection_string=tmp_path, query=insert_query)
        insert_result_json = json.loads(insert_result)
        
        # Check if the row was inserted
        assert insert_result_json["affected_rows"] == 1
        
        # Verify the insert by querying again
        query = "SELECT * FROM test_table WHERE id = 2"
        result = await execute_query(connection_string=tmp_path, query=query)
        result_json = json.loads(result)
        
        assert len(result_json) == 1
        assert result_json[0]["id"] == 2
        assert result_json[0]["name"] == "Second Test"
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@pytest.mark.asyncio
async def test_list_tables():
    """
    Test that list_tables returns the correct list of tables in a database.
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Set up a test database with multiple tables
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE table1 (id INTEGER PRIMARY KEY, value TEXT)")
        cursor.execute("CREATE TABLE table2 (id INTEGER PRIMARY KEY, value TEXT)")
        conn.commit()
        conn.close()
        
        # Test list_tables
        result = await list_tables(connection_string=tmp_path)
        result_json = json.loads(result)
        
        # Check if both tables are listed
        assert "tables" in result_json
        assert "table1" in result_json["tables"]
        assert "table2" in result_json["tables"]
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@pytest.mark.asyncio
async def test_describe_table():
    """
    Test that describe_table returns the correct schema for a table.
    """
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        # Set up a test database with a table that has various column types
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                salary REAL,
                hire_date TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        # Test describe_table
        result = await describe_table(connection_string=tmp_path, table_name="test_table")
        result_json = json.loads(result)
        
        # Check if the schema is correct
        assert result_json["table"] == "test_table"
        
        # Check column details
        columns = {col["name"]: col for col in result_json["columns"]}
        
        assert "id" in columns
        assert columns["id"]["type"] == "INTEGER"
        assert columns["id"]["pk"] == 1
        
        assert "name" in columns
        assert columns["name"]["type"] == "TEXT"
        assert columns["name"]["notnull"] == 1
        
        assert "age" in columns
        assert columns["age"]["type"] == "INTEGER"
        
        assert "salary" in columns
        assert columns["salary"]["type"] == "REAL"
        
        assert "hire_date" in columns
        assert columns["hire_date"]["type"] == "TEXT"
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)