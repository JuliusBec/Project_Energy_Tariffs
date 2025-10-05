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
    
# EnBW tariffs as EnergyTariff instances
def create_enbw_tariffs():
    """Create EnBW tariffs using EnergyTariff classes"""
    start_date = datetime.now()
    
    return [
        DynamicTariff(
            name="mobility+ dynamic",
            provider="EnBW",
            base_price=14.90,
            start_date=start_date,
            is_dynamic=True
        ),
        DynamicTariff(
            name="easy dynamic", 
            provider="EnBW",
            base_price=9.90,
            start_date=start_date,
            is_dynamic=True
        ),
        FixedTariff(
            name="mobility+ Zuhause",
            provider="EnBW", 
            base_price=14.90,
            kwh_rate=0.3299,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        ),
        FixedTariff(
            name="easy+",
            provider="EnBW",
            base_price=9.90, 
            kwh_rate=0.3499,
            start_date=start_date,
            min_duration=12,
            is_dynamic=False
        ),
        FixedTariff(
            name="Basis",
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
    file: UploadFile = File(...),
    household_size: int = Form(2)  # Use Form() to properly handle form data
):
    """
    For users WITH smart meters - they upload their CSV data
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
        results = []
        
        for tariff in tariffs:
            try:
                # Pass only the consumption data (DataFrame or None)
                cost = tariff.calculate_cost(df)
                
                results.append(TariffCalculationResponse(
                    tariff_name=tariff.name,
                    monthly_cost=cost,
                    annual_cost=cost * 12,
                    tariff_type="dynamic" if tariff.is_dynamic else "fixed"
                ))
            except Exception as e:
                # Skip tariffs that can't be calculated
                continue
        
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
        tariffs = create_enbw_tariffs()
        results = []
        
        print(f"Created {len(tariffs)} tariffs")
        
        for tariff in tariffs:
            print(f"Processing tariff: {tariff.name}, is_dynamic: {tariff.is_dynamic}")
            try:
                print(f"Calculating cost for tariff: {tariff.name}")
                # Calculate cost for both fixed and dynamic tariffs
                cost = tariff.calculate_cost(user_data.annual_consumption or 3500)
                
                print(f"Cost calculated: {cost}")
                
                results.append(TariffCalculationResponse(
                    tariff_name=tariff.name,
                    monthly_cost=cost,
                    annual_cost=cost * 12,
                    tariff_type="fixed" if not tariff.is_dynamic else "dynamic"
                ))
            except Exception as e:
                print(f"Error calculating cost for {tariff.name}: {str(e)}")
                continue
        
        print(f"Final results: {len(results)} tariffs calculated")
        
        return {
            "results": results, 
            "data_source": "synthetic_data",
            "household_size": household_size
        }
        
    except Exception as e:
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