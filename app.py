from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import random
from datetime import datetime
import pandas as pd
import io
import sys
import os

# Add src to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.core.EnergyTariff import FixedTariff, DynamicTariff
from src.core.forecasting.usage_forecasting.UsageForecaster import create_backtest

app = FastAPI(title="DYNERGY API", description="Backend for Dynamic Energy Tariff Comparison")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:5173",  # Default Vite port
        "http://127.0.0.1:5173",
        "http://localhost:4173",  # Vite preview port
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Data models
class UsageData(BaseModel):
    consumption: float
    hasSmartMeter: bool
    preferredTimes: Optional[List[str]] = []

class BasicUserData(BaseModel):
    household_size: int  # 1, 2, or 3+
    annual_consumption: Optional[float] = None  # kWh per year
    has_smart_meter: bool

class TariffRequest(BaseModel):
    annualConsumption: Optional[float] = None
    hasSmartMeter: Optional[bool] = None
    zipCode: Optional[str] = "70173"
    # Frontend compatibility
    annual_kwh: Optional[float] = None
    has_smart_meter: Optional[bool] = None
    tariff_id: Optional[str] = None
    usage_pattern: Optional[str] = None

class TariffResult(BaseModel):
    name: str
    provider: str
    baseFee: float
    workingPrice: float
    totalCost: float
    savings: Optional[float] = None
    features: List[str]

class TariffCalculationResponse(BaseModel):
    tariff_name: str
    monthly_cost: float
    annual_cost: float
    tariff_type: str  # "fixed" or "dynamic"
    avg_kwh_price: float  # Average price per kWh for the forecasted period

class BacktestDataResponse(BaseModel):
    hourly_data: dict
    daily_data: dict
    metrics: dict

# EnBW tariffs as EnergyTariff instances
def create_enbw_tariffs():
    """Create EnBW tariffs using EnergyTariff classes"""
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    return [
        DynamicTariff(
            name="EnBW mobility+ dynamic",
            provider="EnBW",
            base_price=14.90,
            start_date=start_date,
            is_dynamic=True,
            markup=0.18,  # 18ct/kWh markup for premium dynamic tariff
            features=["dynamic", "green"]
        ),
        DynamicTariff(
            name="EnBW easy dynamic", 
            provider="EnBW",
            base_price=9.90,
            start_date=start_date,
            is_dynamic=True,
            markup=0.22,  # 22ct/kWh markup for standard dynamic tariff
            features=["dynamic", "green"]
        ),
        FixedTariff(
            name="EnBW mobility+ Zuhause",
            provider="EnBW", 
            base_price=14.90,
            kwh_rate=0.3299,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False,
            features=["green"]
        ),
        FixedTariff(
            name="EnBW easy+",
            provider="EnBW",
            base_price=9.90, 
            kwh_rate=0.3499,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False,
            features=["green"]
        ),
        FixedTariff(
            name="EnBW Basis",
            provider="EnBW",
            base_price=12.90,
            kwh_rate=0.3699,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False,
            features=["green"]
        ),
        FixedTariff(
            name="Komfort",
            provider="EnBW",
            base_price=15.90,
            kwh_rate=0.3599,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False,
            features=["green"]
        )
    ]

# Create tariff instances
ENBW_TARIFFS = create_enbw_tariffs()

# Mock EnBW tariffs data for frontend compatibility
ENBW_TARIFFS_MOCK = [
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
    """Get available tariffs using real EnergyTariff objects"""
    print("GET /api/tariffs called")  # Debug log
    try:
        # Use real tariff objects
        tariffs = ENBW_TARIFFS
        frontend_tariffs = []
        
        for i, tariff in enumerate(tariffs):
            # Get kwh_rate from tariff object
            kwh_rate = getattr(tariff, 'kwh_rate', 0.30) if not tariff.is_dynamic else 0.25
            
            frontend_tariff = {
                "id": tariff.name.lower().replace(" ", "_").replace("+", "plus"),
                "name": tariff.name,
                "provider": tariff.provider,
                "base_price": tariff.base_price,
                "kwh_price": kwh_rate,
                "is_dynamic": tariff.is_dynamic,
                "features": tariff.features if tariff.features else [],
                "contract_duration": getattr(tariff, 'min_duration', 1),
                "green_energy": "green" in (tariff.features or []),  # Check if 'green' feature exists
                "description": f"{'Dynamischer' if tariff.is_dynamic else 'Fester'} Stromtarif von {tariff.provider}",
                "type": "dynamic" if tariff.is_dynamic else "fixed"
            }
            frontend_tariffs.append(frontend_tariff)
        
        print(f"Returning {len(frontend_tariffs)} tariffs")  # Debug log
        return frontend_tariffs
    
    except Exception as e:
        # Fallback to mock data if real tariffs fail
        print(f"Error loading real tariffs, using mock data: {str(e)}")
        frontend_tariffs = []
        for i, tariff in enumerate(ENBW_TARIFFS_MOCK):
            frontend_tariff = {
                "id": tariff["name"].lower().replace(" ", "_").replace("+", "plus"),
                "name": tariff["name"],
                "provider": tariff["provider"],
                "base_price": tariff["baseFee"],
                "kwh_price": tariff["workingPrice"],
                "is_dynamic": tariff["isDynamic"],
                "features": tariff["features"],
                "contract_duration": 12 if tariff["name"] == "Basis" else 1,
                "green_energy": True,
                "description": f"{'Dynamischer' if tariff['isDynamic'] else 'Fester'} Stromtarif von {tariff['provider']}",
                "type": "dynamic" if tariff["isDynamic"] else "fixed"
            }
            frontend_tariffs.append(frontend_tariff)
        
        return frontend_tariffs

@app.options("/api/tariffs")
async def options_tariffs():
    """Handle preflight OPTIONS request for CORS"""
    return {"message": "OK"}

@app.post("/api/calculate-with-csv")
async def calculate_with_csv(
    file: UploadFile = File(...)
):
    """
    For users WITH smart meters - they upload their CSV data
    Note: household_size is not needed since we use actual consumption data
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read the uploaded CSV
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate CSV has required columns
        if 'datetime' not in df.columns or 'value' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="CSV must have 'datetime' and 'value' columns"
            )
        
        # Convert datetime column
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Calculate costs for each tariff using user's actual data
        tariffs = ENBW_TARIFFS
        print(f"Created {len(tariffs)} tariffs")
        results = []
        
        for tariff in tariffs:
            try:
                print(f"Processing tariff: {tariff.name}, is_dynamic: {tariff.is_dynamic}")
                
                if tariff.is_dynamic:
                    # For dynamic tariffs, use the breakdown method to get average price
                    result = tariff.calculate_cost_with_breakdown(df)
                    cost = result['total_cost']
                    avg_kwh_price = result['avg_kwh_price']
                    print(f"Dynamic tariff - Cost: {cost}, Avg kWh price: {avg_kwh_price:.4f}")
                else:
                    # For fixed tariffs, use regular calculation and get kwh_rate directly
                    cost = tariff.calculate_cost(df)
                    avg_kwh_price = tariff.kwh_rate
                    print(f"Fixed tariff - Cost: {cost}, kWh rate: {avg_kwh_price}")
                
                results.append(TariffCalculationResponse(
                    tariff_name=tariff.name,
                    monthly_cost=cost,
                    annual_cost=cost * 12,
                    tariff_type="dynamic" if tariff.is_dynamic else "fixed",
                    avg_kwh_price=avg_kwh_price
                ))
            except Exception as e:
                # Log the error instead of silently skipping
                print(f"ERROR calculating tariff {tariff.name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Final results: {len(results)} tariffs calculated")
        return {"results": results, "data_source": "uploaded_csv"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/calculate-basic")
async def calculate_basic(user_data: BasicUserData):
    """
    For users WITHOUT smart meters - use synthetic data
    """
    if user_data.has_smart_meter:
        raise HTTPException(
            status_code=400, 
            detail="Use /api/calculate-with-csv for smart meter users"
        )
    
    # Validate household size
    if user_data.household_size not in [1, 2, 3]:
        household_size = 3  # Default to 3+ person household
    else:
        household_size = user_data.household_size
    
    try:
        # Calculate costs using synthetic data
        tariffs = ENBW_TARIFFS
        results = []
        
        print(f"Created {len(tariffs)} tariffs")
        
        for tariff in tariffs:
            print(f"Processing tariff: {tariff.name}, is_dynamic: {tariff.is_dynamic}")
            try:
                print(f"Calculating cost for tariff: {tariff.name}")
                
                if tariff.is_dynamic:
                    # For dynamic tariffs, use the breakdown method
                    result = tariff.calculate_cost_with_breakdown(user_data.annual_consumption or 3500)
                    cost = result['total_cost']
                    avg_kwh_price = result['avg_kwh_price']
                else:
                    # For fixed tariffs, use regular calculation and get kwh_rate directly
                    cost = tariff.calculate_cost(user_data.annual_consumption or 3500)
                    avg_kwh_price = tariff.kwh_rate
                
                print(f"Cost calculated: {cost}")
                
                results.append(TariffCalculationResponse(
                    tariff_name=tariff.name,
                    monthly_cost=cost,
                    annual_cost=cost * 12,
                    tariff_type="fixed" if not tariff.is_dynamic else "dynamic",
                    avg_kwh_price=avg_kwh_price
                ))
            except Exception as e:
                print(f"Error calculating cost for {tariff.name}: {str(e)}")
                # Add a fallback calculation for failed tariffs
                fallback_cost = tariff.base_price + (user_data.annual_consumption or 3500) * 0.30 / 12  # Rough estimate
                fallback_kwh_price = 0.30 if tariff.is_dynamic else (tariff.kwh_rate if hasattr(tariff, 'kwh_rate') else 0.30)
                results.append(TariffCalculationResponse(
                    tariff_name=f"{tariff.name} (estimated)",
                    monthly_cost=fallback_cost,
                    annual_cost=fallback_cost * 12,
                    tariff_type="fixed" if not tariff.is_dynamic else "dynamic",
                    avg_kwh_price=fallback_kwh_price
                ))
                continue
        
        print(f"Final results: {len(results)} tariffs calculated")
        
        if not results:
            raise HTTPException(status_code=500, detail="No tariffs could be calculated")
        
        return {
            "results": results, 
            "data_source": "synthetic_data",
            "household_size": household_size
        }
        
    except Exception as e:
        print(f"General error in calculate_basic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating costs: {str(e)}")

@app.post("/api/backtest-data")
async def get_backtest_data(file: UploadFile = File(...)):
    """
    Generate backtest data for visualization (returns JSON data instead of matplotlib plots)
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read the uploaded CSV
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate CSV has required columns
        if 'datetime' not in df.columns or 'value' not in df.columns:
            raise HTTPException(
                status_code=400, 
                detail="CSV must have 'datetime' and 'value' columns"
            )
        
        # Convert datetime column
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Generate backtest data
        backtest_data = create_backtest(df, return_data=True)
        
        if backtest_data is None:
            raise HTTPException(status_code=500, detail="Failed to generate backtest data")
        
        return BacktestDataResponse(**backtest_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing backtest: {str(e)}")

@app.post("/api/calculate")
async def calculate_tariffs(request: TariffRequest):
    """Calculate tariff costs for given consumption - enhanced with real business logic"""
    
    # Handle both frontend and direct API formats
    annual_consumption = request.annualConsumption or request.annual_kwh or 3500
    has_smart_meter = request.hasSmartMeter if request.hasSmartMeter is not None else request.has_smart_meter
    
    try:
        if request.tariff_id:
            # Frontend sends specific tariff calculation
            # Find the specific tariff
            target_tariff = None
            for tariff in ENBW_TARIFFS:
                tariff_id = tariff.name.lower().replace(" ", "_").replace("+", "plus")
                if tariff_id == request.tariff_id:
                    target_tariff = tariff
                    break
            
            if not target_tariff:
                target_tariff = ENBW_TARIFFS[0]  # fallback
            
            # Use real tariff calculation
            if target_tariff.is_dynamic:
                # For dynamic tariffs, use the breakdown method
                result = target_tariff.calculate_cost_with_breakdown(annual_consumption)
                monthly_cost = result['total_cost']
                working_price = result['avg_kwh_price']
            else:
                # For fixed tariffs, use regular calculation
                monthly_cost = target_tariff.calculate_cost(annual_consumption)
                working_price = target_tariff.kwh_rate
            
            annual_cost = monthly_cost * 12
            
            # Calculate savings potential for smart meter users
            savings_potential = 0
            if has_smart_meter and target_tariff.is_dynamic:
                savings_potential = random.uniform(10, 25)  # 10-25% savings possible
            
            return {
                "annual_cost": annual_cost,
                "monthly_cost": monthly_cost,
                "savings_potential": savings_potential,
                "cost_breakdown": {
                    "base_fee_annual": target_tariff.base_price * 12,
                    "energy_cost_annual": annual_consumption * working_price,
                    "working_price": working_price
                }
            }
        
        else:
            # Return all tariffs comparison using real calculations
            results = []
            
            for tariff in ENBW_TARIFFS:
                try:
                    # Use real tariff calculation
                    if tariff.is_dynamic:
                        # For dynamic tariffs, use the breakdown method
                        result = tariff.calculate_cost_with_breakdown(annual_consumption)
                        monthly_cost = result['total_cost']
                        working_price = result['avg_kwh_price']
                    else:
                        # For fixed tariffs, use regular calculation
                        monthly_cost = tariff.calculate_cost(annual_consumption)
                        working_price = tariff.kwh_rate
                    
                    annual_cost = monthly_cost * 12
                    
                    results.append(TariffResult(
                        name=tariff.name,
                        provider=tariff.provider,
                        baseFee=tariff.base_price,
                        workingPrice=working_price,
                        totalCost=annual_cost,
                        features=["Dynamischer Tarif", "100% Ökostrom"] if tariff.is_dynamic else ["Fester Tarif", "100% Ökostrom"]
                    ))
                    
                except Exception as e:
                    print(f"Error calculating tariff {tariff.name}: {str(e)}")
                    # Fallback calculation
                    fallback_cost = (tariff.base_price * 12) + (annual_consumption * 0.30)
                    results.append(TariffResult(
                        name=f"{tariff.name} (estimated)",
                        provider=tariff.provider,
                        baseFee=tariff.base_price,
                        workingPrice=0.30,
                        totalCost=fallback_cost,
                        features=["Estimated calculation"]
                    ))
            
            # Sort by total cost
            results.sort(key=lambda x: x.totalCost)
            
            # Calculate savings compared to most expensive
            if results:
                highest_cost = max(results, key=lambda x: x.totalCost).totalCost
                for result in results:
                    result.savings = highest_cost - result.totalCost
            
            return results
    
    except Exception as e:
        print(f"Error in calculate_tariffs: {str(e)}")
        # Fallback to mock calculation
        return await calculate_tariffs_mock(request)

async def calculate_tariffs_mock(request: TariffRequest):
    """Fallback calculation using mock data"""
    # Handle both frontend and direct API formats
    annual_consumption = request.annualConsumption or request.annual_kwh or 3500
    has_smart_meter = request.hasSmartMeter if request.hasSmartMeter is not None else request.has_smart_meter
    
    if request.tariff_id:
        # Frontend sends specific tariff calculation
        target_tariff = None
        for tariff in ENBW_TARIFFS_MOCK:
            tariff_id = tariff["name"].lower().replace(" ", "_").replace("+", "plus")
            if tariff_id == request.tariff_id:
                target_tariff = tariff
                break
        
        if not target_tariff:
            target_tariff = ENBW_TARIFFS_MOCK[0]  # fallback
        
        # Mock spot price for dynamic tariffs
        spot_price = random.uniform(0.08, 0.15)  # €/kWh
        
        # Calculate working price
        if target_tariff["isDynamic"]:
            working_price = spot_price + (target_tariff["workingPrice"] - 0.08)  # Add markup
        else:
            working_price = target_tariff["workingPrice"]
        
        # Calculate total cost
        annual_cost = (target_tariff["baseFee"] * 12) + (annual_consumption * working_price)
        
        # Calculate savings potential for smart meter users
        savings_potential = 0
        if has_smart_meter and target_tariff["isDynamic"]:
            savings_potential = random.uniform(10, 25)  # 10-25% savings possible
        
        return {
            "annual_cost": annual_cost,
            "monthly_cost": annual_cost / 12,
            "savings_potential": savings_potential,
            "cost_breakdown": {
                "base_fee_annual": target_tariff["baseFee"] * 12,
                "energy_cost_annual": annual_consumption * working_price,
                "working_price": working_price
            }
        }
    
    else:
        # Return all tariffs comparison
        results = []
        
        # Mock spot price for dynamic tariffs
        spot_price = random.uniform(0.08, 0.15)  # €/kWh
        
        for tariff in ENBW_TARIFFS_MOCK:
            # Calculate working price
            if tariff["isDynamic"]:
                working_price = spot_price + (tariff["workingPrice"] - 0.08)  # Add markup
            else:
                working_price = tariff["workingPrice"]
            
            # Calculate total cost
            annual_cost = (tariff["baseFee"] * 12) + (annual_consumption * working_price)
            
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