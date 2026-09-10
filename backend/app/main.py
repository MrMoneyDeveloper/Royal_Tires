from fastapi import FastAPI

app = FastAPI(title="Royal Tyres IT Asset Requests", version="0.1.0")


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
