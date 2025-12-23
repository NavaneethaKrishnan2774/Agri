from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/farmers', methods=['GET'])
@jwt_required()
def get_all_farmers():
    """Get all farmers (admin only)"""
    # Admin authentication check would go here
    return jsonify({
        'success': True,
        'farmers': []
    }), 200

@admin_bp.route('/verify/<farmer_id>', methods=['POST'])
@jwt_required()
def verify_farmer(farmer_id):
    """Verify a farmer"""
    # Admin verification logic
    return jsonify({
        'success': True,
        'message': f'Farmer {farmer_id} verified successfully'
    }), 200