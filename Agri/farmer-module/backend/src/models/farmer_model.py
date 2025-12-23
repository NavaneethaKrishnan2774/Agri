"""
Database Models for Farmer Module
SQLAlchemy models for all database tables
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import uuid
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import func
from sqlalchemy import Index, CheckConstraint, UniqueConstraint
import enum

db = SQLAlchemy()

def generate_uuid():
    """Generate UUID for primary keys"""
    return str(uuid.uuid4())

# ============================================
# ENUMERATIONS
# ============================================

class QualityGrade(enum.Enum):
    """Product quality grades"""
    A = "Premium"
    B = "Good"
    C = "Standard"

class SellingMode(enum.Enum):
    """Product selling modes"""
    FIXED = "fixed"
    AUCTION = "auction"
    BARGAIN = "bargain"

class OrderStatus(enum.Enum):
    """Order statuses"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class PaymentMethod(enum.Enum):
    """Payment methods"""
    COD = "cash_on_delivery"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"

class PaymentStatus(enum.Enum):
    """Payment statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class VerificationStatus(enum.Enum):
    """Verification statuses"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

# ============================================
# CORE MODELS
# ============================================

class Farmer(db.Model):
    """
    Farmer Profile Model
    """
    __tablename__ = 'farmers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default='en')
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    farm_size_acres = db.Column(db.Float)
    crops_grown = db.Column(ARRAY(db.String(50)))  # Array of crop names
    experience_years = db.Column(db.Integer, default=0)
    is_verified = db.Column(db.Boolean, default=False)
    trust_score = db.Column(db.Float, default=5.0, nullable=False)  # 0-10 scale
    total_transactions = db.Column(db.Integer, default=0)
    total_sales_amount = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    profile_image_url = db.Column(db.String(500))
    cover_image_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    verifications = db.relationship('FarmerVerification', backref='farmer', lazy=True)
    products = db.relationship('Product', backref='farmer', lazy=True)
    orders = db.relationship('Order', backref='farmer', lazy=True)
    reviews = db.relationship('Review', backref='farmer', lazy=True)
    community_posts = db.relationship('CommunityPost', backref='farmer', lazy=True)
    notifications = db.relationship('Notification', backref='farmer', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_farmers_location', 'location_lat', 'location_lon'),
        Index('idx_farmers_trust_score', 'trust_score'),
        Index('idx_farmers_is_verified', 'is_verified'),
        Index('idx_farmers_created_at', 'created_at'),
    )
    
    @hybrid_property
    def location(self):
        """Get location as tuple"""
        if self.location_lat and self.location_lon:
            return (self.location_lat, self.location_lon)
        return None
    
    @location.setter
    def location(self, value):
        """Set location from tuple"""
        if value and len(value) == 2:
            self.location_lat, self.location_lon = value
    
    @hybrid_property
    def is_premium(self):
        """Check if farmer is premium (high trust score)"""
        return self.trust_score >= 8.0
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary for API response"""
        data = {
            'id': str(self.id),
            'phone': self.phone,
            'name': self.name,
            'email': self.email if include_sensitive else self._mask_email(self.email),
            'language': self.language,
            'location': self.location,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'farm_size_acres': self.farm_size_acres,
            'crops_grown': self.crops_grown or [],
            'experience_years': self.experience_years,
            'is_verified': self.is_verified,
            'trust_score': round(self.trust_score, 2),
            'total_transactions': self.total_transactions,
            'total_sales_amount': round(self.total_sales_amount, 2),
            'avg_rating': round(self.avg_rating, 2),
            'profile_image_url': self.profile_image_url,
            'cover_image_url': self.cover_image_url,
            'bio': self.bio,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'is_premium': self.is_premium
        }
        return data
    
    @staticmethod
    def _mask_email(email):
        """Mask email for display"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@')
        if len(local) <= 2:
            return f"{'*' * len(local)}@{domain}"
        return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"


class FarmerVerification(db.Model):
    """
    Farmer Verification Documents
    """
    __tablename__ = 'farmer_verifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    
    # Document details
    aadhaar_number_hash = db.Column(db.String(255))  # Hashed Aadhaar number
    pan_number_hash = db.Column(db.String(255))      # Hashed PAN number
    land_document_hash = db.Column(db.String(255))   # Hashed land document
    bank_account_hash = db.Column(db.String(255))    # Hashed bank account
    
    # Document URLs (encrypted in production)
    aadhaar_front_url = db.Column(db.String(500))
    aadhaar_back_url = db.Column(db.String(500))
    pan_card_url = db.Column(db.String(500))
    land_document_url = db.Column(db.String(500))
    bank_passbook_url = db.Column(db.String(500))
    
    # Verification details
    status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verified_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admins.id', ondelete='SET NULL'))
    verified_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    verification_notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_verifications_farmer_id', 'farmer_id'),
        Index('idx_verifications_status', 'status'),
        UniqueConstraint('farmer_id', name='unique_farmer_verification'),
    )


# ============================================
# PRODUCT & INVENTORY MODELS
# ============================================

class ProductCategory(db.Model):
    """
    Product Categories (Wheat, Rice, Vegetables, etc.)
    """
    __tablename__ = 'product_categories'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_hindi = db.Column(db.String(100))
    name_tamil = db.Column(db.String(100))
    name_telugu = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    parent_category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_categories.id', ondelete='SET NULL'))
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)
    parent = db.relationship('ProductCategory', remote_side=[id], backref='subcategories')
    
    # Indexes
    __table_args__ = (
        Index('idx_categories_name', 'name'),
        Index('idx_categories_parent', 'parent_category_id'),
    )


class Product(db.Model):
    """
    Agricultural Products listed by farmers
    """
    __tablename__ = 'products'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('product_categories.id', ondelete='SET NULL'))
    
    # Product details
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    variety = db.Column(db.String(100))  # e.g., Basmati Rice, Alphonso Mango
    quality_grade = db.Column(db.Enum(QualityGrade), default=QualityGrade.B)
    
    # Quantity & Pricing
    quantity = db.Column(db.Float, nullable=False)  # In specified unit
    unit = db.Column(db.String(20), default='kg')   # kg, quintal, ton, piece
    price_per_unit = db.Column(db.Float, nullable=False)
    min_order_quantity = db.Column(db.Float, default=1.0)
    max_order_quantity = db.Column(db.Float)
    
    # Location
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    harvest_location = db.Column(db.String(200))
    
    # Timing
    harvest_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    available_from = db.Column(db.Date, default=date.today)
    available_until = db.Column(db.Date)
    
    # Selling mode
    selling_mode = db.Column(db.Enum(SellingMode), default=SellingMode.FIXED)
    auction_end_time = db.Column(db.DateTime)
    minimum_bid = db.Column(db.Float)
    current_bid = db.Column(db.Float)
    
    # Images
    images = db.Column(ARRAY(db.String(500)))  # Array of image URLs
    video_url = db.Column(db.String(500))
    
    # Status
    status = db.Column(db.String(20), default='available')  # available, sold, reserved, expired
    is_featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    favorites_count = db.Column(db.Integer, default=0)
    
    # Organic/Certification
    is_organic = db.Column(db.Boolean, default=False)
    organic_certificate = db.Column(db.String(500))
    certifications = db.Column(ARRAY(db.String(100)))  # Array of certification names
    
    # Storage details
    storage_method = db.Column(db.String(100))
    storage_duration_days = db.Column(db.Integer)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='product', lazy=True)
    favorites = db.relationship('ProductFavorite', backref='product', lazy=True)
    reviews = db.relationship('ProductReview', backref='product', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_products_farmer_id', 'farmer_id'),
        Index('idx_products_category_id', 'category_id'),
        Index('idx_products_location', 'location_lat', 'location_lon'),
        Index('idx_products_status', 'status'),
        Index('idx_products_harvest_date', 'harvest_date'),
        Index('idx_products_price', 'price_per_unit'),
        Index('idx_products_created_at', 'created_at'),
        Index('idx_products_selling_mode', 'selling_mode'),
        CheckConstraint('quantity >= 0', name='check_quantity_positive'),
        CheckConstraint('price_per_unit >= 0', name='check_price_positive'),
    )
    
    @hybrid_property
    def is_available(self):
        """Check if product is available for sale"""
        if self.status != 'available':
            return False
        
        if self.available_until and date.today() > self.available_until:
            return False
        
        if self.quantity <= 0:
            return False
        
        return True
    
    @hybrid_property
    def location(self):
        """Get location as tuple"""
        if self.location_lat and self.location_lon:
            return (self.location_lat, self.location_lon)
        return None
    
    @location.setter
    def location(self, value):
        """Set location from tuple"""
        if value and len(value) == 2:
            self.location_lat, self.location_lon = value
    
    @hybrid_property
    def estimated_delivery_cost(self):
        """Calculate estimated delivery cost (simplified)"""
        # This would integrate with logistics API
        base_cost = 50.0  # Base delivery cost
        weight_factor = self.quantity * 0.5  # ₹0.5 per kg
        return round(base_cost + weight_factor, 2)
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            'id': str(self.id),
            'farmer_id': str(self.farmer_id),
            'farmer_name': self.farmer.name if self.farmer else None,
            'category_id': str(self.category_id) if self.category_id else None,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'description': self.description,
            'variety': self.variety,
            'quality_grade': self.quality_grade.value if self.quality_grade else None,
            'quantity': round(self.quantity, 2),
            'unit': self.unit,
            'price_per_unit': round(self.price_per_unit, 2),
            'total_price': round(self.quantity * self.price_per_unit, 2),
            'min_order_quantity': self.min_order_quantity,
            'max_order_quantity': self.max_order_quantity,
            'location': self.location,
            'harvest_location': self.harvest_location,
            'harvest_date': self.harvest_date.isoformat() if self.harvest_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'available_from': self.available_from.isoformat() if self.available_from else None,
            'available_until': self.available_until.isoformat() if self.available_until else None,
            'selling_mode': self.selling_mode.value if self.selling_mode else None,
            'auction_end_time': self.auction_end_time.isoformat() if self.auction_end_time else None,
            'minimum_bid': self.minimum_bid,
            'current_bid': self.current_bid,
            'images': self.images or [],
            'video_url': self.video_url,
            'status': self.status,
            'is_featured': self.is_featured,
            'is_available': self.is_available,
            'views_count': self.views_count,
            'favorites_count': self.favorites_count,
            'is_organic': self.is_organic,
            'organic_certificate': self.organic_certificate,
            'certifications': self.certifications or [],
            'storage_method': self.storage_method,
            'storage_duration_days': self.storage_duration_days,
            'estimated_delivery_cost': self.estimated_delivery_cost,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class ProductFavorite(db.Model):
    """
    Track products favorited by buyers
    """
    __tablename__ = 'product_favorites'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('product_id', 'buyer_id', name='unique_product_favorite'),
        Index('idx_favorites_buyer_id', 'buyer_id'),
        Index('idx_favorites_product_id', 'product_id'),
    )


class ProductReview(db.Model):
    """
    Reviews for products by buyers
    """
    __tablename__ = 'product_reviews'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    images = db.Column(ARRAY(db.String(500)))
    
    # Review metrics
    quality_rating = db.Column(db.Integer)  # 1-5
    delivery_rating = db.Column(db.Integer)  # 1-5
    value_rating = db.Column(db.Integer)     # 1-5
    
    is_verified_purchase = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    report_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_product_reviews_product_id', 'product_id'),
        Index('idx_product_reviews_buyer_id', 'buyer_id'),
        Index('idx_product_reviews_rating', 'rating'),
        UniqueConstraint('order_id', name='unique_order_review'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )


# ============================================
# BUYER MODELS
# ============================================

class Buyer(db.Model):
    """
    Buyer Profile Model
    """
    __tablename__ = 'buyers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default='en')
    
    # Business details (if applicable)
    business_name = db.Column(db.String(200))
    business_type = db.Column(db.String(50))  # retailer, wholesaler, exporter, etc.
    gst_number = db.Column(db.String(15))
    
    # Location
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # Preferences
    preferred_crops = db.Column(ARRAY(db.String(50)))
    preferred_quality = db.Column(ARRAY(db.String(10)))  # ['A', 'B', 'C']
    max_distance_km = db.Column(db.Integer, default=50)
    
    # Stats
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    successful_transactions = db.Column(db.Integer, default=0)
    
    # Profile
    profile_image_url = db.Column(db.String(500))
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='buyer', lazy=True)
    favorites = db.relationship('ProductFavorite', backref='buyer', lazy=True)
    reviews = db.relationship('ProductReview', backref='buyer', lazy=True)
    buyer_preferences = db.relationship('BuyerPreference', backref='buyer', lazy=True, uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_buyers_location', 'location_lat', 'location_lon'),
        Index('idx_buyers_business_type', 'business_type'),
        Index('idx_buyers_is_verified', 'is_verified'),
    )
    
    @hybrid_property
    def location(self):
        """Get location as tuple"""
        if self.location_lat and self.location_lon:
            return (self.location_lat, self.location_lon)
        return None
    
    @location.setter
    def location(self, value):
        """Set location from tuple"""
        if value and len(value) == 2:
            self.location_lat, self.location_lon = value


class BuyerPreference(db.Model):
    """
    Detailed buyer preferences for matching algorithm
    """
    __tablename__ = 'buyer_preferences'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Price preferences
    price_sensitivity = db.Column(db.Float, default=0.5)  # 0-1 scale
    preferred_price_range_low = db.Column(db.Float)
    preferred_price_range_high = db.Column(db.Float)
    
    # Quality preferences
    quality_importance = db.Column(db.Float, default=0.7)  # 0-1 scale
    minimum_acceptable_quality = db.Column(db.String(10), default='C')
    
    # Timing preferences
    preferred_delivery_days = db.Column(db.Integer, default=3)
    urgent_order_willingness = db.Column(db.Float, default=0.3)  # 0-1 scale
    
    # Location preferences
    location_importance = db.Column(db.Float, default=0.8)  # 0-1 scale
    
    # Farmer preferences
    prefer_verified_farmers = db.Column(db.Boolean, default=True)
    prefer_organic = db.Column(db.Boolean, default=False)
    min_farmer_rating = db.Column(db.Float, default=3.0)
    
    # Notification preferences
    notify_new_products = db.Column(db.Boolean, default=True)
    notify_price_drops = db.Column(db.Boolean, default=True)
    notify_auctions = db.Column(db.Boolean, default=False)
    
    # Algorithm weights (used by matching engine)
    weight_price = db.Column(db.Float, default=0.25)
    weight_quality = db.Column(db.Float, default=0.25)
    weight_location = db.Column(db.Float, default=0.25)
    weight_farmer_reputation = db.Column(db.Float, default=0.15)
    weight_timing = db.Column(db.Float, default=0.10)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# ORDER & TRANSACTION MODELS
# ============================================

class Order(db.Model):
    """
    Order placed by buyers
    """
    __tablename__ = 'orders'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='SET NULL'))
    
    # Order details
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    negotiated_price = db.Column(db.Float)  # For bargain mode
    
    # Delivery details
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_city = db.Column(db.String(100))
    delivery_state = db.Column(db.String(100))
    delivery_pincode = db.Column(db.String(10))
    delivery_lat = db.Column(db.Float)
    delivery_lon = db.Column(db.Float)
    
    # Delivery instructions
    delivery_instructions = db.Column(db.Text)
    preferred_delivery_date = db.Column(db.Date)
    delivery_time_slot = db.Column(db.String(50))  # morning, afternoon, evening
    
    # Status
    order_status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = db.Column(db.Enum(PaymentMethod))
    
    # Logistics
    logistics_partner = db.Column(db.String(100))
    tracking_number = db.Column(db.String(100))
    estimated_delivery_date = db.Column(db.Date)
    actual_delivery_date = db.Column(db.Date)
    delivery_cost = db.Column(db.Float, default=0.0)
    
    # Cancellation/Return
    cancellation_reason = db.Column(db.Text)
    return_reason = db.Column(db.Text)
    refund_amount = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    payments = db.relationship('Payment', backref='order', lazy=True)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    reviews = db.relationship('ProductReview', backref='order', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_orders_farmer_id', 'farmer_id'),
        Index('idx_orders_buyer_id', 'buyer_id'),
        Index('idx_orders_product_id', 'product_id'),
        Index('idx_orders_order_status', 'order_status'),
        Index('idx_orders_payment_status', 'payment_status'),
        Index('idx_orders_created_at', 'created_at'),
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
        CheckConstraint('total_amount >= 0', name='check_amount_positive'),
    )
    
    @hybrid_property
    def delivery_location(self):
        """Get delivery location as tuple"""
        if self.delivery_lat and self.delivery_lon:
            return (self.delivery_lat, self.delivery_lon)
        return None
    
    @delivery_location.setter
    def delivery_location(self, value):
        """Set delivery location from tuple"""
        if value and len(value) == 2:
            self.delivery_lat, self.delivery_lon = value
    
    @hybrid_property
    def is_completed(self):
        """Check if order is completed"""
        return self.order_status == OrderStatus.DELIVERED
    
    @hybrid_property
    def days_since_order(self):
        """Calculate days since order was placed"""
        return (datetime.utcnow() - self.created_at).days


class OrderItem(db.Model):
    """
    Individual items in an order (for multi-product orders)
    """
    __tablename__ = 'order_items'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='SET NULL'))
    
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # Product snapshot at time of order (in case product details change)
    product_name = db.Column(db.String(200))
    product_variety = db.Column(db.String(100))
    quality_grade = db.Column(db.String(10))
    
    status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered, cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_order_items_order_id', 'order_id'),
        Index('idx_order_items_product_id', 'product_id'),
        CheckConstraint('quantity > 0', name='check_item_quantity_positive'),
    )


class Payment(db.Model):
    """
    Payment records
    """
    __tablename__ = 'payments'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'))
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'))
    
    # Payment details
    payment_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    payment_status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Gateway details
    gateway_transaction_id = db.Column(db.String(100))
    gateway_response = db.Column(JSONB)  # Store complete gateway response
    gateway_name = db.Column(db.String(50))  # razorpay, stripe, paytm, etc.
    
    # UPI/Bank details
    upi_id = db.Column(db.String(100))
    bank_account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    ifsc_code = db.Column(db.String(20))
    
    # Cash on delivery
    collected_by = db.Column(db.String(100))
    collection_date = db.Column(db.DateTime)
    
    # Metadata
    initiated_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_payments_order_id', 'order_id'),
        Index('idx_payments_farmer_id', 'farmer_id'),
        Index('idx_payments_buyer_id', 'buyer_id'),
        Index('idx_payments_payment_status', 'payment_status'),
        Index('idx_payments_payment_number', 'payment_number'),
        Index('idx_payments_created_at', 'created_at'),
    )


# ============================================
# AUCTION & BARGAIN MODELS
# ============================================

class Auction(db.Model):
    """
    Auction details for products
    """
    __tablename__ = 'auctions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    start_price = db.Column(db.Float, nullable=False)
    reserve_price = db.Column(db.Float)  # Minimum price to sell
    current_bid = db.Column(db.Float)
    bid_increment = db.Column(db.Float, default=1.0)  # Minimum bid increment
    
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False)
    extended_time = db.Column(db.DateTime)  # If auction is extended
    
    status = db.Column(db.String(20), default='active')  # active, ended, cancelled
    winner_bid_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bids.id', ondelete='SET NULL'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bids = db.relationship('Bid', backref='auction', lazy=True)
    winner_bid = db.relationship('Bid', foreign_keys=[winner_bid_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_auctions_product_id', 'product_id'),
        Index('idx_auctions_status', 'status'),
        Index('idx_auctions_end_time', 'end_time'),
        CheckConstraint('end_time > start_time', name='check_auction_timing'),
    )
    
    @hybrid_property
    def is_active(self):
        """Check if auction is currently active"""
        now = datetime.utcnow()
        return self.status == 'active' and self.start_time <= now <= self.end_time
    
    @hybrid_property
    def time_remaining(self):
        """Calculate time remaining in auction"""
        if not self.is_active:
            return 0
        return (self.end_time - datetime.utcnow()).total_seconds()


class Bid(db.Model):
    """
    Bids placed in auctions
    """
    __tablename__ = 'bids'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auction_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auctions.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    is_auto_bid = db.Column(db.Boolean, default=False)  # Automatic bidding
    max_auto_bid = db.Column(db.Float)  # Maximum for auto-bidding
    
    status = db.Column(db.String(20), default='active')  # active, outbid, won, cancelled
    outbid_by = db.Column(UUID(as_uuid=True), db.ForeignKey('bids.id', ondelete='SET NULL'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    buyer = db.relationship('Buyer', backref='bids')
    outbid_by_bid = db.relationship('Bid', remote_side=[id], foreign_keys=[outbid_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_bids_auction_id', 'auction_id'),
        Index('idx_bids_buyer_id', 'buyer_id'),
        Index('idx_bids_amount', 'amount'),
        Index('idx_bids_created_at', 'created_at'),
        CheckConstraint('amount > 0', name='check_bid_amount_positive'),
    )


class Bargain(db.Model):
    """
    Bargain negotiations between farmer and buyer
    """
    __tablename__ = 'bargains'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = db.Column(UUID(as_uuid=True), db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    
    original_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    buyer_offer = db.Column(db.Float)
    farmer_counter_offer = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='active')  # active, accepted, rejected, expired
    initiated_by = db.Column(db.String(10), nullable=False)  # farmer or buyer
    
    expires_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('BargainMessage', backref='bargain', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_bargains_product_id', 'product_id'),
        Index('idx_bargains_farmer_id', 'farmer_id'),
        Index('idx_bargains_buyer_id', 'buyer_id'),
        Index('idx_bargains_status', 'status'),
        UniqueConstraint('product_id', 'buyer_id', name='unique_bargain_request'),
    )


class BargainMessage(db.Model):
    """
    Messages exchanged during bargain negotiation
    """
    __tablename__ = 'bargain_messages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bargain_id = db.Column(UUID(as_uuid=True), db.ForeignKey('bargains.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(UUID(as_uuid=True), nullable=False)  # Farmer or Buyer ID
    sender_type = db.Column(db.String(10), nullable=False)  # farmer or buyer
    
    message_type = db.Column(db.String(20), default='text')  # text, offer, counter_offer
    message = db.Column(db.Text)
    offer_price = db.Column(db.Float)
    
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_bargain_messages_bargain_id', 'bargain_id'),
        Index('idx_bargain_messages_sender', 'sender_id', 'sender_type'),
        Index('idx_bargain_messages_created_at', 'created_at'),
    )


# ============================================
# COMMUNITY & FORUM MODELS
# ============================================

class CommunityPost(db.Model):
    """
    Forum posts in farmer community
    """
    __tablename__ = 'community_posts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default='en')
    
    # Categories and tags
    category = db.Column(db.String(50))  # question, experience, tip, news, etc.
    tags = db.Column(ARRAY(db.String(50)))
    
    # Engagement metrics
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    
    # Media
    images = db.Column(ARRAY(db.String(500)))
    video_url = db.Column(db.String(500))
    
    # Moderation
    is_pinned = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    report_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('CommunityComment', backref='post', lazy=True)
    likes = db.relationship('CommunityLike', backref='post', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_community_posts_farmer_id', 'farmer_id'),
        Index('idx_community_posts_category', 'category'),
        Index('idx_community_posts_created_at', 'created_at'),
        Index('idx_community_posts_tags', 'tags', postgresql_using='gin'),
    )


class CommunityComment(db.Model):
    """
    Comments on community posts
    """
    __tablename__ = 'community_comments'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey('community_posts.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    parent_comment_id = db.Column(UUID(as_uuid=True), db.ForeignKey('community_comments.id', ondelete='CASCADE'))
    
    content = db.Column(db.Text, nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    report_count = db.Column(db.Integer, default=0)
    
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('CommunityComment', remote_side=[id], backref='replies')
    
    # Indexes
    __table_args__ = (
        Index('idx_community_comments_post_id', 'post_id'),
        Index('idx_community_comments_farmer_id', 'farmer_id'),
        Index('idx_community_comments_parent_id', 'parent_comment_id'),
    )


class CommunityLike(db.Model):
    """
    Likes on community posts
    """
    __tablename__ = 'community_likes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey('community_posts.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('post_id', 'farmer_id', name='unique_post_like'),
        Index('idx_community_likes_post_id', 'post_id'),
        Index('idx_community_likes_farmer_id', 'farmer_id'),
    )


# ============================================
# NOTIFICATION MODELS
# ============================================

class Notification(db.Model):
    """
    System notifications for users
    """
    __tablename__ = 'notifications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'))
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'))
    
    # Notification details
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # order, auction, bargain, system, community
    
    # Target entity
    entity_type = db.Column(db.String(50))  # product, order, auction, etc.
    entity_id = db.Column(UUID(as_uuid=True))
    
    # Delivery status
    sent_via_sms = db.Column(db.Boolean, default=False)
    sent_via_email = db.Column(db.Boolean, default=False)
    sent_via_push = db.Column(db.Boolean, default=False)
    
    # Read status
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime)  # For scheduled notifications
    
    # Indexes
    __table_args__ = (
        Index('idx_notifications_farmer_id', 'farmer_id'),
        Index('idx_notifications_buyer_id', 'buyer_id'),
        Index('idx_notifications_type', 'notification_type'),
        Index('idx_notifications_created_at', 'created_at'),
        Index('idx_notifications_is_read', 'is_read'),
    )


# ============================================
# MARKET DATA MODELS
# ============================================

class MarketPrice(db.Model):
    """
    Current market prices for crops
    """
    __tablename__ = 'market_prices'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_name = db.Column(db.String(100), nullable=False, index=True)
    variety = db.Column(db.String(100))
    
    # Location
    market_name = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    
    # Prices
    min_price = db.Column(db.Float, nullable=False)
    max_price = db.Column(db.Float, nullable=False)
    avg_price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='kg')
    
    # Quality grades
    quality_a_price = db.Column(db.Float)
    quality_b_price = db.Column(db.Float)
    quality_c_price = db.Column(db.Float)
    
    # Price trends
    price_trend = db.Column(db.String(20))  # increasing, decreasing, stable
    change_percentage = db.Column(db.Float)
    prev_day_avg = db.Column(db.Float)
    
    # Source and timeliness
    source = db.Column(db.String(100))  # govt_api, manual, etc.
    is_verified = db.Column(db.Boolean, default=False)
    recorded_date = db.Column(db.Date, nullable=False, default=date.today)
    recorded_time = db.Column(db.Time)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_market_prices_crop', 'crop_name', 'variety'),
        Index('idx_market_prices_location', 'city', 'state'),
        Index('idx_market_prices_date', 'recorded_date'),
        Index('idx_market_prices_price', 'avg_price'),
        UniqueConstraint('crop_name', 'variety', 'market_name', 'recorded_date', name='unique_daily_price'),
    )


class PriceAlert(db.Model):
    """
    Price alerts set by farmers
    """
    __tablename__ = 'price_alerts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    
    crop_name = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100))
    
    alert_type = db.Column(db.String(20), nullable=False)  # above, below, change
    target_price = db.Column(db.Float, nullable=False)
    percentage_change = db.Column(db.Float)
    
    is_active = db.Column(db.Boolean, default=True)
    triggered_at = db.Column(db.DateTime)
    last_notified_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_price_alerts_farmer_id', 'farmer_id'),
        Index('idx_price_alerts_crop', 'crop_name'),
        Index('idx_price_alerts_is_active', 'is_active'),
    )


# ============================================
# WEATHER & ADVISORY MODELS
# ============================================

class WeatherAlert(db.Model):
    """
    Weather alerts for farmers
    """
    __tablename__ = 'weather_alerts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'))
    location_lat = db.Column(db.Float, nullable=False)
    location_lon = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100))
    
    alert_type = db.Column(db.String(50), nullable=False)  # rainfall, temperature, storm, etc.
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, severe
    message = db.Column(db.Text, nullable=False)
    
    forecast_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    
    # Weather parameters
    rainfall_mm = db.Column(db.Float)
    temperature_min = db.Column(db.Float)
    temperature_max = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    
    # Advisory
    advisory = db.Column(db.Text)
    impact_on_crops = db.Column(db.Text)
    recommended_actions = db.Column(db.Text)
    
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_weather_alerts_farmer_id', 'farmer_id'),
        Index('idx_weather_alerts_location', 'location_lat', 'location_lon'),
        Index('idx_weather_alerts_date', 'forecast_date'),
        Index('idx_weather_alerts_alert_type', 'alert_type'),
    )


class CropAdvisory(db.Model):
    """
    Crop advisory and recommendations
    """
    __tablename__ = 'crop_advisories'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crop_name = db.Column(db.String(100), nullable=False)
    variety = db.Column(db.String(100))
    
    # Advisory details
    advisory_type = db.Column(db.String(50), nullable=False)  # planting, irrigation, pest, harvest, storage
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Seasonal information
    season = db.Column(db.String(50))  # kharif, rabi, zaid
    month = db.Column(db.Integer)  # 1-12
    region = db.Column(db.String(100))
    
    # Expert information
    expert_name = db.Column(db.String(100))
    expert_qualification = db.Column(db.String(200))
    source = db.Column(db.String(200))  # Government, University, etc.
    
    # Media
    images = db.Column(ARRAY(db.String(500)))
    video_url = db.Column(db.String(500))
    document_url = db.Column(db.String(500))
    
    # Metadata
    is_featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    helpful_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_crop_advisories_crop', 'crop_name'),
        Index('idx_crop_advisories_type', 'advisory_type'),
        Index('idx_crop_advisories_season', 'season'),
        Index('idx_crop_advisories_created_at', 'created_at'),
    )


# ============================================
# GOVERNMENT SCHEME MODELS
# ============================================

class GovernmentScheme(db.Model):
    """
    Government schemes and subsidies
    """
    __tablename__ = 'government_schemes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_name = db.Column(db.String(200), nullable=False)
    scheme_name_regional = db.Column(db.String(200))  # In regional language
    
    # Scheme details
    description = db.Column(db.Text, nullable=False)
    benefits = db.Column(ARRAY(db.String(500)))
    eligibility_criteria = db.Column(ARRAY(db.String(500)))
    documents_required = db.Column(ARRAY(db.String(200)))
    
    # Financial details
    subsidy_percentage = db.Column(db.Float)
    max_subsidy_amount = db.Column(db.Float)
    loan_amount = db.Column(db.Float)
    interest_rate = db.Column(db.Float)
    
    # Applicability
    applicable_states = db.Column(ARRAY(db.String(100)))
    applicable_crops = db.Column(ARRAY(db.String(100)))
    farmer_category = db.Column(ARRAY(db.String(100)))  # small, marginal, women, SC/ST, etc.
    
    # Timeline
    launch_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    last_date_to_apply = db.Column(db.Date)
    
    # Application details
    application_url = db.Column(db.String(500))
    contact_number = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    
    # Department/Ministry
    department = db.Column(db.String(200))
    ministry = db.Column(db.String(200))
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    priority_level = db.Column(db.Integer, default=1)  # 1-5, 5 being highest
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_government_schemes_name', 'scheme_name'),
        Index('idx_government_schemes_active', 'is_active'),
        Index('idx_government_schemes_end_date', 'end_date'),
        Index('idx_government_schemes_priority', 'priority_level'),
    )


class SchemeApplication(db.Model):
    """
    Farmer applications for government schemes
    """
    __tablename__ = 'scheme_applications'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheme_id = db.Column(UUID(as_uuid=True), db.ForeignKey('government_schemes.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    
    application_number = db.Column(db.String(50), unique=True)
    application_date = db.Column(db.Date, nullable=False, default=date.today)
    
    status = db.Column(db.String(30), default='draft')  # draft, submitted, under_review, approved, rejected
    approval_date = db.Column(db.Date)
    rejection_date = db.Column(db.Date)
    rejection_reason = db.Column(db.Text)
    
    # Application data (store as JSON)
    application_data = db.Column(JSONB, nullable=False)
    documents = db.Column(ARRAY(db.String(500)))  # URLs to uploaded documents
    
    # Sanction details (if approved)
    sanctioned_amount = db.Column(db.Float)
    sanction_number = db.Column(db.String(50))
    disbursement_date = db.Column(db.Date)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scheme = db.relationship('GovernmentScheme', backref='applications')
    farmer = db.relationship('Farmer', backref='scheme_applications')
    
    # Indexes
    __table_args__ = (
        Index('idx_scheme_applications_farmer_id', 'farmer_id'),
        Index('idx_scheme_applications_scheme_id', 'scheme_id'),
        Index('idx_scheme_applications_status', 'status'),
        Index('idx_scheme_applications_application_date', 'application_date'),
    )


# ============================================
# LOGISTICS MODELS
# ============================================

class LogisticsProvider(db.Model):
    """
    Logistics and transport service providers
    """
    __tablename__ = 'logistics_providers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    
    # Service details
    service_type = db.Column(ARRAY(db.String(50)))  # truck, tempo, pickup, etc.
    vehicle_types = db.Column(ARRAY(db.String(50)))  # open, closed, refrigerated, etc.
    max_capacity_kg = db.Column(db.Float)
    min_capacity_kg = db.Column(db.Float, default=0)
    
    # Coverage area
    service_cities = db.Column(ARRAY(db.String(100)))
    service_states = db.Column(ARRAY(db.String(100)))
    service_pincodes = db.Column(ARRAY(db.String(10)))
    
    # Pricing
    base_rate_per_km = db.Column(db.Float, nullable=False)
    min_charge = db.Column(db.Float)
    loading_charges = db.Column(db.Float)
    unloading_charges = db.Column(db.Float)
    
    # Ratings
    avg_rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    on_time_delivery_rate = db.Column(db.Float, default=0.0)
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    verification_documents = db.Column(ARRAY(db.String(500)))
    
    # Availability
    is_available = db.Column(db.Boolean, default=True)
    operating_hours = db.Column(db.String(100))  # e.g., "9:00-18:00"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_logistics_name', 'name'),
        Index('idx_logistics_cities', 'service_cities', postgresql_using='gin'),
        Index('idx_logistics_available', 'is_available'),
        Index('idx_logistics_rating', 'avg_rating'),
    )
class DeliveryRequest(db.Model):
    """
    Delivery requests for logistics
    """
    __tablename__ = 'delivery_requests'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    buyer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('buyers.id', ondelete='CASCADE'), nullable=False)
    
    # Pickup details
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_city = db.Column(db.String(100))
    pickup_state = db.Column(db.String(100))
    pickup_pincode = db.Column(db.String(10))
    pickup_lat = db.Column(db.Float)
    pickup_lon = db.Column(db.Float)
    pickup_date = db.Column(db.Date, nullable=False)
    pickup_time_slot = db.Column(db.String(50))
    
    # Delivery details
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_city = db.Column(db.String(100))
    delivery_state = db.Column(db.String(100))
    delivery_pincode = db.Column(db.String(10))
    delivery_lat = db.Column(db.Float)
    delivery_lon = db.Column(db.Float)
    delivery_date = db.Column(db.Date, nullable=False)
    delivery_time_slot = db.Column(db.String(50))
    
    # Goods details
    goods_type = db.Column(db.String(100), nullable=False)  # agricultural, perishable, etc.
    weight_kg = db.Column(db.Float, nullable=False)
    volume_cubic_m = db.Column(db.Float)
    packaging_type = db.Column(db.String(50))  # bags, boxes, crates, etc.
    special_instructions = db.Column(db.Text)
    
    # Provider details
    logistics_provider_id = db.Column(UUID(as_uuid=True), db.ForeignKey('logistics_providers.id', ondelete='SET NULL'))
    assigned_driver = db.Column(db.String(100))
    driver_contact = db.Column(db.String(20))
    vehicle_number = db.Column(db.String(20))
    
    # Pricing
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    payment_status = db.Column(db.String(20), default='pending')
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, assigned, picked_up, in_transit, delivered
    tracking_number = db.Column(db.String(100))
    
    # Timestamps
    assigned_at = db.Column(db.DateTime)
    picked_up_at = db.Column(db.DateTime)
    in_transit_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref='delivery_request')
    logistics_provider = db.relationship('LogisticsProvider', backref='delivery_requests')
    
    # Indexes
    __table_args__ = (
        Index('idx_delivery_requests_order_id', 'order_id'),
        Index('idx_delivery_requests_farmer_id', 'farmer_id'),
        Index('idx_delivery_requests_buyer_id', 'buyer_id'),
        Index('idx_delivery_requests_status', 'status'),
        Index('idx_delivery_requests_dates', 'pickup_date', 'delivery_date'),
    )


# ============================================
# FARMING INPUTS MODELS
# ============================================

class FarmingInputCategory(db.Model):
    """
    Categories for farming inputs (seeds, fertilizers, tools)
    """
    __tablename__ = 'farming_input_categories'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True)
    name_hindi = db.Column(db.String(100))
    name_tamil = db.Column(db.String(100))
    name_telugu = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    parent_category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farming_input_categories.id', ondelete='SET NULL'))
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inputs = db.relationship('FarmingInput', backref='category', lazy=True)
    parent = db.relationship('FarmingInputCategory', remote_side=[id], backref='subcategories')
    
    # Indexes
    __table_args__ = (
        Index('idx_input_categories_name', 'name'),
        Index('idx_input_categories_parent', 'parent_category_id'),
    )


class FarmingInput(db.Model):
    """
    Farming inputs for sale (seeds, fertilizers, tools)
    """
    __tablename__ = 'farming_inputs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farming_input_categories.id', ondelete='SET NULL'), nullable=False)
    supplier_id = db.Column(UUID(as_uuid=True), db.ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    
    # Product details
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Specifications
    specifications = db.Column(JSONB)  # Store as JSON for flexible fields
    suitable_for_crops = db.Column(ARRAY(db.String(100)))
    usage_instructions = db.Column(db.Text)
    safety_precautions = db.Column(db.Text)
    
    # Pricing & Inventory
    price_per_unit = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='kg')  # kg, liter, piece, packet, etc.
    min_order_quantity = db.Column(db.Float, default=1.0)
    max_order_quantity = db.Column(db.Float)
    stock_quantity = db.Column(db.Float, nullable=False, default=0)
    low_stock_threshold = db.Column(db.Float, default=10.0)
    
    # Discounts
    discount_percentage = db.Column(db.Float, default=0.0)
    discount_start_date = db.Column(db.Date)
    discount_end_date = db.Column(db.Date)
    
    # Certification & Quality
    is_organic = db.Column(db.Boolean, default=False)
    certifications = db.Column(ARRAY(db.String(100)))
    quality_rating = db.Column(db.Float, default=0.0)
    
    # Images
    images = db.Column(ARRAY(db.String(500)))
    
    # Status
    is_available = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    views_count = db.Column(db.Integer, default=0)
    orders_count = db.Column(db.Integer, default=0)
    
    # Government schemes
    eligible_for_subsidy = db.Column(db.Boolean, default=False)
    subsidy_percentage = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    supplier = db.relationship('Supplier', backref='inputs')
    input_orders = db.relationship('FarmingInputOrder', backref='input', lazy=True)
    reviews = db.relationship('FarmingInputReview', backref='input', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_farming_inputs_category_id', 'category_id'),
        Index('idx_farming_inputs_supplier_id', 'supplier_id'),
        Index('idx_farming_inputs_price', 'price_per_unit'),
        Index('idx_farming_inputs_stock', 'stock_quantity'),
        Index('idx_farming_inputs_available', 'is_available'),
        CheckConstraint('price_per_unit >= 0', name='check_input_price_positive'),
        CheckConstraint('stock_quantity >= 0', name='check_stock_positive'),
    )


class Supplier(db.Model):
    """
    Suppliers of farming inputs
    """
    __tablename__ = 'suppliers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True)
    
    # Business details
    business_type = db.Column(db.String(50))  # manufacturer, distributor, retailer
    gst_number = db.Column(db.String(15))
    trade_license = db.Column(db.String(100))
    
    # Address
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    
    # Business info
    year_established = db.Column(db.Integer)
    total_products = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)
    verification_documents = db.Column(ARRAY(db.String(500)))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    account_manager = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    input_orders = db.relationship('FarmingInputOrder', backref='supplier', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_suppliers_name', 'name'),
        Index('idx_suppliers_city', 'city'),
        Index('idx_suppliers_is_verified', 'is_verified'),
        Index('idx_suppliers_rating', 'avg_rating'),
    )


class FarmingInputOrder(db.Model):
    """
    Orders for farming inputs placed by farmers
    """
    __tablename__ = 'farming_input_orders'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    input_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farming_inputs.id', ondelete='CASCADE'))
    supplier_id = db.Column(UUID(as_uuid=True), db.ForeignKey('suppliers.id', ondelete='CASCADE'))
    
    # Order details
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    final_amount = db.Column(db.Float, nullable=False)
    
    # Delivery details
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_city = db.Column(db.String(100))
    delivery_state = db.Column(db.String(100))
    delivery_pincode = db.Column(db.String(10))
    delivery_date = db.Column(db.Date)
    delivery_time_slot = db.Column(db.String(50))
    
    # Status
    order_status = db.Column(db.String(20), default='pending')  # pending, confirmed, processing, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20))
    
    # Government subsidy
    subsidy_applied = db.Column(db.Boolean, default=False)
    subsidy_amount = db.Column(db.Float, default=0.0)
    subsidy_reference = db.Column(db.String(100))
    
    # Cancellation
    cancellation_reason = db.Column(db.Text)
    refund_amount = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    
    # Relationships
    farmer = db.relationship('Farmer', backref='input_orders')
    payments = db.relationship('FarmingInputPayment', backref='order', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_input_orders_farmer_id', 'farmer_id'),
        Index('idx_input_orders_supplier_id', 'supplier_id'),
        Index('idx_input_orders_input_id', 'input_id'),
        Index('idx_input_orders_status', 'order_status'),
        Index('idx_input_orders_created_at', 'created_at'),
        CheckConstraint('quantity > 0', name='check_input_order_quantity'),
    )


class FarmingInputReview(db.Model):
    """
    Reviews for farming inputs
    """
    __tablename__ = 'farming_input_reviews'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    input_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farming_inputs.id', ondelete='CASCADE'), nullable=False)
    farmer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('farming_input_orders.id', ondelete='CASCADE'), nullable=False)
    
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    comment = db.Column(db.Text)
    images = db.Column(ARRAY(db.String(500)))
    
    # Aspect ratings
    quality_rating = db.Column(db.Integer)  # 1-5
    effectiveness_rating = db.Column(db.Integer)  # 1-5
    value_rating = db.Column(db.Integer)  # 1-5
    
    is_verified_purchase = db.Column(db.Boolean, default=False)
    helpful_count = db.Column(db.Integer, default=0)
    report_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_input_reviews_input_id', 'input_id'),
        Index('idx_input_reviews_farmer_id', 'farmer_id'),
        Index('idx_input_reviews_rating', 'rating'),
        UniqueConstraint('order_id', name='unique_input_order_review'),
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_input_rating_range'),
    )


# ============================================
# ADMIN MODELS
# ============================================

class Admin(db.Model):
    """
    Admin users for platform management
    """
    __tablename__ = 'admins'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal details
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20))
    
    # Role and permissions
    role = db.Column(db.String(50), nullable=False)  # super_admin, admin, moderator, support
    permissions = db.Column(ARRAY(db.String(50)))  # Array of permission codes
    department = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Security
    two_factor_enabled = db.Column(db.Boolean, default=False)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    admin_actions = db.relationship('AdminActionLog', backref='admin', lazy=True)
    farmer_verifications = db.relationship('FarmerVerification', backref='verified_by_admin', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_admins_username', 'username'),
        Index('idx_admins_email', 'email'),
        Index('idx_admins_role', 'role'),
        Index('idx_admins_is_active', 'is_active'),
    )


class AdminActionLog(db.Model):
    """
    Log of admin actions for audit trail
    """
    __tablename__ = 'admin_action_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = db.Column(UUID(as_uuid=True), db.ForeignKey('admins.id', ondelete='SET NULL'))
    
    action_type = db.Column(db.String(50), nullable=False)  # create, update, delete, approve, reject
    entity_type = db.Column(db.String(50), nullable=False)  # farmer, product, order, etc.
    entity_id = db.Column(UUID(as_uuid=True), nullable=False)
    
    # Action details
    description = db.Column(db.Text, nullable=False)
    changes = db.Column(JSONB)  # Store changes as JSON
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_admin_actions_admin_id', 'admin_id'),
        Index('idx_admin_actions_entity', 'entity_type', 'entity_id'),
        Index('idx_admin_actions_created_at', 'created_at'),
        Index('idx_admin_actions_type', 'action_type'),
    )


# ============================================
# SECURITY & AUDIT MODELS
# ============================================

class SecurityLog(db.Model):
    """
    Security-related events log
    """
    __tablename__ = 'security_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True))  # Could be farmer_id, buyer_id, or admin_id
    user_type = db.Column(db.String(20))  # farmer, buyer, admin
    
    event_type = db.Column(db.String(50), nullable=False)  # login, logout, password_change, etc.
    event_status = db.Column(db.String(20), nullable=False)  # success, failure, warning
    severity = db.Column(db.String(20), default='info')  # info, low, medium, high, critical
    
    # Event details
    description = db.Column(db.Text)
    details = db.Column(JSONB)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    location = db.Column(db.String(100))
    
    # Device info
    device_type = db.Column(db.String(50))
    browser = db.Column(db.String(100))
    os = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_security_logs_user', 'user_id', 'user_type'),
        Index('idx_security_logs_event_type', 'event_type'),
        Index('idx_security_logs_status', 'event_status'),
        Index('idx_security_logs_severity', 'severity'),
        Index('idx_security_logs_created_at', 'created_at'),
        Index('idx_security_logs_ip', 'ip_address'),
    )


class FailedLoginAttempt(db.Model):
    """
    Track failed login attempts for security
    """
    __tablename__ = 'failed_login_attempts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(100), nullable=False)  # Could be phone, email, username
    user_type = db.Column(db.String(20), nullable=False)  # farmer, buyer, admin
    
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text)
    attempted_password = db.Column(db.String(100))  # Hashed for security
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_failed_logins_username', 'username', 'user_type'),
        Index('idx_failed_logins_ip', 'ip_address'),
        Index('idx_failed_logins_created_at', 'created_at'),
    )


class BlockedIP(db.Model):
    """
    Blocked IP addresses for security
    """
    __tablename__ = 'blocked_ips'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = db.Column(db.String(45), nullable=False, unique=True)
    
    # Block details
    reason = db.Column(db.String(200), nullable=False)
    blocked_by = db.Column(db.String(50))  # system, admin
    severity = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Block duration
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_until = db.Column(db.DateTime)  # Null for permanent block
    
    # Counters
    violation_count = db.Column(db.Integer, default=1)
    
    # Metadata
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_blocked_ips_ip', 'ip_address'),
        Index('idx_blocked_ips_blocked_until', 'blocked_until'),
        Index('idx_blocked_ips_severity', 'severity'),
    )


# ============================================
# MISCELLANEOUS MODELS
# ============================================

class AppSetting(db.Model):
    """
    Application settings and configuration
    """
    __tablename__ = 'app_settings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    data_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean, json
    category = db.Column(db.String(50), default='general')
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_app_settings_key', 'setting_key'),
        Index('idx_app_settings_category', 'category'),
    )


class Language(db.Model):
    """
    Supported languages for localization
    """
    __tablename__ = 'languages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = db.Column(db.String(10), unique=True, nullable=False)  # en, hi, ta, te, etc.
    name = db.Column(db.String(50), nullable=False)  # English, Hindi, Tamil, Telugu
    native_name = db.Column(db.String(50))  # English, हिन्दी, தமிழ், తెలుగు
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_languages_code', 'code'),
        Index('idx_languages_active', 'is_active'),
    )


class Country(db.Model):
    """
    Countries (currently India-focused, but extensible)
    """
    __tablename__ = 'countries'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)
    iso_code = db.Column(db.String(2), unique=True)  # IN, US, etc.
    phone_code = db.Column(db.String(10))
    currency_code = db.Column(db.String(3))
    currency_symbol = db.Column(db.String(5))
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    states = db.relationship('State', backref='country', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_countries_name', 'name'),
        Index('idx_countries_iso_code', 'iso_code'),
    )


class State(db.Model):
    """
    States within countries
    """
    __tablename__ = 'states'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = db.Column(UUID(as_uuid=True), db.ForeignKey('countries.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10))  # State code like MH, TN, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cities = db.relationship('City', backref='state', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_states_country_id', 'country_id'),
        Index('idx_states_name', 'name'),
        UniqueConstraint('country_id', 'name', name='unique_state_country'),
    )


class City(db.Model):
    """
    Cities within states
    """
    __tablename__ = 'cities'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id = db.Column(UUID(as_uuid=True), db.ForeignKey('states.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10))
    location_lat = db.Column(db.Float)
    location_lon = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_cities_state_id', 'state_id'),
        Index('idx_cities_name', 'name'),
        Index('idx_cities_pincode', 'pincode'),
    )


# ============================================
# VIEW MODELS (Database Views)
# ============================================

class FarmerSummary(db.Model):
    """
    Materialized view for farmer summary statistics
    """
    __tablename__ = 'farmer_summary_view'
    
    farmer_id = db.Column(UUID(as_uuid=True), primary_key=True)
    farmer_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    is_verified = db.Column(db.Boolean)
    trust_score = db.Column(db.Float)
    
    total_products_listed = db.Column(db.Integer, default=0)
    active_products = db.Column(db.Integer, default=0)
    total_orders = db.Column(db.Integer, default=0)
    completed_orders = db.Column(db.Integer, default=0)
    total_sales_amount = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    
    last_order_date = db.Column(db.DateTime)
    last_active = db.Column(db.DateTime)
    
    # This is not a real table, just for querying
    __table_args__ = {'info': dict(is_view=True)}


class ProductSummary(db.Model):
    """
    Materialized view for product summary statistics
    """
    __tablename__ = 'product_summary_view'
    
    product_id = db.Column(UUID(as_uuid=True), primary_key=True)
    product_name = db.Column(db.String(200))
    farmer_id = db.Column(UUID(as_uuid=True))
    farmer_name = db.Column(db.String(100))
    
    category_id = db.Column(UUID(as_uuid=True))
    category_name = db.Column(db.String(100))
    
    quantity_available = db.Column(db.Float)
    price_per_unit = db.Column(db.Float)
    quality_grade = db.Column(db.String(10))
    
    total_orders = db.Column(db.Integer, default=0)
    total_quantity_sold = db.Column(db.Float, default=0.0)
    total_revenue = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    
    views_count = db.Column(db.Integer, default=0)
    favorites_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime)
    last_order_date = db.Column(db.DateTime)
    
    # This is not a real table, just for querying
    __table_args__ = {'info': dict(is_view=True)}


# ============================================
# HELPER FUNCTIONS
# ============================================

def init_database(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create database views
        create_views()
        
        # Insert initial data
        insert_initial_data()
        
        print("✓ Database initialized successfully")


def create_views():
    """Create database views for reporting"""
    # In production, you would create materialized views here
    pass


def insert_initial_data():
    """Insert initial data into database"""
    from sqlalchemy import inspect
    
    # Check if languages table is empty
    inspector = inspect(db.engine)
    if inspector.has_table('languages'):
        if db.session.query(Language).count() == 0:
            # Insert default languages
            languages = [
                Language(code='en', name='English', native_name='English', is_active=True),
                Language(code='hi', name='Hindi', native_name='हिन्दी', is_active=True),
                Language(code='ta', name='Tamil', native_name='தமிழ்', is_active=True),
                Language(code='te', name='Telugu', native_name='తెలుగు', is_active=True),
                Language(code='kn', name='Kannada', native_name='ಕನ್ನಡ', is_active=True),
                Language(code='ml', name='Malayalam', native_name='മലയാളം', is_active=True),
                Language(code='mr', name='Marathi', native_name='मराठी', is_active=True),
                Language(code='bn', name='Bengali', native_name='বাংলা', is_active=True),
                Language(code='gu', name='Gujarati', native_name='ગુજરાતી', is_active=True),
                Language(code='or', name='Odia', native_name='ଓଡ଼ିଆ', is_active=True),
                Language(code='pa', name='Punjabi', native_name='ਪੰਜਾਬੀ', is_active=True),
                Language(code='ur', name='Urdu', native_name='اردو', is_active=True),
            ]
            db.session.add_all(languages)
            
            # Insert default country (India)
            if db.session.query(Country).count() == 0:
                india = Country(
                    name='India',
                    iso_code='IN',
                    phone_code='+91',
                    currency_code='INR',
                    currency_symbol='₹',
                    is_active=True
                )
                db.session.add(india)
                db.session.flush()  # Get the ID
                
                # Insert some Indian states
                states = [
                    State(country_id=india.id, name='Maharashtra', code='MH'),
                    State(country_id=india.id, name='Tamil Nadu', code='TN'),
                    State(country_id=india.id, name='Uttar Pradesh', code='UP'),
                    State(country_id=india.id, name='Karnataka', code='KA'),
                    State(country_id=india.id, name='Gujarat', code='GJ'),
                    State(country_id=india.id, name='Rajasthan', code='RJ'),
                    State(country_id=india.id, name='Madhya Pradesh', code='MP'),
                    State(country_id=india.id, name='West Bengal', code='WB'),
                    State(country_id=india.id, name='Andhra Pradesh', code='AP'),
                    State(country_id=india.id, name='Telangana', code='TG'),
                ]
                db.session.add_all(states)
            
            # Insert default product categories
            if db.session.query(ProductCategory).count() == 0:
                categories = [
                    ProductCategory(name='Cereals', description='Rice, Wheat, Maize, etc.'),
                    ProductCategory(name='Pulses', description='Lentils, Chickpeas, Beans, etc.'),
                    ProductCategory(name='Vegetables', description='Tomato, Potato, Onion, etc.'),
                    ProductCategory(name='Fruits', description='Mango, Banana, Apple, etc.'),
                    ProductCategory(name='Spices', description='Turmeric, Chili, Coriander, etc.'),
                    ProductCategory(name='Oilseeds', description='Mustard, Sunflower, Groundnut, etc.'),
                    ProductCategory(name='Plantation Crops', description='Coffee, Tea, Rubber, etc.'),
                    ProductCategory(name='Flowers', description='Rose, Marigold, Jasmine, etc.'),
                    ProductCategory(name='Medicinal Plants', description='Tulsi, Aloe Vera, Neem, etc.'),
                ]
                db.session.add_all(categories)
            
            # Insert default farming input categories
            if db.session.query(FarmingInputCategory).count() == 0:
                input_categories = [
                    FarmingInputCategory(name='Seeds', description='All types of seeds'),
                    FarmingInputCategory(name='Fertilizers', description='Chemical and organic fertilizers'),
                    FarmingInputCategory(name='Pesticides', description='Insecticides, fungicides, herbicides'),
                    FarmingInputCategory(name='Tools', description='Farming tools and equipment'),
                    FarmingInputCategory(name='Irrigation', description='Pipes, sprinklers, drip systems'),
                    FarmingInputCategory(name='Machinery', description='Tractors, harvesters, tillers'),
                ]
                db.session.add_all(input_categories)
            
            db.session.commit()
            print("✓ Initial data inserted")


# ============================================
# MODEL RELATIONSHIP SUMMARY
# ============================================

"""
Key Relationships:

1. Farmer has:
   - Many Products
   - Many Orders
   - Many Reviews
   - One Verification
   - Many Community Posts
   - Many Notifications
   - Many Input Orders

2. Product has:
   - One Farmer
   - One Category
   - Many Orders
   - Many Favorites
   - Many Reviews
   - One Auction (optional)
   - One Bargain (optional)

3. Order has:
   - One Farmer
   - One Buyer
   - One Product
   - One Delivery Request
   - Many Payments
   - One Review

4. Buyer has:
   - Many Orders
   - Many Favorites
   - Many Reviews
   - Many Bids
   - One BuyerPreference

5. Auction has:
   - One Product
   - Many Bids
   - One Winner Bid

6. CommunityPost has:
   - One Farmer
   - Many Comments
   - Many Likes
"""


# ============================================
# EXPORT ALL MODELS
# ============================================

__all__ = [
    # Core Models
    'Farmer',
    'FarmerVerification',
    'Buyer',
    'BuyerPreference',
    
    # Product Models
    'ProductCategory',
    'Product',
    'ProductFavorite',
    'ProductReview',
    
    # Order & Transaction Models
    'Order',
    'OrderItem',
    'Payment',
    
    # Auction & Bargain Models
    'Auction',
    'Bid',
    'Bargain',
    'BargainMessage',
    
    # Community Models
    'CommunityPost',
    'CommunityComment',
    'CommunityLike',
    
    # Notification Models
    'Notification',
    
    # Market Data Models
    'MarketPrice',
    'PriceAlert',
    
    # Weather & Advisory Models
    'WeatherAlert',
    'CropAdvisory',
    
    # Government Scheme Models
    'GovernmentScheme',
    'SchemeApplication',
    
    # Logistics Models
    'LogisticsProvider',
    'DeliveryRequest',
    
    # Farming Input Models
    'FarmingInputCategory',
    'FarmingInput',
    'Supplier',
    'FarmingInputOrder',
    'FarmingInputReview',
    
    # Admin Models
    'Admin',
    'AdminActionLog',
    
    # Security Models
    'SecurityLog',
    'FailedLoginAttempt',
    'BlockedIP',
    
    # Miscellaneous Models
    'AppSetting',
    'Language',
    'Country',
    'State',
    'City',
    
    # View Models
    'FarmerSummary',
    'ProductSummary',
    
    # Enums
    'QualityGrade',
    'SellingMode',
    'OrderStatus',
    'PaymentMethod',
    'PaymentStatus',
    'VerificationStatus',
    
    # Database instance
    'db',
    'init_database',
]