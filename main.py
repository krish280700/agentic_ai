# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from chatBot import chat  # <-- this imports your chatbot.py logic
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Krishna Sridhar Chatbot API")

origins = [
    "http://127.0.0.1:3000",   # local Next.js
    "http://localhost:3000",   # also common in Next.js
    "https://agentic-ai-ov9y.onrender.com",  # your deployed backend (optional)
    "https://krishna-portfolio-nu.vercel.app/"  # add this when you deploy frontend
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # during dev, allow all; later restrict to your Next.js URL
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
