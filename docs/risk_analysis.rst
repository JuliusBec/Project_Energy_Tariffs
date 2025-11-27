Risk Analysis
==============

Risk assessment for dynamic electricity tariff suitability based on consumption patterns and price volatility.

Overview
--------

The risk analysis module (``backend.risk_analysis``) evaluates whether a household's consumption pattern is favorable for dynamic tariffs by analyzing historical usage against market prices.

Module: ``backend.risk_analysis``

Key Functions
-------------

create_historic_risk_analysis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Compare user's consumption-weighted price against market average.

.. code-block:: python

   from src.backend.risk_analysis import create_historic_risk_analysis
   import pandas as pd
   
   # Load consumption data
   df = pd.read_csv('smart_meter_data.csv')
   
   # Analyze last 30 days
   risk = create_historic_risk_analysis(df, days=30)
   
   print(f"Market avg: {risk['market_avg_price']}€/kWh")
   print(f"Your weighted avg: {risk['user_weighted_price']}€/kWh")
   print(f"Differential: {risk['price_differential_pct']}%")
   print(f"Risk exposure: {risk['risk_exposure']}")  # 'favorable' or 'unfavorable'

**Returns:**

Dictionary with market_avg_price, user_weighted_price, price_differential_pct, risk_exposure, total_consumption, price_volatility, and analysis_period.

**Interpretation:**

- **Negative differential**: User consumed more during cheap periods (favorable)
- **Positive differential**: User consumed more during expensive periods (unfavorable)

calculate_coincidence_factor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Measure consumption overlap with expensive price periods.

.. code-block:: python

   from src.backend.risk_analysis import calculate_coincidence_factor
   
   # Check if consumption coincides with top 20% expensive hours
   coincidence = calculate_coincidence_factor(
       df, 
       days=30, 
       expensive_hours_pct=20.0
   )
   
   print(f"Consumption in expensive hours: {coincidence['consumption_coincidence_pct']}%")
   print(f"Rating: {coincidence['coincidence_rating']}")  # 'low', 'medium', 'high'
   print(f"Correlation: {coincidence['correlation']}")

**Returns:**

Dictionary with consumption_coincidence_pct, cost_coincidence_pct, coincidence_rating, correlation, avg_price_expensive_hours, avg_price_cheap_hours.

**Ratings:**

- **Low (<15%)**: Favorable - avoids expensive hours
- **Medium (15-25%)**: Neutral - typical pattern
- **High (>25%)**: Unfavorable - high consumption during expensive periods

get_aggregated_risk_score
^^^^^^^^^^^^^^^^^^^^^^^^^^

Combine multiple risk factors into overall assessment.

.. code-block:: python

   from src.backend.risk_analysis import (
       create_historic_risk_analysis,
       calculate_coincidence_factor,
       get_price_forecast_volatility,
       get_aggregated_risk_score
   )
   
   # Collect all risk factors
   historic = create_historic_risk_analysis(df, days=30)
   coincidence = calculate_coincidence_factor(df, days=30)
   volatility = get_price_forecast_volatility()
   
   # Calculate aggregated score
   risk_score = get_aggregated_risk_score(
       historic_risk_analysis=historic,
       coincidence_factor=coincidence,
       forecast_price_volatility=volatility,
       is_dynamic=True,
       usage_forecast_quality=backtest_metrics  # Optional
   )
   
   print(f"Risk level: {risk_score['risk_level']}")  # 'low', 'moderate', 'high'
   print(f"Risk score: {risk_score['risk_score']}/100")  # Lower is better
   print(f"Message: {risk_score['risk_message']}")
   
   for factor in risk_score['risk_factors']:
       print(f"  - {factor['factor']}: {factor['impact']} ({factor['detail']})")

**Risk Score Ranges:**

- **0-30**: Low risk - Well-suited for dynamic tariffs
- **31-50**: Moderate risk - Dynamic tariffs can be beneficial
- **51-100**: High risk - Consumption pattern unfavorable, optimization needed

**Risk Factors:**

- Historical consumption timing (weighted price vs market avg)
- Coincidence with expensive hours
- Price volatility (historical and forecasted)
- Consumption forecast quality (if backtest provided)
- Tariff type (fixed tariffs have inherently lower risk)

Helper Functions
----------------

get_price_forecast_volatility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Calculate price forecast uncertainty metrics.

.. code-block:: python

   from src.backend.risk_analysis import get_price_forecast_volatility
   
   volatility = get_price_forecast_volatility()
   print(f"Std dev: {volatility['forecast_std_dev']}€/kWh")
   print(f"CI width: {volatility['avg_confidence_interval_width']}€/kWh")

get_user_load_profile
^^^^^^^^^^^^^^^^^^^^^^

Analyze hourly consumption patterns and price correlation.

.. code-block:: python

   from src.backend.risk_analysis import get_user_load_profile
   
   profile = get_user_load_profile(df, days=30)
   
   # Access hourly averages (0-23)
   for hour_data in profile['hourly_data']:
       print(f"Hour {hour_data['hour']}: {hour_data['avg_consumption_kwh']}kWh @ {hour_data['avg_price_eur_per_kwh']}€/kWh")
   
   # Summary statistics
   summary = profile['summary']
   print(f"Peak hour: {summary['peak_consumption_hour']}")
   print(f"Correlation: {summary['correlation']}")

get_simplified_risk_score_for_yearly_usage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Risk score for standard load profile scenarios (no smart meter data).

.. code-block:: python

   from src.backend.risk_analysis import (
       get_price_forecast_volatility,
       get_simplified_risk_score_for_yearly_usage
   )
   
   # For annual consumption only (no consumption pattern available)
   volatility = get_price_forecast_volatility()
   risk = get_simplified_risk_score_for_yearly_usage(
       forecast_price_volatility=volatility,
       is_dynamic=True
   )
   
   print(f"Simplified risk score: {risk['risk_score']}/100")
   print(risk['note'])

Complete Example
----------------

Full risk analysis workflow:

.. code-block:: python

   import pandas as pd
   from src.backend.risk_analysis import (
       create_historic_risk_analysis,
       calculate_coincidence_factor,
       get_user_load_profile,
       get_price_forecast_volatility,
       get_aggregated_risk_score
   )
   from src.backend.forecasting.energy_usage_forecast import create_backtest
   
   # Load data
   df = pd.read_csv('app_data/example_smart_meter.csv')
   
   # 1. Analyze historical consumption patterns
   historic = create_historic_risk_analysis(df, days=30)
   print(f"\nHistorical Analysis:")
   print(f"  Price differential: {historic['price_differential_pct']:.1f}%")
   print(f"  Exposure: {historic['risk_exposure']}")
   
   # 2. Check coincidence with expensive hours
   coincidence = calculate_coincidence_factor(df, days=30)
   print(f"\nCoincidence Factor:")
   print(f"  Rating: {coincidence['coincidence_rating']}")
   print(f"  {coincidence['rating_message']}")
   
   # 3. Analyze hourly load profile
   profile = get_user_load_profile(df, days=30)
   print(f"\nLoad Profile:")
   print(f"  Peak hour: {profile['summary']['peak_consumption_hour']}:00")
   print(f"  Price correlation: {profile['summary']['correlation']:.3f}")
   
   # 4. Get price forecast uncertainty
   volatility = get_price_forecast_volatility()
   print(f"\nPrice Forecast:")
   print(f"  Volatility: {volatility['forecast_std_dev']:.4f}€/kWh")
   
   # 5. Validate consumption forecast (optional)
   backtest = create_backtest(df)
   print(f"\nForecast Quality:")
   print(f"  MAE: {backtest['metrics']['mae']:.2f}kWh")
   print(f"  Error: {backtest['metrics']['forecast_error_percentage']:.1f}%")
   
   # 6. Calculate aggregated risk score
   risk = get_aggregated_risk_score(
       historic_risk_analysis=historic,
       coincidence_factor=coincidence,
       forecast_price_volatility=volatility,
       is_dynamic=True,
       usage_forecast_quality=backtest['metrics']
   )
   
   print(f"\n{'='*60}")
   print(f"OVERALL RISK ASSESSMENT")
   print(f"{'='*60}")
   print(f"Risk Level: {risk['risk_level'].upper()}")
   print(f"Risk Score: {risk['risk_score']}/100 (lower is better)")
   print(f"\n{risk['risk_message']}")
   print(f"\nContributing Factors:")
   for factor in risk['risk_factors']:
       impact_symbol = {'positive': '✓', 'neutral': '○', 'negative': '✗'}[factor['impact']]
       print(f"  {impact_symbol} {factor['factor']}: {factor['detail']}")

API Reference
-------------

.. automodule:: backend.risk_analysis
   :members:
   :undoc-members:
   :show-inheritance:

Data Requirements
-----------------

**Minimum Requirements:**

- Historical consumption data (15-minute or hourly intervals)
- At least 30 days of data recommended
- Timestamps matching available price data

**Optimal Setup:**

- 90+ days of consumption history
- Smart meter data in kWh
- Consistent time intervals
- Complete records (minimal gaps)

Integration
-----------

Risk analysis integrates with tariff comparison:

.. code-block:: python

   from src.backend.energy_tariff import DynamicTariff, FixedTariff
   from src.backend.risk_analysis import get_aggregated_risk_score
   
   # Create tariffs
   dynamic = DynamicTariff(name="Tibber", ...)
   fixed = FixedTariff(name="EnBW", ...)
   
   # Calculate costs
   dynamic_cost = dynamic.calculate_cost_with_breakdown(df)
   fixed_cost = fixed.calculate_cost(df)
   
   # Assess risk for dynamic tariff
   risk = get_aggregated_risk_score(...)
   
   # Decision logic
   if risk['risk_level'] == 'low' and dynamic_cost['total_cost'] < fixed_cost:
       print("Recommendation: Switch to dynamic tariff")
   elif risk['risk_level'] == 'high':
       print("Recommendation: Stay with fixed tariff or optimize consumption")

See Also
--------

- :doc:`tariff_models` - Tariff cost calculations
- :doc:`usage_forecasting` - Consumption prediction
- :doc:`price_forecasting` - Price prediction
- :doc:`api` - REST API endpoints
