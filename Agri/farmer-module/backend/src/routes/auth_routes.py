from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from security.auth import SecurityManager
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

security_manager = SecurityManager()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new farmer"""
    data = request.json
    
    # Validate input
    required_fields = ['phone', 'name', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'error': f'{field} is required'
            }), 400
    
    # Validate phone number (Indian format)
    phone = data['phone']
    if not re.match(r'^[6-9]\d{9}$', phone):
        return jsonify({
            'success': False,
            'error': 'Invalid phone number format'
        }), 400
    
    # Validate password strength
    password = data['password']
    if len(password) < 8:
        return jsonify({
            'success': False,
            'error': 'Password must be at least 8 characters long'
        }), 400
    
    # Hash password
    hashed_password = security_manager.hash_password(password)
    
    # Create farmer record (database insert would go here)
    farmer_data = {
        'id': 'generated-uuid',  # Would be actual UUID
        'phone': phone,
        'name': data['name'],
        'email': data.get('email'),
        'language': data.get('language', 'en'),
        'password_hash': hashed_password
    }
    
    # Generate tokens
    access_token = create_access_token(identity=farmer_data['id'])
    refresh_token = create_refresh_token(identity=farmer_data['id'])
    
    return jsonify({
        'success': True,
        'message': 'Farmer registered successfully',
        'data': {
            'farmer_id': farmer_data['id'],
            'name': farmer_data['name'],
            'phone': farmer_data['phone'],
            'is_verified': False,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login farmer"""
    data = request.json
    
    # Validate input
    if not data.get('phone') or not data.get('password'):
        return jsonify({
            'success': False,
            'error': 'Phone and password are required'
        }), 400
    
    # Verify farmer exists (database query would go here)
    farmer_data = {
        'id': 'farmer-uuid',
        'phone': data['phone'],
        'password_hash': 'hashed-password-from-db',
        'name': 'Farmer Name',
        'is_verified': True
    }
    
    # Verify password (in production, compare with hashed password from database)
    if data['password'] != 'testpassword':  # Replace with actual verification
        return jsonify({
            'success': False,
            'error': 'Invalid phone or password'
        }), 401
    
    # Generate tokens
    access_token = create_access_token(identity=farmer_data['id'])
    refresh_token = create_refresh_token(identity=farmer_data['id'])
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'farmer_id': farmer_data['id'],
            'name': farmer_data['name'],
            'phone': farmer_data['phone'],
            'is_verified': farmer_data['is_verified'],
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    
    return jsonify({
        'success': True,
        'access_token': new_access_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout farmer (client-side token invalidation)"""
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    }), 200