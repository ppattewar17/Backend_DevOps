"""
Mock LLM service for testing without OpenAI API key
To use: Rename this file to llm_service.py
"""
import random
from typing import List, Dict
from app.config import get_settings

settings = get_settings()


class LLMService:
    """Mock service that simulates LLM responses without API calls"""
    
    def __init__(self):
        self.valid_categories = settings.VALID_CATEGORIES
    
    def classify_transactions_batch(self, transactions: List) -> List[Dict]:
        """Mock classification - returns random categories"""
        print("⚠️  Using MOCK LLM Service (no OpenAI API calls)")
        
        results = []
        for t in transactions:
            # Simple rule-based classification
            merchant = t.merchant.lower()
            
            if 'swiggy' in merchant or 'zomato' in merchant:
                category = 'Food'
            elif 'amazon' in merchant or 'flipkart' in merchant:
                category = 'Shopping'
            elif 'ola' in merchant or 'uber' in merchant:
                category = 'Transport'
            elif 'irctc' in merchant or 'makemytrip' in merchant:
                category = 'Travel'
            elif 'atm' in merchant:
                category = 'Cash Withdrawal'
            elif 'jio' in merchant or 'recharge' in merchant:
                category = 'Utilities'
            else:
                category = 'Other'
            
            results.append({"category": category})
        
        return results
    
    def generate_narrative(self, summary_data: Dict, transactions: List) -> Dict:
        """Mock narrative generation"""
        print("⚠️  Using MOCK LLM Service (no OpenAI API calls)")
        
        anomaly_rate = summary_data['anomaly_count'] / len(transactions) * 100
        
        if anomaly_rate > 20:
            risk_level = "high"
            narrative = f"High anomaly rate detected ({summary_data['anomaly_count']} out of {len(transactions)} transactions). Multiple suspicious patterns observed including currency mismatches and statistical outliers. Immediate review recommended."
        elif anomaly_rate > 10:
            risk_level = "medium"
            narrative = f"Moderate spending patterns observed with {summary_data['anomaly_count']} anomalies detected. Top spending on {summary_data['top_merchants'][0]['merchant']} accounts for significant portion of transactions. Review recommended for flagged transactions."
        else:
            risk_level = "low"
            narrative = f"Normal spending patterns detected across {len(transactions)} transactions. Primary spending on {summary_data['top_merchants'][0]['merchant']} and {summary_data['top_merchants'][1]['merchant']}. Only {summary_data['anomaly_count']} minor anomalies require attention."
        
        return {
            'narrative': narrative,
            'risk_level': risk_level
        }
