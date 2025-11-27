"""
Test script for the new /api/calculate-yearly-usage endpoint
This tests that the yearly usage calculation from CSV files works correctly.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import io

# Create a sample CSV file with 3 months of hourly data
def create_test_csv():
    """Create a test CSV with 3 months of hourly consumption data"""
    start_date = datetime(2024, 1, 1)
    hours = 90 * 24  # 3 months worth of hours
    
    data = []
    for i in range(hours):
        current_date = start_date + timedelta(hours=i)
        # Simulate varying consumption (higher during day, lower at night)
        hour_of_day = current_date.hour
        if 6 <= hour_of_day <= 22:  # Daytime
            consumption = 0.5 + (i % 10) * 0.1  # 0.5-1.5 kWh
        else:  # Nighttime
            consumption = 0.2 + (i % 5) * 0.05  # 0.2-0.4 kWh
            
        data.append({
            'datetime': current_date.strftime('%Y-%m-%d %H:%M:%S'),
            'value': consumption
        })
    
    df = pd.DataFrame(data)
    return df

# Test the API endpoint
def test_yearly_usage_endpoint():
    """Test the /api/calculate-yearly-usage endpoint"""
    print("Creating test CSV data...")
    df = create_test_csv()
    
    # Calculate expected values
    total_consumption = df['value'].sum()
    days_of_data = (pd.to_datetime(df['datetime'].iloc[-1]) - pd.to_datetime(df['datetime'].iloc[0])).days
    expected_annual_kwh = total_consumption * (365 / days_of_data)
    
    print(f"Test data created:")
    print(f"  - Records: {len(df)}")
    print(f"  - Days of data: {days_of_data}")
    print(f"  - Total consumption: {total_consumption:.2f} kWh")
    print(f"  - Expected annual: {expected_annual_kwh:.2f} kWh")
    
    # Convert DataFrame to CSV bytes
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    # Test the endpoint
    print("\nTesting /api/calculate-yearly-usage endpoint...")
    url = "http://localhost:8000/api/calculate-yearly-usage"
    
    files = {
        'file': ('test_data.csv', csv_bytes, 'text/csv')
    }
    
    try:
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! API Response:")
            print(f"  - Annual kWh: {result['annual_kwh']}")
            print(f"  - Total consumption: {result['total_consumption']}")
            print(f"  - Data range: {result['data_start']} to {result['data_end']}")
            print(f"  - Days of data: {result['days_of_data']}")
            print(f"  - Number of records: {result['number_of_records']}")
            
            # Validate the result
            if abs(result['annual_kwh'] - expected_annual_kwh) < 10:  # Allow 10 kWh tolerance
                print("\n✅ Calculation is correct!")
            else:
                print(f"\n⚠️  Warning: Expected {expected_annual_kwh:.2f} kWh, got {result['annual_kwh']} kWh")
        else:
            print(f"\n❌ ERROR: API returned status {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API at http://localhost:8000")
        print("Make sure the FastAPI server is running (python app.py)")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

def test_calculate_with_csv_endpoint():
    """Test that /api/calculate-with-csv returns annual_kwh"""
    print("\n" + "="*80)
    print("Testing /api/calculate-with-csv endpoint...")
    
    df = create_test_csv()
    
    # Convert DataFrame to CSV bytes
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    url = "http://localhost:8000/api/calculate-with-csv"
    
    files = {
        'file': ('test_data.csv', csv_bytes, 'text/csv')
    }
    
    try:
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS! API Response includes:")
            print(f"  - Number of tariffs: {len(result['results'])}")
            print(f"  - Data source: {result['data_source']}")
            print(f"  - Annual kWh: {result.get('annual_kwh', 'NOT FOUND ❌')}")
            
            if 'annual_kwh' in result:
                print("\n✅ annual_kwh is now included in the response!")
                
                # Check if individual results also have annual_kwh
                if result['results'] and 'annual_kwh' in result['results'][0]:
                    print("✅ Individual tariff results also include annual_kwh!")
                else:
                    print("ℹ️  Individual results don't include annual_kwh (this is expected)")
            else:
                print("\n❌ ERROR: annual_kwh is NOT in the response")
        else:
            print(f"\n❌ ERROR: API returned status {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API at http://localhost:8000")
        print("Make sure the FastAPI server is running (python app.py)")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    print("="*80)
    print("TESTING NEW YEARLY USAGE API ENDPOINTS")
    print("="*80)
    
    test_yearly_usage_endpoint()
    test_calculate_with_csv_endpoint()
    
    print("\n" + "="*80)
    print("TESTS COMPLETED")
    print("="*80)
