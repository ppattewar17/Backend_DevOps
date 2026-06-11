import pandas as pd
from typing import List
from app.core.config import get_settings

settings = get_settings()


class AnomalyDetector:
    """Service for detecting anomalies in transaction data"""
    
    def __init__(self):
        self.domestic_merchants = [m.lower() for m in settings.DOMESTIC_MERCHANTS]
    
    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies following rules:
        Rule 1: Amount > 3x account median
        Rule 2: USD currency with domestic merchant
        
        Returns: DataFrame with is_anomaly and anomaly_reason columns
        """
        df = df.copy()
        df['is_anomaly'] = False
        df['anomaly_reason'] = None
        
        # Rule 1: Statistical outliers
        df = self._detect_statistical_outliers(df)
        
        # Rule 2: Currency mismatches
        df = self._detect_currency_mismatches(df)
        
        return df
    
    def _detect_statistical_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 1: Flag transactions where amount > 3x account median
        """
        # Calculate median amount per account
        account_medians = df.groupby('account_id')['amount'].median()
        
        for idx, row in df.iterrows():
            account_median = account_medians.get(row['account_id'], 0)
            
            if account_median > 0 and row['amount'] > (3 * account_median):
                df.at[idx, 'is_anomaly'] = True
                reason = f"Amount exceeds 3x account median"
                
                # Append to existing reason if any
                if df.at[idx, 'anomaly_reason']:
                    df.at[idx, 'anomaly_reason'] += f"; {reason}"
                else:
                    df.at[idx, 'anomaly_reason'] = reason
        
        return df
    
    def _detect_currency_mismatches(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 2: Flag transactions where currency is USD with domestic merchant
        Domestic merchants: Swiggy, Ola, IRCTC
        """
        for idx, row in df.iterrows():
            merchant_lower = row['merchant'].lower()
            currency_upper = row['currency'].upper()
            
            # Check if USD transaction with domestic merchant
            if currency_upper == 'USD' and any(
                domestic in merchant_lower 
                for domestic in self.domestic_merchants
            ):
                df.at[idx, 'is_anomaly'] = True
                reason = f"Domestic merchant using USD"
                
                # Append to existing reason if any
                if df.at[idx, 'anomaly_reason']:
                    df.at[idx, 'anomaly_reason'] += f"; {reason}"
                else:
                    df.at[idx, 'anomaly_reason'] = reason
        
        return df
