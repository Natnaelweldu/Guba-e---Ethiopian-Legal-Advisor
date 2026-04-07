from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from generator import ask_gubae
from schema import ChatRequest

app = FastAPI()

# --- CORS SETUP ---
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://natnaelweldu.github.io"  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    answer, sources = ask_gubae(request.query)
    
    return {
        "answer": answer,
        "citation": sources
    }

