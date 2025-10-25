# %%
from openai import OpenAI;
from dotenv import load_dotenv;
from pypdf import PdfReader;
import json;
import requests;
import os;


# %%
load_dotenv(override=True);

open_ai_api = os.getenv("OPENAI_API_KEY");
pushover_user = os.getenv("PUSHOVER_USER");
pushover_token = os.getenv("PUSHOVER_TOKEN");

openai = OpenAI()


# %%
def push(message):
    return requests.post(
        "https://api.pushover.net/1/messages.json",
        data = {"user": pushover_user, "token": pushover_token, "message": message}
    )

# %%
push("hey")

# %%
def record_user_details(email, name, message="not provides"):
    try:
        push(f"New user details received: \nEmail: {email}\nName: {name}\nMessage: {message}");
    except Exception as e:
        print('API call failed', e)
    return {"recorded": "ok"}


# %%
def record_unknown_question(question):
    try:
        push(f"New unknown question received: \nQuestion: {question}");
    except Exception as e:
        print('API call failed', e)
    return {"recorded": "ok"}


# %%
record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "message": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "The question that couldn't be answered"}}
    },
    "required": ["question"],
    "additionalProperties": False
}

# %%
tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json}
]


# %%
def handle_tool_call(tool_calls):
    results = [];
    for tool_call in tool_calls:
        tool_name = tool_call.function.name;
        args = json.loads(tool_call.function.arguments);
        if tool_name == "record_user_details":
            result = record_user_details(**args)
        elif tool_name == "record_unknown_question":
            result = record_unknown_question(**args)
        results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": tool_call.id});
    return results

# %%
linkedin_pdf_reader = PdfReader("./me/linkedin.pdf");
resume_pdf_reader = PdfReader("./me/resume.pdf");

# %%
linkedin = ""
for page in linkedin_pdf_reader.pages:
    text = page.extract_text();
    if text:
        linkedin += text;

resume = ""
for page in resume_pdf_reader.pages:
    text = page.extract_text();
    if text:
        resume += text;



# %%
with open("./me/summary.txt", "r") as file:
    summary = file.read();


# %%
name = "Krishna Sridhar";


# %%
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so."

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n ## Resume:\n{resume}"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."

# %%
from pydantic import BaseModel

class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

# %%
evaluator_system_prompt = f"""You are an evaluator for a {name}'s website chatbot agent. \
    You are given a conversation between a user and an agent. \
    Your task is to decide whether the Agent's latest response is acceptable quality and determine if it is in character as {name}. \
    You should look for the following: \
    - The chatbot's response is in character as {name}. \
    - The chatbot's response is professional and engaging. \
    - The chatbot's response is helpful and informative. \

    Here is the information:
    Summary: {summary}
    LinkedIn Profile: {linkedin}
    Resume: {resume}"""



# %%
def evaluator_user_prompt(reply, message, history):
    return f"""
    Here is the conversation:
    {history}
    Here is the latest message:
    {message}
    Here is the chatbot's recent message:
    {reply}"""

# %%
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"), 
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# %%
def evaluator(message, reply, history) -> Evaluation:
    messages = [{"role": "system", "content": evaluator_system_prompt}] + [{"role": "user", "content": evaluator_user_prompt(reply, message, history)}]
    response = gemini.beta.chat.completions.parse(model="gemini-2.0-flash", messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed


# %%
def rerun(reply, message, history, feedback):
    updated_system_prompt = system_prompt + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message

# %%
def chat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}];
    done = False;
    reply = ""
    while not done:
        client = OpenAI(api_key=open_ai_api);
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools)
        
        finish_reason = response.choices[0].finish_reason;
        reply = response.choices[0].message;
        print(reply.content, 'res 1')
        if finish_reason == "tool_calls":
            tool_calls = reply.tool_calls;
            results = handle_tool_call(tool_calls);
            messages.append(message);
            messages.extend(results);
        else:
            evaluation = evaluator(reply, message, history)
            print(evaluation)
            if(evaluation.is_acceptable):
                done = True
            else:
                reply = rerun(reply, message, history, evaluation.feedback)
                print(reply.content, 'res 2')
                done = True
            
    return reply.content;

    

# %%


