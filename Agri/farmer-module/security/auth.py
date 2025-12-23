# security/auth.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
import secrets

class SecurityManager:
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET', secrets.token_hex(32))
        self.algorithm = "HS256"
        
    # Password Hashing
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    # JWT Token Generation
    def generate_token(self, farmer_id: str, phone: str) -> str:
        payload = {
            'farmer_id': farmer_id,
            'phone': phone,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    # Data Encryption
    @staticmethod
    def encrypt_data(plaintext: str, key: bytes) -> tuple:
        """Encrypt sensitive data"""
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return ciphertext, iv, encryptor.tag
    
    @staticmethod
    def decrypt_data(ciphertext: bytes, key: bytes, iv: bytes, tag: bytes) -> str:
        """Decrypt sensitive data"""
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()

# Authentication Middleware
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        security = SecurityManager()
        data = security.verify_token(token)
        
        if not data:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        request.farmer_id = data['farmer_id']
        request.phone = data['phone']
        
        return f(*args, **kwargs)
    
    return decorated

# Rate Limiting Middleware
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)