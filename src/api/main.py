from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Energy Tariff API",
    description="API for managing energy tariffs and usage data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Which domains can access API
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Which HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Which headers are allowed
)

@app.get("/")
def read_root():
    return {"Hello": "World"}