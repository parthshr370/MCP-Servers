import streamlit as st
import os
import tempfile
from pathlib import Path
import re
import sys
import logging # Import logging

# --- Basic Logging Configuration --- #
logging.basicConfig(
    level=logging.INFO, # Set the logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr, # Ensure logs go to stderr (terminal)
)

# --- Dynamically add local package path --- #
# Calculate the path to the 'src' directory of the local 'markitdown' package
_PROJECT_ROOT = Path(__file__).resolve().parent
_MARKITDOWN_SRC_PATH = _PROJECT_ROOT / "packages" / "markitdown" / "src"

# Add the path to sys.path if it's not already there
if str(_MARKITDOWN_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_MARKITDOWN_SRC_PATH))
    print(f"DEBUG: Added '{_MARKITDOWN_SRC_PATH}' to sys.path")

# Attempt to import the core MarkItDown class
try:
    from markitdown import MarkItDown
    from markitdown._exceptions import MarkItDownException
except ImportError as e:
    logging.error(f"Failed to import markitdown: {e}", exc_info=True)
    st.error(
        f"Failed to import the `markitdown` library or its exceptions. "
        f"Error: {e}\n"
        "Please ensure it is installed correctly (e.g., `pip install -e ./packages/markitdown`) "
        f"and that the path '{_MARKITDOWN_SRC_PATH}' exists and is accessible."
    )
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="MarkItDown Converter",
    page_icon=":memo:",
    layout="wide",
)

# --- Session State Initialization ---
if 'markdown_output' not in st.session_state:
    st.session_state.markdown_output = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'input_uri' not in st.session_state:
    st.session_state.input_uri = ""

# --- Helper Functions ---
def is_valid_uri_scheme(uri):
    """Basic check for supported URI schemes."""
    return uri.startswith(("http://", "https://", "file://", "data:"))

def clean_filename(filename):
    """Remove invalid characters for filenames."""
    # Remove URL scheme if present
    name = re.sub(r'^(http|https|file|data):[\/]*', '', filename)
    # Replace problematic characters
    name = re.sub(r'[\/:*?\"<>|%#&.]+', '_', name)
    # Limit length
    return name[:100] or "converted"

# --- UI Layout ---
st.title("📝 MarkItDown Content Converter")
st.markdown(
    "Convert content from various sources (URLs or uploaded files) into Markdown."
)
st.divider()

# --- Input Method Selection ---
input_method = st.radio(
    "Select Input Method:",
    ("Enter URL", "Upload File"),
    horizontal=True,
    key="input_method_radio",
    help="Choose whether to provide a web URL or upload a local file."
)

col1, col2 = st.columns([3, 1])

with col1:
    if input_method == "Enter URL":
        st.session_state.input_uri = st.text_input(
            "Enter URL (http://, https://, data:)",
            value=st.session_state.input_uri,
            placeholder="e.g., https://www.example.com or data:text/plain;base64,...",
            key="url_input",
        )
        uploaded_file = None
    else: # Upload File
        uploaded_file = st.file_uploader(
            "Upload a file (will be converted to a `file://` URI)",
            type=None, # Allow any file type MarkItDown might support
            key="file_uploader",
        )
        st.session_state.input_uri = "" # Clear URI input if file is chosen

with col2:
    st.markdown("&nbsp;", unsafe_allow_html=True) # Vertical alignment hack
    st.markdown("&nbsp;", unsafe_allow_html=True)
    convert_button = st.button("Convert to Markdown", type="primary", use_container_width=True)

# --- Conversion Logic ---
if convert_button:
    logging.info("'Convert to Markdown' button clicked.")
    st.session_state.markdown_output = None # Clear previous output
    st.session_state.error_message = None # Clear previous error
    final_uri = None
    tmp_file_path = None # Ensure tmp_file_path is defined

    if uploaded_file is not None:
        try:
            # Save uploaded file temporarily to get a path
            # Use a consistent way to create temp files
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            logging.info(f"Uploaded file '{uploaded_file.name}' saved to temporary path: {tmp_file_path}")
            final_uri = Path(tmp_file_path).as_uri()
            logging.info(f"Processing uploaded file as URI: {final_uri}")
            st.info(f"Processing uploaded file as: {final_uri}")
        except Exception as e:
             logging.error(f"Error saving uploaded file: {e}", exc_info=True)
             st.error(f"Error handling uploaded file: {e}")
             final_uri = None # Prevent further processing

    elif st.session_state.input_uri:
        final_uri = st.session_state.input_uri.strip()
        if not is_valid_uri_scheme(final_uri):
             # Attempt to fix common local path issue
            if final_uri.startswith('/'):
                st.warning(f"Assuming '{final_uri}' is a local path. Prepending 'file://'.")
                final_uri = f"file://{final_uri}"
            else:
                st.error(f"Invalid or unsupported URI scheme in '{final_uri}'. Must start with http://, https://, file://, or data:")
                final_uri = None
        logging.info(f"Processing input URI: {final_uri}") # Log the final URI used

    else:
        logging.warning("Conversion attempt with no input URI or file.")
        st.warning("Please enter a URL or upload a file.")

    if final_uri:
        progress_bar = st.progress(0, text="Starting conversion...")
        try:
            logging.info(f"Initializing MarkItDown converter for URI: {final_uri}")
            md_converter = MarkItDown()
            progress_bar.progress(25, text=f"Converting URI: {final_uri[:100]}...")

            # Perform the conversion
            logging.info(f"Calling convert_uri for: {final_uri}")
            result = md_converter.convert_uri(final_uri)
            logging.info(f"convert_uri successful for: {final_uri}")

            progress_bar.progress(100, text="Conversion successful!")
            st.session_state.markdown_output = result.markdown
            st.success("Content successfully converted to Markdown!")

        except MarkItDownException as e:
            logging.error(f"MarkItDown Conversion Error for URI {final_uri}: {e}", exc_info=True)
            st.session_state.error_message = f"MarkItDown Conversion Error: {e}"
            st.error(st.session_state.error_message)
            progress_bar.progress(100, text="Conversion failed.")
        except Exception as e:
            logging.error(f"Unexpected Error during conversion for URI {final_uri}: {e}", exc_info=True)
            st.session_state.error_message = f"An unexpected error occurred: {e}"
            st.error(st.session_state.error_message)
            progress_bar.progress(100, text="Conversion failed.")
        finally:
            # Clean up temporary file if created
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.remove(tmp_file_path)
                    logging.info(f"Cleaned up temporary file: {tmp_file_path}")
                except Exception as e:
                     logging.error(f"Error removing temporary file {tmp_file_path}: {e}", exc_info=True)
            # Remove progress bar after completion/error
            progress_bar.empty()

st.divider()

# --- Output Display and Download ---
st.subheader("Output")

if st.session_state.error_message and not st.session_state.markdown_output:
    # Show error prominently if conversion failed and there's no output
    st.error(st.session_state.error_message)
elif st.session_state.markdown_output:
    st.text_area(
        "Generated Markdown",
        value=st.session_state.markdown_output,
        height=400,
        key="markdown_display",
        help="The Markdown generated from the source."
    )

    # Determine a sensible filename
    download_filename_base = "converted_markdown"
    if st.session_state.input_uri:
        download_filename_base = clean_filename(st.session_state.input_uri)
    elif uploaded_file:
        download_filename_base = clean_filename(uploaded_file.name)

    st.download_button(
        label="Download Markdown (.md)",
        data=st.session_state.markdown_output,
        file_name=f"{download_filename_base}.md",
        mime="text/markdown",
        key="download_button",
        use_container_width=True,
    )
else:
    st.info("Enter a URL or upload a file and click 'Convert to Markdown' to see the output here.") 