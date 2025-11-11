from fastapi import FastAPI, File, HTTPException, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import random
from datetime import datetime
import pandas as pd
import io
import sys
import os
import logging
from src.backend.energy_tariff import FixedTariff, DynamicTariff
from src.backend.forecasting.energy_usage_forecast import create_backtest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


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
    annual_kwh: Optional[float] = None  # Annual consumption in kWh (from CSV data)

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
            network_fee=18.00,  # 18€ one-time network fee for premium dynamic tariff
            features=["dynamic", "green"]
        ),
        DynamicTariff(
            name="EnBW easy dynamic", 
            provider="EnBW",
            base_price=9.90,
            start_date=start_date,
            is_dynamic=True,
            network_fee=22.00,  # 22€ one-time network fee for standard dynamic tariff
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

@app.options("/api/calculate-yearly-usage")
async def options_calculate_yearly_usage():
    """Handle preflight OPTIONS request for CORS"""
    return {"message": "OK"}

@app.post("/api/calculate-yearly-usage")
async def calculate_yearly_usage(
    file: UploadFile = File(...)
):
    """
    Calculate the total yearly usage from an uploaded CSV file.
    Returns the annual kWh consumption extrapolated from the provided data.
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
        
        # Calculate total consumption from the data
        # Note: CSV values are in 15-minute intervals, so divide by 4 to get kWh
        # (since 1 hour = 4 x 15-minute intervals)
        total_consumption = df['value'].sum() / 4
        
        # Calculate the time span of the data
        date_range = (df['datetime'].max() - df['datetime'].min()).total_seconds() / (365.25 * 24 * 3600)
        
        # Extrapolate to yearly consumption if data is less than a year
        if date_range > 0 and date_range < 1:
            annual_kwh = total_consumption / date_range
        else:
            annual_kwh = total_consumption
        
        print(f"CSV Analysis:")
        print(f"  - Data range: {df['datetime'].min()} to {df['datetime'].max()}")
        print(f"  - Time span: {date_range:.2f} years")
        print(f"  - Total consumption in data: {total_consumption:.2f} kWh")
        print(f"  - Extrapolated annual consumption: {annual_kwh:.2f} kWh")
        
        return {
            "annual_kwh": round(annual_kwh, 2),
            "total_consumption": round(total_consumption, 2),
            "data_start": df['datetime'].min().isoformat(),
            "data_end": df['datetime'].max().isoformat(),
            "days_of_data": (df['datetime'].max() - df['datetime'].min()).days,
            "number_of_records": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# =============================================================================
# NEW: CSV + PLZ-specific Scraper Integration
# =============================================================================

class TariffComparisonRequest(BaseModel):
    """Request for tariff comparison with CSV and PLZ"""
    zip_code: str  # Postleitzahl (5-stellig)
    providers: List[str] = ["tibber", "enbw"]  # Anbieter zum Vergleich

@app.post("/api/compare-tariffs-with-csv")
async def compare_tariffs_with_csv(
    file: UploadFile = File(...),
    zip_code: str = Form(...),
    providers: str = Form("tibber,enbw")  # Comma-separated
):
    """
    Tarifvergleich mit hochgeladenen Verbrauchsdaten (CSV) und PLZ-spezifischen Preisen
    
    **Dieser Endpunkt kombiniert:**
    - Hochgeladene CSV-Verbrauchsdaten (echte Smart-Meter Daten)
    - PLZ-spezifische Preise von verschiedenen Anbietern (gescrapt)
    - Prophet-Forecast für zukünftige Börsenstrompreise
    
    **Parameter:**
    - file: CSV-Datei mit Verbrauchsdaten (Spalten: datetime, value)
    - zip_code: Deutsche Postleitzahl (5 Stellen, z.B. "68167")
    - providers: Komma-separierte Liste von Anbietern (z.B. "tibber,enbw")
    
    **Rückgabe:**
    - Tarifvergleich mit realistischen, PLZ-spezifischen Preisen
    - Basierend auf ECHTEN Verbrauchsdaten aus CSV
    """
    try:
        # 1. CSV-Datei validieren und einlesen
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        print(f"\n{'='*80}")
        print(f"📊 CSV-DATEI ANALYSE")
        print(f"{'='*80}")
        print(f"Datei: {file.filename}")
        print(f"Spalten: {list(df.columns)}")
        print(f"Zeilen: {len(df)}")
        print(f"Erste 3 Zeilen:")
        print(df.head(3))
        
        # Flexible Spaltenerkennung
        time_col = None
        value_col = None
        
        # Suche Zeitstempel-Spalte
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['time', 'date', 'zeit', 'datum', 'timestamp']):
                time_col = col
                break
        
        # Suche Verbrauchs-Spalte
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['value', 'consumption', 'verbrauch', 'kwh', 'wh', 'leistung']):
                value_col = col
                break
        
        if not time_col or not value_col:
            raise HTTPException(
                status_code=400,
                detail=f"CSV-Spalten nicht erkannt. Gefunden: {list(df.columns)}. Erwartet: Zeitstempel + Verbrauchswert"
            )
        
        print(f"✓ Erkannte Zeitstempel-Spalte: '{time_col}'")
        print(f"✓ Erkannte Verbrauchs-Spalte: '{value_col}'")
        
        # Normalisiere Spaltennamen
        df['datetime'] = pd.to_datetime(df[time_col])
        df['value'] = pd.to_numeric(df[value_col], errors='coerce')
        
        # Entferne NaN-Werte
        original_len = len(df)
        df = df.dropna(subset=['datetime', 'value'])
        if len(df) < original_len:
            print(f"⚠️  {original_len - len(df)} Zeilen mit ungültigen Werten entfernt")
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Keine gültigen Daten in CSV gefunden")
        
        # 2. Jahresverbrauch aus CSV berechnen
        # Erkenne automatisch das Intervall
        if len(df) > 1:
            time_diff_seconds = (df['datetime'].iloc[1] - df['datetime'].iloc[0]).total_seconds()
            if time_diff_seconds <= 900:  # 15 Minuten
                interval_factor = 4  # 4 x 15min = 1 Stunde
            elif time_diff_seconds <= 3600:  # 1 Stunde
                interval_factor = 1  # Werte sind bereits kWh
            else:
                interval_factor = 1  # Fallback
        else:
            interval_factor = 1
        
        total_consumption = df['value'].sum() / interval_factor
        date_range_years = (df['datetime'].max() - df['datetime'].min()).total_seconds() / (365.25 * 24 * 3600)
        
        if 0 < date_range_years < 1:
            annual_kwh = total_consumption / date_range_years
        else:
            annual_kwh = total_consumption
        
        print(f"\n{'='*80}")
        print(f"📊 CSV-VERBRAUCHSDATEN ANALYSE")
        print(f"{'='*80}")
        print(f"Datei: {file.filename}")
        print(f"PLZ: {zip_code}")
        print(f"Zeitraum: {df['datetime'].min()} bis {df['datetime'].max()}")
        print(f"Daten: {len(df)} Einträge ({date_range_years:.2f} Jahre)")
        print(f"Jahresverbrauch: {annual_kwh:.2f} kWh")
        print(f"{'='*80}\n")
        
        # 3. Anbieter scrapen und Tarife erstellen
        provider_list = [p.strip() for p in providers.split(",")]
        tariffs = []
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for provider in provider_list:
            try:
                print(f"\n🔍 Scrape {provider.upper()} für PLZ {zip_code}...")
                
                if provider.lower() == "tibber":
                    from src.webscraping.scraper_tibber import TibberScraper
                    scraper = TibberScraper(debug_mode=False)
                    scraped_data = scraper.scrape_tariff(
                        zip_code=zip_code,
                        annual_consumption=int(annual_kwh)
                    )
                    
                    tariff = DynamicTariff(
                        name="Tibber Dynamic",
                        provider="Tibber",
                        base_price=scraped_data['total_base_monthly'],
                        start_date=start_date,
                        network_fee=0,
                        postal_code=zip_code,
                        additional_price_ct_kwh=scraped_data['additional_price_ct']
                    )
                    tariffs.append(('Tibber', tariff, scraped_data))
                    print(f"   ✓ Grundpreis: {scraped_data['total_base_monthly']:.2f} €/Mon")
                    print(f"   ✓ Zusatz-Komponenten: {scraped_data['additional_price_ct']:.2f} ct/kWh")
                    
                elif provider.lower() == "enbw":
                    from src.webscraping.scraper_enbw import EnbwScraper
                    scraper = EnbwScraper(headless=True, debug=False, use_edge=False)
                    scraped_data = scraper.scrape_tariff(
                        zip_code=zip_code,
                        annual_consumption=int(annual_kwh)
                    )
                    
                    tariff = DynamicTariff(
                        name="EnBW Dynamisch",
                        provider="EnBW",
                        base_price=scraped_data['base_price_monthly'],
                        start_date=start_date,
                        network_fee=0,
                        postal_code=zip_code,
                        additional_price_ct_kwh=scraped_data['markup_ct_kwh']
                    )
                    tariffs.append(('EnBW', tariff, scraped_data))
                    print(f"   ✓ Grundpreis: {scraped_data['base_price_monthly']:.2f} €/Mon")
                    print(f"   ✓ Zusatz-Komponenten: {scraped_data['markup_ct_kwh']:.2f} ct/kWh")
                
            except Exception as e:
                print(f"   ❌ Fehler beim Scrapen von {provider}: {e}")
                continue
        
        # 4. Kosten für jeden Tarif mit ECHTEN CSV-Daten berechnen
        results = []
        
        for provider_name, tariff, scraped_data in tariffs:
            try:
                print(f"\n💰 Berechne Kosten für {provider_name} mit CSV-Daten...")
                
                # Verwende die ECHTEN Verbrauchsdaten aus der CSV!
                result = tariff.calculate_cost_with_breakdown(df)
                
                results.append({
                    "provider": provider_name,
                    "tariff_name": tariff.name,
                    "base_price_monthly": tariff.base_price,
                    "additional_price_ct_kwh": tariff.additional_price_ct_kwh,
                    "avg_kwh_price_ct": result['avg_kwh_price'] * 100,
                    "monthly_cost": result['total_cost'],
                    "annual_cost": result['total_cost'] * 12,
                    "postal_code": zip_code,
                    "data_source": "csv_uploaded"
                })
                
                print(f"   ✓ Durchschnitt: {result['avg_kwh_price']*100:.2f} ct/kWh")
                print(f"   ✓ Monatliche Kosten: {result['total_cost']:.2f} €")
                
            except Exception as e:
                print(f"   ❌ Fehler bei Berechnung für {provider_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # 5. Sortiere nach Kosten
        results.sort(key=lambda x: x['monthly_cost'])
        
        # 6. Berechne Ersparnis
        if len(results) > 1:
            cheapest = results[0]['monthly_cost']
            for r in results[1:]:
                r['savings_monthly'] = r['monthly_cost'] - cheapest
                r['savings_annual'] = r['savings_monthly'] * 12
        
        print(f"\n{'='*80}")
        print(f"✅ VERGLEICH ABGESCHLOSSEN")
        print(f"{'='*80}\n")
        
        return {
            "success": True,
            "zip_code": zip_code,
            "annual_consumption_kwh": round(annual_kwh, 2),
            "data_source": "uploaded_csv",
            "csv_filename": file.filename,
            "csv_date_range": {
                "start": df['datetime'].min().isoformat(),
                "end": df['datetime'].max().isoformat(),
                "days": (df['datetime'].max() - df['datetime'].min()).days
            },
            "tariffs": results,
            "cheapest_provider": results[0]['provider'] if results else None
        }
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# Original CSV endpoint (ohne Scraper-Integration)
# =============================================================================

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
        
        # Calculate total consumption and extrapolate to yearly
        # Note: CSV values are in 15-minute intervals, so divide by 4 to get kWh
        # (since 1 hour = 4 x 15-minute intervals)
        total_consumption = df['value'].sum() / 4
        date_range = (df['datetime'].max() - df['datetime'].min()).total_seconds() / (365.25 * 24 * 3600)
        
        # Extrapolate to yearly consumption if data is less than a year
        if date_range > 0 and date_range < 1:
            annual_kwh = total_consumption / date_range
        else:
            annual_kwh = total_consumption
        
        # DEBUG: Print uploaded data info
        print(f"\n{'='*80}")
        print(f"UPLOADED CSV FILE: {file.filename}")
        print(f"Data shape: {df.shape}")
        print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
        print(f"Total consumption: {total_consumption:.2f} kWh")
        print(f"Time span: {date_range:.2f} years")
        print(f"Extrapolated annual consumption: {annual_kwh:.2f} kWh")
        print(f"Average hourly consumption: {df['value'].mean():.4f} kWh")
        print(f"First 5 rows:\n{df.head()}")
        print(f"{'='*80}\n")
        
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
                    avg_kwh_price=avg_kwh_price,
                    annual_kwh=round(annual_kwh, 2)
                ))
            except Exception as e:
                # Log the error instead of silently skipping
                print(f"ERROR calculating tariff {tariff.name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Final results: {len(results)} tariffs calculated")
        return {
            "results": results, 
            "data_source": "uploaded_csv",
            "annual_kwh": round(annual_kwh, 2)
        }
        
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

@app.get("/api/price-chart-data")
async def get_price_chart_data():
    """Get historical and forecast price data for chart visualization"""
    try:
        from src.backend.forecasting.energy_price_forecast import create_chart_data
        
        # Generate chart data
        chart_data = create_chart_data()
        
        if chart_data is None:
            raise HTTPException(status_code=500, detail="Failed to generate price chart data")
        
        return chart_data
        
    except Exception as e:
        print(f"Error generating price chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating price chart data: {str(e)}")

@app.get("/api/price-breakdown")
async def get_price_breakdown():
    """Get energy price component breakdown for doughnut chart visualization"""
    try:
        from src.backend.forecasting.energy_price_forecast import get_price_breakdown
        
        # Generate price breakdown data
        breakdown_data = get_price_breakdown()
        
        if breakdown_data is None:
            raise HTTPException(status_code=500, detail="Failed to generate price breakdown data")
        
        return breakdown_data
        
    except Exception as e:
        print(f"Error generating price breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating price breakdown: {str(e)}")

@app.get("/api/forecast")
async def get_price_forecast():
    """Get price forecast for the next 7 days from Prophet model"""
    import os
    import pandas as pd
    from datetime import datetime
    
    try:
        # Load the actual Prophet forecast data
        project_root = os.path.dirname(os.path.abspath(__file__))
        app_data_path = os.path.join(project_root, "app_data")
        
        # Find the most recent price forecast file
        forecast_files = [f for f in os.listdir(app_data_path) if f.startswith('germany_price_forecast_') and f.endswith('.csv')]
        if not forecast_files:
            raise FileNotFoundError("No price forecast files found")
        
        latest_forecast_file = sorted(forecast_files)[-1]
        forecast_path = os.path.join(app_data_path, latest_forecast_file)
        
        # Read forecast data
        df = pd.read_csv(forecast_path)
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Use only next 7 days (168 hours)
        df = df.head(168)
        
        # Convert yhat_energy from EUR/MWh to EUR/kWh
        df['price_eur_kwh'] = df['yhat_energy'] / 10 / 100  # EUR/MWh -> ct/kWh -> EUR/kWh
        
        # Group by day
        forecast_data = []
        for date in df['ds'].dt.date.unique()[:7]:
            day_data = df[df['ds'].dt.date == date]
            
            hourly_prices = []
            for _, row in day_data.iterrows():
                hourly_prices.append({
                    "hour": row['ds'].hour,
                    "price": round(row['price_eur_kwh'], 4),
                    "datetime": row['ds'].isoformat()
                })
            
            forecast_data.append({
                "date": str(date),
                "day_name": pd.Timestamp(date).strftime("%A"),
                "hourly_prices": hourly_prices,
                "avg_price": round(day_data['price_eur_kwh'].mean(), 4),
                "min_price": round(day_data['price_eur_kwh'].min(), 4),
                "max_price": round(day_data['price_eur_kwh'].max(), 4)
            })
        
        return {
            "forecast": forecast_data,
            "generated_at": datetime.now().isoformat(),
            "currency": "EUR/kWh",
            "source": "prophet_model"
        }
        
    except Exception as e:
        # Fallback to mock data if Prophet data not available
        import random
        from datetime import datetime, timedelta
        print(f"⚠️ Could not load Prophet forecast: {e}, using mock data")
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

@app.post("/api/risk-analysis")
async def get_risk_analysis(file: UploadFile = File(...), days: int = Form(30)):
    """
    Perform comprehensive risk analysis on user consumption data.
    Returns historic risk analysis, coincidence factor, and load profile data.
    """
    import traceback
    from src.backend.risk_analysis import (
        create_historic_risk_analysis,
        calculate_coincidence_factor,
        get_user_load_profile
    )
    
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
        
        # Determine app_data directory
        app_data_dir = os.path.join(os.path.dirname(__file__), "app_data")
        
        # Calculate all risk metrics
        historic_risk = create_historic_risk_analysis(df, days=days, app_data_dir=app_data_dir)
        coincidence = calculate_coincidence_factor(df, days=days, expensive_hours_pct=20.0, app_data_dir=app_data_dir)
        load_profile = get_user_load_profile(df, days=days, app_data_dir=app_data_dir)
        
        return {
            "historic_risk": historic_risk,
            "coincidence_factor": coincidence,
            "load_profile": load_profile
        }
        
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"FileNotFoundError in risk analysis: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=404, detail=error_msg)
    except ValueError as e:
        error_msg = str(e)
        print(f"ValueError in risk analysis: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error processing risk analysis: {str(e)}"
        print(f"Unexpected error in risk analysis: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/risk-score")
async def get_risk_score(file: UploadFile = File(...), days: int = Form(30)):
    """
    Get aggregated risk score for dynamic tariff suitability.
    Returns a simple low/moderate/high risk assessment.
    """
    import traceback
    from src.backend.risk_analysis import (
        create_historic_risk_analysis,
        calculate_coincidence_factor,
        get_aggregated_risk_score
    )
    
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
        
        # Determine app_data directory
        app_data_dir = os.path.join(os.path.dirname(__file__), "app_data")
        
        # Calculate risk metrics
        historic_risk = create_historic_risk_analysis(df, days=days, app_data_dir=app_data_dir)
        coincidence = calculate_coincidence_factor(df, days=days, expensive_hours_pct=20.0, app_data_dir=app_data_dir)
        
        # Get aggregated risk score
        risk_assessment = get_aggregated_risk_score(historic_risk, coincidence)
        
        return risk_assessment
        
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"FileNotFoundError in risk score: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=404, detail=error_msg)
    except ValueError as e:
        error_msg = str(e)
        print(f"ValueError in risk score: {error_msg}")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error calculating risk score: {str(e)}"
        print(f"Unexpected error in risk score: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)


# =============================================================================
# SCRAPER ENDPOINTS - EnBW, Tado, Tibber
# =============================================================================

# Helper function to create DynamicTariff objects from scraper data
def create_dynamic_tariff_from_scraper(scraper_data: dict, provider: str) -> DynamicTariff:
    """
    Create a DynamicTariff object from scraper response data.
    
    Args:
        scraper_data: Raw scraper response dictionary
        provider: Provider name (e.g., "EnBW", "Tado", "Tibber")
    
    Returns:
        DynamicTariff: Configured tariff object with scraped pricing data
    """
    from datetime import datetime
    
    # Extract common fields
    base_price = scraper_data.get("total_base_monthly", scraper_data.get("base_price_monthly", 0))
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Extract provider-specific additional_price_ct_kwh
    additional_price_ct_kwh = None
    network_fee = 0
    
    if provider.lower() == "tibber":
        # Tibber: additional_price_ct enthält Netzentgelte, Steuern, Umlagen (~18.4 ct/kWh)
        additional_price_ct_kwh = scraper_data.get("additional_price_ct", 18.4)
        network_fee = 0  # Bei Tibber in base_price enthalten
        
    elif provider.lower() == "enbw":
        # EnBW: markup_ct_kwh enthält die festen Komponenten (Netzentgelte + Steuern + Umlagen)
        # Diese werden direkt als ct/kWh berechnet, NICHT als einmalige network_fee!
        additional_price_ct_kwh = scraper_data.get("markup_ct_kwh", 18.4)
        network_fee = 0  # EnBW hat keine einmalige Netzgebühr, alles ist im markup_ct_kwh
        
    elif provider.lower() == "tado":
        # Tado: Monatliche Netzgebühr umrechnen in ct/kWh
        annual_consumption = scraper_data.get("annual_consumption", 2500)
        network_fee_monthly = scraper_data.get("network_fee_monthly", 51.85)
        # (51.85€/Monat * 12) / annual_consumption * 100 = ct/kWh
        additional_price_ct_kwh = (network_fee_monthly * 12 / annual_consumption * 100) if annual_consumption > 0 else 18.4
        network_fee = 0  # Bei Tado monatlich, nicht einmalig
    
    # Fallback auf default, falls nicht gesetzt
    if additional_price_ct_kwh is None:
        additional_price_ct_kwh = 18.4
    
    # Create DynamicTariff object
    tariff = DynamicTariff(
        name=scraper_data.get("tariff_name", f"{provider} Dynamic"),
        provider=provider,
        base_price=base_price,
        start_date=start_date,
        is_dynamic=True,
        network_fee=network_fee,
        features=["dynamic", "real-time-pricing", "smart-meter-required"],
        postal_code=scraper_data.get("zip_code"),
        additional_price_ct_kwh=additional_price_ct_kwh  # ← NEUE PARAMETER!
    )
    
    return tariff


# Helper function to convert scraper data to EnergyTariff-compatible dict (legacy)
def scraper_to_tariff(scraper_data: dict, provider: str, tariff_type: str = "dynamic") -> dict:
    """
    Convert scraper response data to EnergyTariff-compatible format.
    
    Args:
        scraper_data: Raw scraper response dictionary
        provider: Provider name (e.g., "EnBW", "Tado", "Tibber")
        tariff_type: Type of tariff ("dynamic" or "fixed")
    
    Returns:
        dict: EnergyTariff-compatible data structure
    """
    from datetime import datetime
    
    # Base tariff data
    tariff_dict = {
        "name": scraper_data.get("tariff_name", f"{provider} Dynamic"),
        "provider": provider,
        "is_dynamic": tariff_type == "dynamic",
        "start_date": datetime.now().isoformat(),
        "features": ["dynamic", "real-time-pricing", "smart-meter-required"]
    }
    
    # Provider-specific data mapping
    if provider == "EnBW":
        # EnBW: markup_ct_kwh enthält Netznutzung, Steuern, Umlagen
        tariff_dict.update({
            "base_price": scraper_data.get("base_price_monthly", 0),
            "kwh_rate": scraper_data.get("exchange_price_ct_kwh", 0) / 100 if scraper_data.get("exchange_price_ct_kwh") else 0,  # Börsenpreis
            "network_fee": 0,  # Bei EnBW nicht separat
            "additional_price_ct_kwh": scraper_data.get("markup_ct_kwh", 15.36),  # Netzentgelte, Steuern, Umlagen in ct/kWh
            "min_duration": None
        })
    elif provider == "Tado":
        # Tado: markup_ct_kwh enthält nur Netzentgelte/Steuern (ohne aktuellen Börsenpreis)
        # Der Scraper berechnet: kwh_price_ct (gesamt) - tatsächlicher Börsenpreis = markup_ct_kwh
        tariff_dict.update({
            "base_price": scraper_data.get("base_price_monthly", 0),
            "kwh_rate": 0,  # Forecast-Preis wird später verwendet
            "network_fee": 0,  # Bei Tado im markup_ct_kwh enthalten
            "additional_price_ct_kwh": scraper_data.get("markup_ct_kwh", 18.0),  # Nur Markup (Netz + Steuern, ohne Börse)
            "min_duration": None
        })
    elif provider == "Tibber":
        # Tibber: additional_price_ct_kwh enthält alle Zusatzkosten (18,25 ct/kWh)
        tariff_dict.update({
            "base_price": scraper_data.get("base_price_monthly", 0),  # Grundpreis
            "kwh_rate": 0,  # Forecast-Preis wird später verwendet
            "network_fee": 0,  # Bei Tibber in additional_price_ct_kwh enthalten
            "additional_price_ct_kwh": scraper_data.get("additional_price_ct_kwh", 18.25),  # Netzentgelte + Steuern + Umlagen
            "min_duration": None
        })
    
    return tariff_dict


# ============================================================
# EnBW Dynamic Tariff Scraper Endpoint (NEW)
# ============================================================

class EnbwScraperRequest(BaseModel):
    """Request model for EnBW scraper"""
    zip_code: str  # Postleitzahl (5-stellig)
    annual_consumption: float  # Jahresverbrauch in kWh
    headless: bool = True  # Browser im Headless-Modus
    debug_mode: bool = False  # Debug-Ausgaben und Screenshots

class EnbwScraperResponse(BaseModel):
    """Response model for EnBW scraper"""
    success: bool
    provider: str
    tariff_name: str
    base_price_monthly: Optional[float] = None
    markup_ct_kwh: Optional[float] = None
    exchange_price_ct_kwh: Optional[float] = None
    total_kwh_price_ct: Optional[float] = None
    monthly_cost_example: Optional[float] = None
    zip_code: str
    annual_consumption: float
    timestamp: str
    source_url: str
    error: Optional[str] = None

@app.post("/api/scrape/enbw")
async def scrape_enbw_tariff(request: EnbwScraperRequest):
    """
    Scrape real-time pricing from EnBW dynamic tariff page using Playwright
    
    This endpoint uses Playwright to scrape actual prices from the EnBW website
    for the given zip code and annual consumption.
    
    - **zip_code**: German postal code (5 digits, e.g., "71065")
    - **annual_consumption**: Annual consumption in kWh (e.g., 2250)
    
    Returns real-time pricing data including:
    - Base price (monthly, €)
    - Markup price (ct/kWh)
    - Average exchange price (ct/kWh, variable)
    - Total kWh price (ct/kWh)
    - Example monthly cost (€)
    """
    try:
        # Import EnBW scraper
        from src.webscraping.scraper_enbw import scrape_enbw_tariff as scrape_tariff
        
        logger.info(f"🔍 EnBW Scraper API Request: PLZ {request.zip_code}, {request.annual_consumption} kWh")
        
        # Scrape data using async function
        result = await scrape_tariff(
            zip_code=request.zip_code,
            annual_consumption=request.annual_consumption
        )
        
        if result and 'provider' in result:
            # Success
            response = EnbwScraperResponse(
                success=True,
                provider=result.get('provider', 'EnBW'),
                tariff_name=result.get('tariff_name', 'Dynamischer Stromtarif'),
                base_price_monthly=result.get('base_price_monthly'),
                markup_ct_kwh=result.get('markup_ct_kwh'),
                exchange_price_ct_kwh=result.get('exchange_price_ct_kwh'),
                total_kwh_price_ct=result.get('total_kwh_price_ct'),
                monthly_cost_example=result.get('monthly_cost_example'),
                zip_code=result.get('zip_code', request.zip_code),
                annual_consumption=result.get('annual_consumption', request.annual_consumption),
                timestamp=result.get('scraped_at', datetime.now().isoformat()),
                source_url=result.get('url', 'https://www.enbw.com/strom/dynamischer-stromtarif')
            )
            
            logger.info(f"✅ EnBW Scraping erfolgreich: {response.base_price_monthly} €/Mon, {response.markup_ct_kwh} ct/kWh (Quelle: {result.get('data_source')})")
            
            return response
        else:
            # Scraping failed
            raise HTTPException(
                status_code=500,
                detail="Scraping fehlgeschlagen - keine Daten erhalten"
            )
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"EnBW Scraper nicht verfügbar: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Scraping Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return EnbwScraperResponse(
            success=False,
            provider="EnBW",
            tariff_name="Dynamischer Stromtarif",
            zip_code=request.zip_code,
            annual_consumption=request.annual_consumption,
            timestamp=datetime.now().isoformat(),
            source_url="https://www.enbw.com/strom/dynamischer-stromtarif",
            error=str(e)
        )


# ============================================================
# Tado Energy Tariff Scraper Endpoint (NEW)
# ============================================================

class TadoScraperRequest(BaseModel):
    """Request model for Tado scraper"""
    zip_code: str
    annual_consumption: float
    headless: bool = True
    debug_mode: bool = False

class TadoScraperResponse(BaseModel):
    """Response model for Tado scraper"""
    success: bool
    provider: str
    tariff_name: str
    base_price_monthly: Optional[float] = None
    kwh_price_ct: Optional[float] = None
    monthly_cost: Optional[float] = None
    annual_cost: Optional[float] = None
    zip_code: str
    annual_consumption: float
    timestamp: str
    source_url: str
    note: Optional[str] = None
    error: Optional[str] = None

@app.post("/api/scrape/tado")
async def scrape_tado_tariff(request: TadoScraperRequest):
    """
    Scrape real-time pricing from Tado Energy using Playwright
    
    This endpoint uses Playwright to scrape actual prices from the Tado Energy website
    for the given zip code and annual consumption.
    
    - **zip_code**: German postal code (5 digits, e.g., "71065")
    - **annual_consumption**: Annual consumption in kWh (e.g., 2500)
    
    Returns pricing data including:
    - Base price (monthly, €)
    - kWh price (ct/kWh, dynamic/variable)
    - Monthly cost (€)
    - Annual cost (€)
    """
    try:
        # Import Tado scraper
        from src.webscraping.scraper_tado import scrape_tado_tariff as scrape_tariff
        
        logger.info(f"🔍 Tado Energy API Request: PLZ {request.zip_code}, {request.annual_consumption} kWh")
        
        # Scrape data using async function
        result = await scrape_tariff(
            zip_code=request.zip_code,
            annual_consumption=request.annual_consumption
        )
        
        if result and 'provider' in result:
            # Success
            response = TadoScraperResponse(
                success=True,
                provider=result.get('provider', 'Tado Energy'),
                tariff_name=result.get('tariff_name', 'Tado Hourly'),
                base_price_monthly=result.get('base_price_monthly'),
                kwh_price_ct=result.get('kwh_price_ct'),
                monthly_cost=result.get('monthly_cost_estimated'),
                annual_cost=result.get('annual_cost_estimated'),
                zip_code=result.get('zip_code', request.zip_code),
                annual_consumption=result.get('annual_consumption_kwh', request.annual_consumption),
                timestamp=result.get('scraped_at', datetime.now().isoformat()),
                source_url=result.get('url', 'https://energy.tado.com'),
                note=f"Quelle: {result.get('data_source')}"
            )
            
            logger.info(f"✅ Tado scraping erfolgreich: {response.base_price_monthly} €/Mon, {response.kwh_price_ct} ct/kWh (Quelle: {result.get('data_source')})")
            
            return response
        else:
            # Failed
            raise HTTPException(
                status_code=500,
                detail="Scraping fehlgeschlagen - keine Daten erhalten"
            )
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Tado Scraper nicht verfügbar: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return TadoScraperResponse(
            success=False,
            provider="Tado Energy",
            tariff_name="Tado Dynamic",
            zip_code=request.zip_code,
            annual_consumption=request.annual_consumption,
            timestamp=datetime.now().isoformat(),
            source_url="https://energy.tado.com",
            error=str(e)
        )


# =============================================================================
# TIBBER SCRAPER ENDPOINT
# =============================================================================

class TibberScraperRequest(BaseModel):
    """Request-Modell für Tibber Scraper"""
    zip_code: str = Field(..., description="Deutsche Postleitzahl")
    annual_consumption: int = Field(..., description="Jahresverbrauch in kWh", gt=0)
    headless: bool = Field(default=True, description="Browser im Headless-Modus")
    debug_mode: bool = Field(default=False, description="Debug-Ausgaben aktivieren")


class TibberScraperResponse(BaseModel):
    """Response-Modell für Tibber Scraper"""
    success: bool
    kwh_price_ct: float = Field(..., description="Arbeitspreis in ct/kWh")
    exchange_price_ct: float = Field(..., description="Börsenstrompreis in ct/kWh")
    additional_price_ct: float = Field(..., description="Weitere Preisbestandteile (Steuern, Abgaben) in ct/kWh")
    average_price_12m_ct: float = Field(..., description="Durchschnittspreis letzte 12 Monate in ct/kWh")
    network_fees_monthly: float = Field(..., description="Netznutzungs- und Messstellengebühren pro Monat in €")
    tibber_fee_monthly: float = Field(..., description="Tibber-Gebühr pro Monat in €")
    total_base_monthly: float = Field(..., description="Summe Grundpreis pro Monat in €")
    monthly_cost_example: float = Field(..., description="Beispiel-Monatskosten von Webseite in €")
    calculated_monthly_cost: float = Field(..., description="Berechnete Monatskosten in €")
    calculated_annual_cost: float = Field(..., description="Berechnete Jahreskosten in €")
    timestamp: str
    note: Optional[str] = Field(default=None, description="Hinweis bei Fallback-Daten")


@app.post(
    "/api/scrape/tibber",
    response_model=TibberScraperResponse,
    tags=["scraper"],
    summary="Tibber Energiepreise scrapen",
    description="Extrahiert aktuelle Preisdaten von Tibber für eine PLZ und Jahresverbrauch"
)
async def scrape_tibber_tariff(request: TibberScraperRequest):
    """
    Scraped Tibber Energiepreise
    
    **Parameter:**
    - zip_code: Deutsche Postleitzahl (5 Stellen)
    - annual_consumption: Jahresverbrauch in kWh
    - headless: Browser ohne GUI (Standard: True)
    - debug_mode: Erweiterte Logs (Standard: False)
    
    **Rückgabe:**
    - Preisdaten inkl. Arbeitspreis, Börsenstrompreis, Grundpreise
    - Berechnete Monats- und Jahreskosten
    - Bei Scraping-Fehler: Realistische Fallback-Beispieldaten
    
    **Beispiel:**
    ```
    curl -X POST "http://localhost:8000/api/scrape/tibber" \\
         -H "Content-Type: application/json" \\
         -d '{
               "zip_code": "71065",
               "annual_consumption": 2500,
               "headless": true,
               "debug_mode": false
             }'
    ```
    """
    try:
        logger.info(f"📞 Tibber-Scraper API-Request: PLZ {request.zip_code}, {request.annual_consumption} kWh/Jahr")
        
        # Import Scraper function
        from src.webscraping.scraper_tibber import scrape_tibber_price
        
        # Scrape prices (async)
        result = await scrape_tibber_price(
            postal_code=request.zip_code,
            annual_consumption_kwh=request.annual_consumption
        )
        
        # Calculate costs
        monthly_consumption_kwh = request.annual_consumption / 12
        base_price_monthly = result['base_price_monthly']
        additional_price_ct_kwh = result['additional_price_ct_kwh']
        
        # Get current exchange price (estimate from source)
        exchange_price_ct = 9.15  # From Prophet forecast
        total_kwh_price_ct = exchange_price_ct + additional_price_ct_kwh
        
        monthly_cost = base_price_monthly + (monthly_consumption_kwh * total_kwh_price_ct / 100)
        annual_cost = monthly_cost * 12
        
        # Response formatieren
        response = TibberScraperResponse(
            success=True,
            kwh_price_ct=total_kwh_price_ct,
            exchange_price_ct=exchange_price_ct,
            additional_price_ct=additional_price_ct_kwh,
            average_price_12m_ct=total_kwh_price_ct,  # Simplified
            network_fees_monthly=base_price_monthly * 0.65,  # Rough estimate
            tibber_fee_monthly=5.99,  # Tibber's fixed fee
            total_base_monthly=base_price_monthly,
            monthly_cost_example=monthly_cost,
            calculated_monthly_cost=monthly_cost,
            calculated_annual_cost=annual_cost,
            timestamp=datetime.now().isoformat(),
            note=f"Datenquelle: {result['source']}"
        )
        
        logger.info(f"✅ Tibber-Scraper erfolgreich: {response.calculated_monthly_cost:.2f} €/Monat")
        return response
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Tibber-Scraping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Tibber-Scraping fehlgeschlagen: {str(e)}"
        )


# =============================================================================
# COMBINED SCRAPER ENDPOINT - Returns EnergyTariff-compatible format
# =============================================================================

class ScraperTariffRequest(BaseModel):
    """Request for getting scraped tariffs in EnergyTariff format"""
    zip_code: str
    annual_consumption: float
    providers: List[str] = ["enbw", "tado", "tibber"]
    headless: bool = True
    debug_mode: bool = False


@app.post("/api/scrape/tariffs")
async def scrape_all_tariffs(request: ScraperTariffRequest):
    """
    Scrape multiple providers and return data in EnergyTariff-compatible format.
    
    Returns tariff objects with fields matching EnergyTariff class structure:
    - name, provider, base_price, kwh_rate, is_dynamic, start_date, features
    """
    tariffs = []
    errors = []
    
    logger.info(f"🔍 Scraping tariffs for providers: {request.providers}, PLZ: {request.zip_code}, {request.annual_consumption} kWh")
    
    for provider in request.providers:
        try:
            if provider.lower() == "enbw":
                from src.webscraping.scraper_enbw import scrape_enbw_tariff
                result = await scrape_enbw_tariff(
                    zip_code=request.zip_code,
                    annual_consumption=request.annual_consumption
                )
                if result and result.get('base_price_monthly') is not None:
                    tariff_data = scraper_to_tariff(result, "EnBW", "dynamic")
                    tariffs.append(tariff_data)
                    logger.info(f"✅ EnBW: {result.get('base_price_monthly')} €/Mon, {result.get('markup_ct_kwh')} ct/kWh")
                else:
                    errors.append({"provider": "EnBW", "error": "No data returned"})
                    
            elif provider.lower() == "tado":
                from src.webscraping.scraper_tado import scrape_tado_tariff
                result = await scrape_tado_tariff(
                    zip_code=request.zip_code,
                    annual_consumption=request.annual_consumption
                )
                if result and result.get('base_price_monthly') is not None:
                    tariff_data = scraper_to_tariff(result, "Tado", "dynamic")
                    tariffs.append(tariff_data)
                    logger.info(f"✅ Tado: {result.get('base_price_monthly')} €/Mon, {result.get('markup_ct_kwh')} ct/kWh markup (gesamt: {result.get('kwh_price_ct')} ct/kWh)")
                else:
                    errors.append({"provider": "Tado", "error": "No data returned"})
                    
            elif provider.lower() == "tibber":
                from src.webscraping.scraper_tibber import scrape_tibber_price
                result = await scrape_tibber_price(
                    postal_code=request.zip_code,
                    annual_consumption_kwh=request.annual_consumption
                )
                if result and result.get('base_price_monthly') is not None:
                    tariff_data = scraper_to_tariff(result, "Tibber", "dynamic")
                    tariffs.append(tariff_data)
                    logger.info(f"✅ Tibber: {result.get('base_price_monthly')} €/Mon, {result.get('additional_price_ct_kwh')} ct/kWh")
                else:
                    errors.append({"provider": "Tibber", "error": "No data returned"})
                    
        except Exception as e:
            logger.error(f"❌ Error scraping {provider}: {e}")
            errors.append({"provider": provider, "error": str(e)})
    
    logger.info(f"✅ Scraped {len(tariffs)} tariffs successfully, {len(errors)} errors")
    
    return {
        "success": len(tariffs) > 0,
        "tariffs": tariffs,
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat()
    }


# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



# =============================================================================
