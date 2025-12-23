# backend/src/routes/farmer_routes.py
from flask import Blueprint, request, jsonify
from security.auth import token_required, limiter
from algorithms.buyer_matcher import BuyerMatchingAlgorithm
from algorithms.community_connector import CommunityGraphBuilder, ForumRecommendationEngine
from algorithms.fraud_detector import FraudDetectionSystem, RealTimeFraudMonitor
import json
from datetime import datetime

farmer_bp = Blueprint('farmer', __name__, url_prefix='/api/farmer')

# Initialize algorithms
buyer_matcher = BuyerMatchingAlgorithm()
community_builder = CommunityGraphBuilder()
forum_engine = ForumRecommendationEngine()
fraud_detector = FraudDetectionSystem()
fraud_monitor = RealTimeFraudMonitor()

@farmer_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register_farmer():
    """Register new farmer with security checks"""
    data = request.json
    
    # Validate input
    if not data.get('phone') or not data.get('name'):
        return jsonify({'error': 'Phone and name are required'}), 400
    
    # Check for existing phone
    # (Database check would go here)
    
    # Fraud check on registration data
    fraud_check = fraud_detector.analyze_farmer_risk(data, [])
    
    if fraud_check['risk_level'] == 'critical':
        return jsonify({
            'error': 'Registration blocked due to security concerns',
            'requires_manual_verification': True
        }), 403
    
    # Create farmer account
    # (Database insert would go here)
    
    # Generate verification token
    # (Token generation would go here)
    
    return jsonify({
        'message': 'Farmer registered successfully',
        'requires_verification': fraud_check['requires_verification'],
        'risk_level': fraud_check['risk_level']
    }), 201

@farmer_bp.route('/products', methods=['POST'])
@token_required
@limiter.limit("20 per hour")
def upload_product():
    """Upload new product with fraud detection"""
    farmer_id = request.farmer_id
    data = request.json
    
    # Validate product data
    required_fields = ['name', 'quantity', 'price_per_unit']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check for price manipulation
    market_data = get_crop_prices(data.get('name')) # Function to get market data
    is_price_manipulated = fraud_detector.detect_price_manipulation(data, market_data)
    
    if is_price_manipulated:
        return jsonify({
            'error': 'Price appears to be manipulated. Please check market rates.',
            'market_price_range': market_data
        }), 400
    
    # Validate location
    if data.get('location'):
        location_validation = fraud_detector.validate_location(data['location'])
        if not location_validation['valid']:
            return jsonify({
                'error': f'Location validation failed: {location_validation["reason"]}'
            }), 400
    
    # Save product to database
    # (Database insert would go here)
    
    # Find buyers for this product
    buyers = get_nearby_buyers(data.get('location'), 50)  # 50km radius
    matches = buyer_matcher.match_by_preferences(data, buyers)
    
    # Log activity for fraud monitoring
    fraud_monitor.monitor_activity({
        'type': 'product_upload',
        'farmer_id': farmer_id,
        'product_data': data,
        'timestamp': datetime.now()
    })
    
    return jsonify({
        'message': 'Product uploaded successfully',
        'product_id': 'generated_id',  # Would be actual ID
        'buyer_matches': matches[:5],  # Top 5 matches
        'suggested_price': buyer_matcher.calculate_recommended_price(data, {})
    }), 201

@farmer_bp.route('/buyers/match', methods=['GET'])
@token_required
def match_buyers():
    """Get buyer matches for farmer's products"""
    farmer_id = request.farmer_id
    
    # Get farmer's active products
    products = get_farmer_products(farmer_id)  # Database function
    
    all_matches = []
    for product in products:
        buyers = get_nearby_buyers(product['location'], 50)
        matches = buyer_matcher.match_by_preferences(product, buyers)
        
        for match in matches:
            match['product_name'] = product['name']
            match['product_id'] = product['id']
            all_matches.append(match)
    
    # Sort by match score
    all_matches.sort(key=lambda x: x['match_score'], reverse=True)
    
    return jsonify({
        'matches': all_matches[:20],  # Top 20 matches
        'total_matches': len(all_matches)
    }), 200

@farmer_bp.route('/community/recommendations', methods=['GET'])
@token_required
def get_community_recommendations():
    """Get community farmer recommendations"""
    farmer_id = request.farmer_id
    
    # Get all farmers and interactions
    farmers = get_all_farmers()  # Database function
    interactions = get_farmer_interactions(farmer_id)  # Database function
    
    # Build or update community graph
    community_builder.build_community_graph(farmers, interactions)
    
    # Get recommendations
    recommendations = community_builder.get_community_recommendations(farmer_id, limit=15)
    
    # Get forum post recommendations
    forum_posts = get_forum_posts()  # Database function
    post_recommendations = forum_engine.recommend_posts(farmer_id, forum_posts, limit=10)
    
    # Detect communities
    communities = community_builder.detect_communities()
    farmer_community = None
    for comm_id, members in communities.items():
        if farmer_id in members:
            farmer_community = {
                'community_id': comm_id,
                'members_count': len(members),
                'similar_farmers': [m for m in members if m != farmer_id][:5]
            }
            break
    
    return jsonify({
        'farmer_recommendations': recommendations,
        'forum_recommendations': post_recommendations,
        'community': farmer_community,
        'total_connections': len(community_builder.graph.nodes())
    }), 200

@farmer_bp.route('/security/check', methods=['GET'])
@token_required
def security_check():
    """Run security check on farmer account"""
    farmer_id = request.farmer_id
    
    # Get farmer data and transactions
    farmer_data = get_farmer_data(farmer_id)  # Database function
    transactions = get_farmer_transactions(farmer_id)  # Database function
    
    # Run fraud detection
    risk_analysis = fraud_detector.analyze_farmer_risk(farmer_data, transactions)
    
    # Get recent security alerts
    recent_alerts = fraud_monitor.suspicious_activities[-10:]  # Last 10 alerts
    
    return jsonify({
        'risk_analysis': risk_analysis,
        'recent_alerts': recent_alerts,
        'security_score': 100 - risk_analysis['risk_score'],
        'recommended_actions': risk_analysis['recommendations']
    }), 200

@farmer_bp.route('/market/prices', methods=['GET'])
@token_required
def get_market_prices():
    """Get current market prices for crops"""
    crops = request.args.getlist('crops')
    
    if not crops:
        return jsonify({'error': 'No crops specified'}), 400
    
    market_data = {}
    for crop in crops:
        # Get market data from database or external API
        prices = get_crop_prices(crop)  # Database function
        
        market_data[crop] = {
            'current_price': prices.get('current', 0),
            'average_price': prices.get('average', 0),
            'price_range': {
                'min': prices.get('min', 0),
                'max': prices.get('max', 0)
            },
            'trend': prices.get('trend', 'stable'),
            'last_updated': datetime.now().isoformat()
        }
    
    return jsonify({'market_prices': market_data}), 200

# Helper functions (would connect to database)
def get_nearby_buyers(location, radius_km):
    """Get nearby buyers from database"""
    # This would be a database query
    return []

def get_farmer_products(farmer_id):
    """Get farmer's products from database"""
    return []

def get_all_farmers():
    """Get all farmers from database"""
    return []

def get_farmer_interactions(farmer_id):
    """Get farmer's interactions from database"""
    return []

def get_forum_posts():
    """Get forum posts from database"""
    return []

def get_farmer_data(farmer_id):
    """Get farmer data from database"""
    return {}

def get_farmer_transactions(farmer_id):
    """Get farmer's transactions from database"""
    return []

def get_crop_prices(crop_name):
    """Get crop prices from database or API"""
    return {}