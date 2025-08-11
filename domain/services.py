from typing import Dict, Any, List
import pandas as pd
import pandera.pandas as pa
from .models import PageSchema, ProcessingResult
from .repositories import DataRepository


class ValidationService:
    """Service for data validation using Pandera schemas"""
    
    @staticmethod
    def validate_wikipedia_pages(df: pd.DataFrame) -> ProcessingResult:
        """
        Validate Wikipedia pages DataFrame against schema
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ProcessingResult with validation outcome
        """
        try:
            # Validate using Pandera schema
            validated_df = PageSchema.validate(df)
            
            return ProcessingResult(
                success=True,
                message="Data validation successful",
                record_count=len(validated_df)
            )
            
        except pa.errors.SchemaError as e:
            return ProcessingResult(
                success=False,
                message="Schema validation failed",
                record_count=len(df),
                errors=[str(e)]
            )
        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Validation error occurred",
                record_count=len(df) if df is not None else 0,
                errors=[f"Unexpected error: {str(e)}"]
            )
    
    @staticmethod
    def validate_generic_data(df: pd.DataFrame, required_columns: List[str]) -> ProcessingResult:
        """
        Generic data validation
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            ProcessingResult with validation outcome
        """
        try:
            if df.empty:
                return ProcessingResult(
                    success=False,
                    message="DataFrame is empty",
                    record_count=0,
                    errors=["No data to validate"]
                )
            
            # Check for required columns
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return ProcessingResult(
                    success=False,
                    message="Missing required columns",
                    record_count=len(df),
                    errors=[f"Missing columns: {', '.join(missing_columns)}"]
                )
            
            # Check for null values in required columns
            null_counts = df[required_columns].isnull().sum()
            columns_with_nulls = [col for col, count in null_counts.items() if count > 0]
            
            if columns_with_nulls:
                return ProcessingResult(
                    success=False,
                    message="Null values found in required columns",
                    record_count=len(df),
                    errors=[f"Null values in columns: {', '.join(columns_with_nulls)}"]
                )
            
            return ProcessingResult(
                success=True,
                message="Generic validation successful",
                record_count=len(df)
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Validation error occurred",
                record_count=len(df) if df is not None else 0,
                errors=[f"Unexpected error: {str(e)}"]
            )


class DataProcessingService:
    """Service for data processing operations"""
    
    def __init__(self, repository: DataRepository):
        self.repository = repository
        self.validation_service = ValidationService()
    
    def clean_text_data(self, df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
        """
        Clean text data in specified columns
        
        Args:
            df: Input DataFrame
            text_columns: List of column names to clean
            
        Returns:
            DataFrame with cleaned text data
        """
        cleaned_df = df.copy()
        
        for column in text_columns:
            if column in cleaned_df.columns:
                # Remove extra whitespace
                cleaned_df[column] = cleaned_df[column].astype(str).str.strip()
                # Remove multiple spaces
                cleaned_df[column] = cleaned_df[column].str.replace(r'\s+', ' ', regex=True)
                # Handle null/empty values
                cleaned_df[column] = cleaned_df[column].replace(['', 'nan', 'None'], pd.NA)
        
        return cleaned_df
    
    def filter_data(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to DataFrame
        
        Args:
            df: Input DataFrame
            filters: Dictionary of column:value filters
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        for column, filter_value in filters.items():
            if column in filtered_df.columns:
                if isinstance(filter_value, str) and filter_value.startswith("contains:"):
                    # String contains filter
                    search_term = filter_value.replace("contains:", "")
                    filtered_df = filtered_df[
                        filtered_df[column].astype(str).str.contains(search_term, case=False, na=False)
                    ]
                elif isinstance(filter_value, str) and filter_value.startswith("startswith:"):
                    # String starts with filter
                    prefix = filter_value.replace("startswith:", "")
                    filtered_df = filtered_df[
                        filtered_df[column].astype(str).str.startswith(prefix, na=False)
                    ]
                else:
                    # Exact match filter
                    filtered_df = filtered_df[filtered_df[column] == filter_value]
        
        return filtered_df
    
    def deduplicate_data(self, df: pd.DataFrame, subset_columns: List[str] = None) -> pd.DataFrame:
        """
        Remove duplicate records from DataFrame
        
        Args:
            df: Input DataFrame
            subset_columns: Columns to consider for duplication check
            
        Returns:
            DataFrame without duplicates
        """
        return df.drop_duplicates(subset=subset_columns, keep='first')
    
    def add_metadata_columns(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> pd.DataFrame:
        """
        Add metadata columns to DataFrame
        
        Args:
            df: Input DataFrame
            metadata: Dictionary of column_name:value pairs
            
        Returns:
            DataFrame with additional metadata columns
        """
        result_df = df.copy()
        
        for column_name, value in metadata.items():
            result_df[column_name] = value
            
        return result_df