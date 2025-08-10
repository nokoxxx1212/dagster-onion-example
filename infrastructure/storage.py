from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
import pandas as pd
from pathlib import Path
from domain.models import ProcessingResult


class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""
    
    @abstractmethod
    def save_data(self, df: pd.DataFrame, destination: str, **kwargs) -> ProcessingResult:
        """Save DataFrame to storage destination"""
        pass
    
    @abstractmethod
    def load_data(self, source: str, **kwargs) -> pd.DataFrame:
        """Load DataFrame from storage source"""
        pass


class CsvStorageAdapter(StorageAdapter):
    """CSV file storage adapter"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path("data")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, df: pd.DataFrame, destination: str, **kwargs) -> ProcessingResult:
        """
        Save DataFrame to CSV file
        
        Args:
            df: DataFrame to save
            destination: Relative file path (will be joined with base_path)
            **kwargs: Additional arguments for pandas.to_csv
            
        Returns:
            ProcessingResult with save operation outcome
        """
        try:
            if df.empty:
                return ProcessingResult(
                    success=False,
                    message="Cannot save empty DataFrame",
                    record_count=0,
                    errors=["DataFrame is empty"]
                )
            
            file_path = self.base_path / destination
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Default CSV options
            csv_options = {
                "index": False,
                "encoding": "utf-8",
                **kwargs
            }
            
            df.to_csv(file_path, **csv_options)
            
            return ProcessingResult(
                success=True,
                message=f"Data saved to {file_path}",
                record_count=len(df)
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Failed to save CSV file",
                record_count=len(df) if df is not None else 0,
                errors=[f"Error: {str(e)}"]
            )
    
    def load_data(self, source: str, **kwargs) -> pd.DataFrame:
        """
        Load DataFrame from CSV file
        
        Args:
            source: Relative file path (will be joined with base_path)
            **kwargs: Additional arguments for pandas.read_csv
            
        Returns:
            DataFrame loaded from CSV
            
        Raises:
            FileNotFoundError: If file doesn't exist
            pd.errors.EmptyDataError: If file is empty
        """
        file_path = self.base_path / source
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Default CSV options
        csv_options = {
            "encoding": "utf-8",
            **kwargs
        }
        
        return pd.read_csv(file_path, **csv_options)


class JsonStorageAdapter(StorageAdapter):
    """JSON file storage adapter"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path("data")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, df: pd.DataFrame, destination: str, **kwargs) -> ProcessingResult:
        """
        Save DataFrame to JSON file
        
        Args:
            df: DataFrame to save
            destination: Relative file path (will be joined with base_path)
            **kwargs: Additional arguments for pandas.to_json
            
        Returns:
            ProcessingResult with save operation outcome
        """
        try:
            if df.empty:
                return ProcessingResult(
                    success=False,
                    message="Cannot save empty DataFrame",
                    record_count=0,
                    errors=["DataFrame is empty"]
                )
            
            file_path = self.base_path / destination
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Default JSON options
            json_options = {
                "orient": "records",
                "indent": 2,
                **kwargs
            }
            
            df.to_json(file_path, **json_options)
            
            return ProcessingResult(
                success=True,
                message=f"Data saved to {file_path}",
                record_count=len(df)
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Failed to save JSON file",
                record_count=len(df) if df is not None else 0,
                errors=[f"Error: {str(e)}"]
            )
    
    def load_data(self, source: str, **kwargs) -> pd.DataFrame:
        """
        Load DataFrame from JSON file
        
        Args:
            source: Relative file path (will be joined with base_path)
            **kwargs: Additional arguments for pandas.read_json
            
        Returns:
            DataFrame loaded from JSON
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = self.base_path / source
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Default JSON options
        json_options = {
            "orient": "records",
            **kwargs
        }
        
        return pd.read_json(file_path, **json_options)


class StorageFactory:
    """Factory for creating storage adapters"""
    
    @staticmethod
    def create_adapter(adapter_type: str, base_path: Optional[str] = None) -> StorageAdapter:
        """
        Create storage adapter based on type
        
        Args:
            adapter_type: Type of storage adapter ('csv', 'json')
            base_path: Base path for storage operations
            
        Returns:
            StorageAdapter instance
            
        Raises:
            ValueError: If adapter type is not supported
        """
        if adapter_type.lower() == "csv":
            return CsvStorageAdapter(base_path)
        elif adapter_type.lower() == "json":
            return JsonStorageAdapter(base_path)
        else:
            raise ValueError(f"Unsupported storage adapter type: {adapter_type}")


class DataExporter:
    """High-level data export service"""
    
    def __init__(self, storage_adapter: StorageAdapter):
        self.storage_adapter = storage_adapter
    
    def export_with_metadata(self, 
                           df: pd.DataFrame, 
                           destination: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """
        Export DataFrame with optional metadata
        
        Args:
            df: DataFrame to export
            destination: Destination path
            metadata: Optional metadata to include
            
        Returns:
            ProcessingResult with export outcome
        """
        try:
            # Add metadata columns if provided
            if metadata:
                export_df = df.copy()
                for key, value in metadata.items():
                    export_df[f"meta_{key}"] = value
            else:
                export_df = df
            
            result = self.storage_adapter.save_data(export_df, destination)
            
            if result.success and metadata:
                result.message += f" (with metadata: {', '.join(metadata.keys())})"
            
            return result
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                message="Export failed",
                record_count=len(df) if df is not None else 0,
                errors=[f"Error: {str(e)}"]
            )