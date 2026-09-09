import base64
import re
import requests
from django.conf import settings
from django.utils import timezone


def get_mpesa_access_token():
    """Fetches OAuth access token from Safaricom Daraja API using explicit Base64 Basic Auth."""
    if getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox') == 'live':
        url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    else:
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    # Strip any accidental whitespace or quote characters around keys
    key = str(settings.MPESA_CONSUMER_KEY).strip().strip("'").strip('"')
    secret = str(settings.MPESA_CONSUMER_SECRET).strip().strip("'").strip('"')

    # Construct clean Basic Auth header
    auth_string = f"{key}:{secret}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token')
        
        print(f"M-Pesa Auth Failed | Status Code: {response.status_code} | Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching M-Pesa token: {e}")
    return None


def format_phone_number(phone):
    """Formats phone numbers to 2547XXXXXXXX or 2541XXXXXXXX format required by Safaricom."""
    phone = re.sub(r'\D', '', str(phone).strip())
    if phone.startswith('0') and len(phone) == 10:
        return f"254{phone[1:]}"
    elif (phone.startswith('7') or phone.startswith('1')) and len(phone) == 9:
        return f"254{phone}"
    elif phone.startswith('254') and len(phone) == 12:
        return phone
    return phone


def trigger_stk_push(phone, amount, order_reference):
    """Initiates M-Pesa Express (STK Push) prompt on the user's phone."""
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'success': False, 'message': 'Failed to authenticate with M-Pesa gateway.'}

    formatted_phone = format_phone_number(phone)
    
    # Generate timestamp in EAT/UTC format (YYYYMMDDHHMMSS)
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    
    # Clean shortcode & passkey strings before base64 encoding
    shortcode = str(settings.MPESA_SHORTCODE).strip().strip("'").strip('"')
    passkey = str(settings.MPESA_PASSKEY).strip().strip("'").strip('"')
    
    password_str = f"{shortcode}{passkey}{timestamp}"
    password = base64.b64encode(password_str.encode('utf-8')).decode('utf-8')

    if getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox') == 'live':
        endpoint = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    else:
        endpoint = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Clean account reference: Alphanumeric only, max 12 chars
    clean_account_ref = f"Order{order_reference}"[:12]

    # Detect Transaction Type: Paybill vs Buy Goods (Till)
    tx_type = getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')
    party_b = getattr(settings, 'MPESA_TILL_NUMBER', shortcode) if tx_type == 'CustomerBuyGoodsOnline' else shortcode

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": tx_type,
        "Amount": max(1, int(amount)),  # Minimum 1 KES
        "PartyA": formatted_phone,
        "PartyB": party_b,
        "PhoneNumber": formatted_phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": clean_account_ref,
        "TransactionDesc": "Souvenir Order"
    }

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
        res_data = response.json()
        
        if res_data.get('ResponseCode') == '0':
            return {
                'success': True, 
                'checkout_request_id': res_data.get('CheckoutRequestID')
            }
        else:
            return {
                'success': False, 
                'message': res_data.get('CustomerMessage') or res_data.get('ResponseDescription', 'STK Push failed.')
            }
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'M-Pesa gateway connection timed out.'}
    except Exception as e:
        return {'success': False, 'message': str(e)}