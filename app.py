from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import base64
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow JavaScript to call this API

# PayHero Configuration
PAYHERO_BASE_URL = "https://backend.payhero.co.ke/api/v2"
API_USERNAME = os.getenv('PAYHERO_API_USERNAME')
ACCOUNT_ID = os.getenv('PAYHERO_ACCOUNT_ID')
CHANNEL_TYPE = os.getenv('PAYHERO_CHANNEL_TYPE')
ACCOUNT_NUMBER = os.getenv('PAYHERO_ACCOUNT_NUMBER')
CHANNEL_ID = os.getenv('PAYHERO_CHANNEL_ID')

def get_auth_header():
    """Create Basic Auth header for PayHero API"""
    credentials = f"{API_USERNAME}:"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


@app.route('/', methods=['GET'])
def home():
    """API Status Check"""
    return jsonify({
        'status': 'success',
        'message': 'PayHero API is running!',
        'endpoints': {
            'initiate_payment': '/api/payment/initiate',
            'check_status': '/api/payment/status/<transaction_code>'
        }
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
            'Authorization': get_auth_header(),
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{PAYHERO_BASE_URL}/payments",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Handle response
        if response.status_code in [200, 201]:
            result = response.json()
            return jsonify({
                'status': 'success',
                'message': 'Payment initiated successfully',
                'data': result
            }), 200
        else:
            error_data = response.json() if response.text else {}
            return jsonify({
                'status': 'error',
                'message': 'Payment initiation failed',
                'error': error_data
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


@app.route('/api/payment/status/<transaction_code>', methods=['GET'])
def check_payment_status(transaction_code):
    """
    Check payment status
    
    Usage: /api/payment/status/ABC123XYZ
    """
    try:
        headers = {
            'Authorization': get_auth_header(),
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{PAYHERO_BASE_URL}/payments/{transaction_code}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'status': 'success',
                'data': result
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Could not retrieve payment status',
                'error': response.json() if response.text else {}
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500


@app.route('/api/payment/webhook', methods=['POST'])
def payment_webhook():
    """
    Webhook endpoint for PayHero callbacks
    This is where PayHero will send payment confirmations
    """
    try:
        data = request.get_json()
        
        # Log the webhook data (in production, save to database)
        print("Webhook received:", json.dumps(data, indent=2))
        
        # Process the payment confirmation
        # You can add your own logic here (update database, send notifications, etc.)
        
        return jsonify({
            'status': 'success',
            'message': 'Webhook received'
        }), 200
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("PayHero API Server Starting...")
    print("=" * 50)
    print(f"API Username: {API_USERNAME[:10]}...")
    print(f"Channel ID: {CHANNEL_ID}")
    print("=" * 50)
    print("\nServer running at: http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  - GET  /")
    print("  - POST /api/payment/initiate")
    print("  - GET  /api/payment/status/<code>")
    print("  - POST /api/payment/webhook")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)