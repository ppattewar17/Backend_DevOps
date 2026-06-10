import pandas as pd
from typing import List
from app.config import get_settings

settings = get_settings()


class AnomalyDetector:
    """Service for detecting anomalies in transaction data"""
    
    def __init__(self):
        self.domestic_merchants = [m.lower() for m in settings.DOMESTIC_MERCHANTS]
    
    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect anomalies in transactions:
        1. Statistical outliers (amount > 3x account median)
        2. Currency mismatches (USD with domestic merchants)
        
        Args:
            df: Cleaned transaction DataFrame
            
        Returns:
            DataFrame with anomaly flags and reasons
        """
        df = df.copy()
        df['is_anomaly'] = False
        df['anomaly_reason'] = None
        
        # Detect statistical outliers
        df = self._detect_statistical_outliers(df)
        
        # Detect currency mismatches
        df = self._detect_currency_mismatches(df)
        
        return df
    
    def _detect_statistical_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag transactions where amount exceeds 3x the account's median
        """
        # Calculate median amount per account
        account_medians = df.groupby('account_id')['amount'].median()
        
        for idx, row in df.iterrows():
            account_median = account_medians.get(row['account_id'], 0)
            
            if account_median > 0 and row['amount'] > (3 * account_median):
                df.at[idx, 'is_anomaly'] = True
                reason = f"Statistical outlier: Amount {row['amount']} exceeds 3x account median {account_median:.2f}"
                
                # Append to existing reason if any
                if df.at[idx, 'anomaly_reason']:
                    df.at[idx, 'anomaly_reason'] += f"; {reason}"
                else:
                    df.at[idx, 'anomaly_reason'] = reason
        
        return df
    
    def _detect_currency_mismatches(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Flag transactions where currency is USD but merchant is domestic-only
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
                reason = f"Currency mismatch: USD currency with domestic merchant {row['merchant']}"
                
                # Append to existing reason if any
                if df.at[idx, 'anomaly_reason']:
                    df.at[idx, 'anomaly_reason'] += f"; {reason}"
                else:
                    df.at[idx, 'anomaly_reason'] = reason
        
        return df
