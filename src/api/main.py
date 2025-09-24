from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Energy Tariff API",
    description="API for managing energy tariffs and usage data",
    version="1.0.0"
)

# simple request model
class HouseholdData(BaseModel):
    household_size: int

# simple response model
class TariffComparison(BaseModel):
    current_tariff: str
    suggested_tariff: str
    savings: float

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