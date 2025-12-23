# algorithms/community_connector.py
from collections import defaultdict
import networkx as nx
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Set

class CommunityGraphBuilder:
    def __init__(self):
        self.graph = nx.Graph()
        self.farmer_attributes = {}
        
    def build_community_graph(self, farmers: List[Dict], interactions: List[Dict]):
        """Build farmer community graph based on multiple factors"""
        
        # Add farmers as nodes
        for farmer in farmers:
            self.graph.add_node(farmer['id'], **farmer)
            self.farmer_attributes[farmer['id']] = farmer
        
        # Add edges based on interactions
        for interaction in interactions:
            farmer1 = interaction['farmer1_id']
            farmer2 = interaction['farmer2_id']
            
            if farmer1 in self.graph and farmer2 in self.graph:
                weight = self.calculate_connection_weight(farmer1, farmer2, interaction)
                if self.graph.has_edge(farmer1, farmer2):
                    # Update existing edge weight
                    current_weight = self.graph[farmer1][farmer2]['weight']
                    self.graph[farmer1][farmer2]['weight'] = (current_weight + weight) / 2
                else:
                    self.graph.add_edge(farmer1, farmer2, weight=weight)
        
        # Add similarity-based edges
        self.add_similarity_edges()
    
    def calculate_connection_weight(self, farmer1_id: str, farmer2_id: str, 
                                  interaction: Dict) -> float:
        """Calculate connection weight based on multiple factors"""
        weight = 0
        
        # Interaction frequency
        if interaction.get('interaction_count'):
            freq_score = min(1.0, interaction['interaction_count'] / 100)
            weight += freq_score * 0.3
        
        # Recent interactions (more recent = higher weight)
        if interaction.get('last_interaction'):
            days_ago = (datetime.now() - interaction['last_interaction']).days
            recency_score = max(0, 1 - (days_ago / 365))
            weight += recency_score * 0.2
        
        # Shared interests
        farmer1 = self.farmer_attributes.get(farmer1_id, {})
        farmer2 = self.farmer_attributes.get(farmer2_id, {})
        
        shared_interests = self.calculate_shared_interests(farmer1, farmer2)
        weight += shared_interests * 0.25
        
        # Geographical proximity
        if farmer1.get('location') and farmer2.get('location'):
            distance = self.calculate_distance(farmer1['location'], farmer2['location'])
            proximity_score = max(0, 1 - (distance / 100))  # 100km max influence
            weight += proximity_score * 0.15
        
        # Trust score similarity
        trust1 = farmer1.get('trust_score', 5.0)
        trust2 = farmer2.get('trust_score', 5.0)
        trust_similarity = 1 - abs(trust1 - trust2) / 10  # 0-10 scale
        weight += trust_similarity * 0.1
        
        return min(1.0, weight)  # Normalize to 0-1
    
    def calculate_shared_interests(self, farmer1: Dict, farmer2: Dict) -> float:
        """Calculate shared interests between farmers"""
        interests1 = set(farmer1.get('crops_grown', [])) | set(farmer1.get('expertise', []))
        interests2 = set(farmer2.get('crops_grown', [])) | set(farmer2.get('expertise', []))
        
        if not interests1 or not interests2:
            return 0
        
        intersection = interests1.intersection(interests2)
        union = interests1.union(interests2)
        
        return len(intersection) / len(union) if union else 0
    
    def add_similarity_edges(self):
        """Add edges between similar farmers who haven't interacted yet"""
        farmer_ids = list(self.graph.nodes())
        
        for i in range(len(farmer_ids)):
            for j in range(i + 1, len(farmer_ids)):
                farmer1_id = farmer_ids[i]
                farmer2_id = farmer_ids[j]
                
                # Skip if already connected
                if self.graph.has_edge(farmer1_id, farmer2_id):
                    continue
                
                farmer1 = self.farmer_attributes[farmer1_id]
                farmer2 = self.farmer_attributes[farmer2_id]
                
                similarity = self.calculate_farmer_similarity(farmer1, farmer2)
                
                # Add edge if similarity is high enough
                if similarity > 0.6:
                    self.graph.add_edge(farmer1_id, farmer2_id, 
                                      weight=similarity, 
                                      type='similarity')
    
    def calculate_farmer_similarity(self, farmer1: Dict, farmer2: Dict) -> float:
        """Calculate comprehensive similarity score"""
        similarity = 0
        
        # Crop similarity
        crops1 = set(farmer1.get('crops_grown', []))
        crops2 = set(farmer2.get('crops_grown', []))
        if crops1 and crops2:
            crop_similarity = len(crops1.intersection(crops2)) / len(crops1.union(crops2))
            similarity += crop_similarity * 0.3
        
        # Location similarity (closer = more similar)
        if farmer1.get('location') and farmer2.get('location'):
            distance = self.calculate_distance(farmer1['location'], farmer2['location'])
            location_similarity = max(0, 1 - (distance / 200))  # 200km max
            similarity += location_similarity * 0.25
        
        # Experience level similarity
        exp1 = farmer1.get('experience_years', 0)
        exp2 = farmer2.get('experience_years', 0)
        exp_diff = abs(exp1 - exp2)
        exp_similarity = max(0, 1 - (exp_diff / 20))  # 20 years max difference
        similarity += exp_similarity * 0.2
        
        # Language similarity
        lang1 = farmer1.get('language', 'en')
        lang2 = farmer2.get('language', 'en')
        lang_similarity = 1.0 if lang1 == lang2 else 0.5
        similarity += lang_similarity * 0.15
        
        # Farm size similarity
        size1 = farmer1.get('farm_size_acres', 0)
        size2 = farmer2.get('farm_size_acres', 0)
        if size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            similarity += size_ratio * 0.1
        
        return min(1.0, similarity)
    
    def calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two points (simplified)"""
        # Using Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = radians(loc1[0]), radians(loc1[1])
        lat2, lon2 = radians(loc2[0]), radians(loc2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def get_community_recommendations(self, farmer_id: str, limit: int = 10) -> List[Dict]:
        """Get community recommendations for a farmer"""
        if farmer_id not in self.graph:
            return []
        
        recommendations = []
        
        # Get direct connections
        neighbors = list(self.graph.neighbors(farmer_id))
        
        # Calculate recommendation scores
        for neighbor in neighbors:
            # Get common neighbors (friends of friends)
            common_neighbors = set(self.graph.neighbors(farmer_id)) & \
                             set(self.graph.neighbors(neighbor))
            
            # Calculate Jaccard similarity for network structure
            if common_neighbors:
                jaccard = len(common_neighbors) / len(
                    set(self.graph.neighbors(farmer_id)) | 
                    set(self.graph.neighbors(neighbor))
                )
            else:
                jaccard = 0
            
            # Edge weight
            edge_weight = self.graph[farmer_id][neighbor]['weight']
            
            # Combined score
            score = (edge_weight * 0.6) + (jaccard * 0.4)
            
            farmer_data = self.farmer_attributes[neighbor].copy()
            farmer_data['recommendation_score'] = round(score, 3)
            farmer_data['connection_type'] = 'direct' if edge_weight > 0.7 else 'indirect'
            farmer_data['shared_connections'] = len(common_neighbors)
            
            recommendations.append(farmer_data)
        
        # Sort by score
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return recommendations[:limit]
    
    def detect_communities(self):
        """Detect natural communities in the farmer network"""
        # Use Louvain method for community detection
        import community as community_louvain
        
        partition = community_louvain.best_partition(self.graph)
        
        # Group farmers by community
        communities = defaultdict(list)
        for farmer_id, community_id in partition.items():
            communities[community_id].append(farmer_id)
        
        return dict(communities)

class ForumRecommendationEngine:
    """Recommend forum posts and discussions to farmers"""
    
    def __init__(self):
        self.post_vectors = {}
        self.farmer_interests = {}
    
    def recommend_posts(self, farmer_id: str, posts: List[Dict], limit: int = 5) -> List[Dict]:
        """Recommend forum posts to a farmer"""
        if farmer_id not in self.farmer_interests:
            self.build_farmer_profile(farmer_id, posts)
        
        farmer_profile = self.farmer_interests[farmer_id]
        recommendations = []
        
        for post in posts:
            if post['farmer_id'] == farmer_id:
                continue  # Skip own posts
            
            # Calculate relevance score
            relevance = self.calculate_post_relevance(post, farmer_profile)
            
            # Apply recency boost
            recency_boost = self.calculate_recency_boost(post['created_at'])
            
            final_score = relevance * 0.8 + recency_boost * 0.2
            
            if final_score > 0.3:
                post_copy = post.copy()
                post_copy['relevance_score'] = round(final_score, 3)
                recommendations.append(post_copy)
        
        # Sort by relevance
        recommendations.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return recommendations[:limit]
    
    def build_farmer_profile(self, farmer_id: str, posts: List[Dict]):
        """Build farmer's interest profile based on their activity"""
        farmer_posts = [p for p in posts if p['farmer_id'] == farmer_id]
        
        # Extract interests from posts
        interests = set()
        for post in farmer_posts:
            interests.update(post.get('tags', []))
        
        # Add crop interests from farmer data
        # (This would come from farmer profile)
        
        self.farmer_interests[farmer_id] = {
            'interests': list(interests),
            'post_count': len(farmer_posts),
            'avg_post_length': np.mean([len(p['content']) for p in farmer_posts]) 
            if farmer_posts else 0
        }
    
    def calculate_post_relevance(self, post: Dict, farmer_profile: Dict) -> float:
        """Calculate how relevant a post is to a farmer"""
        relevance = 0
        
        # Tag matching
        post_tags = set(post.get('tags', []))
        farmer_interests = set(farmer_profile.get('interests', []))
        
        if post_tags and farmer_interests:
            tag_overlap = len(post_tags.intersection(farmer_interests))
            tag_relevance = tag_overlap / len(post_tags.union(farmer_interests))
            relevance += tag_relevance * 0.4
        
        # Language matching
        if post.get('language') == farmer_profile.get('preferred_language', 'en'):
            relevance += 0.3
        
        # Similar farmers engagement
        # (Check if farmers similar to this one have engaged with the post)
        if post.get('upvotes', 0) > 0:
            engagement_score = min(1.0, post['upvotes'] / 100)
            relevance += engagement_score * 0.2
        
        # Content length preference
        post_length = len(post.get('content', ''))
        avg_preferred = farmer_profile.get('avg_post_length', 500)
        length_similarity = 1 - abs(post_length - avg_preferred) / max(post_length, avg_preferred, 1)
        relevance += length_similarity * 0.1
        
        return min(1.0, relevance)
    
    def calculate_recency_boost(self, post_time: datetime) -> float:
        """Boost score for recent posts"""
        hours_ago = (datetime.now() - post_time).total_seconds() / 3600
        
        if hours_ago < 24:
            return 1.0
        elif hours_ago < 168:  # 1 week
            return 0.7
        elif hours_ago < 720:  # 1 month
            return 0.3
        else:
            return 0.1