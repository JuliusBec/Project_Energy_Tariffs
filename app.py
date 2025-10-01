from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import random
from datetime import datetime

app = FastAPI(title="DYNERGY API", description="Backend for Dynamic Energy Tariff Comparison")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class UsageData(BaseModel):
    consumption: float
    hasSmartMeter: bool
    preferredTimes: Optional[List[str]] = []

class TariffRequest(BaseModel):
    annualConsumption: float
    hasSmartMeter: bool
    zipCode: Optional[str] = "70173"

class TariffResult(BaseModel):
    name: str
    provider: str
    baseFee: float
    workingPrice: float
    totalCost: float
    savings: Optional[float] = None
    features: List[str]

# Mock EnBW tariffs data
ENBW_TARIFFS = [
    {
        "name": "mobility+ dynamic",
        "provider": "EnBW",
        "baseFee": 14.90,
        "workingPrice": 0.25,  # börsenpreis + 2ct/kWh
        "features": ["Dynamischer Tarif", "E-Mobility Bonus", "100% Ökostrom"],
        "isDynamic": True
    },
    {
        "name": "easy dynamic",
        "provider": "EnBW",
        "baseFee": 9.90,
        "workingPrice": 0.32,  # börsenpreis + 3.5ct/kWh
        "features": ["Dynamischer Tarif", "Keine Mindestlaufzeit", "100% Ökostrom"],
        "isDynamic": True
    },
    {
        "name": "mobility+ Zuhause",
        "provider": "EnBW",
        "baseFee": 14.90,
        "workingPrice": 0.3299,
        "features": ["E-Mobility Bonus", "100% Ökostrom", "Wallbox-Rabatt"],
        "isDynamic": False
    },
    {
        "name": "easy+",
        "provider": "EnBW",
        "baseFee": 9.90,
        "workingPrice": 0.3499,
        "features": ["Keine Mindestlaufzeit", "100% Ökostrom", "Online-Bonus"],
        "isDynamic": False
    },
    {
        "name": "Basis",
        "provider": "EnBW",
        "baseFee": 12.90,
        "workingPrice": 0.3699,
        "features": ["Grundversorgung", "Lokaler Versorger", "Sicherheit"],
        "isDynamic": False
    },
    {
        "name": "Komfort",
        "provider": "EnBW",
        "baseFee": 15.90,
        "workingPrice": 0.3599,
        "features": ["Premium Service", "24h Hotline", "Persönlicher Berater"],
        "isDynamic": False
    }
]

@app.get("/")
async def root():
    return {"message": "DYNERGY API is running", "status": "active"}

@app.get("/api/tariffs")
async def get_tariffs():
    """Get available tariffs"""
    return ENBW_TARIFFS

@app.post("/api/calculate")
async def calculate_tariffs(request: TariffRequest):
    """Calculate tariff costs for given consumption"""
    results = []
    
    # Mock spot price for dynamic tariffs
    spot_price = random.uniform(0.08, 0.15)  # €/kWh
    
    for tariff in ENBW_TARIFFS:
        # Calculate working price
        if tariff["isDynamic"]:
            working_price = spot_price + (tariff["workingPrice"] - 0.08)  # Add markup
        else:
            working_price = tariff["workingPrice"]
        
        # Calculate total cost
        annual_cost = (tariff["baseFee"] * 12) + (request.annualConsumption * working_price)
        
        results.append(TariffResult(
            name=tariff["name"],
            provider=tariff["provider"],
            baseFee=tariff["baseFee"],
            workingPrice=working_price,
            totalCost=annual_cost,
            features=tariff["features"]
        ))
    
    # Sort by total cost
    results.sort(key=lambda x: x.totalCost)
    
    # Calculate savings compared to most expensive
    if results:
        highest_cost = max(results, key=lambda x: x.totalCost).totalCost
        for result in results:
            result.savings = highest_cost - result.totalCost
    
    return results

@app.get("/api/market-prices")
async def get_market_prices():
    """Get current market prices"""
    # Mock market data
    current_price = random.uniform(0.08, 0.15)
    
    return {
        "current_price": current_price,
        "currency": "EUR/kWh",
        "timestamp": datetime.now().isoformat(),
        "forecast": [
            {"hour": i, "price": random.uniform(0.06, 0.18)} 
            for i in range(24)
        ]
    }

@app.get("/api/usage-tips")
async def get_usage_tips():
    """Get energy saving tips"""
    tips = [
        "Nutzen Sie Haushaltsgeräte in den günstigen Nachtstunden",
        "LED-Beleuchtung spart bis zu 80% Strom",
        "Standby-Geräte komplett ausschalten",
        "Heizung um 1°C senken spart 6% Energie",
        "Kühlschrank regelmäßig abtauen",
        "Waschmaschine voll beladen und mit niedrigen Temperaturen",
        "Beim Kochen Deckel verwenden und passende Topfgröße",
        "Smart Home Systeme für automatische Optimierung"
    ]
    
    return {
        "tips": random.sample(tips, 5),
        "savings_potential": f"{random.randint(10, 30)}% Ersparnis möglich"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)