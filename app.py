from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow JavaScript to call this API

# PayHero Configuration
PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"
AUTH_TOKEN = os.getenv('PAYHERO_AUTH_TOKEN')
CHANNEL_ID = os.getenv('PAYHERO_CHANNEL_ID', '8271')


@app.route('/', methods=['GET'])
def home():
    """API Status Check"""
    return jsonify({
        'status': 'success',
        'message': 'PayHero STK Push API is running!',
        'endpoint': '/api/payment/initiate'
    })


@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    """
    Initiate M-Pesa STK Push
    
    Expected JSON body:
    {
        "phone": "254712345678",
        "amount": 100,
        "description": "Payment for Order #123"
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        phone = data.get('phone', '').strip()
        amount = data.get('amount')
        description = data.get('description', 'Payment')
        
        # Validate phone number
        if not phone:
            return jsonify({'status': 'error', 'message': 'Phone number is required'}), 400
        
        # Format phone number (remove + or spaces, ensure starts with 254)
        phone = phone.replace('+', '').replace(' ', '')
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('7') or phone.startswith('1'):
            phone = '254' + phone
        
        # Validate amount
        if not amount or float(amount) < 1:
            return jsonify({'status': 'error', 'message': 'Amount must be at least 1 KES'}), 400
        
        # Prepare PayHero payload
        payload = {
            "amount": int(float(amount)),
            "phone_number": phone,
            "channel_id": int(CHANNEL_ID),
            "provider": "m-pesa",
            "external_reference": description,
            "callback_url": data.get('callback_url', '')
        }
        
        # Make request to PayHero
        headers = {
            'Authorization': AUTH_TOKEN,
            'Content-Type': 'application/json'
        }
        
        print(f"Sending payment request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{PAYHERO_BASE_URL}/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"PayHero Response Status: {response.status_code}")
        print(f"PayHero Response: {response.text}")
        
        # Handle response
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                'status': 'success',
                'message': 'STK Push sent successfully',
                'data': result
            }), 200
        else:
            error_data = response.json() if response.text else {}
            return jsonify({
                'status': 'error',
                'message': 'STK Push failed',
                'error': error_data,
                'status_code': response.status_code
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Request timeout - please try again'
        }), 408
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Network error: {str(e)}'
        }), 500
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("PayHero STK Push API Starting...")
    print("=" * 50)
    print(f"Channel ID: {CHANNEL_ID}")
    print(f"Auth Token: {'Configured' if AUTH_TOKEN else 'Missing'}")
    print("=" * 50)
    print("\nServer running at: http://localhost:5000")
    print("\nAvailable endpoint:")
    print("  - GET  / (Status check)")
    print("  - POST /api/payment/initiate (STK Push)")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
