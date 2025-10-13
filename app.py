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

@app.get("/api/forecast")
async def get_price_forecast():
    """Get price forecast for the next 7 days"""
    import random
    from datetime import datetime, timedelta
    
    forecast_data = []
    base_date = datetime.now()
    
    for day in range(7):
        current_date = base_date + timedelta(days=day)
        daily_prices = []
        
        # Simulate realistic hourly price patterns
        for hour in range(24):
            # Lower prices at night (23-6h), higher during peak times (17-20h)
            if 23 <= hour or hour <= 6:  # Night hours
                base_price = random.uniform(0.05, 0.12)
            elif 17 <= hour <= 20:  # Peak hours
                base_price = random.uniform(0.20, 0.35)
            else:  # Regular hours
                base_price = random.uniform(0.12, 0.22)
            
            # Add some volatility
            price = base_price + random.uniform(-0.03, 0.03)
            price = max(0.02, price)  # Minimum price
            
            daily_prices.append({
                "hour": hour,
                "price": round(price, 4),
                "datetime": current_date.replace(hour=hour).isoformat()
            })
        
        forecast_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_name": current_date.strftime("%A"),
            "hourly_prices": daily_prices,
            "avg_price": round(sum(p["price"] for p in daily_prices) / 24, 4),
            "min_price": round(min(p["price"] for p in daily_prices), 4),
            "max_price": round(max(p["price"] for p in daily_prices), 4)
        })
    
    return {
        "forecast": forecast_data,
        "generated_at": datetime.now().isoformat(),
        "currency": "EUR/kWh"
    }

@app.post("/api/predict-savings")
async def predict_savings(usage_data: dict):
    """Predict potential savings with dynamic tariffs"""
    annual_kwh = usage_data.get("annual_kwh", 3500)
    has_smart_meter = usage_data.get("has_smart_meter", False)
    
    # Simulate ML-based predictions
    if has_smart_meter:
        # With smart meter, better optimization possible
        base_savings = random.uniform(15, 35)
        optimization_potential = random.uniform(5, 15)
    else:
        # Without smart meter, limited savings
        base_savings = random.uniform(5, 20)
        optimization_potential = random.uniform(2, 8)
    
    total_potential = base_savings + optimization_potential
    monthly_savings = (annual_kwh * 0.30 * total_potential / 100) / 12  # Assuming 30ct average
    
    return {
        "savings_potential": {
            "percentage": round(total_potential, 1),
            "monthly_euro": round(monthly_savings, 2),
            "annual_euro": round(monthly_savings * 12, 2)
        },
        "recommendations": [
            "Verbrauch in günstige Nachtstunden verschieben" if base_savings > 15 else "Grundlegende Optimierung möglich",
            "Smart Home Integration empfohlen" if has_smart_meter else "Smart Meter Installation empfohlen",
            "E-Auto Ladung zeitoptimiert" if annual_kwh > 5000 else "Haushaltsgeräte zeitgesteuert nutzen"
        ],
        "confidence": "85%" if has_smart_meter else "70%"
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