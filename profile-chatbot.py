#!/usr/bin/env python3

"""
Profile Chatbot - Lab 3 for Week 1 Day 4

This script creates a chatbot that represents a person based on their LinkedIn profile.
It includes evaluation and retry logic to ensure quality responses.

Replace the file in `me/linkedin.pdf` with your own LinkedIn profile PDF.
"""

# =======================
# Imports
# =======================
# If you don't know what any of these packages do - you can always ask ChatGPT for a guide!
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
import os

# =======================
# Setup and Configuration
# =======================
load_dotenv(override=True)
openai = OpenAI()

# =======================
# Load LinkedIn Profile
# =======================
reader = PdfReader("me/linkedin.pdf")
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

# =======================
# Load Summary
# =======================
with open("me/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

# =======================
# Configuration
# =======================
name = "Anjani Prakash"  # Replace with your name

# =======================
# System Prompt Setup
# =======================
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so."

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

# =======================
# Evaluation Model
# =======================
# Create a Pydantic model for the Evaluation
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# =======================
# Evaluator Setup
# =======================
evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
The Agent is playing the role of {name} and is representing {name} on their website. \
The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
The Agent has been provided with context on {name} in the form of their summary and LinkedIn details. Here's the information:"

evaluator_system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
evaluator_system_prompt += f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

def evaluator_user_prompt(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt

# =======================
# Gemini Setup for Evaluation
# =======================
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# =======================
# Evaluation Function
# =======================
def evaluate(reply, message, history) -> Evaluation:
    messages = [{"role": "system", "content": evaluator_system_prompt}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed

# =======================
# Rerun Function
# =======================
def rerun(reply, message, history, feedback):
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content

# =======================
# Chat Function with Evaluation and Retry
# =======================
def chat(message, history):
    """
    Chat function that evaluates responses and retries if needed.
    
    Special note for people not using OpenAI:
    Some providers, like Groq, might give an error when you send your second message in the chat.
    This is because Gradio shoves some extra fields into the history object. OpenAI doesn't mind; but some other models complain.
    If this happens, the solution is to add this first line to clean up the history variable:
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    """
    # Clean up history for non-OpenAI providers if needed
    # history = [{"role": h["role"], "content": h["content"]} for h in history]
    
    # Special handling for patent questions (example)
    if "patent" in message:
        system = system_prompt + "\n\nEverything in your reply needs to be in pig latin - \
              it is mandatory that you respond only and entirely in pig latin"
    else:
        system = system_prompt
    
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = response.choices[0].message.content

    # Evaluate the response
    evaluation = evaluate(reply, message, history)
    
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
    else:
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(reply, message, history, evaluation.feedback)
    
    return reply

# =======================
# Launch Gradio Interface
# =======================
if __name__ == "__main__":
    print("="*60)
    print("Profile Chatbot")
    print("="*60)
    print(f"Chatbot representing: {name}")
    print("Launching Gradio interface...")
    print("="*60)
    
    gr.ChatInterface(chat, type="messages").launch()

