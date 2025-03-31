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
from mcp.server.fastmcp import FastMCP
from camel.logger import get_logger

logger = get_logger(__name__)
mcp = FastMCP("filesystem")

@mcp.tool()
async def read_file(file_path: str) -> str:
    r"""Reads the content of the file at the given file path.
    Args:
        file_path (str): The path to the file.
    Returns:
        str: The content of the file with trailing whitespace removed, or an error message if reading fails.
    """
    logger.info(f"read_file triggered with file_path: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.rstrip()
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"

read_file.inputSchema = {
    "type": "object",
    "properties": {
         "file_path": {
             "type": "string",
             "title": "File Path",
             "description": "The path to the file to read. Default is 'README.md'."
         }
    },
    "required": ["file_path"]
}

@mcp.tool()
async def list_directory(directory_path: str) -> str:
    r"""Lists the contents of the specified directory.
    Args:
        directory_path (str): The path of the directory to list.
    Returns:
        str: A newline-separated string of the directory entries, or an error message if listing fails.
    """
    logger.info(f"list_directory triggered with directory_path: {directory_path}")
    try:
        entries = os.listdir(directory_path)
        return "\n".join(entry.rstrip() for entry in entries)
    except Exception as e:
        return f"Error listing directory '{directory_path}': {e}"

list_directory.inputSchema = {
    "type": "object",
    "properties": {
         "directory_path": {
             "type": "string",
             "title": "Directory Path",
             "description": "The directory path whose contents should be listed. Default is '.'."
         }
    },
    "required": ["directory_path"]
}

def main(transport: str = "stdio"):
    r"""Runs the Filesystem MCP Server.
    This server provides filesystem-related functionalities via MCP.
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
