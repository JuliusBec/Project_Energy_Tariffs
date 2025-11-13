# Per-Tariff Risk Score Implementation

## Overview
This document describes the implementation of per-tariff risk score calculation, which addresses the issue where all tariffs (both dynamic and fixed) were receiving the same risk assessment.

## Problem Statement
Previously, the risk assessment was calculated once for the user's consumption pattern and applied to all tariffs equally. This was problematic because:
- **Fixed tariffs** inherently have lower risk (locked-in prices)
- **Dynamic tariffs** have variable risk based on user consumption patterns
- Users couldn't properly compare risk between tariff types

## Solution Architecture

### Backend Changes

#### 1. Updated `/api/scrape/tariffs` Endpoint
**File:** `app.py`

The endpoint now:
- Accepts an optional CSV file for consumption data analysis
- Changed from `request: ScraperTariffRequest` to individual Form parameters
- Calculates risk scores per tariff based on their `is_dynamic` attribute
- Returns tariffs with individual risk assessments

**New Parameters:**
```python
@app.post("/api/scrape/tariffs")
async def scrape_all_tariffs(
    zip_code: str = Form(...),
    annual_consumption: float = Form(...),
    providers: str = Form('["enbw", "tado", "tibber"]'),
    headless: bool = Form(True),
    debug_mode: bool = Form(False),
    days: int = Form(30),
    file: Optional[UploadFile] = File(None)  # NEW: Optional CSV for risk analysis
)
```

**Risk Calculation Logic:**
1. If CSV file is provided, parse consumption data
2. Calculate base risk metrics (same for all tariffs):
   - Historic risk analysis
   - Coincidence factor
3. For each tariff, call `get_aggregated_risk_score()` with its `is_dynamic` value
4. Attach risk data to each tariff object

**Response Enhancement:**
```json
{
  "success": true,
  "tariffs": [
    {
      "name": "EnBW Dynamic",
      "is_dynamic": true,
      "risk_level": "moderate",
      "risk_score": 55,
      "risk_message": "...",
      "risk_factors": [...]
    },
    {
      "name": "EnBW Fixed",
      "is_dynamic": false,
      "risk_level": "low",
      "risk_score": 30,
      "risk_message": "...",
      "risk_factors": [...]
    }
  ],
  "risk_analysis_performed": true
}
```

#### 2. New `/api/risk-score-per-tariff` Endpoint
**File:** `app.py`

A standalone endpoint for calculating risk for a specific tariff type:
```python
@app.post("/api/risk-score-per-tariff")
async def get_risk_score_per_tariff(
    file: UploadFile = File(...),
    days: int = Form(30),
    is_dynamic: bool = Form(True)
)
```

This endpoint is useful for:
- Testing risk calculations
- Future scenarios where tariff details aren't yet available
- Alternative frontend implementations

### Frontend Changes

#### 1. Updated API Service
**File:** `src/frontend/src/services/api.js`

The `scrapeAllTariffs` method now supports sending CSV files:
```javascript
scrapeAllTariffs: (zipCode, annualConsumption, providers, options = {}) => {
  // If CSV file is provided, send as multipart/form-data
  if (options.csvFile) {
    const formData = new FormData()
    formData.append('file', options.csvFile)
    // ... other fields
    return api.post('/scrape/tariffs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
  // Otherwise, send as JSON (backward compatible)
  return api.post('/scrape/tariffs', { ... })
}
```

#### 2. Updated Tariff Comparison View
**File:** `src/frontend/src/views/TariffComparison.vue`

**Changes:**
1. Pass CSV file to scraper endpoint:
```javascript
const scraperOptions = {}
if (uploadedFile.value) {
  scraperOptions.csvFile = uploadedFile.value
  scraperOptions.days = 30
}

const scraperResponse = await apiService.scrapeAllTariffs(
  zipCode, 
  annualConsumption, 
  ['enbw', 'tado', 'tibber'],
  scraperOptions
)
```

2. Use per-tariff risk data when available:
```javascript
return {
  // ... other fields
  // Use per-tariff risk assessment from backend (if available)
  risk_level: tariff.risk_level || riskAnalysisData.value?.risk_level,
  risk_score: tariff.risk_score || riskAnalysisData.value?.risk_score,
  risk_message: tariff.risk_message || riskAnalysisData.value?.risk_message,
  risk_factors: tariff.risk_factors || []
}
```

3. Enhanced logging:
```javascript
const tariffsWithRisk = scrapedTariffs.filter(t => t.risk_level).length
if (tariffsWithRisk > 0) {
  console.log(`🛡️ Per-tariff risk assessment: ${tariffsWithRisk}/${scrapedTariffs.length} tariffs`)
  scrapedTariffs.forEach(t => {
    if (t.risk_level) {
      console.log(`   ${t.name}: ${t.risk_level} (${t.risk_score})`)
    }
  })
}
```

### Risk Calculation Logic

The `get_aggregated_risk_score()` function in `src/backend/risk_analysis.py` already had support for the `is_dynamic` parameter:

```python
def get_aggregated_risk_score(
    historic_risk_analysis: dict,
    coincidence_factor: dict,
    forecast_price_volatility: dict,
    is_dynamic: bool,  # Key parameter!
    usage_forecast_quality: dict
) -> dict:
    score = 50  # Start at neutral
    
    # ... calculate base score based on consumption patterns ...
    
    # Adjust score for fixed tariffs
    if not is_dynamic:
        score -= 25  # Fixed tariffs are generally less risky
        factors.append({
            'factor': 'Tariftyp',
            'impact': 'positive',
            'detail': 'Fester Tarif'
        })
    
    return {
        'risk_level': risk_level,
        'risk_score': int(overall_risk_score),
        'risk_message': risk_message,
        'risk_factors': factors
    }
```

**Key Point:** Fixed tariffs receive a -25 point adjustment, making them inherently lower risk.

## Testing

A test script has been created: `analysis/test_per_tariff_risk.py`

Run it with:
```bash
python analysis/test_per_tariff_risk.py
```

This script:
1. Loads example consumption data
2. Calculates base risk metrics
3. Compares risk scores for dynamic vs. fixed tariffs
4. Shows the ~25 point difference between tariff types

## Benefits

### 1. **Accurate Risk Assessment**
- Dynamic tariffs show risk based on user's consumption patterns
- Fixed tariffs show inherently lower risk
- Users can make informed decisions

### 2. **Better User Experience**
- Each tariff card shows its specific risk level
- Color-coded badges (🟢 low, 🟡 moderate, 🔴 high)
- Risk factors explain why a tariff is risky/safe

### 3. **Efficient Backend Processing**
- Risk calculated once per scrape request
- No need for multiple API calls from frontend
- Base metrics (historic risk, coincidence) calculated only once

### 4. **Backward Compatibility**
- Frontend can still use old `/api/risk-score` endpoint
- Scraper works without CSV file (no risk data returned)
- Falls back to global risk assessment if per-tariff unavailable

## Example Output

When uploading a CSV file, you'll see different risk scores:

```
📊 Scraped tariffs with CSV data:
🛡️ Per-tariff risk assessment: 5/5 tariffs
   EnBW mobility+ dynamic: moderate (55)
   Tado Dynamic: moderate (55)
   Tibber: moderate (55)
   EnBW basis+ (fixed): low (30)
   EnBW comfort+ (fixed): low (30)
```

Notice how:
- Dynamic tariffs have **moderate risk (55)** - depends on consumption patterns
- Fixed tariffs have **low risk (30)** - inherently safer due to price lock-in

## Future Enhancements

1. **Forecast-based risk**: Include `forecast_price_volatility` parameter
2. **Usage quality metrics**: Use `usage_forecast_quality` for better predictions
3. **Personalized thresholds**: Allow users to set their risk tolerance
4. **Historical comparison**: Show how risk changes over time
5. **Tariff-specific factors**: Include provider-specific risk factors (e.g., reliability, customer service)

## Migration Notes

### For API Consumers
- If you're calling `/api/scrape/tariffs`, you can now optionally send a CSV file
- Use `Content-Type: multipart/form-data` instead of `application/json` when sending files
- The response includes new `risk_level`, `risk_score`, `risk_message` fields per tariff

### For Frontend Developers
- Update `scrapeAllTariffs` calls to pass `csvFile` in options
- Use per-tariff risk data instead of global risk assessment
- Check `risk_analysis_performed` in response to know if risk was calculated

## Conclusion

This implementation provides accurate, per-tariff risk assessments that help users make better-informed decisions when choosing between dynamic and fixed energy tariffs. The solution is efficient, backward-compatible, and extensible for future enhancements.
