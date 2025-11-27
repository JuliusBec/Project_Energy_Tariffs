System Concept & Architecture
==============================

This document explains the complete concept and workflow of the Energy Tariff Analysis System,
from data collection to tariff recommendations.

Overview
--------

The Energy Tariff Analysis System is a comprehensive platform that helps households make informed
decisions about electricity contracts by analyzing their consumption patterns, forecasting future
prices and usage, and comparing different tariff structures.

System Architecture
-------------------

The system consists of four main components that work together in a coordinated pipeline:

.. code-block:: text

   ┌─────────────────┐
   │  Web Scraping   │  ← Collect current tariff data
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Forecasting    │  ← Predict prices & consumption
   │  - Prices       │
   │  - Consumption  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Risk Analysis   │  ← Calculate volatility & exposure
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Tariff Compare  │  ← Generate recommendations
   └─────────────────┘

Complete Workflow
-----------------

Phase 1: Data Collection (Web Scraping)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first phase involves collecting real-time tariff data from German energy providers.

**What happens:**

1. User provides their postal code (PLZ) and annual consumption
2. System launches automated scrapers for multiple providers:
   
   - Tibber (dynamic tariff)
   - EnBW (dynamic tariff)
   - Tado (smart home integration)
   
3. Each scraper extracts:
   
   - Base price (€/month)
   - Energy price (ct/kWh)
   - Additional fees
   - Contract conditions

**Technology:**

- Playwright for browser automation
- Async/await for parallel scraping
- Fallback mechanisms for reliability

**Example:**

.. code-block:: python

   from src.webscraping.scraper_tibber import TibberScraper
   from src.webscraping.scraper_enbw import EnbwScraper
   import asyncio

   async def collect_tariffs(postal_code: str, annual_kwh: int):
       """Collect all available tariffs for a location"""
       
       # Initialize scrapers
       tibber = TibberScraper()
       enbw = EnbwScraper()
       
       # Parallel scraping for efficiency
       results = await asyncio.gather(
           tibber.get_prices(postal_code=postal_code),
           enbw.get_prices(
               postal_code=postal_code,
               annual_consumption=annual_kwh
           )
       )
       
       return {
           'tibber': results[0],
           'enbw': results[1]
       }

**Output:**

Structured tariff data ready for further processing:

.. code-block:: json

   {
     "tibber": {
       "base_price_monthly": 14.99,
       "kwh_price_additional": 15.50,
       "is_dynamic": true
     },
     "enbw": {
       "base_price_monthly": 18.21,
       "markup_ct_kwh": 15.36,
       "is_dynamic": true
     }
   }

Phase 2: Consumption Calculation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system determines the household's energy consumption pattern.

**Two approaches:**

1. **Upload Smart Meter Data (Preferred)**
   
   - User uploads CSV with hourly consumption
   - System analyzes actual usage patterns
   - Identifies peak times and consumption habits

2. **Standard Load Profile (Fallback)**
   
   - Based on household size
   - Uses German standard load profiles (H0)
   - Applies typical consumption patterns

**Example with Smart Meter Data:**

.. code-block:: python

   import pandas as pd
   
   # Load user's smart meter data
   df = pd.read_csv('smart_meter_data.csv')
   # Format: datetime, value (kWh)
   
   # Analyze patterns
   hourly_avg = df.groupby(df['datetime'].dt.hour)['value'].mean()
   daily_total = df.groupby(df['datetime'].dt.date)['value'].sum()
   
   # Identify consumption characteristics
   peak_hours = hourly_avg.nlargest(3).index.tolist()
   avg_daily = daily_total.mean()
   
   print(f"Peak consumption hours: {peak_hours}")
   print(f"Average daily consumption: {avg_daily:.2f} kWh")

**Example with Standard Profile:**

.. code-block:: python

   from src.backend.energy_tariff import StandardLoadProfile
   
   # Create profile for 2-person household
   profile = StandardLoadProfile(
       name="Household Standard",
       base_price=9.99,
       is_dynamic=False,
       start_date=datetime(2024, 1, 1),
       household_size=2
   )
   
   # Generate typical consumption pattern
   annual_kwh = 2500  # Typical for 2 persons
   hourly_distribution = profile.get_hourly_distribution()

**Output:**

Detailed consumption profile:

- Hourly consumption patterns
- Peak vs. off-peak usage
- Seasonal variations
- Total annual consumption

Phase 3: Price Forecasting
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system predicts future electricity prices using machine learning.

**What happens:**

1. **Load Historical Data**
   
   - Downloads day-ahead prices from SMARD (Bundesnetzagentur)
   - Covers at least 1 year of historical data
   - Includes hourly spot market prices

2. **Train Prophet Model**
   
   - Facebook Prophet for time series forecasting
   - Detects daily, weekly, and seasonal patterns
   - Accounts for trend changes

3. **Generate Forecast**
   
   - Predicts prices for next 30 days (720 hours)
   - Provides confidence intervals
   - Accounts for market volatility

**Example:**

.. code-block:: python

   from src.backend.forecasting.energy_price_forecast import (
       load_and_prepare_data,
       create_prophet_model,
       forecast_prices
   )
   
   # Load historical SMARD data
   df = load_and_prepare_data('app_data/germany_dayahead_prices.csv')
   
   # Create and train model
   model = create_prophet_model(
       changepoint_prior_scale=0.15,  # Flexibility for trends
       seasonality_prior_scale=10.0   # Strength of patterns
   )
   model.fit(df)
   
   # Forecast next 30 days
   forecast = forecast_prices(model, periods=720)
   
   # Analyze results
   avg_price = forecast['yhat'].mean()
   min_price = forecast['yhat'].min()
   max_price = forecast['yhat'].max()
   
   print(f"Average predicted price: {avg_price:.2f} €/MWh")
   print(f"Price range: {min_price:.2f} - {max_price:.2f} €/MWh")

**Key Features:**

- **Seasonality Detection**: Identifies daily and weekly patterns
- **Trend Analysis**: Recognizes long-term market trends
- **Uncertainty Quantification**: Provides 90% confidence intervals
- **Market Integration**: Uses official German market data

**Output:**

Hourly price predictions for the next 30 days:

.. code-block:: text

   Date/Time           Predicted Price (€/MWh)   Lower CI   Upper CI
   2024-12-01 00:00    85.32                     75.21      95.43
   2024-12-01 01:00    78.45                     68.34      88.56
   2024-12-01 02:00    72.18                     62.07      82.29
   ...

Phase 4: Usage Forecasting
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The system predicts the household's future energy consumption.

**What happens:**

1. **Analyze Historical Pattern**
   
   - Uses smart meter data or standard profile
   - Identifies consumption habits
   - Detects weekly and daily patterns

2. **Train Forecast Model**
   
   - Prophet for traditional time series
   - Optional: Chronos for deep learning approach
   - Captures seasonality and trends

3. **Generate Consumption Forecast**
   
   - Predicts hourly consumption for 30 days
   - Aligns with price forecast period
   - Provides confidence intervals

**Example:**

.. code-block:: python

   from src.backend.forecasting.energy_usage_forecast import (
       forecast_prophet,
       calculate_total_weekly_usage
   )
   
   # Load smart meter data
   consumption_df = pd.read_csv('smart_meter_data.csv')
   
   # Forecast next 30 days
   usage_forecast = forecast_prophet(consumption_df, days=30)
   
   # Analyze weekly patterns
   weekly_totals = calculate_total_weekly_usage(usage_forecast)
   
   print("Predicted weekly consumption:")
   print(weekly_totals['yhat'])
   
   # Total consumption for period
   total_30_days = usage_forecast['yhat'].sum()
   print(f"\nTotal 30-day consumption: {total_30_days:.2f} kWh")

**Output:**

Hourly consumption predictions:

.. code-block:: text

   Date/Time           Predicted Usage (kWh)   Lower CI   Upper CI
   2024-12-01 00:00    0.45                    0.35       0.55
   2024-12-01 01:00    0.38                    0.28       0.48
   2024-12-01 06:00    1.25                    1.05       1.45
   ...

Phase 5: Risk Analysis
^^^^^^^^^^^^^^^^^^^^^^^

The system calculates the financial risk associated with each tariff type.

**What is analyzed:**

1. **Price Volatility**
   
   - Standard deviation of predicted prices
   - Worst-case vs. best-case scenarios
   - Exposure to market fluctuations

2. **Cost Distribution**
   
   - Percentile analysis (10th, 50th, 90th)
   - Maximum potential monthly cost
   - Probability of exceeding budget

3. **Risk Metrics**
   
   - Value at Risk (VaR)
   - Expected shortfall
   - Risk score (0-100)

**Example:**

.. code-block:: python

   from src.backend.risk_analysis import calculate_risk_metrics
   
   # Combine price and usage forecasts
   combined_forecast = pd.merge(
       usage_forecast[['datetime', 'yhat']],
       price_forecast[['ds', 'yhat']],
       left_on='datetime',
       right_on='ds'
   )
   
   # Calculate hourly costs (price in €/MWh -> €/kWh)
   combined_forecast['cost'] = (
       combined_forecast['yhat_usage'] * 
       combined_forecast['yhat_price'] / 1000
   )
   
   # Risk analysis
   risk_metrics = calculate_risk_metrics(combined_forecast['cost'])
   
   print(f"Average monthly cost: {risk_metrics['mean']:.2f}€")
   print(f"Standard deviation: {risk_metrics['std']:.2f}€")
   print(f"90th percentile: {risk_metrics['p90']:.2f}€")
   print(f"Risk score: {risk_metrics['risk_score']}/100")

**Risk Score Interpretation:**

- **0-30**: Low risk - Stable, predictable costs
- **31-60**: Medium risk - Moderate price fluctuations
- **61-100**: High risk - Significant volatility, budget uncertainty

**Output for Dynamic Tariff:**

.. code-block:: json

   {
     "mean_monthly_cost": 89.45,
     "std_deviation": 15.32,
     "percentile_10": 68.20,
     "percentile_50": 87.15,
     "percentile_90": 112.80,
     "max_expected_cost": 125.50,
     "risk_score": 42,
     "volatility_index": 17.1
   }

**Output for Fixed Tariff:**

.. code-block:: json

   {
     "mean_monthly_cost": 95.00,
     "std_deviation": 2.15,
     "percentile_10": 92.50,
     "percentile_50": 95.00,
     "percentile_90": 97.50,
     "max_expected_cost": 98.00,
     "risk_score": 8,
     "volatility_index": 2.3
   }

Phase 6: Tariff Comparison & Recommendation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The final phase combines all data to generate personalized recommendations.

**Comparison Criteria:**

1. **Total Cost**
   
   - Base price + energy costs
   - Projected 30-day total
   - Annual cost estimate

2. **Risk Profile**
   
   - Price volatility
   - Cost predictability
   - Worst-case scenarios

3. **Savings Potential**
   
   - Comparison with current tariff
   - Best vs. worst case scenarios
   - Time-of-use optimization

4. **User Preferences**
   
   - Risk tolerance
   - Budget constraints
   - Green energy preference

**Example:**

.. code-block:: python

   from src.backend.energy_tariff import (
       FixedPriceTariff,
       DynamicPriceTariff,
       compare_tariffs
   )
   from datetime import datetime
   
   # Create tariff objects
   fixed_tariff = FixedPriceTariff(
       name="EWE Strom Fix",
       base_price=9.99,
       is_dynamic=False,
       start_date=datetime(2024, 12, 1),
       kwh_rate=0.32,
       provider="EWE",
       features=["fixed", "12-month guarantee"]
   )
   
   dynamic_tariff = DynamicPriceTariff(
       name="Tibber",
       base_price=14.99,
       is_dynamic=True,
       start_date=datetime(2024, 12, 1),
       base_rate=0.155,
       provider="Tibber",
       features=["dynamic", "smart home", "green"],
       price_forecast_df=price_forecast
   )
   
   # Compare with user's consumption
   comparison = compare_tariffs(
       tariffs=[fixed_tariff, dynamic_tariff],
       consumption_forecast=usage_forecast,
       period_days=30
   )
   
   # Display results
   for tariff_name, result in comparison.items():
       print(f"\n{tariff_name}:")
       print(f"  Expected cost: {result['total_cost']:.2f}€")
       print(f"  Risk score: {result['risk_score']}/100")
       print(f"  Best case: {result['min_cost']:.2f}€")
       print(f"  Worst case: {result['max_cost']:.2f}€")

**Recommendation Engine:**

The system generates personalized recommendations based on:

.. code-block:: python

   def generate_recommendation(comparison_results, user_profile):
       """
       Generate tariff recommendation based on user profile
       
       Args:
           comparison_results: Dict with tariff comparison data
           user_profile: Dict with user preferences
               - risk_tolerance: 'low' | 'medium' | 'high'
               - budget_limit: float (€)
               - prefer_green: bool
               - smart_home: bool
       """
       
       recommendations = []
       
       for tariff_name, data in comparison_results.items():
           score = 0
           
           # Cost scoring (40% weight)
           if data['total_cost'] < user_profile['budget_limit']:
               score += 40
           elif data['max_cost'] < user_profile['budget_limit']:
               score += 20
           
           # Risk scoring (30% weight)
           if user_profile['risk_tolerance'] == 'low':
               score += max(0, 30 - data['risk_score'] * 0.3)
           elif user_profile['risk_tolerance'] == 'high':
               # Reward potential savings from dynamic pricing
               if data['is_dynamic'] and data['min_cost'] < data['mean_cost']:
                   score += 30
           
           # Feature matching (30% weight)
           if user_profile['prefer_green'] and 'green' in data['features']:
               score += 15
           if user_profile['smart_home'] and 'smart home' in data['features']:
               score += 15
           
           recommendations.append({
               'tariff': tariff_name,
               'score': score,
               'reason': generate_reason(data, user_profile)
           })
       
       # Sort by score
       recommendations.sort(key=lambda x: x['score'], reverse=True)
       
       return recommendations[0]  # Return best match

**Example Output:**

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │ TARIFF RECOMMENDATION                                       │
   └─────────────────────────────────────────────────────────────┘
   
   🏆 BEST MATCH: Tibber Dynamic (Score: 87/100)
   
   📊 Cost Analysis:
      • Expected monthly cost: 89.45€
      • Savings vs. current: 12.30€/month (148€/year)
      • Best case scenario: 68.20€
      • Worst case scenario: 112.80€
   
   📈 Risk Assessment:
      • Risk score: 42/100 (Medium)
      • Price volatility: Moderate
      • Cost predictability: 85%
   
   ✨ Key Features:
      • 100% green energy
      • Smart home integration
      • Real-time price tracking
      • No minimum contract duration
   
   💡 Why this tariff?
      Based on your consumption pattern and risk tolerance,
      this dynamic tariff offers the best balance between
      savings potential and manageable risk. Your flexible
      consumption habits align well with time-of-use pricing.
   
   ⚠️  Important Notes:
      • Requires smart meter installation
      • Monthly costs can vary
      • Best suited for users who can shift consumption
   
   ────────────────────────────────────────────────────────────
   
   Alternative Options:
   
   2. EWE Strom Fix (Score: 73/100)
      • Fixed monthly cost: 95.00€
      • Zero price risk
      • 12-month price guarantee
      → Best for: Maximum budget security

**Real-World Example Scenario**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's walk through a complete example:

**User Profile:**

- 2-person household in Heidelberg (PLZ: 69117)
- Annual consumption: 2,500 kWh
- Has smart meter data available
- Moderate risk tolerance
- Prefers green energy
- Budget limit: 100€/month

**Step 1: Data Collection**

.. code-block:: python

   # Scrape tariffs for Heidelberg
   tariffs = await collect_tariffs(
       postal_code="69117",
       annual_kwh=2500
   )
   # Result: Found Tibber (14.99€ base + 15.5ct/kWh)
   #         Found EnBW (18.21€ base + 15.36ct/kWh)

**Step 2: Consumption Analysis**

.. code-block:: python

   # Load user's smart meter data
   consumption = pd.read_csv('user_smart_meter.csv')
   # Analysis shows: 
   # - Peak usage 6-8 AM and 6-9 PM
   # - Average 6.85 kWh/day
   # - Higher consumption in winter

**Step 3: Price Forecast**

.. code-block:: python

   # Train and forecast prices
   price_forecast = forecast_prices(model, periods=720)
   # Result: Average 85€/MWh, range 60-120€/MWh

**Step 4: Usage Forecast**

.. code-block:: python

   # Forecast consumption
   usage_forecast = forecast_prophet(consumption, days=30)
   # Result: Predicted 205 kWh total for 30 days

**Step 5: Risk Analysis**

.. code-block:: python

   # Calculate costs and risk
   # Tibber Dynamic: Mean 89.45€, Risk score 42
   # Fixed Alternative: Mean 95.00€, Risk score 8

**Step 6: Recommendation**

.. code-block:: text

   RECOMMENDATION: Tibber Dynamic
   
   Reasoning:
   ✓ Saves ~148€/year vs. fixed tariff
   ✓ Risk score (42) acceptable for moderate tolerance
   ✓ Green energy matches preference
   ✓ Smart meter already installed
   ✓ Peak consumption times have moderate prices
   
   Action: Switch to Tibber, consider shifting 
           some evening consumption to off-peak hours
           for additional 10-15% savings

Integration & API
-----------------

The complete workflow is exposed through a REST API:

**Main Endpoint:**

.. code-block:: python

   @app.route('/api/compare-tariffs', methods=['POST'])
   def compare_tariffs_endpoint():
       """
       Complete tariff comparison pipeline
       
       Request body:
       {
         "postal_code": "69117",
         "annual_kwh": 2500,
         "household_size": 2,
         "smart_meter_data": "base64_encoded_csv",  # optional
         "risk_tolerance": "medium",
         "prefer_green": true,
         "budget_limit": 100
       }
       
       Response:
       {
         "recommendations": [...],
         "forecast_period": 30,
         "analysis": {...}
       }
       """
       pass

**Frontend Integration:**

The Vue.js frontend provides an interactive interface:

.. code-block:: javascript

   // User inputs postal code and preferences
   async function getTariffRecommendation() {
     const response = await fetch('/api/compare-tariffs', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         postal_code: userInput.postalCode,
         annual_kwh: userInput.annualConsumption,
         household_size: userInput.householdSize,
         risk_tolerance: userInput.riskTolerance,
         prefer_green: userInput.preferGreen
       })
     });
     
     const result = await response.json();
     displayRecommendation(result.recommendations[0]);
     showComparison(result.analysis);
   }

Key Benefits of This Architecture
----------------------------------

1. **Data-Driven Decisions**
   
   - Real-time tariff data
   - Personalized consumption analysis
   - Scientific forecasting methods

2. **Comprehensive Risk Assessment**
   
   - Quantified volatility
   - Clear worst/best case scenarios
   - Informed decision support

3. **Flexible & Extensible**
   
   - Easy to add new providers
   - Modular architecture
   - Scalable forecasting

4. **User-Centric**
   
   - Clear recommendations
   - Transparent calculations
   - Multiple risk profiles supported

Technical Stack Summary
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Technology
   * - Web Scraping
     - Playwright (async), Python
   * - Data Processing
     - Pandas, NumPy
   * - Forecasting
     - Prophet, Chronos (optional)
   * - Risk Analysis
     - Statistical modeling, VaR
   * - Backend API
     - Flask, Python
   * - Frontend
     - Vue.js, Vite
   * - Visualization
     - Chart.js, Matplotlib
   * - Data Storage
     - CSV files, JSON

Future Enhancements
-------------------

Planned improvements to the system:

1. **Machine Learning Optimization**
   
   - Ensemble forecasting (Prophet + Chronos)
   - Consumption pattern recognition
   - Automated parameter tuning

2. **Extended Provider Support**
   
   - Additional German energy providers
   - European market integration
   - Solar/battery integration

3. **Advanced Features**
   
   - Real-time price alerts
   - Automatic switching recommendations
   - Carbon footprint tracking
   - Solar production forecasting

4. **Mobile App**
   
   - Native iOS/Android apps
   - Push notifications
   - Quick consumption logging

5. **AI-Powered Insights**
   
   - Anomaly detection in consumption
   - Personalized saving tips
   - Predictive maintenance alerts

Conclusion
----------

The Energy Tariff Analysis System provides a complete, end-to-end solution for
household electricity tariff optimization. By combining web scraping, machine learning
forecasting, risk analysis, and user-centric design, it empowers consumers to make
informed decisions about their energy contracts.

The modular architecture ensures maintainability and extensibility, while the
comprehensive documentation enables easy understanding and contribution.

For detailed information on specific components, see:

- :doc:`api` - REST API endpoints
- :doc:`tariff_models` - Tariff calculation models
- :doc:`risk_analysis` - Risk assessment
- :doc:`webscraping` - Web scraping modules
- :doc:`price_forecasting` - Energy price forecasting
- :doc:`usage_forecasting` - Consumption forecasting

Contributing
------------

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Follow the existing architecture patterns
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

For questions or suggestions, please open an issue on GitHub.
