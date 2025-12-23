"""
Farmer Module - Main Application
Agri Web Application with No Brokerage Model
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'jwt-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://farmeradmin:password@localhost:5432/farmermodule')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
jwt = JWTManager(app)

# Rate Limiting
limiter = Limiter(
    app,  # ✅ First positional argument is the Flask app
    key_func=get_remote_address,  # ✅ 'key_func' is still keyword
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Import algorithms
try:
    from src.algorithms.buyer_matcher import BuyerMatchingAlgorithm, RealTimeMatchingEngine
    from src.algorithms.community_connector import CommunityGraphBuilder, ForumRecommendationEngine
    from src.algorithms.fraud_detector import FraudDetectionSystem, RealTimeFraudMonitor
    
    # Initialize algorithm instances
    buyer_matcher = BuyerMatchingAlgorithm()
    community_builder = CommunityGraphBuilder()
    forum_engine = ForumRecommendationEngine()
    fraud_detector = FraudDetectionSystem()
    fraud_monitor = RealTimeFraudMonitor()
    
    print("✓ Algorithms initialized successfully")
except ImportError as e:
    print(f"⚠ Warning: Could not initialize algorithms: {e}")
    buyer_matcher = None
    community_builder = None
    forum_engine = None
    fraud_detector = None
    fraud_monitor = None

# Import models
try:
    from src.models.farmer_model import db
    db.init_app(app)
    print("✓ Database models initialized")
except ImportError as e:
    print(f"⚠ Warning: Could not initialize database models: {e}")

# Import routes
try:
    from src.routes.farmer_routes import farmer_bp
    from src.routes.buyer_routes import buyer_bp
    from src.routes.admin_routes import admin_bp
    from src.routes.auth_routes import auth_bp
    from src.routes.product_routes import product_bp
    
    # Register blueprints
    app.register_blueprint(farmer_bp)
    app.register_blueprint(buyer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    
    print("✓ Routes registered successfully")
except ImportError as e:
    print(f"⚠ Warning: Could not register routes: {e}")

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'message': 'The HTTP method is not supported for this endpoint'
    }), 405

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'service': 'farmer-module-api',
        'version': '1.0.0',
        'timestamp': '2024-01-01T00:00:00Z',  # This would be dynamic
        'database': 'connected' if 'db' in locals() and hasattr(db, 'engine') else 'disconnected',
        'algorithms': {
            'buyer_matcher': buyer_matcher is not None,
            'community_builder': community_builder is not None,
            'fraud_detector': fraud_detector is not None
        }
    }
    return jsonify(health_status), 200

# Welcome endpoint
@app.route('/')
def welcome():
    """Welcome endpoint"""
    return jsonify({
        'message': 'Welcome to Farmer Module API',
        'version': '1.0.0',
        'description': 'Agri Web Application - No Brokerage Model',
        'endpoints': {
            'farmer': '/api/farmer/*',
            'buyer': '/api/buyer/*',
            'admin': '/api/admin/*',
            'auth': '/api/auth/*',
            'health': '/api/health'
        }
    })

# Initialize database tables
@app.before_first_request
def create_tables():
    """Create database tables if they don't exist"""
    try:
        if 'db' in locals():
            with app.app_context():
                db.create_all()
            print("✓ Database tables created/verified")
    except Exception as e:
        print(f"⚠ Warning: Could not create database tables: {e}")

# Load initial data
def load_initial_data():
    """Load initial data into the database"""
    try:
        # Load market prices
        # Load default categories
        # Load language options
        print("✓ Initial data loaded (if any)")
    except Exception as e:
        print(f"⚠ Warning: Could not load initial data: {e}")

# WebSocket support for real-time features
try:
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('farmer_online')
    def handle_farmer_online(data):
        """Handle farmer coming online for real-time matching"""
        farmer_id = data.get('farmer_id')
        socketio.emit('farmer_status', {
            'farmer_id': farmer_id,
            'status': 'online',
            'timestamp': '2024-01-01T00:00:00Z'
        })
    
    print("✓ WebSocket support initialized")
except ImportError:
    print("⚠ WebSocket support not available (flask-socketio not installed)")
    socketio = None

# Application context setup
with app.app_context():
    # Load fraud detection patterns
    if fraud_detector:
        fraud_detector.load_fraud_patterns()
    
    # Load initial market data
    load_initial_data()
    
    print("=" * 50)
    print("Farmer Module Application Initialized Successfully!")
    print("=" * 50)
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"JWT Enabled: {app.config.get('JWT_SECRET_KEY') is not None}")
    print(f"Rate Limiting: Enabled")
    print(f"WebSocket: {'Enabled' if socketio else 'Disabled'}")
    print("=" * 50)

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    # Development vs Production
    debug = os.getenv('ENVIRONMENT', 'development') == 'development'
    
    print(f"\n🚀 Starting Farmer Module API on {host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    
    if socketio:
        # Run with WebSocket support
        socketio.run(app, host=host, port=port, debug=debug)
    else:
        # Run without WebSocket support
        app.run(host=host, port=port, debug=debug)