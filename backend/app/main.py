from fastapi import FastAPI

app = FastAPI(title="Школьный журнал", version="1.0.0")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
