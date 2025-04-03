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
Google Forms MCP Server using FastMCP

This server provides MCP tools for interacting with Google Forms.
"""

import os
import json
import pickle
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

import asyncio  # noqa: F401
from mcp.server.fastmcp import FastMCP, Context
from camel.logger import get_logger

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Add necessary imports for WebSocket server
import argparse

logger = get_logger(__name__)

# Define the scopes needed for Google Forms API
SCOPES = [
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

@dataclass
class FormServices:
    """Class to hold the Google API services"""
    form_service: Any
    drive_service: Any
    sheets_service: Any


# Find the app_lifespan function in google_forms_server_mcp.py
# Look for this section (around line 60-80):

# Update the app_lifespan function in google_forms_server_mcp.py with this code

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[FormServices]:
    """Manage application lifecycle with Google API services"""
    logger.info("Initializing Google API services...")
    # Get credentials and initialize services
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # We need to make this work with async
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            
            # Generate the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            print("\n\n================================================")
            print("Go to this URL in your browser to authenticate:")
            print(f"{auth_url}")
            print("================================================\n")
            
            # Get authorization code from user input (using asyncio event loop)
            loop = asyncio.get_event_loop()
            auth_code = await loop.run_in_executor(
                None, 
                lambda: input("Enter the authorization code: ")
            )
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    # Build API services
    form_service = build('forms', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    
    services = FormServices(
        form_service=form_service,
        drive_service=drive_service,
        sheets_service=sheets_service
    )
    
    logger.info("Google API services initialized successfully")
    
    try:
        yield services
    finally:
        # No specific cleanup needed for Google API services
        logger.info("Shutting down Google API services")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "GoogleForms", 
    lifespan=app_lifespan,
    # Optionally add description, version etc.
    # description="MCP Server for Google Forms interaction.", 
    # version="0.1.0"
)

# Form Structure Tools

@mcp.tool()
async def create_form(title: str, description: str = "", ctx: Context = None) -> str:
    """
    Create a new Google Form with title and description
    
    Args:
        title (str): The title of the form
        description (str): The description of the form
    
    Returns:
        str: JSON string containing form details including ID
    """
    logger.info(f"create_form triggered with title: {title}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        form_body = {
            "info": {
                "title": title,
                "documentTitle": title
            }
        }
        
        if description:
            form_body["info"]["description"] = description
        
        result = form_service.forms().create(body=form_body).execute()
        
        return json.dumps({
            "form_id": result["formId"],
            "title": title,
            "description": description,
            "edit_url": f"https://docs.google.com/forms/d/{result['formId']}/edit",
            "view_url": f"https://docs.google.com/forms/d/{result['formId']}/viewform"
        }, indent=2)
    except Exception as e:
        return f"Error creating form: {e}"

create_form.inputSchema = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "title": "Form Title",
            "description": "The title of the Google Form"
        },
        "description": {
            "type": "string",
            "title": "Form Description",
            "description": "The description of the Google Form"
        }
    },
    "required": ["title"]
}

@mcp.tool()
async def add_section(form_id: str, title: str, description: str = "", ctx: Context = None) -> str:
    """
    Add a section to a Google Form
    
    Args:
        form_id (str): The ID of the form
        title (str): The title of the section
        description (str): The description of the section
    
    Returns:
        str: JSON string containing the updated form details
    """
    logger.info(f"add_section triggered with form_id: {form_id}, title: {title}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # First, get the current form
        form = form_service.forms().get(formId=form_id).execute()
        
        # Create the update request
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": {
                            "title": title,
                            "description": description,
                            "pageBreakItem": {}
                        },
                        "location": {
                            "index": len(form.get("items", []))
                        }
                    }
                }
            ]
        }
        
        # Execute the update
        updated_form = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "section_added": title,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding section: {e}"

add_section.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "title": {
            "type": "string",
            "title": "Section Title",
            "description": "The title of the section"
        },
        "description": {
            "type": "string",
            "title": "Section Description",
            "description": "The description of the section"
        }
    },
    "required": ["form_id", "title"]
}

@mcp.tool()
async def modify_form_settings(
    form_id: str, 
    collect_email: Optional[bool] = None,
    limit_responses: Optional[bool] = None,
    response_limit: Optional[int] = None,
    ctx: Context = None
) -> str:
    """
    Modify Google Form settings
    
    Args:
        form_id (str): The ID of the form
        collect_email (bool, optional): Whether to collect email addresses
        limit_responses (bool, optional): Whether to limit responses
        response_limit (int, optional): Maximum number of responses allowed
    
    Returns:
        str: JSON string containing the updated form settings
    """
    logger.info(f"modify_form_settings triggered with form_id: {form_id}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # Get the current form
        form = form_service.forms().get(formId=form_id).execute()
        
        updates = []
        
        # Update collect email setting
        if collect_email is not None:
            updates.append({
                "updateSettings": {
                    "settings": {
                        "collectEmail": collect_email
                    },
                    "updateMask": "collectEmail"
                }
            })
        
        # Update response limit settings
        if limit_responses is not None and not limit_responses:
            updates.append({
                "updateSettings": {
                    "settings": {
                        "isQuiz": False
                    },
                    "updateMask": "isQuiz"
                }
            })
        elif limit_responses and response_limit:
            updates.append({
                "updateSettings": {
                    "settings": {
                        "limitOneResponsePerUser": True
                    },
                    "updateMask": "limitOneResponsePerUser"
                }
            })
        
        # Execute the updates if any
        if updates:
            update_request = {"requests": updates}
            updated_form = form_service.forms().batchUpdate(
                formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "settings_updated": True,
            "collect_email": collect_email,
            "limit_responses": limit_responses,
            "response_limit": response_limit
        }, indent=2)
    except Exception as e:
        return f"Error modifying form settings: {e}"

modify_form_settings.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "collect_email": {
            "type": "boolean",
            "title": "Collect Email",
            "description": "Whether to collect email addresses"
        },
        "limit_responses": {
            "type": "boolean",
            "title": "Limit Responses",
            "description": "Whether to limit responses"
        },
        "response_limit": {
            "type": "integer",
            "title": "Response Limit",
            "description": "Maximum number of responses allowed"
        }
    },
    "required": ["form_id"]
}

# Question Type Tools

@mcp.tool()
async def add_short_answer(
    form_id: str, 
    question_text: str, 
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a short answer question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_short_answer triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        question_item = {
            "title": question_text,
            "required": required,
            "textQuestion": {
                "paragraph": False
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "short_answer",
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding short answer question: {e}"

add_short_answer.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text"]
}

@mcp.tool()
async def add_paragraph(
    form_id: str, 
    question_text: str, 
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a paragraph question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_paragraph triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        question_item = {
            "title": question_text,
            "required": required,
            "textQuestion": {
                "paragraph": True
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "paragraph",
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding paragraph question: {e}"

add_paragraph.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text"]
}

@mcp.tool()
async def add_multiple_choice(
    form_id: str, 
    question_text: str, 
    choices: List[str],
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a multiple choice question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        choices (List[str]): List of choices for the multiple choice question
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_multiple_choice triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # Create choices objects
        choice_items = [{"value": choice} for choice in choices]
        
        question_item = {
            "title": question_text,
            "required": required,
            "questionItem": {
                "question": {
                    "choiceQuestion": {
                        "type": "RADIO",
                        "options": choice_items,
                        "shuffle": False
                    }
                }
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "multiple_choice",
            "choices": choices,
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding multiple choice question: {e}"

add_multiple_choice.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "choices": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "title": "Choices",
            "description": "List of choices for the multiple choice question"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text", "choices"]
}

@mcp.tool()
async def add_checkboxes(
    form_id: str, 
    question_text: str, 
    choices: List[str],
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a checkboxes question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        choices (List[str]): List of choices for the checkboxes
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_checkboxes triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # Create choices objects
        choice_items = [{"value": choice} for choice in choices]
        
        question_item = {
            "title": question_text,
            "required": required,
            "questionItem": {
                "question": {
                    "choiceQuestion": {
                        "type": "CHECKBOX",
                        "options": choice_items,
                        "shuffle": False
                    }
                }
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "checkboxes",
            "choices": choices,
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding checkboxes question: {e}"

add_checkboxes.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "choices": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "title": "Choices",
            "description": "List of choices for the checkboxes"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text", "choices"]
}

@mcp.tool()
async def add_dropdown(
    form_id: str, 
    question_text: str, 
    choices: List[str],
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a dropdown question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        choices (List[str]): List of choices for the dropdown
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_dropdown triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # Create choices objects
        choice_items = [{"value": choice} for choice in choices]
        
        question_item = {
            "title": question_text,
            "required": required,
            "questionItem": {
                "question": {
                    "choiceQuestion": {
                        "type": "DROP_DOWN",
                        "options": choice_items,
                        "shuffle": False
                    }
                }
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "dropdown",
            "choices": choices,
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding dropdown question: {e}"

add_dropdown.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "choices": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "title": "Choices",
            "description": "List of choices for the dropdown"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text", "choices"]
}

@mcp.tool()
async def add_file_upload(
    form_id: str, 
    question_text: str, 
    required: bool = False,
    help_text: str = "",
    ctx: Context = None
) -> str:
    """
    Add a file upload question to a Google Form
    
    Args:
        form_id (str): The ID of the form
        question_text (str): The text of the question
        required (bool, optional): Whether the question is required
        help_text (str, optional): Help text for the question
    
    Returns:
        str: JSON string containing the question details
    """
    logger.info(f"add_file_upload triggered with form_id: {form_id}, question: {question_text}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        question_item = {
            "title": question_text,
            "required": required,
            "questionItem": {
                "question": {
                    "fileUploadQuestion": {
                        "folderId": None  # This will use the default folder
                    }
                }
            }
        }
        
        if help_text:
            question_item["description"] = help_text
        
        update_request = {
            "requests": [
                {
                    "createItem": {
                        "item": question_item,
                        "location": {
                            "index": 0
                        }
                    }
                }
            ]
        }
        
        result = form_service.forms().batchUpdate(
            formId=form_id, body=update_request).execute()
        
        return json.dumps({
            "form_id": form_id,
            "question_text": question_text,
            "type": "file_upload",
            "required": required,
            "status": "success"
        }, indent=2)
    except Exception as e:
        return f"Error adding file upload question: {e}"

add_file_upload.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "question_text": {
            "type": "string",
            "title": "Question Text",
            "description": "The text of the question"
        },
        "required": {
            "type": "boolean",
            "title": "Required",
            "description": "Whether the question is required"
        },
        "help_text": {
            "type": "string",
            "title": "Help Text",
            "description": "Help text for the question"
        }
    },
    "required": ["form_id", "question_text"]
}

# Response Management Tools

@mcp.tool()
async def get_responses(form_id: str, ctx: Context = None) -> str:
    """
    Get responses from a Google Form
    
    Args:
        form_id (str): The ID of the form
    
    Returns:
        str: JSON string containing the form responses
    """
    logger.info(f"get_responses triggered with form_id: {form_id}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        
        # Get the form first to check if it has a linked response sheet
        form = form_service.forms().get(formId=form_id).execute()
        
        # Get responses
        responses = form_service.forms().responses().list(formId=form_id).execute()
        
        # Simplify the response data for readability
        simplified_responses = []
        for response in responses.get("responses", []):
            answer_data = {}
            for key, value in response.get("answers", {}).items():
                question_id = key
                # Try to get the question text from the form
                question_text = "Unknown Question"
                for item in form.get("items", []):
                    if item.get("questionItem", {}).get("question", {}).get("questionId") == question_id:
                        question_text = item.get("title", "Unknown Question")
                        break
                
                # Extract the answer value based on type
                answer_value = None
                if "textAnswers" in value:
                    answer_value = value["textAnswers"]["answers"][0]["value"]
                elif "fileUploadAnswers" in value:
                    answer_value = [file.get("fileId") for file in value["fileUploadAnswers"]["answers"]]
                elif "choiceAnswers" in value:
                    answer_value = [choice.get("value") for choice in value["choiceAnswers"]["answers"]]
                
                answer_data[question_text] = answer_value
            
            simplified_responses.append({
                "response_id": response.get("responseId"),
                "timestamp": response.get("createTime"),
                "answers": answer_data
            })
        
        return json.dumps({
            "form_id": form_id,
            "title": form.get("info", {}).get("title", ""),
            "response_count": len(responses.get("responses", [])),
            "responses": simplified_responses
        }, indent=2)
    except Exception as e:
        return f"Error getting responses: {e}"

get_responses.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        }
    },
    "required": ["form_id"]
}

@mcp.tool()
async def export_responses(form_id: str, format: str = "csv", ctx: Context = None) -> str:
    """
    Export responses from a Google Form to a spreadsheet or CSV
    
    Args:
        form_id (str): The ID of the form
        format (str, optional): The format to export (csv or sheets)
    
    Returns:
        str: JSON string containing the export details
    """
    logger.info(f"export_responses triggered with form_id: {form_id}, format: {format}")
    
    try:
        services = ctx.lifespan_context
        form_service = services.form_service
        drive_service = services.drive_service
        sheets_service = services.sheets_service
        
        # Get the form
        form = form_service.forms().get(formId=form_id).execute()
        
        # Check if there's already a response spreadsheet
        response_sheet_id = None
        try:
            form_info = form_service.forms().get(formId=form_id).execute()
            if "responderUri" in form_info:
                # Extract the spreadsheet ID from the responder URI
                uri_parts = form_info["responderUri"].split("/")
                if len(uri_parts) > 5:
                    response_sheet_id = uri_parts[5]
        except Exception as e:
            logger.error(f"Error getting form: {e}")
        
        if not response_sheet_id:
            # Create a new spreadsheet for responses
            spreadsheet_body = {
                'properties': {
                    'title': f"Responses for {form.get('info', {}).get('title', 'Form')}"
                }
            }
            sheet = sheets_service.spreadsheets().create(body=spreadsheet_body).execute()
            response_sheet_id = sheet.get('spreadsheetId')
            
            # Link the form to the spreadsheet
            update_request = {
                "requests": [
                    {
                        "updateSettings": {
                            "settings": {
                                "responseDestination": "SPREADSHEET",
                                "spreadsheetId": response_sheet_id
                            },
                            "updateMask": "responseDestination,spreadsheetId"
                        }
                    }
                ]
            }
            form_service.forms().batchUpdate(formId=form_id, body=update_request).execute()
        
        # For CSV format, create a link to download as CSV
        if format.lower() == "csv":
            csv_export_link = f"https://docs.google.com/spreadsheets/d/{response_sheet_id}/export?format=csv"
            return json.dumps({
                "form_id": form_id,
                "export_format": "csv",
                "download_link": csv_export_link
            }, indent=2)
        else:
            # For sheets format, return the spreadsheet link
            sheets_link = f"https://docs.google.com/spreadsheets/d/{response_sheet_id}/edit"
            return json.dumps({
                "form_id": form_id,
                "export_format": "sheets",
                "spreadsheet_id": response_sheet_id,
                "spreadsheet_link": sheets_link
            }, indent=2)
    except Exception as e:
        return f"Error exporting responses: {e}"

export_responses.inputSchema = {
    "type": "object",
    "properties": {
        "form_id": {
            "type": "string",
            "title": "Form ID",
            "description": "The ID of the Google Form"
        },
        "format": {
            "type": "string",
            "title": "Export Format",
            "description": "The format to export (csv or sheets)",
            "enum": ["csv", "sheets"]
        }
    },
    "required": ["form_id"]
}

@mcp.tool()
async def list_forms(ctx: Context = None) -> str:
    """
    List all Google Forms created by the user
    
    Returns:
        str: JSON string containing the list of forms
    """
    logger.info("list_forms triggered")
    
    try:
        services = ctx.lifespan_context
        drive_service = services.drive_service
        
        # Search for Google Forms files
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.form'",
            spaces='drive',
            fields='files(id, name, webViewLink, createdTime)'
        ).execute()
        
        forms = results.get('files', [])
        
        if not forms:
            return json.dumps({"forms": [], "message": "No forms found"}, indent=2)
        
        # Format the forms list
        forms_list = []
        for form in forms:
            forms_list.append({
                "id": form.get('id'),
                "name": form.get('name'),
                "url": form.get('webViewLink'),
                "created": form.get('createdTime')
            })
        
        return json.dumps({"forms": forms_list}, indent=2)
    except Exception as e:
        return f"Error listing forms: {e}"

list_forms.inputSchema = {
    "type": "object",
    "properties": {},
    "required": []
}

# Update the main function to handle different transports using mcp.run
def main(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000):
    """Starts the MCP server using the specified transport via mcp.run()."""
    
    # Pass arguments like host and port if mcp.run supports them
    # Assuming mcp.run handles stdio and ws transports appropriately
    logger.info(f"Starting MCP server with {transport} transport...")
    try:
        # Check if mcp.run accepts host/port for relevant transports (like ws)
        # This structure assumes mcp.run handles the server lifecycles
        if transport == "ws":
             # We might need to pass host/port here if mcp.run accepts them
             # Trying without them first, assuming defaults or internal handling
             # If it fails, we may need to inspect mcp.run or FastMCP source
             # mcp.run(transport=transport) # Run with only transport for ws - Changed to sse
             # Assuming mcp.run handles sse transport correctly
             mcp.run(transport=transport)
        elif transport == "stdio":
             mcp.run(transport=transport)
        else:
             # logger.error(f"Unsupported transport type for mcp.run: {transport}")
             # Since we only support stdio and sse now, this path shouldn't be hit with arg choices
             # If it somehow is, mcp.run will raise its own error. 
             # We'll rely on mcp.run to validate the transport.
             mcp.run(transport=transport) 

    except AttributeError:
         logger.error(f"mcp.run does not support the arguments provided for transport '{transport}'. Trying without host/port.")
         try:
             mcp.run(transport=transport)
         except Exception as e:
             logger.error(f"Failed to start server with mcp.run(transport='{transport}'): {e}")
    except Exception as e:
        logger.error(f"Failed to start server with mcp.run: {e}")
        
# Add argument parsing for command-line execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Forms MCP Server")
    parser.add_argument(
        "--transport", 
        default="sse",  # Default to Server-Sent Events
        choices=["stdio", "sse"], # Only allow stdio or sse
        help="Server transport method (default: sse)"
    )
    parser.add_argument(
        "--host", 
        default="127.0.0.1", 
        help="Host address for WebSocket server (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port for WebSocket server (default: 8000)"
    )
    args = parser.parse_args()
    
    main(transport=args.transport, host=args.host, port=args.port)