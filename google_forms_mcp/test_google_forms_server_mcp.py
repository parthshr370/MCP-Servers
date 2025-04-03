import asyncio  # noqa: F401
import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the async tools to test
from google_forms_server_mcp import (
    create_form,
    add_section,
    add_short_answer,
    add_paragraph,
    add_multiple_choice,
    add_checkboxes,
    add_dropdown,
    add_file_upload,
    modify_form_settings,
    get_responses,
    export_responses,
    list_forms,
)

# Mock Google API services
@pytest.fixture
def mock_google_services():
    # Create mock services
    mock_form_service = MagicMock()
    mock_drive_service = MagicMock()
    mock_sheets_service = MagicMock()
    
    # Create mock context with mock services
    mock_context = MagicMock()
    mock_context.lifespan_context = MagicMock()
    mock_context.lifespan_context.form_service = mock_form_service
    mock_context.lifespan_context.drive_service = mock_drive_service
    mock_context.lifespan_context.sheets_service = mock_sheets_service
    
    return mock_context

@pytest.mark.asyncio
async def test_create_form(mock_google_services):
    """
    Test that create_form creates a form correctly
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    mock_create = mock_forms_obj.create.return_value
    mock_create.execute.return_value = {"formId": form_id}
    
    # Call the create_form function
    form_title = "Test Form"
    form_description = "A test form"
    result = await create_form(title=form_title, description=form_description, ctx=mock_google_services)
    result_json = json.loads(result)
    
    # Check that the form creation was successful
    assert result_json["form_id"] == form_id
    assert result_json["title"] == form_title
    assert result_json["description"] == form_description
    assert "edit_url" in result_json
    assert "view_url" in result_json
    
    # Check that the correct API calls were made
    mock_forms_obj.create.assert_called_once()
    form_body = mock_forms_obj.create.call_args[1]["body"]
    assert form_body["info"]["title"] == form_title
    assert form_body["info"]["description"] == form_description

@pytest.mark.asyncio
async def test_add_section(mock_google_services):
    """
    Test that add_section adds a section to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the get method
    mock_get = mock_forms_obj.get.return_value
    mock_get.execute.return_value = {
        "formId": form_id,
        "items": [{"item1": "data"}]
    }
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_section function
    section_title = "Test Section"
    section_description = "A test section"
    result = await add_section(
        form_id=form_id, 
        title=section_title, 
        description=section_description, 
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the section addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["section_added"] == section_title
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.get.assert_called_once_with(formId=form_id)
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == section_title
    assert update_request["requests"][0]["createItem"]["item"]["description"] == section_description
    assert "pageBreakItem" in update_request["requests"][0]["createItem"]["item"]

@pytest.mark.asyncio
async def test_modify_form_settings(mock_google_services):
    """
    Test that modify_form_settings updates form settings correctly
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the get method
    mock_get = mock_forms_obj.get.return_value
    mock_get.execute.return_value = {
        "formId": form_id,
        "settings": {"collectEmail": False}
    }
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the modify_form_settings function
    collect_email = True
    result = await modify_form_settings(
        form_id=form_id,
        collect_email=collect_email,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the settings update was successful
    assert result_json["form_id"] == form_id
    assert result_json["settings_updated"] == True
    assert result_json["collect_email"] == collect_email
    
    # Check that the correct API calls were made
    mock_forms_obj.get.assert_called_once_with(formId=form_id)
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["updateSettings"]["settings"]["collectEmail"] == collect_email
    assert update_request["requests"][0]["updateSettings"]["updateMask"] == "collectEmail"

@pytest.mark.asyncio
async def test_add_short_answer(mock_google_services):
    """
    Test that add_short_answer adds a question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_short_answer function
    question_text = "What is your name?"
    required = True
    help_text = "Please enter your full name"
    result = await add_short_answer(
        form_id=form_id, 
        question_text=question_text, 
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "short_answer"
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    assert update_request["requests"][0]["createItem"]["item"]["textQuestion"]["paragraph"] == False

@pytest.mark.asyncio
async def test_add_paragraph(mock_google_services):
    """
    Test that add_paragraph adds a paragraph question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_paragraph function
    question_text = "Tell us about yourself"
    required = False
    help_text = "Write a brief description"
    result = await add_paragraph(
        form_id=form_id, 
        question_text=question_text, 
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "paragraph"
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    assert update_request["requests"][0]["createItem"]["item"]["textQuestion"]["paragraph"] == True

@pytest.mark.asyncio
async def test_add_multiple_choice(mock_google_services):
    """
    Test that add_multiple_choice adds a multiple choice question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_multiple_choice function
    question_text = "What is your favorite color?"
    choices = ["Red", "Blue", "Green", "Yellow"]
    required = True
    help_text = "Select one option"
    result = await add_multiple_choice(
        form_id=form_id, 
        question_text=question_text,
        choices=choices,
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "multiple_choice"
    assert result_json["choices"] == choices
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    
    # Check that the choices were set correctly
    choice_question = update_request["requests"][0]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]
    assert choice_question["type"] == "RADIO"
    assert len(choice_question["options"]) == len(choices)
    for i, choice in enumerate(choices):
        assert choice_question["options"][i]["value"] == choice
    assert choice_question["shuffle"] == False

@pytest.mark.asyncio
async def test_add_checkboxes(mock_google_services):
    """
    Test that add_checkboxes adds a checkboxes question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_checkboxes function
    question_text = "Which fruits do you like?"
    choices = ["Apple", "Banana", "Orange", "Strawberry"]
    required = True
    help_text = "Select all that apply"
    result = await add_checkboxes(
        form_id=form_id, 
        question_text=question_text,
        choices=choices,
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "checkboxes"
    assert result_json["choices"] == choices
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    
    # Check that the choices were set correctly
    choice_question = update_request["requests"][0]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]
    assert choice_question["type"] == "CHECKBOX"
    assert len(choice_question["options"]) == len(choices)
    for i, choice in enumerate(choices):
        assert choice_question["options"][i]["value"] == choice
    assert choice_question["shuffle"] == False

@pytest.mark.asyncio
async def test_add_dropdown(mock_google_services):
    """
    Test that add_dropdown adds a dropdown question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_dropdown function
    question_text = "Select your country"
    choices = ["USA", "Canada", "UK", "Australia"]
    required = True
    help_text = "Select one"
    result = await add_dropdown(
        form_id=form_id, 
        question_text=question_text,
        choices=choices,
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "dropdown"
    assert result_json["choices"] == choices
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    
    # Check that the choices were set correctly
    choice_question = update_request["requests"][0]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]
    assert choice_question["type"] == "DROP_DOWN"
    assert len(choice_question["options"]) == len(choices)
    for i, choice in enumerate(choices):
        assert choice_question["options"][i]["value"] == choice
    assert choice_question["shuffle"] == False

@pytest.mark.asyncio
async def test_add_file_upload(mock_google_services):
    """
    Test that add_file_upload adds a file upload question to a form
    """
    # Set up the mock response
    form_id = "abc123formid"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the add_file_upload function
    question_text = "Upload your resume"
    required = True
    help_text = "PDF files only please"
    result = await add_file_upload(
        form_id=form_id, 
        question_text=question_text,
        required=required,
        help_text=help_text,
        ctx=mock_google_services
    )
    result_json = json.loads(result)
    
    # Check that the question addition was successful
    assert result_json["form_id"] == form_id
    assert result_json["question_text"] == question_text
    assert result_json["type"] == "file_upload"
    assert result_json["required"] == required
    assert result_json["status"] == "success"
    
    # Check that the correct API calls were made
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["createItem"]["item"]["title"] == question_text
    assert update_request["requests"][0]["createItem"]["item"]["required"] == required
    assert update_request["requests"][0]["createItem"]["item"]["description"] == help_text
    
    # Check that it's a file upload question
    assert "fileUploadQuestion" in update_request["requests"][0]["createItem"]["item"]["questionItem"]["question"]

@pytest.mark.asyncio
async def test_get_responses(mock_google_services):
    """
    Test that get_responses retrieves form responses correctly
    """
    # Set up the mock response
    form_id = "abc123formid"
    form_title = "Test Form"
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    
    # Mock the get method
    mock_get = mock_forms_obj.get.return_value
    mock_get.execute.return_value = {
        "formId": form_id,
        "info": {"title": form_title},
        "items": [
            {
                "title": "What is your name?",
                "questionItem": {
                    "question": {
                        "questionId": "q1"
                    }
                }
            },
            {
                "title": "What is your age?",
                "questionItem": {
                    "question": {
                        "questionId": "q2"
                    }
                }
            }
        ]
    }
    
    # Mock the responses.list method
    mock_responses = mock_forms_obj.responses.return_value
    mock_responses_list = mock_responses.list.return_value
    mock_responses_list.execute.return_value = {
        "responses": [
            {
                "responseId": "resp1",
                "createTime": "2023-04-01T12:00:00Z",
                "answers": {
                    "q1": {
                        "textAnswers": {
                            "answers": [
                                {"value": "John Doe"}
                            ]
                        }
                    },
                    "q2": {
                        "textAnswers": {
                            "answers": [
                                {"value": "30"}
                            ]
                        }
                    }
                }
            }
        ]
    }
    
    # Call the get_responses function
    result = await get_responses(form_id=form_id, ctx=mock_google_services)
    result_json = json.loads(result)
    
    # Check that the responses were retrieved successfully
    assert result_json["form_id"] == form_id
    assert result_json["title"] == form_title
    assert result_json["response_count"] == 1
    assert len(result_json["responses"]) == 1
    
    # Check the response details
    response = result_json["responses"][0]
    assert response["response_id"] == "resp1"
    assert response["timestamp"] == "2023-04-01T12:00:00Z"
    assert "What is your name?" in response["answers"]
    assert response["answers"]["What is your name?"] == "John Doe"
    assert "What is your age?" in response["answers"]
    assert response["answers"]["What is your age?"] == "30"
    
    # Check that the correct API calls were made
    mock_forms_obj.get.assert_called_once_with(formId=form_id)
    mock_forms_obj.responses.assert_called_once()
    mock_responses.list.assert_called_once_with(formId=form_id)

@pytest.mark.asyncio
async def test_export_responses(mock_google_services):
    """
    Test that export_responses correctly sets up response export
    """
    # Set up the mock response
    form_id = "abc123formid"
    form_title = "Test Form"
    sheet_id = "xyz789sheetid"
    
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    mock_sheets_obj = mock_google_services.lifespan_context.sheets_service.spreadsheets.return_value
    
    # Mock form get method
    mock_get = mock_forms_obj.get.return_value
    mock_get.execute.return_value = {
        "formId": form_id,
        "info": {"title": form_title},
        "responderUri": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    }
    
    # Call the export_responses function for CSV
    result_csv = await export_responses(form_id=form_id, format="csv", ctx=mock_google_services)
    result_csv_json = json.loads(result_csv)
    
    # Call the export_responses function for sheets
    result_sheets = await export_responses(form_id=form_id, format="sheets", ctx=mock_google_services)
    result_sheets_json = json.loads(result_sheets)
    
    # Check the CSV export result
    assert result_csv_json["form_id"] == form_id
    assert result_csv_json["export_format"] == "csv"
    assert sheet_id in result_csv_json["download_link"]
    
    # Check the Sheets export result
    assert result_sheets_json["form_id"] == form_id
    assert result_sheets_json["export_format"] == "sheets"
    assert result_sheets_json["spreadsheet_id"] == sheet_id
    assert sheet_id in result_sheets_json["spreadsheet_link"]
    
    # Check that the correct API calls were made
    mock_forms_obj.get.assert_called_with(formId=form_id)

@pytest.mark.asyncio
async def test_export_responses_create_new(mock_google_services):
    """
    Test that export_responses creates a new spreadsheet when none exists
    """
    # Set up the mock response
    form_id = "abc123formid"
    form_title = "Test Form"
    new_sheet_id = "new789sheetid"
    
    mock_forms_obj = mock_google_services.lifespan_context.form_service.forms.return_value
    mock_sheets_obj = mock_google_services.lifespan_context.sheets_service.spreadsheets.return_value
    
    # Mock form get method with no responderUri
    mock_get = mock_forms_obj.get.return_value
    mock_get.execute.return_value = {
        "formId": form_id,
        "info": {"title": form_title}
    }
    
    # Mock spreadsheet create method
    mock_create = mock_sheets_obj.create.return_value
    mock_create.execute.return_value = {"spreadsheetId": new_sheet_id}
    
    # Mock form batchUpdate method
    mock_batch_update = mock_forms_obj.batchUpdate.return_value
    mock_batch_update.execute.return_value = {"success": True}
    
    # Call the export_responses function
    result = await export_responses(form_id=form_id, format="csv", ctx=mock_google_services)
    result_json = json.loads(result)
    
    # Check the export result
    assert result_json["form_id"] == form_id
    assert result_json["export_format"] == "csv"
    assert new_sheet_id in result_json["download_link"]
    
    # Check that the correct API calls were made
    mock_forms_obj.get.assert_called_with(formId=form_id)
    mock_sheets_obj.create.assert_called_once()
    
    # Check that we tried to link the form to the spreadsheet
    mock_forms_obj.batchUpdate.assert_called_once()
    update_request = mock_forms_obj.batchUpdate.call_args[1]["body"]
    assert update_request["requests"][0]["updateSettings"]["settings"]["responseDestination"] == "SPREADSHEET"
    assert update_request["requests"][0]["updateSettings"]["settings"]["spreadsheetId"] == new_sheet_id

@pytest.mark.asyncio
async def test_list_forms(mock_google_services):
    """
    Test that list_forms returns all forms correctly
    """
    # Set up the mock response
    mock_drive_obj = mock_google_services.lifespan_context.drive_service.files.return_value
    mock_list = mock_drive_obj.list.return_value
    mock_list.execute.return_value = {
        "files": [
            {
                "id": "form1",
                "name": "Customer Feedback",
                "webViewLink": "https://docs.google.com/forms/d/form1/viewform",
                "createdTime": "2023-01-15T12:00:00Z"
            },
            {
                "id": "form2",
                "name": "Job Application",
                "webViewLink": "https://docs.google.com/forms/d/form2/viewform",
                "createdTime": "2023-02-20T10:30:00Z"
            }
        ]
    }
    
    # Call the list_forms function
    result = await list_forms(ctx=mock_google_services)
    result_json = json.loads(result)
    
    # Check that the forms were listed correctly
    assert len(result_json["forms"]) == 2
    
    # Check the first form details
    form1 = result_json["forms"][0]
    assert form1["id"] == "form1"
    assert form1["name"] == "Customer Feedback"
    assert form1["url"] == "https://docs.google.com/forms/d/form1/viewform"
    assert form1["created"] == "2023-01-15T12:00:00Z"
    
    # Check the second form details
    form2 = result_json["forms"][1]
    assert form2["id"] == "form2"
    assert form2["name"] == "Job Application"
    assert form2["url"] == "https://docs.google.com/forms/d/form2/viewform"
    assert form2["created"] == "2023-02-20T10:30:00Z"
    
    # Check that the correct API calls were made
    mock_drive_obj.list.assert_called_once()
    list_args = mock_drive_obj.list.call_args[1]
    assert list_args["q"] == "mimeType='application/vnd.google-apps.form'"
    assert "id" in list_args["fields"]
    assert "name" in list_args["fields"]
    assert "webViewLink" in list_args["fields"]
    assert "createdTime" in list_args["fields"]

@pytest.mark.asyncio
async def test_list_forms_empty(mock_google_services):
    """
    Test that list_forms handles the case of no forms
    """
    # Set up the mock response with no forms
    mock_drive_obj = mock_google_services.lifespan_context.drive_service.files.return_value
    mock_list = mock_drive_obj.list.return_value
    mock_list.execute.return_value = {"files": []}
    
    # Call the list_forms function
    result = await list_forms(ctx=mock_google_services)
    result_json = json.loads(result)
    
    # Check that the response is formatted correctly
    assert result_json["forms"] == []
    assert "message" in result_json
    assert result_json["message"] == "No forms found"
    
    # Check that the correct API call was made
    mock_drive_obj.list.assert_called_once()