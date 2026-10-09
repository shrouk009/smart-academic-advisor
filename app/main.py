from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import gpa, pdf, chatbot


app = FastAPI(
    title="Smart Academic Advisor API",
    version="0.1.0",
    description="Backend for Smart Academic Advisor"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    gpa.router,
    prefix="/api/gpa",
    tags=["GPA"]
)

app.include_router(
    pdf.router,
    prefix="/api/pdf",
    tags=["PDF Summarizer"]
)

app.include_router(
    chatbot.router,
    prefix="/api/chatbot",
    tags=["Academic Chatbot"]
)


@app.get("/")
def home():
    return {
        "message": "Smart Academic Advisor API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }