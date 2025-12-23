"""
Authentication and Security Manager for Farmer Module
Handles password hashing, JWT tokens, and authentication middleware
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import re

class SecurityManager:
    """
    Main security manager for handling authentication and encryption
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security manager with Flask app"""
        self.app = app
        self.secret_key = app.config.get('JWT_SECRET_KEY', os.getenv('JWT_SECRET', secrets.token_hex(32)))
        self.algorithm = app.config.get('JWT_ALGORITHM', 'HS256')
        self.token_expiry = app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(days=7))
        self.refresh_expiry = app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
    
    # ============================================
    # PASSWORD HANDLING
    # ============================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password
            hashed_password: Bcrypt hashed password
            
        Returns:
            Boolean indicating if password matches
        """
        if not password or not hashed_password:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'score': 0
        }
        
        # Check length
        if len(password) < 8:
            validation_result['is_valid'] = False
            validation_result['errors'].append('Password must be at least 8 characters long')
        else:
            validation_result['score'] += 1
        
        # Check for numbers
        if not re.search(r'\d', password):
            validation_result['errors'].append('Password should contain at least one number')
        else:
            validation_result['score'] += 1
        
        # Check for uppercase
        if not re.search(r'[A-Z]', password):
            validation_result['errors'].append('Password should contain at least one uppercase letter')
        else:
            validation_result['score'] += 1
        
        # Check for lowercase
        if not re.search(r'[a-z]', password):
            validation_result['errors'].append('Password should contain at least one lowercase letter')
        else:
            validation_result['score'] += 1
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            validation_result['errors'].append('Password should contain at least one special character')
        else:
            validation_result['score'] += 1
        
        # Determine strength
        if validation_result['score'] >= 4:
            validation_result['strength'] = 'strong'
        elif validation_result['score'] >= 3:
            validation_result['strength'] = 'medium'
        else:
            validation_result['strength'] = 'weak'
            validation_result['is_valid'] = False
        
        return validation_result
    
    # ============================================
    # JWT TOKEN HANDLING
    # ============================================
    
    def generate_access_token(self, user_id: str, user_type: str = 'farmer', additional_claims: dict = None) -> str:
        """
        Generate JWT access token
        
        Args:
            user_id: User identifier
            user_type: Type of user (farmer, buyer, admin)
            additional_claims: Additional claims to include
            
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user_id: str, user_type: str = 'farmer') -> str:
        """
        Generate JWT refresh token
        
        Args:
            user_id: User identifier
            user_type: Type of user
            
        Returns:
            JWT refresh token string
        """
        payload = {
            'user_id': user_id,
            'user_type': user_type,
            'exp': datetime.utcnow() + self.refresh_expiry,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = 'access') -> dict:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            token_type: Type of token (access/refresh)
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={'verify_exp': True}
            )
            
            # Verify token type
            if payload.get('type') != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return {'error': 'Token expired'}
        except jwt.InvalidTokenError as e:
            return {'error': f'Invalid token: {str(e)}'}
        except Exception as e:
            return {'error': f'Token verification failed: {str(e)}'}
    
    def refresh_access_token(self, refresh_token: str) -> tuple:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (new_access_token, error_message)
        """
        payload = self.verify_token(refresh_token, 'refresh')
        
        if not payload or 'error' in payload:
            return None, payload.get('error', 'Invalid refresh token')
        
        # Generate new access token
        new_access_token = self.generate_access_token(
            payload['user_id'],
            payload.get('user_type', 'farmer')
        )
        
        return new_access_token, None
    
    # ============================================
    # INPUT VALIDATION
    # ============================================
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 500) -> str:
        """
        Sanitize user input to prevent XSS attacks
        
        Args:
            input_string: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_string:
            return ''
        
        # Remove any HTML tags
        import html
        sanitized = html.escape(input_string)
        
        # Trim to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """
        Validate Indian phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Boolean indicating if phone is valid
        """
        # Indian phone number regex (10 digits, starting with 6-9)
        pattern = r'^[6-9]\d{9}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            Boolean indicating if email is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_location(lat: float, lon: float) -> bool:
        """
        Validate geographic coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Boolean indicating if coordinates are valid
        """
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    def generate_session_id(self) -> str:
        """
        Generate secure session ID
        
        Returns:
            Secure session ID string
        """
        return secrets.token_urlsafe(32)
    
    def generate_csrf_token(self) -> str:
        """
        Generate CSRF token
        
        Returns:
            CSRF token string
        """
        return secrets.token_hex(32)
    
    def verify_csrf_token(self, token: str, stored_token: str) -> bool:
        """
        Verify CSRF token
        
        Args:
            token: Token from request
            stored_token: Token stored in session
            
        Returns:
            Boolean indicating if tokens match
        """
        if not token or not stored_token:
            return False
        return secrets.compare_digest(token, stored_token)


# ============================================
# AUTHENTICATION MIDDLEWARE
# ============================================

def token_required(required_user_type: str = None):
    """
    Decorator for requiring valid JWT token
    
    Args:
        required_user_type: Required user type (farmer, buyer, admin)
    
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'success': False,
                    'error': 'Missing or invalid Authorization header',
                    'message': 'Use Bearer token format: Bearer <token>'
                }), 401
            
            token = auth_header.split(' ')[1]
            
            # Initialize security manager
            security = SecurityManager(current_app)
            
            # Verify token
            payload = security.verify_token(token)
            
            if not payload or 'error' in payload:
                return jsonify({
                    'success': False,
                    'error': 'Authentication failed',
                    'message': payload.get('error', 'Invalid token')
                }), 401
            
            # Check user type if required
            if required_user_type and payload.get('user_type') != required_user_type:
                return jsonify({
                    'success': False,
                    'error': 'Access denied',
                    'message': f'This endpoint requires {required_user_type} access'
                }), 403
            
            # Add user info to request context
            request.user_id = payload['user_id']
            request.user_type = payload.get('user_type', 'farmer')
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def farmer_only(f):
    """
    Decorator for allowing only farmers
    """
    return token_required('farmer')(f)


def buyer_only(f):
    """
    Decorator for allowing only buyers
    """
    return token_required('buyer')(f)


def admin_only(f):
    """
    Decorator for allowing only admins
    """
    return token_required('admin')(f)


def rate_limit_by_ip():
    """
    Rate limiting by IP address
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Check rate limit (simplified - in production use Redis)
            # This would connect to Redis to track requests
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def validate_json_schema(schema: dict):
    """
    Validate JSON request body against schema
    
    Args:
        schema: JSON schema to validate against
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Invalid content type',
                    'message': 'Request must be JSON'
                }), 400
            
            data = request.get_json()
            
            # Simple validation (in production use jsonschema library)
            for field, field_type in schema.items():
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Validation error',
                        'message': f'Missing required field: {field}'
                    }), 400
                
                # Type checking
                if not isinstance(data[field], field_type):
                    return jsonify({
                        'success': False,
                        'error': 'Validation error',
                        'message': f'Field {field} must be of type {field_type.__name__}'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


# ============================================
# SECURITY HEADERS MIDDLEWARE
# ============================================

def add_security_headers(response):
    """
    Add security headers to Flask response
    """
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy (adjust based on your needs)
    csp = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self'",
        "connect-src 'self'"
    ]
    response.headers['Content-Security-Policy'] = '; '.join(csp)
    
    # HSTS (only in production)
    if current_app.config.get('ENVIRONMENT') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response


# ============================================
# AUDIT LOGGING
# ============================================

class AuditLogger:
    """
    Log security-related events
    """
    
    @staticmethod
    def log_login(user_id: str, ip_address: str, success: bool, user_agent: str = None):
        """
        Log login attempt
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'login_attempt',
            'user_id': user_id,
            'ip_address': ip_address,
            'success': success,
            'user_agent': user_agent
        }
        
        # In production, save to database or log file
        print(f"[SECURITY] Login attempt: {log_entry}")
    
    @staticmethod
    def log_password_change(user_id: str, ip_address: str):
        """
        Log password change
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'password_change',
            'user_id': user_id,
            'ip_address': ip_address
        }
        
        print(f"[SECURITY] Password changed: {log_entry}")
    
    @staticmethod
    def log_suspicious_activity(user_id: str, ip_address: str, activity: str, details: dict = None):
        """
        Log suspicious activity
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'suspicious_activity',
            'user_id': user_id,
            'ip_address': ip_address,
            'activity': activity,
            'details': details or {}
        }
        
        print(f"[SECURITY] Suspicious activity: {log_entry}")


# Initialize security manager instance
security_manager = SecurityManager()