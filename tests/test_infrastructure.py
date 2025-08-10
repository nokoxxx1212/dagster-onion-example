import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from infrastructure.storage import (
    CsvStorageAdapter,
    JsonStorageAdapter, 
    StorageFactory,
    DataExporter
)
from domain.models import ProcessingResult


class TestCsvStorageAdapter:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = CsvStorageAdapter(self.temp_dir)
        
    def teardown_method(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_data_success(self):
        data = {
            "pageid": [1, 2, 3],
            "title": ["Page 1", "Page 2", "Page 3"]
        }
        df = pd.DataFrame(data)
        
        result = self.adapter.save_data(df, "test_pages.csv")
        
        assert result.success is True
        assert result.record_count == 3
        assert "saved to" in result.message.lower()
        
        # Check if file exists
        file_path = Path(self.temp_dir) / "test_pages.csv"
        assert file_path.exists()
    
    def test_save_data_empty_dataframe(self):
        df = pd.DataFrame()
        
        result = self.adapter.save_data(df, "empty.csv")
        
        assert result.success is False
        assert "empty DataFrame" in result.message
    
    def test_load_data_success(self):
        # First save some data
        data = {
            "pageid": [1, 2, 3],
            "title": ["Page 1", "Page 2", "Page 3"]
        }
        df = pd.DataFrame(data)
        self.adapter.save_data(df, "test_load.csv")
        
        # Then load it back
        loaded_df = self.adapter.load_data("test_load.csv")
        
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ["pageid", "title"]
        assert loaded_df.iloc[0]["title"] == "Page 1"
    
    def test_load_data_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.adapter.load_data("nonexistent.csv")


class TestJsonStorageAdapter:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = JsonStorageAdapter(self.temp_dir)
        
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_data_success(self):
        data = {
            "pageid": [1, 2, 3],
            "title": ["Page 1", "Page 2", "Page 3"]
        }
        df = pd.DataFrame(data)
        
        result = self.adapter.save_data(df, "test_pages.json")
        
        assert result.success is True
        assert result.record_count == 3
        
        # Check if file exists
        file_path = Path(self.temp_dir) / "test_pages.json"
        assert file_path.exists()
    
    def test_load_data_success(self):
        # First save some data
        data = {
            "pageid": [1, 2, 3],
            "title": ["Page 1", "Page 2", "Page 3"]
        }
        df = pd.DataFrame(data)
        self.adapter.save_data(df, "test_load.json")
        
        # Then load it back
        loaded_df = self.adapter.load_data("test_load.json")
        
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ["pageid", "title"]


class TestStorageFactory:
    
    def test_create_csv_adapter(self):
        adapter = StorageFactory.create_adapter("csv", "/tmp")
        assert isinstance(adapter, CsvStorageAdapter)
    
    def test_create_json_adapter(self):
        adapter = StorageFactory.create_adapter("json", "/tmp")
        assert isinstance(adapter, JsonStorageAdapter)
    
    def test_create_unsupported_adapter(self):
        with pytest.raises(ValueError):
            StorageFactory.create_adapter("xml", "/tmp")


class TestDataExporter:
    
    def setup_method(self):
        self.mock_adapter = Mock()
        self.exporter = DataExporter(self.mock_adapter)
    
    def test_export_with_metadata_success(self):
        data = {
            "pageid": [1, 2],
            "title": ["Page 1", "Page 2"]
        }
        df = pd.DataFrame(data)
        
        metadata = {"source": "test", "timestamp": "2023-01-01"}
        
        # Mock successful save
        self.mock_adapter.save_data.return_value = ProcessingResult(
            success=True,
            message="Data saved successfully",
            record_count=2
        )
        
        result = self.exporter.export_with_metadata(df, "test.csv", metadata)
        
        assert result.success is True
        assert "with metadata" in result.message
        
        # Verify adapter was called
        self.mock_adapter.save_data.assert_called_once()
        
        # Check that metadata was added
        call_args = self.mock_adapter.save_data.call_args
        exported_df = call_args[0][0]  # First argument (DataFrame)
        
        assert "meta_source" in exported_df.columns
        assert "meta_timestamp" in exported_df.columns
    
    def test_export_without_metadata(self):
        data = {
            "pageid": [1, 2],
            "title": ["Page 1", "Page 2"]
        }
        df = pd.DataFrame(data)
        
        # Mock successful save
        self.mock_adapter.save_data.return_value = ProcessingResult(
            success=True,
            message="Data saved successfully",
            record_count=2
        )
        
        result = self.exporter.export_with_metadata(df, "test.csv")
        
        assert result.success is True
        assert "with metadata" not in result.message
        
        # Verify adapter was called with original DataFrame
        call_args = self.mock_adapter.save_data.call_args
        exported_df = call_args[0][0]
        
        assert len(exported_df.columns) == 2  # No metadata columns added
    
    def test_export_adapter_failure(self):
        data = {"pageid": [1], "title": ["Page 1"]}
        df = pd.DataFrame(data)
        
        # Mock adapter failure
        self.mock_adapter.save_data.return_value = ProcessingResult(
            success=False,
            message="Save failed",
            errors=["Disk full"]
        )
        
        result = self.exporter.export_with_metadata(df, "test.csv")
        
        assert result.success is False