from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime
import pandas as pd
import io
from src.core.EnergyTariff import FixedTariff, DynamicTariff

import sys
sys.path.append("../")
from src.core.EnergyTariff import FixedTariff, DynamicTariff

app = FastAPI(title="DYNERGY API", description="Backend for Dynamic Energy Tariff Comparison")

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests
class BasicUserData(BaseModel):
    household_size: int  # 1, 2, or 3+
    annual_consumption: Optional[float] = None  # kWh per year
    has_smart_meter: bool

class TariffCalculationResponse(BaseModel):
    tariff_name: str
    monthly_cost: float
    annual_cost: float
    tariff_type: str  # "fixed" or "dynamic"
    avg_kwh_price: float  # Average price per kWh for the forecasted period
    
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
            is_dynamic=True
        ),
        DynamicTariff(
            name="EnBW easy dynamic", 
            provider="EnBW",
            base_price=9.90,
            start_date=start_date,
            is_dynamic=True
        ),
        FixedTariff(
            name="EnBW mobility+ Zuhause",
            provider="EnBW", 
            base_price=14.90,
            kwh_rate=0.3299,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        ),
        FixedTariff(
            name="EnBW easy+",
            provider="EnBW",
            base_price=9.90, 
            kwh_rate=0.3499,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        ),
        FixedTariff(
            name="EnBW Basis",
            provider="EnBW",
            base_price=12.90,
            kwh_rate=0.3699,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        ),
        FixedTariff(
            name="Komfort",
            provider="EnBW",
            base_price=15.90,
            kwh_rate=0.3599,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        )
    ]

# Create tariff instances
ENBW_TARIFFS = create_enbw_tariffs()

@app.get("/")
async def root():
    return {"message": "DYNERGY API is running", "status": "active"}

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
        tariffs = create_enbw_tariffs()
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
    import os
    
    # Get the project root directory (go up from src/api to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"Project root directory: {project_root}")
    print(f"Current working directory: {os.getcwd()}")
    
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
        tariffs = create_enbw_tariffs()
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

@app.get("/api/tariffs")
async def get_available_tariffs():
    """
    Get list of available tariffs
    """
    tariffs = create_enbw_tariffs()
    return {
        "tariffs": [
            {
                "name": t.name,
                "provider": t.provider,
                "type": "dynamic" if t.is_dynamic else "fixed",
                "base_price": t.base_price,
                "kwh_rate": getattr(t, 'kwh_rate', None)
            } for t in tariffs
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)