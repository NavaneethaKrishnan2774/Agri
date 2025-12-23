# algorithms/fraud_detector.py
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import hashlib
import re

class FraudDetectionSystem:
    def __init__(self):
        self.suspicious_patterns = []
        self.load_fraud_patterns()
    
    def load_fraud_patterns(self):
        """Load known fraud patterns"""
        self.suspicious_patterns = [
            {'type': 'price_manipulation', 'threshold': 0.5},
            {'type': 'fake_location', 'pattern': 'duplicate_coordinates'},
            {'type': 'suspicious_behavior', 'pattern': 'rapid_listings'},
            {'type': 'fake_reviews', 'pattern': 'identical_feedback'},
            {'type': 'account_takeover', 'pattern': 'unusual_login'}
        ]
    
    def analyze_farmer_risk(self, farmer_data: Dict, transactions: List[Dict]) -> Dict:
        """Comprehensive farmer risk analysis"""
        risk_score = 0
        risk_factors = []
        
        # 1. Profile completeness check
        profile_risk = self.check_profile_completeness(farmer_data)
        risk_score += profile_risk['score']
        risk_factors.extend(profile_risk['factors'])
        
        # 2. Transaction pattern analysis
        if transactions:
            transaction_risk = self.analyze_transaction_patterns(transactions)
            risk_score += transaction_risk['score']
            risk_factors.extend(transaction_risk['factors'])
        
        # 3. Behavioral analysis
        behavioral_risk = self.analyze_behavioral_patterns(farmer_data)
        risk_score += behavioral_risk['score']
        risk_factors.extend(behavioral_risk['factors'])
        
        # 4. Device and location analysis
        device_risk = self.analyze_device_patterns(farmer_data)
        risk_score += device_risk['score']
        risk_factors.extend(device_risk['factors'])
        
        # Normalize risk score (0-100)
        normalized_score = min(100, risk_score * 20)
        
        return {
            'risk_score': round(normalized_score, 2),
            'risk_level': self.get_risk_level(normalized_score),
            'risk_factors': risk_factors,
            'recommendations': self.get_recommendations(risk_factors),
            'requires_verification': normalized_score > 40
        }
    
    def check_profile_completeness(self, farmer_data: Dict) -> Dict:
        """Check farmer profile completeness"""
        score = 0
        factors = []
        
        required_fields = ['name', 'phone', 'location', 'address']
        optional_fields = ['email', 'aadhaar', 'land_docs']
        
        # Check required fields
        for field in required_fields:
            if not farmer_data.get(field):
                score += 2
                factors.append(f'missing_{field}')
        
        # Check optional fields
        missing_optional = sum(1 for field in optional_fields if not farmer_data.get(field))
        if missing_optional > 2:
            score += 1
            factors.append('incomplete_profile')
        
        return {'score': score, 'factors': factors}
    
    def analyze_transaction_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze transaction patterns for fraud indicators"""
        score = 0
        factors = []
        
        if len(transactions) < 3:
            return {'score': 0, 'factors': []}
        
        # Check for price manipulation
        prices = [t.get('price', 0) for t in transactions]
        price_std = np.std(prices)
        price_mean = np.mean(prices)
        
        if price_std > price_mean * 0.5:  # Large price variations
            score += 3
            factors.append('unusual_price_variations')
        
        # Check transaction timing
        timestamps = [t['timestamp'] for t in transactions]
        timestamps.sort()
        
        # Detect rapid transactions
        rapid_count = 0
        for i in range(1, len(timestamps)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds()
            if time_diff < 300:  # Less than 5 minutes between transactions
                rapid_count += 1
        
        if rapid_count > 3:
            score += 4
            factors.append('rapid_transactions')
        
        # Check for circular transactions
        unique_buyers = len(set(t['buyer_id'] for t in transactions))
        if len(transactions) > 10 and unique_buyers < 3:
            score += 5
            factors.append('limited_buyer_pool')
        
        return {'score': score, 'factors': factors}
    
    def analyze_behavioral_patterns(self, farmer_data: Dict) -> Dict:
        """Analyze behavioral patterns"""
        score = 0
        factors = []
        
        # Check login patterns
        login_times = farmer_data.get('login_times', [])
        if login_times:
            # Detect unusual login times
            unusual_hours = sum(1 for t in login_times 
                              if t.hour < 4 or t.hour > 22)  # 10PM to 4AM
            if unusual_hours > len(login_times) * 0.3:
                score += 2
                factors.append('unusual_login_times')
        
        # Check edit frequency
        profile_edits = farmer_data.get('profile_edits', 0)
        if profile_edits > 10:
            score += 1
            factors.append('frequent_profile_changes')
        
        return {'score': score, 'factors': factors}
    
    def analyze_device_patterns(self, farmer_data: Dict) -> Dict:
        """Analyze device and location patterns"""
        score = 0
        factors = []
        
        devices = farmer_data.get('devices', [])
        locations = farmer_data.get('login_locations', [])
        
        # Multiple device detection
        if len(devices) > 3:
            score += 2
            factors.append('multiple_devices')
        
        # Location hopping detection
        if len(locations) > 2:
            # Calculate distances between locations
            from geopy.distance import great_circle
            
            for i in range(1, len(locations)):
                distance = great_circle(locations[i-1], locations[i]).km
                time_diff = farmer_data.get('location_times', [])[i] - \
                           farmer_data.get('location_times', [])[i-1]
                
                # Check if physically impossible travel
                if distance > 500 and time_diff.total_seconds() < 3600:
                    score += 5
                    factors.append('impossible_travel')
                    break
        
        return {'score': score, 'factors': factors}
    
    def get_risk_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 20:
            return 'low'
        elif score < 50:
            return 'medium'
        elif score < 75:
            return 'high'
        else:
            return 'critical'
    
    def get_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Get recommendations based on risk factors"""
        recommendations = []
        
        recommendations_map = {
            'missing_name': 'Complete your profile name',
            'missing_phone': 'Verify phone number',
            'missing_location': 'Add farm location',
            'incomplete_profile': 'Complete profile with additional details',
            'unusual_price_variations': 'Review pricing strategy',
            'rapid_transactions': 'Slow down transaction pace',
            'limited_buyer_pool': 'Diversify buyer network',
            'unusual_login_times': 'Review account security',
            'frequent_profile_changes': 'Limit profile edits',
            'multiple_devices': 'Verify authorized devices',
            'impossible_travel': 'Account security check required'
        }
        
        for factor in risk_factors:
            if factor in recommendations_map:
                recommendations.append(recommendations_map[factor])
        
        return recommendations
    
    def detect_price_manipulation(self, product_data: Dict, market_data: Dict) -> bool:
        """Detect potential price manipulation"""
        product_price = product_data.get('price_per_unit', 0)
        market_avg = market_data.get('average_price', 0)
        market_std = market_data.get('price_std', 0)
        
        if market_avg == 0:
            return False
        
        # Calculate z-score
        if market_std > 0:
            z_score = abs(product_price - market_avg) / market_std
        else:
            z_score = abs(product_price - market_avg) / market_avg
        
        # Flag if price is more than 3 standard deviations away
        return z_score > 3
    
    def validate_location(self, location: Tuple[float, float]) -> Dict:
        """Validate farm location"""
        lat, lon = location
        
        # Check if location is valid
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return {'valid': False, 'reason': 'invalid_coordinates'}
        
        # Check if location is in known water bodies (simplified)
        # In production, use GIS data
        water_locations = [
            (20.5937, 78.9629),  # Example water body
        ]
        
        for water_loc in water_locations:
            distance = self.calculate_distance(location, water_loc)
            if distance < 1:  # Within 1km of water body
                return {'valid': False, 'reason': 'suspicious_location'}
        
        return {'valid': True}
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two points"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        
        lat1, lon1 = radians(loc1[0]), radians(loc1[1])
        lat2, lon2 = radians(loc2[0]), radians(loc2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

class RealTimeFraudMonitor:
    """Real-time fraud monitoring system"""
    
    def __init__(self):
        self.suspicious_activities = []
        self.blocked_ips = set()
        self.failed_logins = {}
    
    def monitor_activity(self, activity: Dict):
        """Monitor real-time activity for fraud"""
        alerts = []
        
        # Check for brute force attacks
        if activity['type'] == 'login_failed':
            ip = activity.get('ip_address')
            if ip:
                self.failed_logins[ip] = self.failed_logins.get(ip, 0) + 1
                
                if self.failed_logins[ip] > 5:
                    self.blocked_ips.add(ip)
                    alerts.append({
                        'type': 'brute_force_detected',
                        'ip': ip,
                        'severity': 'high'
                    })
        
        # Check for suspicious transaction patterns
        elif activity['type'] == 'transaction':
            if self.is_suspicious_transaction(activity):
                alerts.append({
                    'type': 'suspicious_transaction',
                    'transaction_id': activity.get('transaction_id'),
                    'severity': 'medium'
                })
        
        # Check for account takeover attempts
        elif activity['type'] == 'password_change':
            if self.is_suspicious_password_change(activity):
                alerts.append({
                    'type': 'account_takeover_attempt',
                    'severity': 'critical'
                })
        
        return alerts
    
    def is_suspicious_transaction(self, transaction: Dict) -> bool:
        """Check if transaction is suspicious"""
        # Check amount anomalies
        amount = transaction.get('amount', 0)
        farmer_history = transaction.get('farmer_history', {})
        
        avg_transaction = farmer_history.get('avg_transaction', 0)
        
        if avg_transaction > 0:
            if amount > avg_transaction * 5:  # 5x average
                return True
        
        # Check frequency anomalies
        transaction_count = farmer_history.get('transaction_count', 0)
        if transaction_count > 10:
            recent_transactions = farmer_history.get('recent_transactions', [])
            if len(recent_transactions) > 5:
                # Check if transactions are too frequent
                time_diffs = []
                for i in range(1, len(recent_transactions)):
                    diff = recent_transactions[i]['timestamp'] - \
                           recent_transactions[i-1]['timestamp']
                    time_diffs.append(diff.total_seconds())
                
                avg_diff = np.mean(time_diffs) if time_diffs else 0
                if avg_diff < 60:  # Less than 1 minute between transactions
                    return True
        
        return False
    
    def is_suspicious_password_change(self, activity: Dict) -> bool:
        """Check if password change is suspicious"""
        # Check if from new device
        if activity.get('new_device', False):
            # Check if recent login failures
            recent_failures = activity.get('recent_failures', 0)
            if recent_failures > 2:
                return True
        
        # Check if from suspicious location
        current_location = activity.get('location')
        usual_locations = activity.get('usual_locations', [])
        
        if usual_locations and current_location:
            # Calculate distance to usual locations
            distances = []
            for loc in usual_locations:
                distance = self.calculate_distance(current_location, loc)
                distances.append(distance)
            
            min_distance = min(distances) if distances else float('inf')
            if min_distance > 100:  # More than 100km from usual location
                return True
        
        return False