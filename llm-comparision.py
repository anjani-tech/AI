#!/usr/bin/env python3

"""
This script compares the performance of different LLMs on a given task.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# =======================
# Setup and Configuration
# =======================

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')


if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")

if google_api_key:
    print(f"Google API Key exists and begins {google_api_key[:8]}")
else:
    print("Google API Key not set")

# =======================
# Generate Question
# =======================

request = "Please come up with a JEE Maths Advanced Question"
request+= "Answer only with the question , no explanation"

messages=  [{"role": "user", "content": request}]

print("\n" + "="*60)
print("Generating question...")
print("="*60)

openai = OpenAI()
response = openai.chat.completions.create(
    model="gpt-5-nano",
    messages=messages,
)
question = response.choices[0].message.content
print(f"\nQuestion: {question}\n")

# 
# =======================
# Initialize Lists for Competitors and Answers
# =======================

competitors = []
answers = []
messages = [{"role": "user", "content": question}]

# =======================
# Query Multiple LLM Models
# =======================

print("\n" + "="*60)
print("Querying Multiple LLM Models")
print("="*60)

# Note: Updated model names to use the latest models below, like GPT 5 and Claude Sonnet 4.5.
# These models can be quite slow - like 1-2 minutes - but they do a great job!
# Feel free to switch them for faster models if you'd prefer.

# ----------------------------------------------------------------------------
# OpenAI GPT
# ----------------------------------------------------------------------------
print("\n[1/3] Querying OpenAI GPT...")
model_name = "gpt-5-nano"
response = openai.chat.completions.create(
    model=model_name,
    messages=messages,
)
answer = response.choices[0].message.content
print(f"\nAnswer: {answer}\n")

competitors.append(model_name)
answers.append(answer)

# ----------------------------------------------------------------------------
# Google Gemini 
# ----------------------------------------------------------------------------
print("\n[2/3] Querying Google Gemini...")
model_name = "gemini-2.0-flash"
google = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
response = google.chat.completions.create(
    model=model_name,
    messages=messages,
)
answer = response.choices[0].message.content
print(f"\nAnswer: {answer}\n")

competitors.append(model_name)
answers.append(answer)

# ----------------------------------------------------------------------------
# Ollama (Local Model)
# ----------------------------------------------------------------------------
print("\n[3/3] Querying Ollama (local)...")
model_name = "llama3.2"
ollama = OpenAI(api_key='ollama', base_url="http://localhost:11434/v1")
response = ollama.chat.completions.create(
    model=model_name,
    messages=messages,
)
answer = response.choices[0].message.content
print(f"\nAnswer: {answer}\n")

competitors.append(model_name)
answers.append(answer)

# =======================
# Display Results
# =======================

print("\n" + "="*60)
print("Summary of Competitors and Answers")
print("="*60)

print(f"\nCompetitors: {competitors}")
print(f"Number of answers: {len(answers)}")

# It's nice to know how to use "zip"
print("\n" + "="*60)
print("All Responses:")
print("="*60)
for competitor, answer in zip(competitors, answers):
    print(f"\nCompetitor: {competitor}\n")
    print(answer)
    print("\n" + "-"*60)

# Let's bring this together - note the use of "enumerate"
together = ""
for index, answer in enumerate(answers):
    together += f"# Response from competitor {index+1}\n\n"
    together += answer + "\n\n"

# =======================
# Judge the Responses
# =======================

print("\n" + "="*60)
print("Judging Responses")
print("="*60)

judge = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""

judge_messages = [{"role": "user", "content": judge}]


print("\nSending to judge (GPT-5-nano)...")
response = openai.chat.completions.create(
    model="gpt-5-nano",
    messages=judge_messages,
)
results = response.choices[0].message.content
print(f"\nJudge's response:\n{results}")

# OK let's turn this into results!
try:
    results_dict = json.loads(results)
    ranks = results_dict["results"]
    print("\nRankings (best to worst):")
    for index, result in enumerate(ranks):
        competitor = competitors[int(result)-1]
        print(f"Rank {index+1}: {competitor}")
except json.JSONDecodeError as e:
    print(f"\nError parsing judge's response as JSON: {e}")
    print("Raw response:")
    print(results)

print("\n" + "="*60)
print("Comparision Complete!")
print("="*60)