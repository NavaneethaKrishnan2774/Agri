# utils.py - FIXED VERSION
import random
import requests
from django.conf import settings
from .models import OTP


def send_sms_otp(user):
    """Send OTP via SMS using Fast2SMS"""
    # Generate OTP
    otp_code = OTP.create_otp(user)
    
    # SMS API configuration
    FAST2SMS_API_KEY = getattr(settings, 'FAST2SMS_API_KEY', 'your_api_key_here')
    FAST2SMS_URL = 'https://www.fast2sms.com/dev/bulkV2'
    
    payload = {
        'authorization': FAST2SMS_API_KEY,
        'sender_id': 'TXTIND',
        'message': f'Your Agri App OTP is {otp_code}. Valid for 5 minutes.',
        'language': 'english',
        'route': 'q',
        'numbers': user.contact_number
    }
    
    headers = {
        'authorization': FAST2SMS_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache',
    }
    
    try:
        response = requests.post(FAST2SMS_URL, data=payload, headers=headers)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('return'):
            return True
        else:
            print(f"SMS API Error: {response_data}")
            return False
    except Exception as e:
        print(f"Failed to send SMS: {str(e)}")
        return False