"""
Analytics and insights generation service
"""
from typing import List, Dict, Any
from collections import Counter
from src.models.entry import ConversationEntry
from src.models.metrics import ConversationMetrics
from src.utils.logger import logger


class AnalyticsService:
    """
    📊 ANALYTICS AND INSIGHTS GENERATOR
    """
    
    @staticmethod
    def generate_analytics(conversations: List[ConversationEntry],
                          metrics: ConversationMetrics,
                          session_id: str,
                          model_usage: Dict[str, int],
                          mode_usage: Dict[str, int],
                          cache_stats: dict) -> Dict[str, Any]:
        """
        📊 GENERATE COMPREHENSIVE ANALYTICS
        """
        if not conversations:
            return {}
        
        # Model distribution
        most_used_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else "N/A"
        
        # Reasoning mode distribution
        most_used_mode = max(mode_usage.items(), key=lambda x: x[1])[0] if mode_usage else "N/A"
        
        # Token statistics
        total_tokens = sum(conv.tokens_used for conv in conversations)
        avg_tokens = total_tokens / len(conversations) if conversations else 0
        
        # Time statistics
        total_time = sum(conv.inference_time for conv in conversations)
        avg_time = total_time / len(conversations) if conversations else 0
        
        analytics = {
            'session_id': session_id,
            'total_conversations': len(conversations),
            'total_tokens': total_tokens,
            'avg_tokens_per_conversation': avg_tokens,
            'total_time': total_time,
            'avg_inference_time': avg_time,
            'peak_tokens': metrics.peak_tokens,
            'most_used_model': most_used_model,
            'most_used_mode': most_used_mode,
            'model_distribution': dict(model_usage),
            'mode_distribution': dict(mode_usage),
            'cache_hits': cache_stats.get('hits', 0),
            'cache_misses': cache_stats.get('misses', 0),
            'cache_hit_rate': cache_stats.get('hit_rate', '0.0'),
            'error_count': metrics.error_count,
            'avg_confidence': sum(conv.confidence_score for conv in conversations) / len(conversations) if conversations else 0
        }
        
        logger.debug(f"📊 Analytics generated for {len(conversations)} conversations")
        return analytics
    
    @staticmethod
    def search_conversations(conversations: List[ConversationEntry], 
                           keyword: str) -> List[tuple]:
        """
        🔍 SEARCH CONVERSATIONS BY KEYWORD
        """
        keyword_lower = keyword.lower()
        results = []
        
        for idx, conv in enumerate(conversations):
            if (keyword_lower in conv.user_message.lower() or 
                keyword_lower in conv.assistant_response.lower()):
                results.append((idx, conv))
        
        logger.info(f"🔍 Found {len(results)} results for '{keyword}'")
        return results
