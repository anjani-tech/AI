#!/usr/bin/env python3

"""
Week 2 Day 2

Our first Agentic Framework project!!

Prepare yourself for something ridiculously easy.

We're going to build a simple Agent system for generating cold sales outreach emails:
1. Agent workflow
2. Use of tools to call functions
3. Agent collaboration via Tools and Handoffs
"""

"""
## Before we start - some setup:

Please visit Resend at: https://resend.com/

(Resend is a modern email API service for sending emails.)

Please set up an account - it's free! (3,000 emails/month on the free tier)

Once you've created an account:

1. Go to: https://resend.com/api-keys
2. Click "Create API Key"
3. Give it a name (e.g., "Sales Email Agent")
4. Copy the API key to your clipboard
5. Add a new line to your .env file:

`RESEND_API_KEY=re_xxxxxxxxxxxxx`

6. Go to: https://resend.com/domains
7. Add and verify your domain (or use the test domain for testing)
8. For testing, you can use the default "onboarding@resend.dev" sender

Note: For production, you'll need to verify your own domain. The free tier allows you to send from verified domains.
"""

from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
from openai.types.responses import ResponseTextDeltaEvent
from typing import Dict
import resend
import os
import asyncio

load_dotenv(override=True)

# Let's just check emails are working for you

def send_test_email():
    """Send a test email using Resend"""
    resend.api_key = os.environ.get('RESEND_API_KEY')
    
    # For testing, you can use onboarding@resend.dev
    # For production, use your verified domain email
    params = {
        "from": "onboarding@resend.dev",  # Change to your verified sender
        "to": ["your-email@example.com"],  # Change to your recipient
        "subject": "Test email",
        "text": "This is an important test email",
    }
    
    email = resend.Emails.send(params)
    print(f"Email sent! ID: {email.get('id')}")
    return email

# send_test_email()

"""
### Did you receive the test email

If you see an email ID printed, then you're good to go!

#### Common issues:

1. **API Key Error**: Make sure your RESEND_API_KEY is set in your .env file
2. **Domain Verification**: For production, verify your domain at https://resend.com/domains
3. **Test Domain**: You can use "onboarding@resend.dev" for testing without domain verification
4. **Check Spam Folder**: Emails might end up in spam initially

#### Other errors or no email

If there are other problems, you'll need to check:
- Your API key in the Resend dashboard: https://resend.com/api-keys
- Your verified sender email address or domain
- The Resend dashboard logs: https://resend.com/emails

(Or - you could always replace the email sending code below with a Pushover call, or something to simply write to a flat file)
"""

# Step 1: Agent workflow

instructions1 = "You are a sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write professional, serious cold emails."

instructions2 = "You are a humorous, engaging sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write witty, engaging cold emails that are likely to get a response."

instructions3 = "You are a busy sales agent working for ComplAI, \
a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI. \
You write concise, to the point cold emails."

sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model="gpt-4o-mini"
)

sales_agent2 = Agent(
        name="Engaging Sales Agent",
        instructions=instructions2,
        model="gpt-4o-mini"
)

sales_agent3 = Agent(
        name="Busy Sales Agent",
        instructions=instructions3,
        model="gpt-4o-mini"
)

# Streaming example (commented out as it requires async context)
# result = Runner.run_streamed(sales_agent1, input="Write a cold sales email")
# async for event in result.stream_events():
#     if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
#         print(event.data.delta, end="", flush=True)

# Parallel execution example
async def parallel_cold_emails():
    message = "Write a cold sales email"
    
    with trace("Parallel cold emails"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message),
        )
    
    outputs = [result.final_output for result in results]
    
    for output in outputs:
        print(output + "\n\n")

sales_picker = Agent(
    name="sales_picker",
    instructions="You pick the best cold sales email from the given options. \
Imagine you are a customer and pick the one you are most likely to respond to. \
Do not give an explanation; reply with the selected email only.",
    model="gpt-4o-mini"
)

async def selection_from_sales_people():
    message = "Write a cold sales email"
    
    with trace("Selection from sales people"):
        results = await asyncio.gather(
            Runner.run(sales_agent1, message),
            Runner.run(sales_agent2, message),
            Runner.run(sales_agent3, message),
        )
        outputs = [result.final_output for result in results]
    
        emails = "Cold sales emails:\n\n" + "\n\nEmail:\n\n".join(outputs)
    
        best = await Runner.run(sales_picker, emails)
    
        print(f"Best sales email:\n{best.final_output}")

"""
Now go and check out the trace:

https://platform.openai.com/traces
"""

"""
## Part 2: use of tools

Now we will add a tool to the mix.

Remember all that json boilerplate and the `handle_tool_calls()` function with the if logic..
"""

# Re-initialize agents for Part 2
sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model="gpt-4o-mini",
)

sales_agent2 = Agent(
        name="Engaging Sales Agent",
        instructions=instructions2,
        model="gpt-4o-mini",
)

sales_agent3 = Agent(
        name="Busy Sales Agent",
        instructions=instructions3,
        model="gpt-4o-mini",
)

"""
## Steps 2 and 3: Tools and Agent interactions

Remember all that boilerplate json?

Simply wrap your function with the decorator `@function_tool`
"""

@function_tool
def send_email(body: str):
    """ Send out an email with the given body to all sales prospects """
    resend.api_key = os.environ.get('RESEND_API_KEY')
    
    params = {
        "from": "onboarding@resend.dev",  # Change to your verified sender
        "to": ["your-email@example.com"],  # Change to your recipient
        "subject": "Sales email",
        "text": body,
    }
    
    email = resend.Emails.send(params)
    return {"status": "success", "email_id": email.get('id')}

"""
### This has automatically been converted into a tool, with the boilerplate json created
"""

"""
### And you can also convert an Agent into a tool
"""

description = "Write a cold sales email"

tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)

tools = [tool1, tool2, tool3, send_email]

"""
## And now it's time for our Sales Manager - our planning agent
"""

# Improved instructions thanks to student Guillermo F.

instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
 
3. Use the send_email tool to send the best email (and only the best email) to the user.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must send ONE email using the send_email tool — never more than one.
"""


async def sales_manager_example():
    sales_manager = Agent(name="Sales Manager", instructions=instructions, tools=tools, model="gpt-4o-mini")
    
    message = "Send a cold sales email addressed to 'Dear CEO'"
    
    with trace("Sales manager"):
        result = await Runner.run(sales_manager, message)
    
    return result

"""
Wait - you didn't get an email??
If you don't receive an email after running the prior cell, here are some things to check: 
First, check your Spam folder! Several students have missed that the emails arrived in Spam!
Second, print(result) and see if you are receiving any errors. 
Check the Resend dashboard at https://resend.com/emails to see the email status and any error messages.
Also look at the trace in OpenAI, and investigate on the Resend website, to hunt for clues. Let me know if I can help!
"""

"""
## Remember to check the trace

https://platform.openai.com/traces

And then check your email!!
"""

"""
### Handoffs represent a way an agent can delegate to an agent, passing control to it

Handoffs and Agents-as-tools are similar:

In both cases, an Agent can collaborate with another Agent

With tools, control passes back

With handoffs, control passes across
"""

subject_instructions = "You can write a subject for a cold sales email. \
You are given a message and you need to write a subject for an email that is likely to get a response."

html_instructions = "You can convert a text email body to an HTML email body. \
You are given a text email body which might have some markdown \
and you need to convert it to an HTML email body with simple, clear, compelling layout and design."

subject_writer = Agent(name="Email subject writer", instructions=subject_instructions, model="gpt-4o-mini")
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

html_converter = Agent(name="HTML email body converter", instructions=html_instructions, model="gpt-4o-mini")
html_tool = html_converter.as_tool(tool_name="html_converter", tool_description="Convert a text email body to an HTML email body")

@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body to all sales prospects """
    resend.api_key = os.environ.get('RESEND_API_KEY')
    
    params = {
        "from": "onboarding@resend.dev",  # Change to your verified sender
        "to": ["your-email@example.com"],  # Change to your recipient
        "subject": subject,
        "html": html_body,
    }
    
    email = resend.Emails.send(params)
    return {"status": "success", "email_id": email.get('id')}

tools_html = [subject_tool, html_tool, send_html_email]

instructions_emailer = "You are an email formatter and sender. You receive the body of an email to be sent. \
You first use the subject_writer tool to write a subject for the email, then use the html_converter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject and HTML body."


emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions_emailer,
    tools=tools_html,
    model="gpt-4o-mini",
    handoff_description="Convert an email to HTML and send it")

"""
### Now we have 3 tools and 1 handoff
"""

tools_final = [tool1, tool2, tool3]
handoffs = [emailer_agent]

# Improved instructions thanks to student Guillermo F.

sales_manager_instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
You can use the tools multiple times if you're not satisfied with the results from the first try.
 
3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""


async def automated_sdr_example():
    sales_manager = Agent(
        name="Sales Manager",
        instructions=sales_manager_instructions,
        tools=tools_final,
        handoffs=handoffs,
        model="gpt-4o-mini")
    
    message = "Send out a cold sales email addressed to Dear CEO from Alice"
    
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
    
    return result

"""
### Remember to check the trace

https://platform.openai.com/traces

And then check your email!!
"""

"""
## Exercise
Can you identify the Agentic design patterns that were used here?
What is the 1 line that changed this from being an Agentic "workflow" to "agent" under Anthropic's definition?
Try adding in more tools and Agents! You could have tools that handle the mail merge to send to a list.
HARD CHALLENGE: research how you can have Resend call a Callback webhook when a user replies to an email,
Then have the SDR respond to keep the conversation going! This may require some "vibe coding" 😂
"""

"""
## Commercial implications
This is immediately applicable to Sales Automation; but more generally this could be applied to  end-to-end automation of any business process through conversations and tools. Think of ways you could apply an Agent solution
like this in your day job.
"""

"""
## Extra note:

Google has released their Agent Development Kit (ADK). It's not yet got the traction of the other frameworks on this course, but it's getting some attention. It's interesting to note that it looks quite similar to OpenAI Agents SDK. To give you a preview, here's a peak at sample code from ADK:

```
root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description="Agent to answer questions about the time and weather in a city.",
    instruction="You are a helpful agent who can answer user questions about the time and weather in a city.",
    tools=[get_weather, get_current_time]
)
```

Well, that looks familiar!

And a student has contributed a customer care agent in community_contributions that uses ADK.
"""

# Main execution (uncomment to run)
if __name__ == "__main__":
    # Uncomment the function you want to run:
    # asyncio.run(parallel_cold_emails())
    # asyncio.run(selection_from_sales_people())
    # asyncio.run(sales_manager_example())
    # asyncio.run(automated_sdr_example())
    pass

