from fastapi import FastAPI

app = FastAPI(title="Bangla Government-Service Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}