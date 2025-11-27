"""
Test the risk analysis API endpoint directly
"""
import requests
import os

def test_risk_analysis_api():
    """Test the /api/risk-analysis endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/risk-analysis"
    
    # User data file
    test_file = os.path.join(os.path.dirname(__file__), 'data', 'household_data', 'user_data_10265.csv')
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"Testing API endpoint: {url}")
    print(f"Using file: {test_file}")
    
    try:
        # Prepare the request
        files = {'file': open(test_file, 'rb')}
        data = {'days': 30}
        
        # Send request
        print("\nSending request...")
        response = requests.post(url, files=files, data=data)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            
            print("\nResponse structure:")
            print(f"  - historic_risk: {type(result.get('historic_risk'))}")
            print(f"  - coincidence_factor: {type(result.get('coincidence_factor'))}")
            print(f"  - load_profile: {type(result.get('load_profile'))}")
            
            if 'historic_risk' in result:
                hr = result['historic_risk']
                print(f"\nHistoric Risk Analysis:")
                print(f"  Market avg price: €{hr.get('market_avg_price')}/kWh")
                print(f"  User weighted price: €{hr.get('user_weighted_price')}/kWh")
                print(f"  Risk exposure: {hr.get('risk_exposure')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server.")
        print("Make sure the backend server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_risk_analysis_api()
