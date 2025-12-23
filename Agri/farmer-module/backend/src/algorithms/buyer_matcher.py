# algorithms/buyer_matcher.py
import numpy as np
from sklearn.neighbors import BallTree
from geopy.distance import great_circle
from datetime import datetime, timedelta
import asyncio
from typing import List, Dict, Tuple
import heapq

class BuyerMatchingAlgorithm:
    def __init__(self):
        self.location_tree = None
        self.buyer_data = []
        
    def build_location_index(self, buyers: List[Dict]):
        """Build spatial index for efficient location-based matching"""
        locations = []
        self.buyer_data = buyers
        
        for buyer in buyers:
            if buyer.get('location'):
                lat, lon = buyer['location']
                locations.append([lat, lon])
        
        if locations:
            # Convert to radians for haversine distance
            locations_rad = np.radians(locations)
            self.location_tree = BallTree(locations_rad, metric='haversine')
    
    def find_nearby_buyers(self, farmer_location: Tuple[float, float], 
                          max_distance_km: float = 50) -> List[Dict]:
        """Find buyers within specified distance"""
        if not self.location_tree:
            return []
        
        # Convert to radians
        farmer_loc_rad = np.radians([farmer_location])
        
        # Calculate distance in kilometers (6371 = Earth's radius in km)
        distances, indices = self.location_tree.query(
            farmer_loc_rad, 
            k=min(len(self.buyer_data), 100)
        )
        
        nearby_buyers = []
        for idx, distance in zip(indices[0], distances[0]):
            # Convert radian distance to km
            distance_km = distance * 6371
            
            if distance_km <= max_distance_km:
                buyer = self.buyer_data[idx].copy()
                buyer['distance_km'] = round(distance_km, 2)
                nearby_buyers.append(buyer)
        
        # Sort by distance
        nearby_buyers.sort(key=lambda x: x['distance_km'])
        return nearby_buyers
    
    def match_by_preferences(self, product: Dict, buyers: List[Dict]) -> List[Dict]:
        """Match product to buyers based on preferences using weighted scoring"""
        matches = []
        
        for buyer in buyers:
            score = 0
            weights = {
                'location': 0.3,
                'price': 0.25,
                'quality': 0.2,
                'timing': 0.15,
                'history': 0.1
            }
            
            # Location score (closer is better)
            if buyer.get('distance_km'):
                max_dist = buyer.get('max_distance_km', 50)
                location_score = max(0, 1 - (buyer['distance_km'] / max_dist))
                score += location_score * weights['location']
            
            # Price compatibility score
            if buyer.get('price_range_low') and buyer.get('price_range_high'):
                product_price = product.get('price_per_unit', 0)
                low, high = buyer['price_range_low'], buyer['price_range_high']
                
                if low <= product_price <= high:
                    price_score = 1.0
                else:
                    # Calculate how far outside the range
                    if product_price < low:
                        price_score = max(0, 1 - (low - product_price) / low)
                    else:
                        price_score = max(0, 1 - (product_price - high) / high)
                
                score += price_score * weights['price']
            
            # Quality match
            if buyer.get('preferred_quality') and product.get('quality_grade'):
                if product['quality_grade'] in buyer['preferred_quality']:
                    score += weights['quality']
            
            # Timing score (recently active buyers)
            if buyer.get('last_active'):
                days_since = (datetime.now() - buyer['last_active']).days
                timing_score = max(0, 1 - (days_since / 30))  # 30-day window
                score += timing_score * weights['timing']
            
            # Historical transaction score
            if buyer.get('transaction_success_rate'):
                score += buyer['transaction_success_rate'] * weights['history']
            
            if score > 0.3:  # Threshold for matching
                match = buyer.copy()
                match['match_score'] = round(score, 3)
                match['recommended_price'] = self.calculate_recommended_price(product, buyer)
                matches.append(match)
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]  # Return top 10 matches
    
    def calculate_recommended_price(self, product: Dict, buyer: Dict) -> float:
        """Calculate optimal price based on market and buyer history"""
        base_price = product['price_per_unit']
        
        # Adjust based on buyer's price range
        if buyer.get('price_range_low') and buyer.get('price_range_high'):
            buyer_mid = (buyer['price_range_low'] + buyer['price_range_high']) / 2
            # Weighted average between farmer's price and buyer's mid-range
            recommended = (base_price * 0.6) + (buyer_mid * 0.4)
        else:
            recommended = base_price
        
        # Apply seasonal adjustment
        recommended = self.apply_seasonal_adjustment(recommended, product.get('crop_type'))
        
        return round(recommended, 2)
    
    def apply_seasonal_adjustment(self, price: float, crop_type: str = None) -> float:
        """Adjust price based on seasonality"""
        month = datetime.now().month
        
        # Simple seasonal adjustment factors
        seasonal_factors = {
            'wheat': {1: 1.1, 2: 1.05, 3: 1.0, 4: 0.95, 5: 0.9, 6: 0.85,
                      7: 0.9, 8: 0.95, 9: 1.0, 10: 1.05, 11: 1.1, 12: 1.1},
            'rice': {1: 1.0, 2: 1.05, 3: 1.1, 4: 1.05, 5: 1.0, 6: 0.95,
                     7: 0.9, 8: 0.95, 9: 1.0, 10: 1.05, 11: 1.1, 12: 1.05},
            'default': {m: 1.0 for m in range(1, 13)}
        }
        
        factor = seasonal_factors.get(crop_type, seasonal_factors['default']).get(month, 1.0)
        return price * factor

class RealTimeMatchingEngine:
    """Real-time matching engine using WebSockets"""
    
    def __init__(self):
        self.active_buyers = {}  # buyer_id -> socket connection
        self.product_queue = asyncio.Queue()
        self.matcher = BuyerMatchingAlgorithm()
    
    async def add_buyer(self, buyer_id: str, websocket, preferences: Dict):
        """Add active buyer to matching pool"""
        self.active_buyers[buyer_id] = {
            'websocket': websocket,
            'preferences': preferences,
            'last_ping': datetime.now()
        }
    
    async def process_product(self, product: Dict):
        """Process new product and find real-time matches"""
        # Get nearby active buyers
        nearby_buyers = self.get_nearby_active_buyers(product['location'])
        
        # Match based on preferences
        matches = self.matcher.match_by_preferences(product, nearby_buyers)
        
        # Send real-time notifications to matched buyers
        for match in matches:
            buyer_id = match['buyer_id']
            if buyer_id in self.active_buyers:
                await self.send_match_notification(
                    self.active_buyers[buyer_id]['websocket'],
                    product,
                    match['match_score']
                )
        
        return matches
    
    def get_nearby_active_buyers(self, location: Tuple[float, float]) -> List[Dict]:
        """Get active buyers within 50km"""
        active = []
        current_time = datetime.now()
        
        for buyer_id, data in self.active_buyers.items():
            # Check if buyer is still active (last ping within 5 minutes)
            if (current_time - data['last_ping']).seconds < 300:
                # Calculate distance (simplified)
                buyer_loc = data['preferences'].get('location')
                if buyer_loc:
                    distance = great_circle(location, buyer_loc).km
                    if distance <= 50:
                        buyer_data = data['preferences'].copy()
                        buyer_data['buyer_id'] = buyer_id
                        buyer_data['distance_km'] = distance
                        active.append(buyer_data)
        
        return active
    
    async def send_match_notification(self, websocket, product: Dict, score: float):
        """Send real-time match notification"""
        message = {
            'type': 'product_match',
            'product_id': product['id'],
            'product_name': product['name'],
            'farmer_name': product['farmer_name'],
            'quantity': product['quantity'],
            'price': product['price_per_unit'],
            'quality': product.get('quality_grade'),
            'distance_km': product.get('distance', 0),
            'match_score': score,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            await websocket.send_json(message)
        except:
            pass  # Handle disconnected clients