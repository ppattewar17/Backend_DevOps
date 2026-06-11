import json
import time
from typing import List, Dict
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_settings

settings = get_settings()


class LLMService:
    """Service for OpenAI-based transaction classification and narrative generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.valid_categories = settings.VALID_CATEGORIES
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4)
    )
    def classify_transactions_batch(self, transactions: List) -> List[Dict]:
        """
        Classify transactions in batch using OpenAI
        Retries: 3 times with exponential backoff (1s, 2s, 4s)
        
        Args:
            transactions: List of Transaction objects without categories
            
        Returns:
            List of dicts with category assignments
        """
        if not transactions:
            return []
        
        # Prepare batch data (limit to 50 at a time for API limits)
        batch_size = 50
        all_results = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            
            # Create prompt with transaction details
            transactions_text = []
            for idx, t in enumerate(batch):
                transactions_text.append(
                    f"{idx+1}. Merchant: {t.merchant}, Amount: {t.amount} {t.currency}, "
                    f"Status: {t.status}, Notes: {t.notes or 'None'}"
                )
            
            prompt = f"""Classify the following transactions into one of these categories:
{', '.join(self.valid_categories)}

Transactions:
{chr(10).join(transactions_text)}

Return a JSON array with one category for each transaction in order.
Format: [{{"category": "Food"}}, {{"category": "Shopping"}}, ...]
"""
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a financial transaction classifier. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                
                # Parse response
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Extract categories array
                if isinstance(result, dict) and 'categories' in result:
                    categories = result['categories']
                elif isinstance(result, list):
                    categories = result
                else:
                    # Fallback: assign Other to all
                    categories = [{"category": "Other"} for _ in batch]
                
                all_results.extend(categories)
                
            except Exception as e:
                print(f"Batch classification failed: {e}")
                # Assign "Other" as fallback
                all_results.extend([{"category": "Other"} for _ in batch])
        
        return all_results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4)
    )
    def generate_summary(self, summary_data: Dict, transactions: List) -> Dict:
        """
        Generate narrative summary and risk assessment using OpenAI
        Retries: 3 times with exponential backoff (1s, 2s, 4s)
        
        Args:
            summary_data: Dict with summary statistics
            transactions: List of Transaction objects
            
        Returns:
            Dict with 'narrative' and 'risk_level' keys
        """
        # Prepare transaction summary for OpenAI
        anomaly_examples = self._format_anomalies(transactions)
        
        prompt = f"""Analyze the following financial transaction summary and provide insights:

**Summary Statistics:**
- Total Spend (INR): ₹{summary_data['total_spend_inr']:,.2f}
- Total Spend (USD): ${summary_data['total_spend_usd']:,.2f}
- Top 3 Merchants: {', '.join([m['merchant'] for m in summary_data['top_merchants']])}
- Anomaly Count: {summary_data['anomaly_count']} out of {len(transactions)} transactions

**Anomalies Detected:**
{anomaly_examples}

Generate a JSON response with:
1. "narrative": A 2-3 sentence spending analysis highlighting key patterns, concerns, or insights
2. "risk_level": Overall risk assessment as "low", "medium", or "high"

Consider factors like:
- High anomaly rate
- Large USD transactions
- Suspicious patterns
- Failed transactions

Return format: {{"narrative": "...", "risk_level": "low|medium|high"}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Provide concise, actionable insights. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            return {
                'narrative': result.get('narrative', 'No narrative available'),
                'risk_level': result.get('risk_level', 'medium')
            }
            
        except Exception as e:
            print(f"Narrative generation failed: {e}")
            return {
                'narrative': "Unable to generate narrative due to processing error.",
                'risk_level': "unknown"
            }
    
    def _format_anomalies(self, transactions: List) -> str:
        """Format anomalies for LLM prompt"""
        anomalies = [t for t in transactions if t.is_anomaly]
        
        if not anomalies:
            return "No anomalies detected"
        
        # Show up to 5 example anomalies
        examples = []
        for t in anomalies[:5]:
            examples.append(
                f"- {t.merchant}: {t.currency} {t.amount} - {t.anomaly_reason}"
            )
        
        result = "\n".join(examples)
        if len(anomalies) > 5:
            result += f"\n- ... and {len(anomalies) - 5} more anomalies"
        
        return result
