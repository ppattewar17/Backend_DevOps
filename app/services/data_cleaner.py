import pandas as pd
import re
from dateutil import parser
from datetime import datetime
from typing import Tuple


class DataCleaner:
    """Service for cleaning and normalizing transaction data"""
    
    def clean_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
        """
        Clean transaction data following the pipeline:
        A. Normalize dates to YYYY-MM-DD
        B. Strip currency symbols
        C. Uppercase status
        D. Fill missing categories
        E. Remove exact duplicates
        
        Returns: (cleaned_df, raw_count, clean_count)
        """
        raw_count = len(df)
        
        # A. Normalize dates
        df['date'] = df['date'].apply(self._normalize_date)
        
        # B. Strip currency symbols
        df['amount'] = df['amount'].apply(self._clean_amount)
        
        # C. Uppercase status
        df['status'] = df['status'].str.upper()
        
        # D. Normalize currency
        df['currency'] = df['currency'].str.upper()
        
        # E. Fill missing categories
        df['category'] = df['category'].fillna('Uncategorised')
        df['category'] = df['category'].replace('', 'Uncategorised')
        
        # F. Fill missing notes
        df['notes'] = df['notes'].fillna('')
        
        # G. Remove exact duplicates
        df = df.drop_duplicates()
        
        clean_count = len(df)
        
        return df, raw_count, clean_count
    
    def _normalize_date(self, date_str: str) -> datetime:
        """
        Normalize date string to YYYY-MM-DD format
        
        Handles:
        - DD-MM-YYYY
        - YYYY/MM/DD
        - MM-DD-YYYY
        """
        try:
            # Try parsing with dateutil (handles most formats)
            dt = parser.parse(str(date_str), dayfirst=True)
            return dt
        except Exception as e:
            print(f"Date parsing failed for '{date_str}': {e}")
            return datetime.utcnow()
    
    def _clean_amount(self, amount: any) -> float:
        """
        Strip currency symbols and convert to float
        
        Handles:
        - $1,234.56
        - ₹1234.56
        - 1234.56
        """
        try:
            if isinstance(amount, (int, float)):
                return float(amount)
            
            # Remove currency symbols and commas
            amount_str = str(amount)
            amount_str = re.sub(r'[₹$,\s]', '', amount_str)
            return float(amount_str)
        except Exception as e:
            print(f"Amount parsing failed for '{amount}': {e}")
            return 0.0
