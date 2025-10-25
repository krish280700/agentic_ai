# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from chatBot import chat  # <-- this imports your chatbot.py logic
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Krishna Sridhar Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during dev, allow all; later restrict to your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list

@app.get("/")
def root():
    return {"message": "Krishna Sridhar Chatbot API is running 🚀"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    reply = chat(request.message, request.history)
    return {"reply": reply}
