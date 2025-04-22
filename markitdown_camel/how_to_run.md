# How to Run MarkItDown Integrations

This guide explains how to set up and run the MarkItDown integrations created in this project: the command-line interface (CLI) powered by Camel AI, and the Streamlit web frontend.

**Project Structure Overview:**

```
markitdown/
├── packages/
│   ├── markitdown/          # Core library source
│   │   └── src/
│   ├── markitdown-mcp/       # MCP Server source
│   │   └── src/
│   └── ...
├── camel_markitdown_client.py # Camel AI client script (CLI mode)
├── streamlit_markitdown_app.py # Streamlit frontend script
├── how_to_run.md              # This file
└── ... (other project files like README.md, .git, etc.)
```

## I. Prerequisites

Before running either integration, ensure you have the following set up:

1.  **Conda Environment:** It's highly recommended to use a dedicated Conda environment (like `kratos` used during development). Activate it:
    ```bash
    conda activate kratos
    ```

2.  **Install Base Dependencies:** Install the core `markitdown` library and its dependencies in editable mode. This allows using the local source code.
    ```bash
    # Navigate to the project root directory (e.g., ~/Downloads/markitdown/)
    cd /path/to/your/markitdown

    # Install the core library and all its optional features
    pip install -e './packages/markitdown[all]'

    # Install the MCP server package (needed by markitdown library)
    pip install -e './packages/markitdown-mcp'
    ```

3.  **API Keys:**
    *   **Google Gemini:** The Camel AI client is configured to use Google Gemini. Set your API key as an environment variable:
        ```bash
        export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
        ```
    *   **MarkItDown Dependencies:** The underlying `markitdown` library might require other keys for specific conversions (e.g., Azure Document Intelligence, transcription services). Set these as environment variables if you plan to use those features.

## II. Running the Camel AI Client (CLI Mode)

This mode uses a Large Language Model (LLM) agent (Gemini) to interact with the `markitdown` tool via the `markitdown-mcp` server, which runs in the background.

1.  **Install Camel AI Dependencies:**
    ```bash
    # Install camel-ai with google support
    pip install "camel-ai[google]"
    ```

2.  **Ensure Prerequisites:** Make sure your Conda environment is active and your `GOOGLE_API_KEY` is exported (as described in Prerequisites).

3.  **Run the Client Script:** Execute the client script from the project root directory:
    ```bash
    python camel_markitdown_client.py
    ```

4.  **Interaction:**
    *   The script will start the background `markitdown-mcp` server automatically.
    *   It will connect to the server and initialize the Gemini agent.
    *   You will be prompted in the terminal to enter a URI (`http://`, `https://`, `file://`, `data:`).
    *   Provide a URI (e.g., `https://www.google.com` or `/absolute/path/to/your/local/file.pdf`). Local paths starting with `/` will automatically be converted to `file://` URIs.
    *   The agent will call the `convert_to_markdown` tool on the background server.
    *   The resulting Markdown (or any error messages) will be printed to your terminal.
    *   Type `exit` at the prompt to quit.

## III. Running the Streamlit Frontend (Web UI Mode)

This mode provides a web interface to directly use the `markitdown` library for conversions without involving an LLM agent or the MCP server.

1.  **Install Streamlit Dependency:**
    ```bash
    pip install streamlit
    ```

2.  **Ensure Prerequisites:** Make sure your Conda environment is active. While the Streamlit app doesn't directly use the Google API key, ensure any keys needed by `markitdown` itself for specific conversions are set.

3.  **Run the Streamlit App:** Execute the following command from the project root directory:
    ```bash
    streamlit run streamlit_markitdown_app.py
    ```
    *Note: This script is configured to automatically add the local `markitdown` source path to `sys.path`, so you should **not** need to set the `PYTHONPATH` environment variable manually for this script.* 

4.  **Interaction:**
    *   Streamlit will provide a URL (usually `http://localhost:8501`). Open this in your web browser.
    *   Select the input method: "Enter URL" or "Upload File".
    *   Provide the URL or upload your desired file.
    *   Click the "Convert to Markdown" button.
    *   A progress bar will indicate activity.
    *   The resulting Markdown will be displayed in a text area.
    *   A "Download Markdown (.md)" button will appear, allowing you to save the output.
    *   Check the terminal where you ran `streamlit run` for log messages. 