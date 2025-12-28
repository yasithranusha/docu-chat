from fastapi import FastAPI

app = FastAPI(
    title="DocuChat API",
    description="AI-powered document Q&A system",
    version="0.1.0"
)

@app.get("/")
def root():
    return {
        "message": "DocuChat API is running!",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
