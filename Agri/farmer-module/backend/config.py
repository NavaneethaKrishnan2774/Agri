"""
Configuration settings for Farmer Module Application
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Base configuration class
    """
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    
    # Application
    APP_NAME = "Farmer Module"
    APP_VERSION = "1.0.0"
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Server
    SERVER_NAME = os.getenv('SERVER_NAME', None)
    PREFERRED_URL_SCHEME = 'https' if ENVIRONMENT == 'production' else 'http'
    
    # ============================================
    # SECURITY CONFIGURATION
    # ============================================
    
    # Secret Keys
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'jwt-secret-key-change-this-in-production')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '').encode() if os.getenv('ENCRYPTION_KEY') else None
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    
    # Password Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_UPPERCASE = True
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_STRATEGY = "fixed-window"
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 
        'postgresql://farmeradmin:password@localhost:5432/farmermodule')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 20,
    }
    
    # Redis Configuration (for caching and rate limiting)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # ============================================
    # FILE UPLOAD CONFIGURATION
    # ============================================
    
    # Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # ============================================
    # EXTERNAL API CONFIGURATION
    # ============================================
    
    # SMS Gateway
    SMS_API_KEY = os.getenv('SMS_API_KEY', '')
    SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'FARMER')
    SMS_API_URL = os.getenv('SMS_API_URL', 'https://api.msg91.com/api/v2/sendsms')
    
    # Weather API
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')
    WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org/data/2.5/weather')
    
    # Market Price API
    MARKET_API_KEY = os.getenv('MARKET_API_KEY', '')
    MARKET_API_URL = os.getenv('MARKET_API_URL', 'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070')
    
    # Payment Gateway
    PAYMENT_GATEWAY_KEY = os.getenv('PAYMENT_GATEWAY_KEY', '')
    PAYMENT_GATEWAY_SECRET = os.getenv('PAYMENT_GATEWAY_SECRET', '')
    
    # ============================================
    # ALGORITHM CONFIGURATION
    # ============================================
    
    # Buyer Matching Algorithm
    MATCHING_RADIUS_KM = 50
    MATCHING_SCORE_THRESHOLD = 0.3
    MATCHING_MAX_RESULTS = 20
    
    # Fraud Detection
    FRAUD_RISK_THRESHOLDS = {
        'LOW': 20,
        'MEDIUM': 50,
        'HIGH': 75,
        'CRITICAL': 90
    }
    
    FRAUD_CHECK_INTERVAL_HOURS = 24
    SUSPICIOUS_TRANSACTION_COUNT = 10
    MAX_PRICE_DEVIATION = 3.0  # Standard deviations
    
    # Community Algorithm
    COMMUNITY_CONNECTION_THRESHOLD = 0.6
    MAX_COMMUNITY_RECOMMENDATIONS = 15
    COMMUNITY_UPDATE_INTERVAL_HOURS = 6
    
    # ============================================
    # NOTIFICATION CONFIGURATION
    # ============================================
    
    # SMS Notifications
    SMS_ENABLED = os.getenv('SMS_ENABLED', 'True').lower() == 'true'
    SMS_LANGUAGE = 'english'  # or 'unicode' for regional languages
    
    # Email Notifications
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@farmermodule.com')
    
    # ============================================
    # LOGGING CONFIGURATION
    # ============================================
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'farmer_module.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # ============================================
    # CACHING CONFIGURATION
    # ============================================
    
    CACHE_TYPE = 'redis' if REDIS_URL.startswith('redis://') else 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'farmer_module_'
    
    # Market Data Cache
    MARKET_DATA_CACHE_TTL = 3600  # 1 hour
    WEATHER_DATA_CACHE_TTL = 1800  # 30 minutes
    
    # ============================================
    # LOCALIZATION CONFIGURATION
    # ============================================
    
    SUPPORTED_LANGUAGES = ['en', 'hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn', 'gu', 'or', 'pa', 'ur']
    DEFAULT_LANGUAGE = 'en'
    TIMEZONE = 'Asia/Kolkata'
    
    # ============================================
    # BUSINESS RULES
    # ============================================
    
    # Commission (No brokerage model)
    PLATFORM_COMMISSION_PERCENT = 0.0
    TRANSACTION_FEE_FIXED = 0.0
    
    # Quality Grades
    QUALITY_GRADES = {
        'A': 'Premium',
        'B': 'Good',
        'C': 'Standard'
    }
    
    # Selling Modes
    SELLING_MODES = ['fixed', 'auction', 'bargain']
    DEFAULT_SELLING_MODE = 'fixed'
    
    # Auction Settings
    AUCTION_DURATION_HOURS = 24
    MIN_AUCTION_BID_INCREASE = 0.05  # 5%
    
    # ============================================
    # VALIDATION CONSTANTS
    # ============================================
    
    # Phone Validation (India)
    PHONE_REGEX = r'^[6-9]\d{9}$'
    
    # Email Validation
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Price Validation
    MIN_PRODUCT_PRICE = 1.0
    MAX_PRODUCT_PRICE = 1000000.0
    
    # Quantity Validation
    MIN_PRODUCT_QUANTITY = 0.1  # 100 grams
    MAX_PRODUCT_QUANTITY = 100000.0  # 100 tons
    
    # ============================================
    # FILE PATHS
    # ============================================
    
    # Ensure upload directory exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Static files
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    # Templates
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    # ============================================
    # DEVELOPMENT CONFIGURATION
    # ============================================
    
    @classmethod
    def is_development(cls):
        return cls.ENVIRONMENT == 'development'
    
    @classmethod
    def is_production(cls):
        return cls.ENVIRONMENT == 'production'
    
    @classmethod
    def is_testing(cls):
        return cls.ENVIRONMENT == 'testing'


class DevelopmentConfig(Config):
    """
    Development environment configuration
    """
    DEBUG = True
    ENVIRONMENT = 'development'
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///farmer_module_dev.db')
    
    # Disable rate limiting in development
    RATELIMIT_ENABLED = False
    
    # Use memory for Redis
    REDIS_URL = 'memory://'
    
    # Enable detailed logging
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """
    Testing environment configuration
    """
    TESTING = True
    ENVIRONMENT = 'testing'
    DEBUG = False
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable external APIs
    SMS_ENABLED = False
    EMAIL_ENABLED = False
    
    # Use memory for Redis
    REDIS_URL = 'memory://'


class ProductionConfig(Config):
    """
    Production environment configuration
    """
    DEBUG = False
    ENVIRONMENT = 'production'
    
    # Security enhancements for production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Strict rate limiting
    RATELIMIT_DEFAULT = "1000 per day, 100 per hour"
    
    # Production Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://:password@redis:6379/0')
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Enable all security features
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_UPPERCASE = True


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get configuration based on environment
    """
    env = os.getenv('ENVIRONMENT', 'development').lower()
    return config_by_name.get(env, config_by_name['default'])


# Current configuration
current_config = get_config()


# Validation functions
def validate_config():
    """
    Validate configuration and check for missing required values
    """
    errors = []
    
    # Check required environment variables in production
    if current_config.is_production():
        required_vars = [
            'SECRET_KEY',
            'JWT_SECRET',
            'DATABASE_URL',
            'ENCRYPTION_KEY'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                errors.append(f"Required environment variable '{var}' is not set")
    
    # Check encryption key length
    if current_config.ENCRYPTION_KEY and len(current_config.ENCRYPTION_KEY) != 32:
        errors.append("ENCRYPTION_KEY must be 32 bytes long")
    
    # Check upload folder
    if not os.path.exists(current_config.UPLOAD_FOLDER):
        try:
            os.makedirs(current_config.UPLOAD_FOLDER)
        except Exception as e:
            errors.append(f"Cannot create upload folder: {str(e)}")
    
    return errors


# Print configuration summary
if __name__ == '__main__':
    print("=" * 50)
    print(f"{Config.APP_NAME} Configuration")
    print("=" * 50)
    print(f"Environment: {current_config.ENVIRONMENT}")
    print(f"Debug Mode: {current_config.DEBUG}")
    print(f"Database: {current_config.SQLALCHEMY_DATABASE_URI}")
    print(f"JWT Enabled: {current_config.JWT_SECRET_KEY is not None}")
    print(f"Rate Limiting: {current_config.RATELIMIT_ENABLED}")
    print("=" * 50)
    
    # Validate configuration
    config_errors = validate_config()
    if config_errors:
        print("\n⚠ Configuration Warnings:")
        for error in config_errors:
            print(f"  - {error}")
    else:
        print("\n✓ Configuration is valid")