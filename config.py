import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///food_delivery.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки для SMS (опционально)
    SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'console')  # console, twilio, mtsexolve
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Время жизни SMS-кода (в минутах)
    OTP_EXPIRY_MINUTES = 5