"""
Test the risk score API endpoint (simplified risk assessment)
"""
import requests
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_risk_score_api():
    """Test the /api/risk-score endpoint"""
    
    # API endpoint
    url = "http://localhost:8000/api/risk-score"
    
    # User data file - try multiple possible locations
    possible_files = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data', 'user_data_10265.csv'),
        os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data', 'demo_userdata.csv'),
        os.path.join(os.path.dirname(__file__), '..', 'data', 'household_data', 'synthetic_1_person_household.csv'),
    ]
    
    test_file = None
    for file_path in possible_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print(f"❌ No test file found. Tried:")
        for f in possible_files:
            print(f"  - {f}")
        return
    
    print(f"Testing API endpoint: {url}")
    print(f"Using file: {test_file}")
    
    try:
        # Prepare the request
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {'days': 30}
            
            # Send request
            print("\nSending request...")
            response = requests.post(url, files=files, data=data)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Success!")
            result = response.json()
            
            print("\n" + "="*60)
            print("RISK SCORE RESULT")
            print("="*60)
            print(f"Risk Level: {result.get('risk_level', 'N/A').upper()}")
            print(f"Risk Score: {result.get('risk_score', 'N/A')}/100")
            print(f"\nMessage: {result.get('risk_message', 'N/A')}")
            
            if 'risk_factors' in result:
                print("\nRisk Factors:")
                for factor in result['risk_factors']:
                    impact_symbol = {
                        'positive': '✓',
                        'neutral': '○',
                        'negative': '✗'
                    }.get(factor['impact'], '?')
                    
                    print(f"  {impact_symbol} {factor['factor']}: {factor['detail']}")
            
            print("="*60)
            
            # Visualize risk level
            risk_level = result.get('risk_level', 'unknown')
            if risk_level == 'low':
                print("\n🟢 LOW RISK - Good fit for dynamic tariffs!")
            elif risk_level == 'moderate':
                print("\n🟡 MODERATE RISK - Dynamic tariffs could work with optimization")
            elif risk_level == 'high':
                print("\n🔴 HIGH RISK - Consider optimizing consumption patterns")
            
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
    test_risk_score_api()
