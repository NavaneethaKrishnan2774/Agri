"""
Buyer Routes for Farmer Module
Handles all buyer-related API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

buyer_bp = Blueprint('buyer', __name__, url_prefix='/api/buyer')

# ============================================
# BUYER REGISTRATION & PROFILE
# ============================================

@buyer_bp.route('/register', methods=['POST'])
def register_buyer():
    """Register a new buyer"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['phone', 'name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Here you would save to database
        # For now, return success
        buyer_data = {
            'id': 'temp-buyer-id',
            'phone': data['phone'],
            'name': data['name'],
            'email': data.get('email'),
            'is_verified': False,
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Buyer registered successfully',
            'data': buyer_data
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Registration failed',
            'message': str(e)
        }), 500

@buyer_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_buyer_profile():
    """Get buyer profile (requires authentication)"""
    try:
        buyer_id = get_jwt_identity()
        
        # Here you would fetch from database
        profile_data = {
            'id': buyer_id,
            'name': 'Sample Buyer',
            'phone': '9876543210',
            'email': 'buyer@example.com',
            'total_orders': 5,
            'total_spent': 12500.50,
            'avg_rating': 4.5,
            'created_at': '2024-01-01T10:00:00Z'
        }
        
        return jsonify({
            'success': True,
            'data': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch profile',
            'message': str(e)
        }), 500

# ============================================
# PRODUCT SEARCH & BROWSING
# ============================================

@buyer_bp.route('/search', methods=['GET'])
@jwt_required()
def search_products():
    """Search for agricultural products"""
    try:
        # Get query parameters
        query = request.args.get('q', '')
        category = request.args.get('category')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        location = request.args.get('location')
        radius_km = request.args.get('radius', 50, type=int)
        
        # Sample products (in production, query database)
        sample_products = [
            {
                'id': 'prod-001',
                'name': 'Organic Wheat',
                'farmer_name': 'Rajesh Kumar',
                'quantity': 100,
                'unit': 'kg',
                'price_per_unit': 25.50,
                'quality_grade': 'A',
                'location': [28.7041, 77.1025],
                'distance_km': 15.5,
                'harvest_date': '2024-01-15'
            },
            {
                'id': 'prod-002',
                'name': 'Basmati Rice',
                'farmer_name': 'Suresh Patel',
                'quantity': 50,
                'unit': 'kg',
                'price_per_unit': 45.00,
                'quality_grade': 'A',
                'location': [28.6139, 77.2090],
                'distance_km': 12.3,
                'harvest_date': '2024-01-10'
            }
        ]
        
        return jsonify({
            'success': True,
            'count': len(sample_products),
            'data': sample_products,
            'filters': {
                'query': query,
                'category': category,
                'price_range': f'{min_price}-{max_price}' if min_price or max_price else None,
                'location': location,
                'radius_km': radius_km
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500

@buyer_bp.route('/products/<product_id>', methods=['GET'])
@jwt_required()
def get_product_details(product_id):
    """Get detailed information about a product"""
    try:
        # Sample product details
        product = {
            'id': product_id,
            'name': 'Organic Wheat',
            'description': 'High quality organic wheat, freshly harvested',
            'farmer': {
                'id': 'farmer-001',
                'name': 'Rajesh Kumar',
                'is_verified': True,
                'trust_score': 8.5,
                'total_transactions': 42
            },
            'quantity': 100,
            'unit': 'kg',
            'price_per_unit': 25.50,
            'quality_grade': 'A',
            'harvest_date': '2024-01-15',
            'location': [28.7041, 77.1025],
            'images': [],
            'selling_mode': 'fixed',  # fixed, auction, bargain
            'certifications': ['Organic', 'FSSAI'],
            'delivery_options': [
                {'type': 'self_pickup', 'cost': 0},
                {'type': 'logistics', 'cost': 150, 'estimated_days': 2}
            ]
        }
        
        return jsonify({
            'success': True,
            'data': product
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch product details',
            'message': str(e)
        }), 500

# ============================================
# ORDER MANAGEMENT
# ============================================

@buyer_bp.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    """Place a new order"""
    try:
        data = request.json
        buyer_id = get_jwt_identity()
        
        # Validate required fields
        if not data.get('product_id') or not data.get('quantity'):
            return jsonify({
                'success': False,
                'error': 'Product ID and quantity are required'
            }), 400
        
        # Sample order response
        order_data = {
            'order_id': 'ORD-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'buyer_id': buyer_id,
            'product_id': data['product_id'],
            'quantity': data['quantity'],
            'unit_price': 25.50,
            'total_amount': data['quantity'] * 25.50,
            'status': 'pending',
            'order_date': datetime.now().isoformat(),
            'estimated_delivery': '2024-01-20'
        }
        
        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'data': order_data
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to place order',
            'message': str(e)
        }), 500

@buyer_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_buyer_orders():
    """Get all orders for the buyer"""
    try:
        buyer_id = get_jwt_identity()
        
        # Sample orders
        orders = [
            {
                'order_id': 'ORD-20240115-001',
                'product_name': 'Organic Wheat',
                'quantity': 50,
                'total_amount': 1275.00,
                'status': 'delivered',
                'order_date': '2024-01-10T10:30:00Z',
                'delivery_date': '2024-01-12T14:15:00Z'
            },
            {
                'order_id': 'ORD-20240115-002',
                'product_name': 'Basmati Rice',
                'quantity': 25,
                'total_amount': 1125.00,
                'status': 'processing',
                'order_date': '2024-01-14T09:15:00Z',
                'estimated_delivery': '2024-01-18'
            }
        ]
        
        return jsonify({
            'success': True,
            'count': len(orders),
            'data': orders
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch orders',
            'message': str(e)
        }), 500

# ============================================
# FAVORITES & REVIEWS
# ============================================

@buyer_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    """Get buyer's favorite products"""
    try:
        buyer_id = get_jwt_identity()
        
        # Sample favorites
        favorites = [
            {
                'product_id': 'prod-001',
                'product_name': 'Organic Wheat',
                'farmer_name': 'Rajesh Kumar',
                'price': 25.50,
                'added_date': '2024-01-10T11:30:00Z'
            },
            {
                'product_id': 'prod-002',
                'product_name': 'Basmati Rice',
                'farmer_name': 'Suresh Patel',
                'price': 45.00,
                'added_date': '2024-01-12T15:45:00Z'
            }
        ]
        
        return jsonify({
            'success': True,
            'count': len(favorites),
            'data': favorites
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch favorites',
            'message': str(e)
        }), 500

@buyer_bp.route('/reviews', methods=['POST'])
@jwt_required()
def submit_review():
    """Submit a product review"""
    try:
        data = request.json
        buyer_id = get_jwt_identity()
        
        # Validate required fields
        if not data.get('product_id') or not data.get('rating'):
            return jsonify({
                'success': False,
                'error': 'Product ID and rating are required'
            }), 400
        
        if not 1 <= data['rating'] <= 5:
            return jsonify({
                'success': False,
                'error': 'Rating must be between 1 and 5'
            }), 400
        
        # Sample review response
        review_data = {
            'review_id': 'REV-' + datetime.now().strftime('%Y%m%d-%H%M%S'),
            'buyer_id': buyer_id,
            'product_id': data['product_id'],
            'rating': data['rating'],
            'comment': data.get('comment', ''),
            'review_date': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'data': review_data
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to submit review',
            'message': str(e)
        }), 500

# ============================================
# NOTIFICATIONS
# ============================================

@buyer_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get buyer notifications"""
    try:
        buyer_id = get_jwt_identity()
        
        # Sample notifications
        notifications = [
            {
                'id': 'notif-001',
                'type': 'order_update',
                'title': 'Order Shipped',
                'message': 'Your order ORD-20240115-002 has been shipped',
                'timestamp': '2024-01-15T14:30:00Z',
                'is_read': False
            },
            {
                'id': 'notif-002',
                'type': 'price_alert',
                'title': 'Price Drop Alert',
                'message': 'Organic wheat price has dropped by 10%',
                'timestamp': '2024-01-14T09:15:00Z',
                'is_read': True
            }
        ]
        
        return jsonify({
            'success': True,
            'count': len(notifications),
            'unread_count': len([n for n in notifications if not n['is_read']]),
            'data': notifications
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch notifications',
            'message': str(e)
        }), 500

# ============================================
# HEALTH CHECK
# ============================================

@buyer_bp.route('/health', methods=['GET'])
def buyer_health_check():
    """Health check for buyer routes"""
    return jsonify({
        'success': True,
        'service': 'buyer-routes',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/api/buyer/register',
            '/api/buyer/profile',
            '/api/buyer/search',
            '/api/buyer/orders',
            '/api/buyer/favorites',
            '/api/buyer/reviews',
            '/api/buyer/notifications'
        ]
    }), 200
