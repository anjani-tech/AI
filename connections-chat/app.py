#!/usr/bin/env python3

"""
Professionally You - A Career Chatbot with Tool Use

This script creates a chatbot that represents you based on your LinkedIn profile.
It includes tool use capabilities to:
- Record user interest and contact details
- Track questions that couldn't be answered

The chatbot uses OpenAI's function calling (tool use) feature to interact with
external functions, and sends push notifications via Pushover when events occur.

SETUP INSTRUCTIONS:
1. Visit https://pushover.net/ and sign up for a free account
2. Create an Application/API Token (name it "Agents" or similar)
3. Add to your .env file:
   PUSHOVER_USER=u_xxxxx (from top right of Pushover home screen)
   PUSHOVER_TOKEN=a_xxxxx (from your application page)
4. Install Pushover app on your phone
5. Update me/linkedin.pdf and me/summary.txt with your information
6. Update the 'name' variable below with your name
"""

# =======================
# Imports
# =======================
from dotenv import load_dotenv  # Loads environment variables from .env file
from openai import OpenAI  # OpenAI API client for GPT models
import json  # For parsing JSON data (tool arguments come as JSON strings)
import os  # For accessing environment variables
import requests  # For making HTTP requests to Pushover API
from pypdf import PdfReader  # For reading PDF files (LinkedIn profile)
import gradio as gr  # For creating the web interface

# =======================
# Initialize Environment
# =======================
# Load environment variables from .env file
# override=True means it will overwrite any existing environment variables
load_dotenv(override=True)

# Create OpenAI client instance
# This will use OPENAI_API_KEY from your .env file automatically
openai = OpenAI()

# =======================
# Pushover Configuration
# =======================
# Pushover is a service that sends push notifications to your phone
# Get these values from your .env file after setting up Pushover account

pushover_user = os.getenv("PUSHOVER_USER")  # Your Pushover user key (starts with u_)
pushover_token = os.getenv("PUSHOVER_TOKEN")  # Your Pushover app token (starts with a_)
pushover_url = "https://api.pushover.net/1/messages.json"  # Pushover API endpoint

# Check if Pushover credentials are configured
if pushover_user:
    print(f"Pushover user found and starts with {pushover_user[0]}")
else:
    print("Pushover user not found - push notifications won't work")

if pushover_token:
    print(f"Pushover token found and starts with {pushover_token[0]}")
else:
    print("Pushover token not found - push notifications won't work")

# =======================
# Push Notification Function
# =======================
def push(message):
    """
    Send a push notification to your phone via Pushover.
    
    Args:
        message (str): The message to send as a push notification
    """
    print(f"Push: {message}")
    
    # Check if Pushover credentials are configured
    if not pushover_user or not pushover_token:
        print("ERROR: Pushover credentials not configured. Cannot send push notification.")
        print(f"  pushover_user: {'Found' if pushover_user else 'MISSING'}")
        print(f"  pushover_token: {'Found' if pushover_token else 'MISSING'}")
        return
    
    # Create the payload (data) to send to Pushover API
    payload = {
        "user": pushover_user,
        "token": pushover_token,
        "message": message
    }
    
    # Send POST request to Pushover API
    # This will send a push notification to your phone
    try:
        response = requests.post(pushover_url, data=payload, timeout=10)
        response.raise_for_status()  # Raise an error if the request failed
        
        # Check if the push was successful
        result = response.json()
        if result.get("status") == 1:
            print(f"✓ Push notification sent successfully")
        else:
            print(f"✗ Push notification failed: {result.get('errors', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Error sending push notification: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

# Test the push function (uncomment to test)
# push("HEY!!")

# =======================
# Tool Functions
# =======================
# These are the actual functions that the AI can call (tools)
# The AI will decide when to call these based on the conversation

def record_user_details(email, name="Name not provided", notes="not provided"):
    """
    Record that a user is interested in being contacted.
    This function is called by the AI when a user provides their email.
    
    Args:
        email (str): The user's email address (required)
        name (str): The user's name (optional, defaults to "Name not provided")
        notes (str): Additional context about the conversation (optional)
    
    Returns:
        dict: Confirmation that the details were recorded
    """
    # Send a push notification with the user's information
    push(f"Recording interest from {name} with email {email} and notes {notes}")
    
    # Return a confirmation (the AI will see this response)
    return {"recorded": "ok"}

def record_unknown_question(question):
    """
    Record a question that the AI couldn't answer.
    This helps you identify gaps in knowledge or areas to improve.
    
    Args:
        question (str): The question that couldn't be answered
    
    Returns:
        dict: Confirmation that the question was recorded
    """
    # Send a push notification about the unanswered question
    push(f"Recording {question} asked that I couldn't answer")
    
    return {"recorded": "ok"}

# =======================
# Tool Definitions (JSON Schemas)
# =======================
# These define what tools the AI can use and how to call them
# OpenAI uses these schemas to understand when and how to call our functions

# Schema for record_user_details tool
record_user_details_json = {
    "name": "record_user_details",  # Function name (must match the function above)
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",  # The parameters are an object (dictionary)
        "properties": {  # Define each parameter
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],  # Only email is required, name and notes are optional
        "additionalProperties": False  # Don't allow extra parameters
    }
}

# Schema for record_unknown_question tool
record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            }
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

# =======================
# Tools List
# =======================
# Combine all tool definitions into a list
# This is what we pass to OpenAI so it knows what tools are available
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]

# =======================
# Tool Call Handler
# =======================
# This function executes the tools when the AI decides to call them
# It's like a router that takes tool calls and runs the appropriate function

def handle_tool_calls(tool_calls):
    """
    Execute tool calls requested by the AI.
    
    When the AI wants to use a tool, it returns tool_calls in its response.
    This function:
    1. Extracts the tool name and arguments
    2. Calls the corresponding Python function
    3. Returns the results in a format the AI can understand
    
    Args:
        tool_calls: List of tool call objects from OpenAI response
    
    Returns:
        list: List of tool response messages to send back to the AI
    """
    results = []
    
    # Loop through each tool call (AI might call multiple tools at once)
    for tool_call in tool_calls:
        # Extract the tool name (e.g., "record_user_details")
        tool_name = tool_call.function.name
        
        # Parse the arguments (they come as a JSON string)
        arguments = json.loads(tool_call.function.arguments)
        
        print(f"Tool called: {tool_name}", flush=True)
        
        # Use globals() to get the function by name dynamically
        # This avoids having a big if/elif chain
        # globals() returns a dictionary of all global variables/functions
        tool = globals().get(tool_name)
        
        # Call the function with the arguments if it exists
        # **arguments unpacks the dictionary as keyword arguments
        # Example: record_user_details(email="test@example.com", name="John")
        if tool:
            result = tool(**arguments)
        else:
            result = {}  # If tool not found, return empty dict
        
        # Format the result for the AI
        # The AI expects tool responses in a specific format
        results.append({
            "role": "tool",  # This is a tool response
            "content": json.dumps(result),  # Convert result to JSON string
            "tool_call_id": tool_call.id  # Link this response to the original tool call
        })
    
    return results

# =======================
# Load Profile Data
# =======================
# Load your LinkedIn profile and summary to give the AI context about you

# Read the LinkedIn PDF
reader = PdfReader("me/linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

# Read the summary text file
with open("me/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

# Set your name (UPDATE THIS WITH YOUR NAME!)
name = "Anjani Prakash"  # Change this to your name

# =======================
# System Prompt
# =======================
# This tells the AI how to behave and what its role is
# The system prompt is crucial - it sets the AI's personality and instructions

system_prompt = f"""You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool."""

# Add the context (summary and LinkedIn profile) to the system prompt
system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

# =======================
# Chat Function
# =======================
# This is the main function that handles conversations
# It uses OpenAI's function calling feature to allow the AI to use tools

def chat(message, history):
    """
    Main chat function that handles user messages and tool calls.
    
    This function:
    1. Sends the user's message to OpenAI
    2. Checks if the AI wants to call any tools
    3. If yes, calls the tools and sends results back to the AI
    4. Repeats until the AI has a final answer
    5. Returns the AI's response
    
    Args:
        message (str): The user's message
        history (list): Previous conversation messages
    
    Returns:
        str: The AI's response to the user
    """
    # Build the message list for OpenAI
    # Format: [system message, ...history, new user message]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    
    done = False
    
    # Loop until we get a final answer (not a tool call)
    while not done:
        # Call OpenAI with the messages and available tools
        # The AI will decide if it needs to use any tools
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools  # Tell OpenAI what tools are available
        )
        
        # Check why the AI stopped generating
        finish_reason = response.choices[0].finish_reason
        
        # If the AI wants to call tools, execute them
        if finish_reason == "tool_calls":
            # Get the AI's message (which contains tool calls)
            message_obj = response.choices[0].message
            tool_calls = message_obj.tool_calls
            
            # Execute the tools
            results = handle_tool_calls(tool_calls)
            
            # Add the AI's message (with tool calls) to the conversation
            messages.append(message_obj)
            
            # Add the tool results to the conversation
            # The AI will read these and generate a response
            messages.extend(results)
            
            # Continue the loop - the AI will process the tool results
        else:
            # AI has a final answer, we're done!
            done = True
    
    # Return the AI's final response
    return response.choices[0].message.content

# =======================
# Launch Gradio Interface
# =======================
# Create and launch the web interface
# This creates a nice chat UI that users can interact with

if __name__ == "__main__":
    print("="*60)
    print("Professionally You - Career Chatbot")
    print("="*60)
    print(f"Chatbot representing: {name}")
    print("Launching Gradio interface...")
    print("="*60)
    
    # Create a chat interface using Gradio
    # type="messages" means it uses OpenAI's message format
    gr.ChatInterface(chat, type="messages").launch()

