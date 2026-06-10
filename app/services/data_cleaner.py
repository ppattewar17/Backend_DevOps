import pandas as pd
import re
from dateutil import parser
from datetime import datetime


class DataCleaner:
    """Service for cleaning and normalizing transaction data"""
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean transaction data:
        - Normalize date formats to ISO 8601
        - Strip currency symbols from amounts
        - Uppercase status values
        - Fill missing categories with 'Uncategorised'
        - Remove exact duplicate rows
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df = df.copy()
        
        # Normalize dates
        df['date'] = df['date'].apply(self._normalize_date)
        
        # Clean amounts (remove currency symbols)
        df['amount'] = df['amount'].apply(self._clean_amount)
        
        # Uppercase status values
        df['status'] = df['status'].str.upper()
        
        # Normalize currency
        df['currency'] = df['currency'].str.upper()
        
        # Fill missing categories
        df['category'] = df['category'].fillna('Uncategorised')
        df['category'] = df['category'].replace('', 'Uncategorised')
        
        # Fill missing notes
        df['notes'] = df['notes'].fillna('')
        
        # Remove exact duplicates
        df = df.drop_duplicates()
        
        return df
    
    def _normalize_date(self, date_str: str) -> datetime:
        """
        Normalize date string to ISO 8601 format
        
        Handles formats:
        - DD-MM-YYYY
        - YYYY/MM/DD
        - MM-DD-YYYY
        """
        try:
            # Try parsing with dateutil (handles most formats)
            dt = parser.parse(str(date_str), dayfirst=False)
            return dt
        except Exception as e:
            # Fallback to current date if parsing fails
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
